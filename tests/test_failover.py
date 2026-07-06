"""Provider failover chain tests.

The chain is gemini -> openai(gateway) -> claude -> deterministic rule engine.
These verify the reliability contract: quota/429/transient failures walk to the
next *configured* provider; single-provider setups behave exactly as before; a
fully-failed chain raises LLMError so callers degrade to the rule floor; and
neither logs nor /llm-check ever leak a key.
"""

import logging

import pytest

import backend.llm as L


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for k in ("GEMINI_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY",
              "PRAMAAN_LLM", "OPENAI_BASE_URL", "OPENAI_MODEL"):
        monkeypatch.delenv(k, raising=False)
    # Reset observability between tests.
    L.FAILOVER_STATUS["last_successful_provider"] = None
    L.FAILOVER_STATUS["last_failover"] = None
    yield


def _stub(monkeypatch, provider, result=None, exc=None):
    """Replace a provider's dispatch fn with a success or a failure."""
    def fn(prompt, system, json_mode):
        if exc:
            raise exc
        return result
    monkeypatch.setitem(L._DISPATCH, provider, fn)


def _quota_error():
    return L.LLMError("429 RESOURCE_EXHAUSTED: quota exceeded")


# 1. Gemini success returns Gemini result and does not call fallback.
def test_gemini_success_no_fallback(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "g")
    monkeypatch.setenv("OPENAI_API_KEY", "o")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "a")
    called = []
    monkeypatch.setitem(L._DISPATCH, "gemini",
                        lambda p, s, j: called.append("gemini") or "GEMINI_OK")
    monkeypatch.setitem(L._DISPATCH, "openai",
                        lambda p, s, j: called.append("openai") or "NO")
    monkeypatch.setitem(L._DISPATCH, "claude",
                        lambda p, s, j: called.append("claude") or "NO")
    out = L.complete("hi")
    assert out == "GEMINI_OK"
    assert called == ["gemini"]  # fallbacks never invoked
    assert L.FAILOVER_STATUS["last_successful_provider"] == "gemini"
    assert L.FAILOVER_STATUS["last_failover"] is None


# 2. Gemini quota/429 falls back to Qwen (openai gateway).
def test_gemini_quota_falls_back_to_qwen(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "g")
    monkeypatch.setenv("OPENAI_API_KEY", "o")
    _stub(monkeypatch, "gemini", exc=_quota_error())
    _stub(monkeypatch, "openai", result="QWEN_OK")
    out = L.complete("hi")
    assert out == "QWEN_OK"
    assert L.FAILOVER_STATUS["last_successful_provider"] == "openai"
    fo = L.FAILOVER_STATUS["last_failover"]
    assert fo["from"] == "gemini" and fo["to"] == "openai"
    assert "429" in fo["reason"]


# 3. Qwen failure falls back to Groq (second fallback), then Claude.
def test_qwen_failure_falls_back_to_groq(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "g")
    monkeypatch.setenv("OPENAI_API_KEY", "o")
    monkeypatch.setenv("GROQ_API_KEY", "q")
    _stub(monkeypatch, "gemini", exc=_quota_error())
    _stub(monkeypatch, "openai", exc=L.LLMError("gateway 502"))
    _stub(monkeypatch, "groq", result="GROQ_OK")
    out = L.complete("hi")
    assert out == "GROQ_OK"
    assert L.FAILOVER_STATUS["last_successful_provider"] == "groq"


def test_full_chain_order_and_groq_to_claude(monkeypatch):
    """The canonical chain is gemini -> openai(qwen) -> groq -> claude, and a
    failure of everything above Claude lands on Claude."""
    for k in ("GEMINI_API_KEY", "OPENAI_API_KEY", "GROQ_API_KEY",
              "ANTHROPIC_API_KEY"):
        monkeypatch.setenv(k, "x")
    assert L.provider_chain() == ["gemini", "openai", "groq", "claude"]
    _stub(monkeypatch, "gemini", exc=_quota_error())
    _stub(monkeypatch, "openai", exc=L.LLMError("502"))
    _stub(monkeypatch, "groq", exc=L.LLMError("groq 429"))
    _stub(monkeypatch, "claude", result="CLAUDE_LAST_RESORT")
    assert L.complete("hi") == "CLAUDE_LAST_RESORT"


# 4. All LLMs fail -> LLMError so callers fall back to the deterministic engine.
def test_all_fail_raises_for_rule_floor(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "g")
    monkeypatch.setenv("OPENAI_API_KEY", "o")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "a")
    _stub(monkeypatch, "gemini", exc=_quota_error())
    _stub(monkeypatch, "openai", exc=L.LLMError("gateway down"))
    _stub(monkeypatch, "claude", exc=L.LLMError("anthropic 529 overloaded"))
    with pytest.raises(L.LLMError) as ei:
        L.complete("hi")
    assert "configured provider" in str(ei.value)


def test_all_fail_degrades_to_rule_engine_in_analyze(monkeypatch):
    """End-to-end: with every provider throwing, run_analysis returns the
    deterministic rule-engine result (mode != 'llm'), never an exception."""
    monkeypatch.setenv("GEMINI_API_KEY", "g")
    _stub(monkeypatch, "gemini", exc=_quota_error())
    from backend.analyze import run_analysis
    res = run_analysis("**battery.** required 10 min", "battery 7 min", "UPS")
    assert res.mode == "deterministic"
    assert isinstance(res.deviations, list)


# 5. Only one configured provider keeps existing behavior (single-element chain,
#    the same LLMError on failure — no phantom fallback).
def test_single_provider_unchanged_behavior(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "g")
    assert L.provider_chain() == ["gemini"]
    _stub(monkeypatch, "gemini", result="ONLY_GEMINI")
    assert L.complete("hi") == "ONLY_GEMINI"
    # And on failure, it raises (no other provider to try).
    _stub(monkeypatch, "gemini", exc=L.LLMError("boom"))
    with pytest.raises(L.LLMError):
        L.complete("hi")


