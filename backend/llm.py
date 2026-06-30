"""
LLM wrapper. Gemini primary (multimodal extraction + reasoning); optional
Claude fallback for an A/B on the reconciliation brain.

Set GEMINI_API_KEY (and optionally ANTHROPIC_API_KEY). No keys are committed.
"""

import json
import logging
import os
import re
import time

log = logging.getLogger("pramaan.llm")

PROVIDER = os.getenv("PRAMAAN_LLM", "gemini")  # "gemini" | "claude" | "openai"


class LLMError(Exception):
    pass


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


def complete(prompt: str, system: str = "", json_mode: bool = True) -> str:
    if PROVIDER == "gemini":
        return _gemini(prompt, system, json_mode)
    if PROVIDER == "openai":
        return _openai(prompt, system, json_mode)
    return _claude(prompt, system, json_mode)


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
        kwargs = {"model": model_name, "messages": messages, "temperature": 0.1}
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


def complete_stream(prompt: str, system: str = ""):
    if PROVIDER == "gemini":
        yield from _gemini_stream(prompt, system)
    elif PROVIDER == "openai":
        yield from _openai_stream(prompt, system)
    else:
        yield from _claude_stream(prompt, system)


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
