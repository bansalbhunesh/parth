"""Vision, narrative-grounding, and provider-probe failure contracts."""

from __future__ import annotations

import sys
from types import ModuleType, SimpleNamespace

import pytest

from backend import llm
from backend.llm_core import LLMError


def test_openai_vision_path_forwards_budget_and_multimodal_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: dict[str, object] = {}
    monkeypatch.setenv("PRAMAAN_LLM", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "vision-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://vision.example/v1")
    monkeypatch.setenv("OPENAI_VISION_MODEL", "vision-model")
    monkeypatch.setenv("OPENAI_MAX_TOKENS", "222")
    monkeypatch.setattr(llm, "_budget_charge", lambda provider: calls.update(budget=provider))

    def vision(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202
        calls["args"] = args
        calls["kwargs"] = kwargs
        return "vision-result"

    monkeypatch.setattr(llm, "_openai_compatible_vision", vision)

    assert llm.complete_vision("inspect", b"image", "image/png", "system") == "vision-result"
    assert calls["budget"] == "openai"
    assert calls["args"] == ("inspect", b"image", "image/png", "system")
    assert calls["kwargs"] == {
        "label": "OpenAI-compat",
        "api_key": "vision-key",
        "base_url": "https://vision.example/v1",
        "model": "vision-model",
        "max_tokens": 222,
    }


def test_vision_requires_a_configured_multimodal_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PRAMAAN_LLM", "gemini")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(LLMError, match="Vision requires GEMINI_API_KEY"):
        llm.complete_vision("inspect", b"image", "image/png")


class _VisionModels:
    def __init__(self, responses: list[object]) -> None:
        self.responses = list(responses)
        self.calls: list[dict[str, object]] = []

    def generate_content(self, **kwargs):  # noqa: ANN003, ANN201
        self.calls.append(kwargs)
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def _install_fake_genai(monkeypatch: pytest.MonkeyPatch, models: _VisionModels) -> None:
    import google

    genai = ModuleType("google.genai")
    genai.Client = lambda *, api_key: SimpleNamespace(models=models, api_key=api_key)
    genai.types = SimpleNamespace(
        Part=SimpleNamespace(from_bytes=lambda **kwargs: ("part", kwargs)),
        GenerateContentConfig=lambda **kwargs: SimpleNamespace(**kwargs),
    )
    monkeypatch.setitem(sys.modules, "google.genai", genai)
    monkeypatch.setattr(google, "genai", genai, raising=False)


def test_gemini_vision_retries_transient_failure_and_preserves_image_part(monkeypatch: pytest.MonkeyPatch) -> None:
    models = _VisionModels([RuntimeError("overloaded"), SimpleNamespace(text="gemini-vision")])
    _install_fake_genai(monkeypatch, models)
    monkeypatch.setenv("PRAMAAN_LLM", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-key")
    monkeypatch.setattr(llm, "_budget_charge", lambda _provider: None)
    monkeypatch.setattr(llm, "_is_transient", lambda _exc: True)
    monkeypatch.setattr(llm.time, "sleep", lambda _seconds: None)

    assert llm.complete_vision("inspect", b"image", "image/jpeg", "vision system") == "gemini-vision"
    assert len(models.calls) == 2
    assert models.calls[-1]["contents"][0] == (
        "part",
        {"data": b"image", "mime_type": "image/jpeg"},
    )
    assert models.calls[-1]["config"].system_instruction == "vision system"


def test_gemini_vision_wraps_terminal_provider_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    models = _VisionModels([RuntimeError("invalid image")])
    _install_fake_genai(monkeypatch, models)
    monkeypatch.setenv("PRAMAAN_LLM", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-key")
    monkeypatch.setattr(llm, "_budget_charge", lambda _provider: None)
    monkeypatch.setattr(llm, "_is_transient", lambda _exc: False)
    with pytest.raises(LLMError, match="Gemini vision call failed"):
        llm.complete_vision("inspect", b"image", "image/png")


def test_restate_accepts_only_nonempty_number_grounded_prose(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(llm, "complete", lambda *_args, **_kwargs: "Duration remains 12 weeks")
    assert llm.restate("Duration is 12 weeks", "Be concise", "system") == {
        "narrative": "Duration remains 12 weeks",
        "mode": "llm",
    }

    monkeypatch.setattr(llm, "complete", lambda *_args, **_kwargs: "Duration is 14 weeks")
    assert llm.restate("Duration is 12 weeks", "Be concise", "system") == {
        "narrative": "Duration is 12 weeks",
        "mode": "rule-based-fallback",
    }

    monkeypatch.setattr(llm, "complete", lambda *_args, **_kwargs: "   ")
    assert llm.restate("Duration is 12 weeks", "Be concise", "system")["mode"] == "rule-based-fallback"


def test_provider_probe_distinguishes_unconfigured_success_and_redacted_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(llm, "_configured", lambda _provider: False)
    assert llm.probe_provider("gemini") == {"provider": "gemini", "configured": False, "ok": False}

    monkeypatch.setattr(llm, "_configured", lambda _provider: True)
    monkeypatch.setattr(llm, "_budget_charge", lambda _provider: None)
    monkeypatch.setitem(llm._DISPATCH, "gemini", lambda *_args: "ok")
    assert llm.probe_provider("gemini") == {
        "provider": "gemini",
        "configured": True,
        "ok": True,
        "sample": "ok",
    }

    monkeypatch.setitem(
        llm._DISPATCH,
        "gemini",
        lambda *_args: (_ for _ in ()).throw(RuntimeError("failed with key=super-secret")),
    )
    failed = llm.probe_provider("gemini")
    assert failed["provider"] == "gemini"
    assert failed["configured"] is True
    assert failed["ok"] is False
    assert "super-secret" not in failed["error"]