# 6. No provider key configured still returns safe deterministic output.
def test_no_key_configured_safe_deterministic(monkeypatch):
    assert L.provider_chain() == []
    with pytest.raises(L.LLMError):
        L.complete("hi")
    from backend.analyze import run_analysis
    res = run_analysis("**battery.** required 10 min", "battery 7 min", "UPS")
    assert res.mode == "deterministic"
    assert L.failover_report()["on_rule_engine_floor"] is True


# 7. Logs and failover report never leak API keys.
def test_no_key_leak_in_logs_and_report(monkeypatch, caplog):
    secret = "AQ.SUPERSECRETKEY_do_not_leak_123"
    monkeypatch.setenv("GEMINI_API_KEY", secret)
    monkeypatch.setenv("OPENAI_API_KEY", "o")
    _stub(monkeypatch, "gemini",
          exc=L.LLMError(f"401 invalid key {secret} rejected"))
    _stub(monkeypatch, "openai", result="OK")
    with caplog.at_level(logging.WARNING, logger="pramaan.llm"):
        L.complete("hi")
    joined = " ".join(r.getMessage() for r in caplog.records)
    assert secret not in joined
    fo = L.FAILOVER_STATUS["last_failover"]
    assert secret not in (fo["reason"] if fo else "")
    # failover_report is secret-free by construction (config booleans only).
    import json
    assert secret not in json.dumps(L.failover_report())


def test_stream_pre_emit_failover(monkeypatch):
    """A stream provider that fails before yielding is skipped for the next."""
    monkeypatch.setenv("GEMINI_API_KEY", "g")
    monkeypatch.setenv("OPENAI_API_KEY", "o")

    def bad_stream(prompt, system):
        raise L.LLMError("429 quota")
        yield  # unreachable

    def good_stream(prompt, system):
        yield "hello "
        yield "world"
    monkeypatch.setitem(L._STREAM_DISPATCH, "gemini", bad_stream)
    monkeypatch.setitem(L._STREAM_DISPATCH, "openai", good_stream)
    assert "".join(L.complete_stream("hi")) == "hello world"
    assert L.FAILOVER_STATUS["last_successful_provider"] == "openai"


def test_stream_mid_emit_no_double(monkeypatch):
    """A provider that fails *after* emitting must NOT switch mid-stream
    (that would duplicate text); it raises so the caller hits the rule floor."""
    monkeypatch.setenv("GEMINI_API_KEY", "g")
    monkeypatch.setenv("OPENAI_API_KEY", "o")

    def half_stream(prompt, system):
        yield "partial"
        raise L.LLMError("dropped mid-stream")
    monkeypatch.setitem(L._STREAM_DISPATCH, "gemini", half_stream)
    monkeypatch.setitem(L._STREAM_DISPATCH, "openai",
                        lambda p, s: iter(["should-not-run"]))
    got = []
    with pytest.raises(L.LLMError):
        for c in L.complete_stream("hi"):
            got.append(c)
    assert got == ["partial"]  # no duplication, no second provider


def test_llm_check_reports_chain_and_floor(monkeypatch):
    """/llm-check surfaces the chain and the rule-engine-floor state, with no
    secret in the payload."""
    from fastapi.testclient import TestClient

    from backend.main import app
    client = TestClient(app)
    # Floor: no providers.
    r = client.get("/llm-check")
    assert r.json()["on_rule_engine_floor"] is True
    assert r.json()["ok"] is False
    # With a stubbed provider, chain shows and no key leaks.
    monkeypatch.setenv("GEMINI_API_KEY", "SECRET_XYZ")
    _stub(monkeypatch, "gemini", result="ok")
    data = client.get("/llm-check").json()
    assert data["failover"]["chain"] == ["gemini"]
    assert "SECRET_XYZ" not in str(data)


# ── JSON-completion failover (parse failure == provider failure) ─────
# Found live 2026-07-06: an empty/unparseable JSON-mode response from the
# first provider used to be terminal — the healthy next leg was never tried
# and the sync /analyze path dropped to the rule floor while /analyze/stream
# succeeded on the same input.

def test_unparseable_json_fails_over_to_next_provider(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "g")
    monkeypatch.setenv("OPENAI_API_KEY", "o")
    _stub(monkeypatch, "gemini", result="I am not JSON at all, sorry.")
    _stub(monkeypatch, "openai", result='[{"component": "UPS-02"}]')
    out = L.complete_json("prompt")
    assert out == [{"component": "UPS-02"}]
    assert L.FAILOVER_STATUS["last_successful_provider"] == "openai"
    assert L.FAILOVER_STATUS["last_failover"]["from"] == "gemini"


def test_empty_json_response_fails_over(monkeypatch):
    """A None/blank response (safety block / thinking-budget exhaustion) is a
    provider failure, not a crash and not a terminal parse error."""
    monkeypatch.setenv("GEMINI_API_KEY", "g")
    monkeypatch.setenv("OPENAI_API_KEY", "o")
    _stub(monkeypatch, "gemini", result=None)
    _stub(monkeypatch, "openai", result='{"needs_revision": false}')
    assert L.complete_json("prompt") == {"needs_revision": False}
    assert L.FAILOVER_STATUS["last_successful_provider"] == "openai"


def test_all_providers_unparseable_raises_llmerror(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "g")
    monkeypatch.setenv("OPENAI_API_KEY", "o")
    _stub(monkeypatch, "gemini", result="garbage")
    _stub(monkeypatch, "openai", result="also garbage")
    with pytest.raises(L.LLMError):
        L.complete_json("prompt")
