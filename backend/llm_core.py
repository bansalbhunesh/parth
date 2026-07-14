"""
LLM wrapper with an automatic, self-healing provider failover chain.

Headline order: gemini → Qwen / OpenAI-compatible gateway → Groq → Claude →
local Ollama → the deterministic rule engine (the always-present floor). `PRAMAAN_LLM`
still selects the *primary* provider; on quota/429, timeout, rate-limit, or any
provider failure the chain walks to the next *configured* provider. When every
LLM leg fails (or none is configured) an LLMError is raised and the callers
degrade to the deterministic rule engine. Failover is about **reliability and
availability, not accuracy**: eval labels, narration guards, and numeric
grounding are identical regardless of which model answers, and the rule floor
computes deviations from the actual documents — never seeded labels.

Configured providers only are attempted, so a Gemini-only deployment behaves
exactly as before (a one-element chain). The order is overridable with
PRAMAAN_LLM_PROVIDER_ORDER (comma-separated).

Env keys (canonical name first, older alias still honoured):
  gemini  GEMINI_API_KEY                          GEMINI_MODEL
  qwen    QWEN_GATEWAY_API_KEY  (or OPENAI_API_KEY)   QWEN_GATEWAY_BASE_URL /
          _MODEL  (or OPENAI_BASE_URL / OPENAI_MODEL)
  groq    GROQ_API_KEY                             GROQ_MODEL
  claude  CLAUDE_API_KEY        (or ANTHROPIC_API_KEY)  CLAUDE_MODEL
  ollama  (keyless) LOCAL_LLM_ENABLED=1            OLLAMA_BASE_URL / OLLAMA_MODEL

The Qwen gateway must be a genuinely separate provider/quota (e.g. OpenRouter),
NOT Google's OpenAI-compatible endpoint — pointing it at Google would make the
"backup" share Gemini's quota. /llm-check surfaces this (separate_quota=false).
No keys or secret-bearing base URLs are ever committed, logged, or exposed.
"""

import datetime
import json
import logging
import os
import re
import threading
import time

log = logging.getLogger("pramaan.llm")

PROVIDER = os.getenv("PRAMAAN_LLM", "gemini")  # primary provider id

# Canonical failover order. The primary (PRAMAAN_LLM) is tried first, then the
# rest of this list, skipping any provider that is not configured. Headline
# chain: gemini → Qwen/OpenAI-compatible gateway → Claude → local Ollama → the
# deterministic rule engine (the always-present floor). Groq (its own free-tier
# quota) sits between the gateway and Claude as an extra insurance leg the hosted
# demo already uses; it is filtered out automatically when GROQ_API_KEY is unset,
# so it never changes single-/dual-provider behaviour. Override the whole order
# with PRAMAAN_LLM_PROVIDER_ORDER (comma-separated, unknown names dropped).
_DEFAULT_ORDER = ["gemini", "openai", "groq", "claude", "ollama"]
_CHAIN_ORDER = _DEFAULT_ORDER  # back-compat alias; runtime uses _chain_order()

# Per-provider API-key env vars, in resolution order (first one set wins). The
# canonical Phase-4 names come first; older names are kept as back-compat aliases
# so a deployment already wired with OPENAI_*/ANTHROPIC_* keeps working unchanged.
# Ollama is keyless (a local daemon) — gated by LOCAL_LLM_ENABLED, not a key.
_KEY_ENVS = {
    "gemini": ["GEMINI_API_KEY"],
    "openai": ["QWEN_GATEWAY_API_KEY", "OPENAI_API_KEY"],
    "groq": ["GROQ_API_KEY"],
    "claude": ["CLAUDE_API_KEY", "ANTHROPIC_API_KEY"],
    "ollama": [],
}

# Friendly aliases accepted in PRAMAAN_LLM / PRAMAAN_LLM_PROVIDER_ORDER for the
# OpenAI-compatible gateway leg (its internal provider id is "openai").
_PROVIDER_ALIASES = {"qwen": "openai", "gateway": "openai"}

# Bounded retry for transient server-side failures (500/503/overloaded) on a
# single provider before it fails over. 429/quota is NOT transient and is never
# retried (see _is_transient). Env-configurable so tests can zero the backoff.
_TRANSIENT_RETRIES = int(os.getenv("LLM_TRANSIENT_RETRIES", "2"))
_RETRY_BACKOFF_S = float(os.getenv("LLM_RETRY_BACKOFF_S", "1.0"))

# Observability for /llm-check — which provider last answered, and the last
# failover with its (redacted) reason. Never stores secrets.
FAILOVER_STATUS = {
    "last_successful_provider": None,
    "last_failover": None,  # {"from", "to", "reason", "at"}
}


class LLMError(Exception):
    pass


