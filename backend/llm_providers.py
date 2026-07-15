"""Provider-specific sync, vision, and streaming adapters."""

from __future__ import annotations

import logging
import os
import time

from backend.llm_core import (
    LLMError,
    _env_first,
    _gateway_base_url,
    _gateway_model,
    _is_transient,
    _key,
    _ollama_base,
    _truthy,
    _with_transient_retry,
)

log = logging.getLogger("pramaan.llm.providers")


def _aicredits_extra_body(base_url: str | None) -> dict:
    """Opt out of gateway semantic caching for independent benchmark calls."""
    if os.getenv("AICREDITS_NO_CACHE") == "1" and "aicredits.in" in (base_url or ""):
        return {"no_cache": True}
    return {}


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
        kwargs = {"model": model, "messages": messages, "temperature": 0.1,
                  "max_tokens": max_tokens}
        extra_body = _aicredits_extra_body(base_url)
        if extra_body:
            kwargs["extra_body"] = extra_body
        return _with_transient_retry(
            lambda: client.chat.completions.create(**kwargs).choices[0].message.content,
            label)
    except Exception as exc:
        log.error("%s vision error: %s", label, exc)
        raise LLMError(f"{label} vision call failed: {exc}") from exc

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
        extra_body = _aicredits_extra_body(base_url)
        if extra_body:
            kwargs["extra_body"] = extra_body
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
