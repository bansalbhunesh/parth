"""Contract tests for every external LLM adapter without making network calls."""

from __future__ import annotations

import sys
from types import ModuleType, SimpleNamespace

import pytest

from backend import llm_providers as providers
from backend.llm_core import LLMError


class _OpenAICompletions:
    def __init__(self, responses: list[object] | None = None) -> None:
        self.calls: list[dict[str, object]] = []
        self.responses = list(responses or [])

    def create(self, **kwargs):  # noqa: ANN003, ANN201
        self.calls.append(kwargs)
        if self.responses:
            response = self.responses.pop(0)
            if isinstance(response, Exception):
                raise response
            return response
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="provider-result"))])


def _install_openai(monkeypatch: pytest.MonkeyPatch, completions: _OpenAICompletions) -> list[tuple[str, str | None]]:
    import openai

    clients: list[tuple[str, str | None]] = []

    def factory(*, api_key: str, base_url: str | None):
        clients.append((api_key, base_url))
        return SimpleNamespace(chat=SimpleNamespace(completions=completions))

    monkeypatch.setattr(openai, "OpenAI", factory)
    monkeypatch.setattr(providers, "_with_transient_retry", lambda operation, _label: operation())
    return clients


def test_openai_compatible_chat_builds_scoped_json_request(monkeypatch: pytest.MonkeyPatch) -> None:
    completions = _OpenAICompletions()
    clients = _install_openai(monkeypatch, completions)

    result = providers._openai_compatible(
        "prompt",
        "system",
        True,
        label="Gateway",
        api_key="api-key",
        base_url="https://gateway.example/v1",
        model="model-a",
        json_mode_on=True,
        max_tokens=123,
    )

    assert result == "provider-result"
    assert clients == [("api-key", "https://gateway.example/v1")]
    call = completions.calls[0]
    assert call["messages"] == [
        {"role": "system", "content": "system"},
        {"role": "user", "content": "prompt"},
    ]
    assert call["response_format"] == {"type": "json_object"}
    assert call["max_tokens"] == 123


def test_openai_compatible_chat_plain_mode_and_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    completions = _OpenAICompletions()
    _install_openai(monkeypatch, completions)
    assert providers._openai_compatible(
        "prompt",
        "",
        False,
        label="Gateway",
        api_key="api-key",
        base_url="",
        model="model-a",
        json_mode_on=True,
        max_tokens=50,
    ) == "provider-result"
    assert "response_format" not in completions.calls[0]
    assert completions.calls[0]["messages"] == [{"role": "user", "content": "prompt"}]

    with pytest.raises(LLMError, match="API key not set"):
        providers._openai_compatible(
            "p", "", False, label="Gateway", api_key="", base_url="", model="m", json_mode_on=False, max_tokens=1
        )

    import openai

    monkeypatch.setattr(openai, "OpenAI", lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("connect failed")))
    with pytest.raises(LLMError, match="Gateway API call failed"):
        providers._openai_compatible(
            "p", "", False, label="Gateway", api_key="key", base_url="", model="m", json_mode_on=False, max_tokens=1
        )


def test_openai_compatible_vision_encodes_image_and_wraps_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    completions = _OpenAICompletions()
    _install_openai(monkeypatch, completions)

    assert providers._openai_compatible_vision(
        "inspect",
        b"image",
        "image/png",
        "vision-system",
        label="Vision",
        api_key="key",
        base_url="https://vision.example/v1",
        model="vision-model",
        max_tokens=99,
    ) == "provider-result"
    content = completions.calls[0]["messages"][1]["content"]
    assert content[1]["image_url"]["url"] == "data:image/png;base64,aW1hZ2U="

    assert providers._openai_compatible_vision(
        "inspect",
        b"image",
        "image/png",
        "",
        label="Vision",
        api_key="key",
        base_url="",
        model="vision-model",
        max_tokens=99,
    ) == "provider-result"
    assert completions.calls[1]["messages"][0]["role"] == "user"

    with pytest.raises(LLMError, match="vision API key not set"):
        providers._openai_compatible_vision(
            "p", b"x", "image/png", "", label="Vision", api_key="", base_url="", model="m", max_tokens=1
        )

    import openai

    monkeypatch.setattr(openai, "OpenAI", lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("vision failed")))
    with pytest.raises(LLMError, match="Vision vision call failed"):
        providers._openai_compatible_vision(
            "p", b"x", "image/png", "", label="Vision", api_key="key", base_url="", model="m", max_tokens=1
        )