# ── Per-provider hourly call budget (spend guard for paid legs) ──────────────
# A paid gateway leg (e.g. aicredits/OpenRouter) must not be drainable by demo
# abuse or a failover storm. Each provider can carry an hourly ATTEMPT budget:
# once exhausted, that leg raises LLMError and the chain walks on (next leg or
# the free rule floor) — availability degrades gracefully, spend is capped.
# Process-local sliding window (single-instance demo, same trade-off as the
# per-IP rate limiter in backend/security.py). 0 / unset = unlimited, so free
# legs and existing deployments behave exactly as before. Attempts (not just
# successes) are counted, conservatively.
_BUDGET_ENVS = {
    "gemini": ["GEMINI_BUDGET_PER_HOUR"],
    "openai": ["QWEN_GATEWAY_BUDGET_PER_HOUR", "OPENAI_BUDGET_PER_HOUR"],
    "groq": ["GROQ_BUDGET_PER_HOUR"],
    "claude": ["CLAUDE_BUDGET_PER_HOUR"],
    "ollama": ["OLLAMA_BUDGET_PER_HOUR"],
}
_BUDGET_WINDOW_S = 3600
_budget_calls: dict = {}   # provider -> [timestamps]
_budget_lock = threading.Lock()


def provider_budget(provider: str) -> int:
    """The configured hourly call budget for a provider (0 = unlimited)."""
    for name in _BUDGET_ENVS.get(provider, []):
        v = os.getenv(name, "").strip()
        if v.isdigit():
            return int(v)
    return 0


def _budget_spent(provider: str) -> int:
    now = time.time()
    with _budget_lock:
        hits = _budget_calls.setdefault(provider, [])
        hits[:] = [t for t in hits if t > now - _BUDGET_WINDOW_S]
        return len(hits)


def _budget_charge(provider: str) -> None:
    """Enforce + record one attempt against the provider's hourly budget.
    Raises LLMError (treated as a provider failure → failover) when the budget
    is exhausted. No-op for unlimited (0) budgets."""
    cap = provider_budget(provider)
    if cap <= 0:
        return
    now = time.time()
    with _budget_lock:
        hits = _budget_calls.setdefault(provider, [])
        hits[:] = [t for t in hits if t > now - _BUDGET_WINDOW_S]
        if len(hits) >= cap:
            raise LLMError(
                f"{provider} hourly call budget reached ({cap}/h) — spend guard; "
                "failing over")
        hits.append(now)


def reset_budgets() -> None:
    """Clear budget counters — used by the test suite between cases."""
    with _budget_lock:
        _budget_calls.clear()


def _env_first(*names: str, default=None):
    """First set (non-empty) value among env var `names`, else `default`."""
    for n in names:
        v = os.environ.get(n)
        if v:
            return v
    return default


def _truthy(v) -> bool:
    return str(v).strip().lower() in {"1", "true", "yes", "on"} if v is not None else False


def _key(provider: str):
    """The configured API-key value for a provider (first alias that is set), or
    None. Ollama is keyless, so this is always None for it."""
    return _env_first(*_KEY_ENVS.get(provider, []))


def _key_env(provider: str) -> str:
    """Canonical (preferred) key env var NAME for a provider — used only in
    human-readable messages, never to read a secret value."""
    names = _KEY_ENVS.get(provider, [])
    return names[0] if names else ""


def _resolve_alias(p: str) -> str:
    return _PROVIDER_ALIASES.get(p, p)


def _configured(provider: str) -> bool:
    """A provider is usable if its key is set — or, for keyless Ollama, if
    LOCAL_LLM_ENABLED is truthy."""
    if provider == "ollama":
        return _truthy(os.environ.get("LOCAL_LLM_ENABLED"))
    return bool(_key(provider))


def _chain_order() -> list[str]:
    """The failover order to attempt: PRAMAAN_LLM_PROVIDER_ORDER if set
    (comma-separated, unknown names dropped, `qwen`/`gateway` → the gateway
    leg), else the canonical default. Duplicates removed, first wins."""
    raw = os.getenv("PRAMAAN_LLM_PROVIDER_ORDER", "")
    wanted = ([p.strip().lower() for p in raw.split(",") if p.strip()]
              if raw.strip() else list(_DEFAULT_ORDER))
    seen, order = set(), []
    for p in wanted:
        p = _resolve_alias(p)
        if p in _KEY_ENVS and p not in seen:
            seen.add(p)
            order.append(p)
    return order


def provider_chain() -> list[str]:
    """Configured providers in priority order: the PRAMAAN_LLM primary first,
    then the remaining order (env-overridable), skipping any provider that is not
    configured. Single-key setups therefore behave exactly as before — a
    one-element chain — because every other leg is filtered out."""
    primary = _resolve_alias(os.getenv("PRAMAAN_LLM", "gemini").lower())
    order = _chain_order()
    ordered = ([primary] if primary in _KEY_ENVS else []) + [p for p in order if p != primary]
    seen, chain = set(), []
    for p in ordered:
        if p not in seen and _configured(p):
            seen.add(p)
            chain.append(p)
    return chain


def _redact(text: str) -> str:
    """Strip any configured API key value out of a string before it can reach
    a log line or an API response. Covers every provider's key aliases."""
    for provider in _KEY_ENVS:
        secret = _key(provider)
        if secret and secret in text:
            text = text.replace(secret, "***")
    return text


