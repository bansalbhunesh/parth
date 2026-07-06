"""
LLM wrapper with an automatic, self-healing provider failover chain.

Headline order: gemini → Qwen / OpenAI-compatible gateway → Claude → local
Ollama → the deterministic rule engine (the always-present floor). `PRAMAAN_LLM`
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
    return _env_first("QWEN_GATEWAY_MODEL", "OPENAI_MODEL", default="gemini-2.0-flash")


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
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
            continue
        if c == '"':
            in_str = True
        elif c == "{":
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


def _extract_json(text: str):
    text = text.strip()
    text = re.sub(r"^```(?:json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    try:
        for start, end in [("[", "]"), ("{", "}")]:
            i = text.find(start)
            if i == -1:
                continue
            depth, j = 0, i
            while j < len(text):
                if text[j] == start:
                    depth += 1
                elif text[j] == end:
                    depth -= 1
                    if depth == 0:
                        return json.loads(text[i : j + 1])
                j += 1
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


def complete(prompt: str, system: str = "", json_mode: bool = True) -> str:
    """Complete against the first configured provider in the failover chain,
    walking to the next provider on any failure (quota/429, timeout, transient,
    or LLMError). Raises LLMError only when every configured provider fails —
    the callers then degrade to the deterministic template/rule engine.

    With a single provider configured this is exactly the old behaviour: a
    one-element chain, one attempt, the same LLMError on failure."""
    chain = provider_chain()
    if not chain:
        raise LLMError("No LLM provider configured (set GEMINI_API_KEY, "
                       "OPENAI_API_KEY, or ANTHROPIC_API_KEY)")
    last_exc = None
    for i, provider in enumerate(chain):
        try:
            result = _DISPATCH[provider](prompt, system, json_mode)
            if i > 0:
                _record_failover(chain[i - 1], provider,
                                 last_exc or "previous provider failed")
                log.info("Provider failover succeeded on %s (after %s)",
                         provider, chain[i - 1])
            _record_success(provider)
            return result
        except Exception as exc:  # noqa: BLE001 — try the next provider
            last_exc = _redact(str(exc))[:200]
            nxt = chain[i + 1] if i + 1 < len(chain) else "rule-engine floor"
            log.warning("Provider %s failed (%s) — falling back to %s",
                        provider, last_exc, nxt)
    raise LLMError(f"All {len(chain)} configured provider(s) failed; "
                   f"last error: {last_exc}")


def complete_json(prompt: str, system: str = ""):
    """JSON completion over the failover chain, with the JSON extraction INSIDE
    each per-provider attempt: a provider that returns an empty or unparseable
    response (safety block, thinking-budget exhaustion yielding no text, gateway
    truncation the salvager can't recover) counts as THAT PROVIDER failing, and
    the chain walks on to the next configured provider.

    Found live 2026-07-06: the sync /analyze path intermittently dropped to the
    rule floor in ~3s while /analyze/stream succeeded on the same input —
    Gemini's JSON-mode response for the largest pair came back empty/unparseable,
    and the old two-step (complete() first, parse after) treated that as a
    terminal error, never trying the healthy Groq leg. Raises LLMError only when
    every configured provider fails to produce parseable JSON."""
    chain = provider_chain()
    if not chain:
        raise LLMError("No LLM provider configured (set GEMINI_API_KEY, "
                       "OPENAI_API_KEY, or ANTHROPIC_API_KEY)")
    last_exc = None
    for i, provider in enumerate(chain):
        try:
            raw = _DISPATCH[provider](prompt, system, True)
            if raw is None or not str(raw).strip():
                raise LLMError("provider returned an empty response")
            result = _extract_json(raw)
            if i > 0:
                _record_failover(chain[i - 1], provider,
                                 last_exc or "previous provider failed")
                log.info("JSON failover succeeded on %s (after %s)",
                         provider, chain[i - 1])
            _record_success(provider)
            return result
        except Exception as exc:  # noqa: BLE001 — try the next provider
            last_exc = _redact(str(exc))[:200]
            nxt = chain[i + 1] if i + 1 < len(chain) else "rule-engine floor"
            log.warning("Provider %s failed JSON completion (%s) — falling "
                        "back to %s", provider, last_exc, nxt)
    raise LLMError(f"All {len(chain)} configured provider(s) failed to return "
                   f"parseable JSON; last error: {last_exc}")


def _openai_compatible_vision(prompt, image_bytes, mime_type, system, *, label,
                              api_key, base_url, model, max_tokens):
    """Multimodal reasoning over an OpenAI-compatible /v1 gateway (e.g. aicredits
    or OpenRouter proxying a multimodal model such as gemini-2.5-flash). The
    image is passed inline as a base64 data URI in an image_url content part."""
    if not api_key:
        raise LLMError(f"{label} vision API key not set")
    import base64
    data_uri = f"data:{mime_type};base64,{base64.b64encode(image_bytes).decode()}"
    log.info("%s vision call: model=%s, image_bytes=%d, prompt_len=%d",
             label, model, len(image_bytes), len(prompt))
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url=base_url or None)
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": data_uri}},
        ]})
        return _with_transient_retry(
            lambda: client.chat.completions.create(
                model=model, messages=messages, temperature=0.1, max_tokens=max_tokens
            ).choices[0].message.content, label)
    except Exception as exc:
        log.error("%s vision error: %s", label, exc)
        raise LLMError(f"{label} vision call failed: {exc}") from exc


def complete_vision(prompt: str, image_bytes: bytes, mime_type: str,
                    system: str = "") -> str:
    """Reason over an IMAGE + prompt. Multimodal only: Gemini natively, or an
    OpenAI-compatible multimodal gateway when `PRAMAAN_LLM=openai` (the Groq leg
    is text). No text-model failover applies — if the multimodal provider is
    unreachable this raises LLMError and the caller degrades to the
    deterministic engine (which reads the text layer / OCR). Vision is a
    capability we prove on real documents, not a live demo crutch."""
    if os.getenv("PRAMAAN_LLM", "gemini") == "openai" and os.environ.get("OPENAI_API_KEY"):
        return _openai_compatible_vision(
            prompt, image_bytes, mime_type, system, label="OpenAI-compat",
            api_key=os.environ.get("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL"),
            model=os.getenv("OPENAI_VISION_MODEL", os.getenv("OPENAI_MODEL", "gemini-2.0-flash")),
            max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "4000")))
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise LLMError("Vision requires GEMINI_API_KEY (the only multimodal provider)")
    model_name = os.getenv("GEMINI_VISION_MODEL", os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))
    log.info("Gemini vision call: model=%s, image_bytes=%d, prompt_len=%d",
             model_name, len(image_bytes), len(prompt))
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        image_part = genai.types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        config = genai.types.GenerateContentConfig(
            temperature=0.1,
            system_instruction=system or None,
            response_mime_type="application/json",
        )
        for attempt in range(3):
            try:
                resp = client.models.generate_content(
                    model=model_name, contents=[image_part, prompt], config=config,
                )
                return resp.text
            except Exception as exc:
                if _is_transient(exc) and attempt < 2:
                    time.sleep(1.5 * (attempt + 1))
                    continue
                raise
    except Exception as exc:
        log.error("Gemini vision error: %s", _redact(str(exc)))
        raise LLMError(f"Gemini vision call failed: {_redact(str(exc))}") from exc


_NUM_RE = re.compile(r"\d+(?:\.\d+)?")


def numbers_grounded(prose: str, source: str) -> bool:
    """True iff every numeric token in `prose` also appears verbatim in `source`.
    The narrate() engines tell the LLM to quote only the computed figures; this
    catches a model that invents or re-rounds a number anyway (e.g. restating
    a delivery-risk of 61.9 as '62'), so an ungrounded figure never reaches a
    judge. Conservative by design: a legitimate re-rounding also fails and we
    fall back to the always-correct template."""
    allowed = set(_NUM_RE.findall(source))
    return all(tok in allowed for tok in _NUM_RE.findall(prose))


def restate(template: str, instruction: str, system: str) -> dict:
    """Ask the LLM to restate `template` more fluently for a briefing, but fall
    back to the template verbatim if the LLM is unreachable, returns nothing, or
    introduces any number absent from `template`. Returns {narrative, mode} where
    mode is 'llm' only when the restatement is number-grounded."""
    try:
        prose = complete(
            f"Numbers (quote ONLY these, invent nothing): {template}\n{instruction}",
            system=system, json_mode=False,
        ).strip()
    except Exception:
        return {"narrative": template, "mode": "rule-based-fallback"}
    if prose and numbers_grounded(prose, template):
        return {"narrative": prose, "mode": "llm"}
    return {"narrative": template, "mode": "rule-based-fallback"}


def _gemini(prompt, system, json_mode):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise LLMError("GEMINI_API_KEY not set")
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    log.info("Gemini call: model=%s, json_mode=%s, prompt_len=%d",
             model_name, json_mode, len(prompt))
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        config = genai.types.GenerateContentConfig(
            temperature=0.1,
            system_instruction=system or None,
            response_mime_type="application/json" if json_mode else "text/plain",
        )
        for attempt in range(3):  # 1 try + 2 retries on transient 503/overload
            try:
                resp = client.models.generate_content(
                    model=model_name, contents=prompt, config=config,
                )
                return resp.text
            except Exception as exc:
                if _is_transient(exc) and attempt < 2:
                    log.warning("Gemini transient error (attempt %d/3), retrying: %s",
                                attempt + 1, str(exc)[:100])
                    time.sleep(1.5 * (attempt + 1))
                    continue
                raise
    except Exception as exc:
        log.error("Gemini API error: %s", exc)
        raise LLMError(f"Gemini API call failed: {exc}") from exc


def _openai_compatible(prompt, system, json_mode, *, label, api_key, base_url,
                       model, json_mode_on, max_tokens):
    """Shared OpenAI-compatible chat call — used by both the generic gateway
    (OpenRouter/Qwen) and Groq, which speak the same /v1 protocol. `label` is
    only for logs; secrets are never logged."""
    if not api_key:
        raise LLMError(f"{label} API key not set")
    log.info("%s call: model=%s, base=%s, json_mode=%s, prompt_len=%d",
             label, model, base_url, json_mode, len(prompt))
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url=base_url or None)
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        # Cap output generously: gateways often default to a small max_tokens,
        # which silently truncates a multi-finding reconcile JSON mid-array and
        # makes it unparseable. Match the Claude budget.
        kwargs = {"model": model, "messages": messages, "temperature": 0.1,
                  "max_tokens": max_tokens}
        if json_mode and json_mode_on:
            kwargs["response_format"] = {"type": "json_object"}
        return _with_transient_retry(
            lambda: client.chat.completions.create(**kwargs).choices[0].message.content,
            label)
    except Exception as exc:
        log.error("%s API error: %s", label, exc)
        raise LLMError(f"{label} API call failed: {exc}") from exc


def _openai(prompt, system, json_mode):
    """Qwen / OpenAI-compatible gateway — any /v1 endpoint (e.g. OpenRouter
    proxying Qwen). Canonical env: QWEN_GATEWAY_API_KEY, QWEN_GATEWAY_BASE_URL
    (the /v1 root), QWEN_GATEWAY_MODEL (older OPENAI_* names still honoured).
    Must be a genuinely separate provider/quota — NOT Google's OpenAI endpoint."""
    return _openai_compatible(
        prompt, system, json_mode, label="Qwen-gateway",
        api_key=_key("openai"),
        base_url=_gateway_base_url(),
        model=_gateway_model(),
        json_mode_on=_env_first("QWEN_GATEWAY_JSON_MODE", "OPENAI_JSON_MODE",
                                default="0") == "1",
        max_tokens=int(_env_first("QWEN_GATEWAY_MAX_TOKENS", "OPENAI_MAX_TOKENS",
                                  default="4000")))


def _groq(prompt, system, json_mode):
    """Groq — fast LPU inference on its own free-tier quota (full-insurance
    second fallback). Uses Groq's OpenAI-compatible endpoint. Set GROQ_API_KEY;
    GROQ_MODEL defaults to llama-3.3-70b-versatile."""
    return _openai_compatible(
        prompt, system, json_mode, label="Groq",
        api_key=os.environ.get("GROQ_API_KEY"),
        base_url=os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1"),
        model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        json_mode_on=os.getenv("GROQ_JSON_MODE", "1") == "1",
        max_tokens=int(os.getenv("GROQ_MAX_TOKENS", "4000")))


def _ollama(prompt, system, json_mode):
    """Local Ollama via its OpenAI-compatible /v1 endpoint. Keyless (a local
    daemon), so it needs no network quota — the last LLM leg before the
    deterministic rule floor, keeping the demo answering even fully offline.
    Gated by LOCAL_LLM_ENABLED. Set OLLAMA_BASE_URL (default
    http://localhost:11434) and OLLAMA_MODEL (must be pulled locally)."""
    if not _truthy(os.environ.get("LOCAL_LLM_ENABLED")):
        raise LLMError("Local LLM disabled (set LOCAL_LLM_ENABLED=1)")
    return _openai_compatible(
        prompt, system, json_mode, label="Ollama",
        api_key="ollama",  # local endpoint ignores it, but the client needs one
        base_url=f"{_ollama_base()}/v1",
        model=os.getenv("OLLAMA_MODEL", "llama3.1"),
        json_mode_on=os.getenv("OLLAMA_JSON_MODE", "1") == "1",
        max_tokens=int(os.getenv("OLLAMA_MAX_TOKENS", "4000")))


def _claude(prompt, system, json_mode):
    api_key = _key("claude")
    if not api_key:
        raise LLMError("Claude API key not set (CLAUDE_API_KEY or ANTHROPIC_API_KEY)")
    log.info("Claude call: prompt_len=%d", len(prompt))
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model=os.getenv("CLAUDE_MODEL", "claude-opus-4-8"),
            max_tokens=2000,
            temperature=0.1,
            system=system or None,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text
    except Exception as exc:
        log.error("Claude API error: %s", exc)
        raise LLMError(f"Claude API call failed: {exc}") from exc


_STREAM_DISPATCH = {}  # populated after the per-provider stream functions


def complete_stream(prompt: str, system: str = ""):
    """Stream from the failover chain. A provider that fails *before emitting
    any token* is skipped in favour of the next; once a provider has yielded
    output we do not switch mid-stream (that would duplicate text to the
    judge), so a rare mid-stream failure surfaces to the caller, which then
    degrades to the rule engine. Single-provider setups stream exactly as
    before."""
    chain = provider_chain()
    if not chain:
        raise LLMError("No LLM provider configured (set GEMINI_API_KEY, "
                       "OPENAI_API_KEY, or ANTHROPIC_API_KEY)")
    last_exc = None
    for i, provider in enumerate(chain):
        emitted = False
        try:
            for chunk in _STREAM_DISPATCH[provider](prompt, system):
                emitted = True
                yield chunk
            if i > 0:
                _record_failover(chain[i - 1], provider,
                                 last_exc or "previous provider failed")
            _record_success(provider)
            return
        except Exception as exc:  # noqa: BLE001
            last_exc = _redact(str(exc))[:200]
            if emitted:
                log.error("Provider %s failed mid-stream (%s) — no safe "
                          "failover; degrading to rule engine", provider, last_exc)
                raise LLMError(f"Streaming failed mid-response on {provider}: "
                               f"{last_exc}") from exc
            nxt = chain[i + 1] if i + 1 < len(chain) else "rule-engine floor"
            log.warning("Provider %s stream failed pre-emit (%s) — falling "
                        "back to %s", provider, last_exc, nxt)
    raise LLMError(f"All {len(chain)} configured provider(s) failed to stream; "
                   f"last error: {last_exc}")


def _openai_compatible_stream(prompt, system, *, label, api_key, base_url,
                              model, max_tokens):
    if not api_key:
        raise LLMError(f"{label} API key not set")
    log.info("%s stream: model=%s, base=%s, prompt_len=%d",
             label, model, base_url, len(prompt))
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url=base_url or None)
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        stream = client.chat.completions.create(
            model=model, messages=messages, temperature=0.1, stream=True,
            max_tokens=max_tokens,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
    except Exception as exc:
        log.error("%s stream error: %s", label, exc)
        raise LLMError(f"{label} streaming failed: {exc}") from exc


def _openai_stream(prompt, system):
    yield from _openai_compatible_stream(
        prompt, system, label="Qwen-gateway",
        api_key=_key("openai"),
        base_url=_gateway_base_url(),
        model=_gateway_model(),
        max_tokens=int(_env_first("QWEN_GATEWAY_MAX_TOKENS", "OPENAI_MAX_TOKENS",
                                  default="4000")))


def _ollama_stream(prompt, system):
    if not _truthy(os.environ.get("LOCAL_LLM_ENABLED")):
        raise LLMError("Local LLM disabled (set LOCAL_LLM_ENABLED=1)")
    yield from _openai_compatible_stream(
        prompt, system, label="Ollama",
        api_key="ollama",  # local endpoint ignores it, but the client needs one
        base_url=f"{_ollama_base()}/v1",
        model=os.getenv("OLLAMA_MODEL", "llama3.1"),
        max_tokens=int(os.getenv("OLLAMA_MAX_TOKENS", "4000")))


def _groq_stream(prompt, system):
    yield from _openai_compatible_stream(
        prompt, system, label="Groq",
        api_key=os.environ.get("GROQ_API_KEY"),
        base_url=os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1"),
        model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        max_tokens=int(os.getenv("GROQ_MAX_TOKENS", "4000")))


def _gemini_stream(prompt, system):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise LLMError("GEMINI_API_KEY not set")
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    log.info("Gemini stream: model=%s, prompt_len=%d", model_name, len(prompt))
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        config = genai.types.GenerateContentConfig(
            temperature=0.1,
            system_instruction=system or None,
            response_mime_type="text/plain",
        )
        for chunk in client.models.generate_content_stream(
            model=model_name, contents=prompt, config=config,
        ):
            if chunk.text:
                yield chunk.text
    except Exception as exc:
        log.error("Gemini stream error: %s", exc)
        raise LLMError(f"Gemini streaming failed: {exc}") from exc


def _claude_stream(prompt, system):
    api_key = _key("claude")
    if not api_key:
        raise LLMError("Claude API key not set (CLAUDE_API_KEY or ANTHROPIC_API_KEY)")
    log.info("Claude stream: prompt_len=%d", len(prompt))
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        with client.messages.stream(
            model=os.getenv("CLAUDE_MODEL", "claude-opus-4-8"),
            max_tokens=2000,
            temperature=0.1,
            system=system or None,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            for text in stream.text_stream:
                yield text
    except Exception as exc:
        log.error("Claude stream error: %s", exc)
        raise LLMError(f"Claude streaming failed: {exc}") from exc


# --- Dispatch registration (after the provider functions exist) -------------
_DISPATCH = {"gemini": _gemini, "openai": _openai, "groq": _groq,
             "claude": _claude, "ollama": _ollama}
_STREAM_DISPATCH = {
    "gemini": _gemini_stream,
    "openai": _openai_stream,
    "groq": _groq_stream,
    "claude": _claude_stream,
    "ollama": _ollama_stream,
}


def _provider_public_meta(provider: str) -> dict:
    """Non-secret descriptor of a provider's configuration for /llm-check.
    Reports which model/base is configured — never the key value."""
    if provider == "gemini":
        return {"model": os.getenv("GEMINI_MODEL", "gemini-2.5-flash")}
    if provider == "openai":
        base = _gateway_base_url()
        # separate_quota is the honest check that the "Qwen backup" is a real,
        # independent provider — false if it points at Google's own endpoint
        # (which would just re-spend Gemini's quota) or has no base URL set.
        return {"model": _gateway_model(),
                "base_url_set": bool(base),
                "separate_quota": bool(base) and not _is_google_gateway(base)}
    if provider == "groq":
        return {"model": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")}
    if provider == "ollama":
        return {"model": os.getenv("OLLAMA_MODEL", "llama3.1"),
                "base_url": _ollama_base(), "local": True}
    return {"model": os.getenv("CLAUDE_MODEL", "claude-opus-4-8")}


def failover_report() -> dict:
    """Structured, secret-free view of the failover chain for /llm-check:
    the resolved provider order, the configured subset actually tried (chain),
    each provider's non-secret config, the last provider that answered, the last
    failover reason, whether the system currently has any LLM at all, and that
    the deterministic rule engine is always available as the floor."""
    chain = provider_chain()
    order = _chain_order()
    return {
        "primary": _resolve_alias(os.getenv("PRAMAAN_LLM", "gemini").lower()),
        "order": order,
        "chain": chain,
        "providers": {p: {"configured": _configured(p), **_provider_public_meta(p)}
                      for p in order},
        "last_successful_provider": FAILOVER_STATUS["last_successful_provider"],
        "last_failover": FAILOVER_STATUS["last_failover"],
        "on_rule_engine_floor": len(chain) == 0,
        # The rule engine is always compiled in, so an answer is always available
        # even when every LLM leg fails. Reliability, not accuracy: the floor is
        # deterministic and intentionally conservative — never seeded labels.
        "deterministic_fallback_available": True,
    }


def probe_provider(provider: str) -> dict:
    """Make one tiny real call to a single provider and report the outcome.
    Secret-free. Used by /llm-check?deep is separate — this is the per-provider
    health used to show the chain's live state."""
    if not _configured(provider):
        return {"provider": provider, "configured": False, "ok": False}
    try:
        out = _DISPATCH[provider]("Reply with the single word: ok", "", False)
        return {"provider": provider, "configured": True, "ok": True,
                "sample": _redact((out or "").strip())[:40]}
    except Exception as exc:  # noqa: BLE001
        return {"provider": provider, "configured": True, "ok": False,
                "error": _redact(str(exc))[:200]}
