"""
LLM wrapper. Gemini primary (multimodal extraction + reasoning); optional
Claude fallback for an A/B on the reconciliation brain.

Set GEMINI_API_KEY (and optionally ANTHROPIC_API_KEY). No keys are committed.
"""

import json
import os
import re

PROVIDER = os.getenv("PRAMAAN_LLM", "gemini")  # "gemini" | "claude"


def _extract_json(text: str):
    """Tolerant JSON extraction — strips code fences / prose."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    # grab the outermost JSON object/array
    m = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
    if m:
        text = m.group(1)
    return json.loads(text)


def complete(prompt: str, system: str = "", json_mode: bool = True) -> str:
    if PROVIDER == "gemini":
        return _gemini(prompt, system, json_mode)
    return _claude(prompt, system, json_mode)


def complete_json(prompt: str, system: str = ""):
    raw = complete(prompt, system, json_mode=True)
    return _extract_json(raw)


def _gemini(prompt, system, json_mode):
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    try:
        from google import genai
        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        config = genai.types.GenerateContentConfig(
            temperature=0.1,
            system_instruction=system or None,
            response_mime_type="application/json" if json_mode else "text/plain",
        )
        resp = client.models.generate_content(
            model=model_name, contents=prompt, config=config,
        )
        return resp.text
    except ImportError:
        import google.generativeai as genai
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
        model = genai.GenerativeModel(
            model_name,
            system_instruction=system or None,
            generation_config={
                "temperature": 0.1,
                "response_mime_type": "application/json" if json_mode else "text/plain",
            },
        )
        return model.generate_content(prompt).text


def _claude(prompt, system, json_mode):
    import anthropic
    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY
    msg = client.messages.create(
        model=os.getenv("CLAUDE_MODEL", "claude-opus-4-8"),
        max_tokens=2000,
        temperature=0.1,
        system=system or None,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text