def _is_google_gateway(base_url) -> bool:
    """True if a gateway base URL points at Google's own endpoint — which would
    make the 'Qwen backup' share Gemini's quota instead of being a genuinely
    separate provider. Surfaced honestly in /llm-check rather than silently
    accepted."""
    if not base_url:
        return False
    b = str(base_url).lower()
    return "googleapis.com" in b or "generativelanguage" in b or "google.com" in b


def _gateway_base_url():
    return _env_first("QWEN_GATEWAY_BASE_URL", "OPENAI_BASE_URL")


def _gateway_model():
    # Default matches the documented .env.example gateway model — the same
    # model the frozen ps4_external_v1 benchmark was measured on.
    return _env_first("QWEN_GATEWAY_MODEL", "OPENAI_MODEL",
                      default="google/gemini-3.1-flash-lite")


def _ollama_base() -> str:
    return os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")


def _is_transient(exc) -> bool:
    """True for transient server-side errors worth a quick retry — free-tier
    models routinely return 503 'high demand'. NOT 429 (quota): retrying an
    exhausted daily cap just wastes time."""
    s = str(exc).lower()
    return "503" in s or "unavailable" in s or "overloaded" in s or "internal" in s


def _with_transient_retry(call, label):
    """Run `call`, retrying up to `_TRANSIENT_RETRIES` times on transient
    server-side errors (500/503/overloaded) with exponential backoff. 429/quota
    is not transient and is never retried — it fails straight through so the
    chain can fail over to the next provider or the rule floor."""
    for attempt in range(_TRANSIENT_RETRIES + 1):
        try:
            return call()
        except Exception as exc:  # noqa: BLE001
            if attempt < _TRANSIENT_RETRIES and _is_transient(exc):
                delay = _RETRY_BACKOFF_S * (2 ** attempt)
                log.warning("%s transient error (%s) — retry %d/%d in %.1fs",
                            label, str(exc)[:80], attempt + 1, _TRANSIENT_RETRIES, delay)
                time.sleep(delay)
                continue
            raise


def _json_string_state(char: str, in_string: bool, escaped: bool) -> tuple[bool, bool, bool]:
    """Return ``(in_string, escaped, handled)`` for one JSON character."""
    if not in_string:
        starts_string = char == '"'
        return starts_string, False, starts_string
    if escaped:
        return True, False, True
    if char == "\\":
        return True, True, True
    if char == '"':
        return False, False, True
    return True, False, True


def _salvage_json_objects(text: str) -> list:
    """Best-effort recovery of the complete top-level ``{...}`` objects from a
    truncated or partially-malformed JSON array — e.g. a reasoning model that
    exhausted its output budget mid-array. String-aware (braces inside string
    values do not miscount), it returns the objects that parse and silently
    drops a trailing truncated one. Called only after a strict parse fails, so
    well-formed payloads are never affected."""
    objs, depth, start = [], 0, None
    in_str = esc = False
    for k, c in enumerate(text):
        in_str, esc, handled = _json_string_state(c, in_str, esc)
        if handled:
            continue
        if c == "{":
            if depth == 0:
                start = k
            depth += 1
        elif c == "}":
            if depth > 0:
                depth -= 1
                if depth == 0 and start is not None:
                    try:
                        objs.append(json.loads(text[start : k + 1]))
                    except (ValueError, TypeError):
                        pass
                    start = None
    return objs


def _balanced_json(text: str, offset: int, opening: str, closing: str):
    depth = 0
    for index in range(offset, len(text)):
        if text[index] == opening:
            depth += 1
        elif text[index] == closing:
            depth -= 1
            if depth == 0:
                return json.loads(text[offset : index + 1])
    return None


def _extract_json(text: str):
    text = text.strip()
    text = re.sub(r"^```(?:json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    try:
        for start, end in [("[", "]"), ("{", "}")]:
            i = text.find(start)
            if i == -1:
                continue
            parsed = _balanced_json(text, i, start, end)
            if parsed is not None:
                return parsed
            # An opening "[" that never closes is a truncated array: salvage the
            # complete objects instead of letting the "{" branch return only the
            # first one.
            if start == "[":
                salvaged = _salvage_json_objects(text[i:])
                if salvaged:
                    return salvaged
        return json.loads(text)
    except (ValueError, TypeError):
        # Truncated/malformed payload (e.g. a reasoning model that ran out of
        # output budget mid-array): salvage the complete objects rather than
        # dropping the whole reconcile to the rule floor.
        salvaged = _salvage_json_objects(text)
        if salvaged:
            return salvaged
        raise


_DISPATCH = {}  # populated after the per-provider functions are defined


def _record_success(provider: str) -> None:
    FAILOVER_STATUS["last_successful_provider"] = provider


def _record_failover(frm: str, to: str, reason: str) -> None:
    FAILOVER_STATUS["last_failover"] = {
        "from": frm,
        "to": to,
        "reason": _redact(str(reason))[:200],
        "at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