def test_openai_compatible_stream_filters_empty_chunks_and_wraps_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    chunks = [
        SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=None))]),
        SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content="first"))]),
        SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content="second"))]),
    ]
    completions = _OpenAICompletions([chunks])
    _install_openai(monkeypatch, completions)
    assert list(
        providers._openai_compatible_stream(
            "prompt", "system", label="Stream", api_key="key", base_url="", model="m", max_tokens=5
        )
    ) == ["first", "second"]
    assert completions.calls[0]["stream"] is True

    no_system_chunks = [SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content="only"))])]
    no_system = _OpenAICompletions([no_system_chunks])
    _install_openai(monkeypatch, no_system)
    assert list(
        providers._openai_compatible_stream(
            "prompt", "", label="Stream", api_key="key", base_url="", model="m", max_tokens=5
        )
    ) == ["only"]
    assert no_system.calls[0]["messages"] == [{"role": "user", "content": "prompt"}]

    with pytest.raises(LLMError, match="API key not set"):
        list(
            providers._openai_compatible_stream(
                "p", "", label="Stream", api_key="", base_url="", model="m", max_tokens=1
            )
        )

    import openai

    monkeypatch.setattr(openai, "OpenAI", lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("stream failed")))
    with pytest.raises(LLMError, match="Stream streaming failed"):
        list(
            providers._openai_compatible_stream(
                "p", "", label="Stream", api_key="key", base_url="", model="m", max_tokens=1
            )
        )


def test_openai_groq_and_ollama_wrappers_forward_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[tuple[object, ...], dict[str, object]]] = []

    def fake(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202
        calls.append((args, kwargs))
        return kwargs["label"]

    monkeypatch.setattr(providers, "_openai_compatible", fake)
    monkeypatch.setenv("QWEN_GATEWAY_API_KEY", "qwen-key")
    monkeypatch.setenv("QWEN_GATEWAY_BASE_URL", "https://qwen.example/v1")
    monkeypatch.setenv("QWEN_GATEWAY_MODEL", "qwen-model")
    monkeypatch.setenv("QWEN_GATEWAY_JSON_MODE", "1")
    monkeypatch.setenv("QWEN_GATEWAY_MAX_TOKENS", "321")
    assert providers._openai("p", "s", True) == "Qwen-gateway"

    monkeypatch.setenv("GROQ_API_KEY", "groq-key")
    monkeypatch.setenv("GROQ_MODEL", "groq-model")
    assert providers._groq("p", "s", True) == "Groq"

    with pytest.raises(LLMError, match="Local LLM disabled"):
        providers._ollama("p", "s", False)
    monkeypatch.setenv("LOCAL_LLM_ENABLED", "yes")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://ollama:11434/")
    assert providers._ollama("p", "s", False) == "Ollama"

    assert calls[0][1]["api_key"] == "qwen-key"
    assert calls[0][1]["json_mode_on"] is True
    assert calls[0][1]["max_tokens"] == 321
    assert calls[1][1]["api_key"] == "groq-key"
    assert calls[2][1]["base_url"] == "http://ollama:11434/v1"


def test_stream_wrappers_forward_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    labels: list[str] = []

    def fake_stream(*_args, **kwargs):  # noqa: ANN003, ANN202
        labels.append(kwargs["label"])
        yield kwargs["model"]

    monkeypatch.setattr(providers, "_openai_compatible_stream", fake_stream)
    monkeypatch.setenv("QWEN_GATEWAY_API_KEY", "qwen-key")
    monkeypatch.setenv("QWEN_GATEWAY_MODEL", "qwen-model")
    monkeypatch.setenv("GROQ_API_KEY", "groq-key")
    assert list(providers._openai_stream("p", "s")) == ["qwen-model"]
    assert list(providers._groq_stream("p", "s")) == ["llama-3.3-70b-versatile"]

    with pytest.raises(LLMError, match="Local LLM disabled"):
        list(providers._ollama_stream("p", "s"))
    monkeypatch.setenv("LOCAL_LLM_ENABLED", "1")
    assert list(providers._ollama_stream("p", "s")) == ["llama3.1"]
    assert labels == ["Qwen-gateway", "Groq", "Ollama"]


class _GeminiModels:
    def __init__(self, responses: list[object]) -> None:
        self.responses = list(responses)
        self.calls: list[dict[str, object]] = []

    def generate_content(self, **kwargs):  # noqa: ANN003, ANN201
        self.calls.append(kwargs)
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    def generate_content_stream(self, **kwargs):  # noqa: ANN003, ANN201
        self.calls.append(kwargs)
        return iter(self.responses)


def _install_gemini(
    monkeypatch: pytest.MonkeyPatch, models: _GeminiModels
) -> tuple[list[str], ModuleType]:
    import google

    keys: list[str] = []
    genai = ModuleType("google.genai")
    genai.Client = lambda *, api_key: keys.append(api_key) or SimpleNamespace(models=models)
    genai.types = SimpleNamespace(GenerateContentConfig=lambda **kwargs: SimpleNamespace(**kwargs))
    monkeypatch.setitem(sys.modules, "google.genai", genai)
    monkeypatch.setattr(google, "genai", genai, raising=False)
    return keys, genai


def test_gemini_sync_retries_transient_errors_and_supports_plain_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    models = _GeminiModels(
        [RuntimeError("overloaded"), RuntimeError("overloaded"), SimpleNamespace(text="json-result")]
    )
    keys, _genai = _install_gemini(monkeypatch, models)
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-key")
    monkeypatch.setattr(providers, "_is_transient", lambda _exc: True)
    monkeypatch.setattr(providers.time, "sleep", lambda _seconds: None)
    assert providers._gemini("prompt", "system", True) == "json-result"
    assert keys == ["gemini-key"]
    assert models.calls[-1]["config"].response_mime_type == "application/json"

    plain = _GeminiModels([SimpleNamespace(text="plain-result")])
    _install_gemini(monkeypatch, plain)
    assert providers._gemini("prompt", "", False) == "plain-result"
    assert plain.calls[0]["config"].system_instruction is None
    assert plain.calls[0]["config"].response_mime_type == "text/plain"


def test_gemini_sync_missing_key_and_terminal_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(LLMError, match="GEMINI_API_KEY not set"):
        providers._gemini("p", "", False)

    models = _GeminiModels([RuntimeError("bad request")])
    _install_gemini(monkeypatch, models)
    monkeypatch.setenv("GEMINI_API_KEY", "key")
    monkeypatch.setattr(providers, "_is_transient", lambda _exc: False)
    with pytest.raises(LLMError, match="Gemini API call failed"):
        providers._gemini("p", "", False)


def test_gemini_stream_filters_empty_chunks_and_wraps_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(LLMError, match="GEMINI_API_KEY not set"):
        list(providers._gemini_stream("p", ""))

    models = _GeminiModels([SimpleNamespace(text=""), SimpleNamespace(text="one"), SimpleNamespace(text="two")])
    _keys, genai = _install_gemini(monkeypatch, models)
    monkeypatch.setenv("GEMINI_API_KEY", "key")
    assert list(providers._gemini_stream("p", "system")) == ["one", "two"]

    genai.Client = lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("stream failed"))
    with pytest.raises(LLMError, match="Gemini streaming failed"):
        list(providers._gemini_stream("p", ""))


