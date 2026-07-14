"""Provider-neutral LLM orchestration and failover policy."""

from __future__ import annotations

import logging
import os
import re
import time

from backend import llm_core as _core
from backend.llm_core import (
    FAILOVER_STATUS,
    LLMError,
    _budget_charge,
    _budget_spent,
    _chain_order,
    _configured,
    _extract_json,
    _gateway_base_url,
    _gateway_model,
    _is_google_gateway,
    _is_transient,
    _ollama_base,
    _record_failover,
    _record_success,
    _redact,
    _resolve_alias,
    provider_budget,
    provider_chain,
)
from backend.llm_providers import (
    _claude,
    _claude_stream,
    _gemini,
    _gemini_stream,
    _groq,
    _groq_stream,
    _ollama,
    _ollama_stream,
    _openai,
    _openai_compatible_vision,
    _openai_stream,
)

log = logging.getLogger("pramaan.llm")

# Compatibility surface for callers and tests that imported the original
# single-module helpers. State remains owned by llm_core.
PROVIDER = _core.PROVIDER
reset_budgets = _core.reset_budgets
_key = _core._key
_key_env = _core._key_env
_truthy = _core._truthy
_RETRY_BACKOFF_S = _core._RETRY_BACKOFF_S


def _with_transient_retry(call, label):  # noqa: ANN001, ANN201
    previous = _core._RETRY_BACKOFF_S
    _core._RETRY_BACKOFF_S = _RETRY_BACKOFF_S
    try:
        return _core._with_transient_retry(call, label)
    finally:
        _core._RETRY_BACKOFF_S = previous

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
            _budget_charge(provider)  # spend guard: exhausted budget == leg failure
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
            _budget_charge(provider)  # spend guard: exhausted budget == leg failure
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

def complete_vision(prompt: str, image_bytes: bytes, mime_type: str,
                    system: str = "") -> str:
    """Reason over an IMAGE + prompt. Multimodal only: Gemini natively, or an
    OpenAI-compatible multimodal gateway when `PRAMAAN_LLM=openai` (the Groq leg
    is text). No text-model failover applies — if the multimodal provider is
    unreachable this raises LLMError and the caller degrades to the
    deterministic engine (which reads the text layer / OCR). Vision is a
    capability we prove on real documents, not a live demo crutch."""
    if os.getenv("PRAMAAN_LLM", "gemini") == "openai" and os.environ.get("OPENAI_API_KEY"):
        _budget_charge("openai")  # spend guard applies to vision calls too
        return _openai_compatible_vision(
            prompt, image_bytes, mime_type, system, label="OpenAI-compat",
            api_key=os.environ.get("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL"),
            model=os.getenv("OPENAI_VISION_MODEL",
                            os.getenv("OPENAI_MODEL", "google/gemini-3.1-flash-lite")),
            max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "4000")))
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise LLMError("Vision requires GEMINI_API_KEY (the only multimodal provider)")
    _budget_charge("gemini")  # spend guard applies to vision calls too
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
            _budget_charge(provider)  # spend guard: exhausted budget == leg failure
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
        meta = {"model": os.getenv("GEMINI_MODEL", "gemini-2.5-flash")}
    elif provider == "openai":
        base = _gateway_base_url()
        # separate_quota is the honest check that the gateway backup is a real,
        # independent provider — false if it points at Google's own endpoint
        # (which would just re-spend Gemini's quota) or has no base URL set.
        meta = {"model": _gateway_model(),
                "base_url_set": bool(base),
                "separate_quota": bool(base) and not _is_google_gateway(base)}
    elif provider == "groq":
        meta = {"model": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")}
    elif provider == "ollama":
        meta = {"model": os.getenv("OLLAMA_MODEL", "llama3.1"),
                "base_url": _ollama_base(), "local": True}
    else:
        meta = {"model": os.getenv("CLAUDE_MODEL", "claude-opus-4-8")}
    # Spend-guard visibility (counts only — never a key or a cost figure).
    cap = provider_budget(provider)
    if cap > 0:
        meta["budget_per_hour"] = cap
        meta["budget_used_last_hour"] = _budget_spent(provider)
    return meta


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
        _budget_charge(provider)  # probes are real spend — they count too
        out = _DISPATCH[provider]("Reply with the single word: ok", "", False)
        return {"provider": provider, "configured": True, "ok": True,
                "sample": _redact((out or "").strip())[:40]}
    except Exception as exc:  # noqa: BLE001
        return {"provider": provider, "configured": True, "ok": False,
                "error": _redact(str(exc))[:200]}
