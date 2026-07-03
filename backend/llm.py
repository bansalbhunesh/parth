"""
LLM wrapper with an automatic provider failover chain.

Priority order: gemini-2.5-flash → OpenAI-compatible gateway (e.g. Qwen) →
Claude. `PRAMAAN_LLM` still selects the *primary* provider; on quota/429,
timeouts, or any provider failure the chain walks to the next *configured*
provider. When every provider fails (or none is configured) an LLMError is
raised and the callers degrade to the deterministic rule engine — the safe
floor. Failover is about reliability, not accuracy: eval labels, narration
guards, and numeric grounding are identical regardless of which model answers.

Set GEMINI_API_KEY (and optionally OPENAI_API_KEY[+OPENAI_BASE_URL/MODEL],
ANTHROPIC_API_KEY). No keys are committed, logged, or exposed.
"""

import datetime
import json
import logging
import os
import re
import time

log = logging.getLogger("pramaan.llm")

PROVIDER = os.getenv("PRAMAAN_LLM", "gemini")  # "gemini" | "claude" | "openai"

# Canonical failover order (primary is tried first, then the rest of this
# list, skipping anything without a key configured).
_CHAIN_ORDER = ["gemini", "openai", "claude"]

# Observability for /llm-check — which provider last answered, and the last
# failover with its (redacted) reason. Never stores secrets.
FAILOVER_STATUS = {
    "last_successful_provider": None,
    "last_failover": None,  # {"from", "to", "reason", "at"}
}


class LLMError(Exception):
    pass


def _key_env(provider: str) -> str:
    return {"gemini": "GEMINI_API_KEY", "openai": "OPENAI_API_KEY",
            "claude": "ANTHROPIC_API_KEY"}[provider]


def _configured(provider: str) -> bool:
    return bool(os.environ.get(_key_env(provider)))


def provider_chain() -> list[str]:
    """Configured providers in priority order: the PRAMAAN_LLM primary first,
    then the remaining canonical order. Single-key setups therefore behave
    exactly as before — a one-element chain."""
    primary = os.getenv("PRAMAAN_LLM", "gemini")
    ordered = [primary] + [p for p in _CHAIN_ORDER if p != primary]
    return [p for p in ordered if p in _CHAIN_ORDER and _configured(p)]


def _redact(text: str) -> str:
    """Strip any configured API key value out of a string before it can reach
    a log line or an API response."""
    for provider in _CHAIN_ORDER:
        secret = os.environ.get(_key_env(provider))
        if secret and secret in text:
            text = text.replace(secret, "***")
    return text


def _is_transient(exc) -> bool:
    """True for transient server-side errors worth a quick retry — free-tier
    models routinely return 503 'high demand'. NOT 429 (quota): retrying an
    exhausted daily cap just wastes time."""
    s = str(exc).lower()
    return "503" in s or "unavailable" in s or "overloaded" in s or "internal" in s


def _extract_json(text: str):
    text = text.strip()
    text = re.sub(r"^```(?:json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
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
    return json.loads(text)


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
    raw = complete(prompt, system, json_mode=True)
    try:
        return _extract_json(raw)
    except (json.JSONDecodeError, ValueError) as exc:
        log.error("JSON extraction failed: %s — raw[:200]: %s", exc, raw[:200])
        raise LLMError(f"LLM returned unparseable JSON: {exc}") from exc


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


def _openai(prompt, system, json_mode):
    """OpenAI-compatible provider — works with any /v1 gateway (e.g. an
    aggregator that proxies Gemini/Claude). Set OPENAI_API_KEY, OPENAI_BASE_URL
    (the gateway's /v1 root), and OPENAI_MODEL (e.g. gemini-2.0-flash)."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise LLMError("OPENAI_API_KEY not set")
    base_url = os.getenv("OPENAI_BASE_URL") or None
    model_name = os.getenv("OPENAI_MODEL", "gemini-2.0-flash")
    log.info("OpenAI-compat call: model=%s, base=%s, json_mode=%s, prompt_len=%d",
             model_name, base_url, json_mode, len(prompt))
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url=base_url)
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        # Cap output generously: gateways (OpenRouter etc.) often default to a
        # small max_tokens, which silently truncates a multi-finding reconcile
        # JSON mid-array and makes it unparseable. Match the Claude budget.
        kwargs = {"model": model_name, "messages": messages, "temperature": 0.1,
                  "max_tokens": int(os.getenv("OPENAI_MAX_TOKENS", "4000"))}
        if json_mode and os.getenv("OPENAI_JSON_MODE", "0") == "1":
            kwargs["response_format"] = {"type": "json_object"}
        resp = client.chat.completions.create(**kwargs)
        return resp.choices[0].message.content
    except Exception as exc:
        log.error("OpenAI-compat API error: %s", exc)
        raise LLMError(f"OpenAI-compatible API call failed: {exc}") from exc


def _claude(prompt, system, json_mode):
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise LLMError("ANTHROPIC_API_KEY not set")
    log.info("Claude call: prompt_len=%d", len(prompt))
    try:
        import anthropic
        client = anthropic.Anthropic()
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


def _openai_stream(prompt, system):
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise LLMError("OPENAI_API_KEY not set")
    base_url = os.getenv("OPENAI_BASE_URL") or None
    model_name = os.getenv("OPENAI_MODEL", "gemini-2.0-flash")
    log.info("OpenAI-compat stream: model=%s, base=%s, prompt_len=%d",
             model_name, base_url, len(prompt))
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url=base_url)
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        stream = client.chat.completions.create(
            model=model_name, messages=messages, temperature=0.1, stream=True,
            max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "4000")),
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
    except Exception as exc:
        log.error("OpenAI-compat stream error: %s", exc)
        raise LLMError(f"OpenAI-compatible streaming failed: {exc}") from exc


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
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise LLMError("ANTHROPIC_API_KEY not set")
    log.info("Claude stream: prompt_len=%d", len(prompt))
    try:
        import anthropic
        client = anthropic.Anthropic()
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
_DISPATCH = {"gemini": _gemini, "openai": _openai, "claude": _claude}
_STREAM_DISPATCH = {
    "gemini": _gemini_stream,
    "openai": _openai_stream,
    "claude": _claude_stream,
}


def _provider_public_meta(provider: str) -> dict:
    """Non-secret descriptor of a provider's configuration for /llm-check.
    Reports which model/base is configured — never the key value."""
    if provider == "gemini":
        return {"model": os.getenv("GEMINI_MODEL", "gemini-2.5-flash")}
    if provider == "openai":
        return {"model": os.getenv("OPENAI_MODEL", "gemini-2.0-flash"),
                "base_url_set": bool(os.getenv("OPENAI_BASE_URL"))}
    return {"model": os.getenv("CLAUDE_MODEL", "claude-opus-4-8")}


def failover_report() -> dict:
    """Structured, secret-free view of the failover chain for /llm-check:
    configured providers in priority order, each provider's non-secret config,
    the last provider that answered, the last failover reason, and whether the
    system currently has any LLM at all (else it runs on the rule-engine floor)."""
    chain = provider_chain()
    return {
        "primary": os.getenv("PRAMAAN_LLM", "gemini"),
        "chain": chain,
        "providers": {p: {"configured": _configured(p), **_provider_public_meta(p)}
                      for p in _CHAIN_ORDER},
        "last_successful_provider": FAILOVER_STATUS["last_successful_provider"],
        "last_failover": FAILOVER_STATUS["last_failover"],
        "on_rule_engine_floor": len(chain) == 0,
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