class _ClaudeStream:
    def __init__(self, texts: list[str]) -> None:
        self.text_stream = texts

    def __enter__(self):
        return self

    def __exit__(self, *_args: object) -> None:
        return None


def test_claude_sync_and_stream_success(monkeypatch: pytest.MonkeyPatch) -> None:
    import anthropic

    calls: list[tuple[str, dict[str, object]]] = []

    class Messages:
        def create(self, **kwargs):  # noqa: ANN003, ANN201
            calls.append(("create", kwargs))
            return SimpleNamespace(content=[SimpleNamespace(text="claude-result")])

        def stream(self, **kwargs):  # noqa: ANN003, ANN201
            calls.append(("stream", kwargs))
            return _ClaudeStream(["first", "second"])

    monkeypatch.setattr(anthropic, "Anthropic", lambda *, api_key: SimpleNamespace(messages=Messages()))
    monkeypatch.setenv("CLAUDE_API_KEY", "claude-key")
    assert providers._claude("prompt", "system", False) == "claude-result"
    assert list(providers._claude_stream("prompt", "system")) == ["first", "second"]
    assert [name for name, _kwargs in calls] == ["create", "stream"]


def test_claude_missing_key_and_provider_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(LLMError, match="Claude API key not set"):
        providers._claude("p", "", False)
    with pytest.raises(LLMError, match="Claude API key not set"):
        list(providers._claude_stream("p", ""))

    import anthropic

    monkeypatch.setenv("CLAUDE_API_KEY", "key")
    monkeypatch.setattr(anthropic, "Anthropic", lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("claude failed")))
    with pytest.raises(LLMError, match="Claude API call failed"):
        providers._claude("p", "", False)
    with pytest.raises(LLMError, match="Claude streaming failed"):
        list(providers._claude_stream("p", ""))
