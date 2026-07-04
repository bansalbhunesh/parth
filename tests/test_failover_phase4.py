"""Phase-4 failover additions: the local-Ollama leg, canonical env names
(QWEN_GATEWAY_* / CLAUDE_*) with back-compat aliases, PRAMAAN_LLM_PROVIDER_ORDER,
the genuinely-separate-quota guard on the Qwen gateway, and the enriched
/llm-check report — all proving the *reliability* contract without changing any
behaviour when only one provider (or the older env names) is configured.

These sit alongside test_failover.py (the pre-Phase-4 contract) rather than
editing it, so both the old and new guarantees are pinned.
"""

import json
import logging

import pytest

import backend.llm as L


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    # Every provider key alias + the Phase-4 knobs, so each test starts from a
    # known-empty chain regardless of the host's shell.
    for k in ("GEMINI_API_KEY", "OPENAI_API_KEY", "QWEN_GATEWAY_API_KEY",
              "QWEN_GATEWAY_BASE_URL", "QWEN_GATEWAY_MODEL", "OPENAI_BASE_URL",
              "OPENAI_MODEL", "GROQ_API_KEY", "ANTHROPIC_API_KEY",
              "CLAUDE_API_KEY", "LOCAL_LLM_ENABLED", "OLLAMA_BASE_URL",
              "OLLAMA_MODEL", "PRAMAAN_LLM", "PRAMAAN_LLM_PROVIDER_ORDER"):
        monkeypatch.delenv(k, raising=False)
    L.FAILOVER_STATUS["last_successful_provider"] = None
    L.FAILOVER_STATUS["last_failover"] = None
    yield


def _stub(monkeypatch, provider, result=None, exc=None):
    def fn(prompt, system, json_mode):
        if exc:
            raise exc
        return result
    monkeypatch.setitem(L._DISPATCH, provider, fn)


def _quota():
    return L.LLMError("429 RESOURCE_EXHAUSTED: quota exceeded")


# 1. Ollama only joins the chain when LOCAL_LLM_ENABLED is truthy — it is keyless,
#    so nothing else can pull it in and a default deployment is unaffected.
def test_ollama_only_configured_when_enabled(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "g")
    assert "ollama" not in L.provider_chain()          # off by default
    monkeypatch.setenv("LOCAL_LLM_ENABLED", "1")
    assert L.provider_chain() == ["gemini", "ollama"]  # now the tail leg
    assert L._configured("ollama") is True


# 2. The full canonical chain reaches Ollama after Claude, then the rule floor.
def test_claude_failure_falls_back_to_ollama(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "g")
    monkeypatch.setenv("CLAUDE_API_KEY", "c")
    monkeypatch.setenv("LOCAL_LLM_ENABLED", "1")
    assert L.provider_chain() == ["gemini", "claude", "ollama"]
    _stub(monkeypatch, "gemini", exc=_quota())
    _stub(monkeypatch, "claude", exc=L.LLMError("anthropic 529 overloaded"))
    _stub(monkeypatch, "ollama", result="OLLAMA_LOCAL_OK")
    assert L.complete("hi") == "OLLAMA_LOCAL_OK"
    assert L.FAILOVER_STATUS["last_successful_provider"] == "ollama"
    fo = L.FAILOVER_STATUS["last_failover"]
    assert fo["from"] == "claude" and fo["to"] == "ollama"


# 3. Every LLM leg (incl. Ollama) failing raises LLMError so the caller lands on
#    the deterministic rule engine — never a seeded/fake result.
def test_all_legs_including_ollama_fail_hits_rule_floor(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "g")
    monkeypatch.setenv("LOCAL_LLM_ENABLED", "1")
    _stub(monkeypatch, "gemini", exc=_quota())
    _stub(monkeypatch, "ollama", exc=L.LLMError("connection refused 11434"))
    with pytest.raises(L.LLMError):
        L.complete("hi")
    # analyze-level: degrades to the deterministic engine, never raises.
    from backend.analyze import run_analysis
    res = run_analysis("**battery.** required 10 min", "battery 7 min", "UPS")
    assert res.mode == "deterministic"
    assert isinstance(res.deviations, list)


# 4. Canonical QWEN_GATEWAY_API_KEY alone configures the gateway leg; the older
#    OPENAI_API_KEY still works too (back-compat), so a live deployment is safe.
def test_canonical_and_legacy_gateway_env_both_configure(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "g")
    monkeypatch.setenv("QWEN_GATEWAY_API_KEY", "sk-or-canonical")
    monkeypatch.setenv("QWEN_GATEWAY_MODEL", "qwen/qwen3-235b")
    assert "openai" in L.provider_chain()
    assert L._provider_public_meta("openai")["model"] == "qwen/qwen3-235b"
    monkeypatch.delenv("QWEN_GATEWAY_API_KEY")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-legacy")   # older alias
    assert "openai" in L.provider_chain()


# 5. Canonical CLAUDE_API_KEY configures Claude without ANTHROPIC_API_KEY set,
#    and the provider function resolves it explicitly.
def test_canonical_claude_env_configures_claude(monkeypatch):
    monkeypatch.setenv("CLAUDE_API_KEY", "sk-ant-canonical")
    assert L._configured("claude") is True
    assert L._key("claude") == "sk-ant-canonical"
    # and the no-key message still names ANTHROPIC_API_KEY (older muscle memory).
    monkeypatch.delenv("CLAUDE_API_KEY")
    with pytest.raises(L.LLMError) as ei:
        L._claude("hi", "", True)
    assert "ANTHROPIC_API_KEY" in str(ei.value)


# 6. PRAMAAN_LLM_PROVIDER_ORDER overrides the order; `qwen` is accepted as an
#    alias for the gateway leg, and unknown names are dropped.
def test_provider_order_override(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "g")
    monkeypatch.setenv("OPENAI_API_KEY", "o")
    monkeypatch.setenv("CLAUDE_API_KEY", "c")
    monkeypatch.setenv("PRAMAAN_LLM_PROVIDER_ORDER", "claude, qwen, gemini, bogus")
    # bogus dropped; qwen -> openai; primary (gemini) still floated to the front.
    assert L.provider_chain() == ["gemini", "claude", "openai"]


# 7. The Qwen-gateway separate-quota guard: a Google endpoint is flagged as NOT a
#    separate quota; a real third-party gateway is.
def test_qwen_google_endpoint_flagged_not_separate_quota(monkeypatch):
    monkeypatch.setenv("QWEN_GATEWAY_API_KEY", "k")
    monkeypatch.setenv("QWEN_GATEWAY_BASE_URL",
                       "https://generativelanguage.googleapis.com/v1beta/openai")
    assert L._provider_public_meta("openai")["separate_quota"] is False
    monkeypatch.setenv("QWEN_GATEWAY_BASE_URL", "https://openrouter.ai/api/v1")
    assert L._provider_public_meta("openai")["separate_quota"] is True


# 8. No secret from any alias leaks into logs, the failover record, or the report.
def test_no_secret_leak_across_aliases(monkeypatch, caplog):
    secret = "QWEN.SUPERSECRET_do_not_leak_456"
    monkeypatch.setenv("QWEN_GATEWAY_API_KEY", secret)
    monkeypatch.setenv("GEMINI_API_KEY", "g")
    _stub(monkeypatch, "gemini", exc=_quota())
    _stub(monkeypatch, "openai",
          exc=L.LLMError(f"401 invalid key {secret} rejected"))
    with caplog.at_level(logging.WARNING, logger="pramaan.llm"):
        with pytest.raises(L.LLMError):
            L.complete("hi")
    joined = " ".join(r.getMessage() for r in caplog.records)
    assert secret not in joined
    fo = L.FAILOVER_STATUS["last_failover"]
    assert secret not in (fo["reason"] if fo else "")
    assert secret not in json.dumps(L.failover_report())


# 9. /llm-check surfaces the resolved order and that the deterministic floor is
#    always available, with no secret in the payload.
def test_llm_check_reports_order_and_deterministic_floor(monkeypatch):
    from fastapi.testclient import TestClient

    from backend.main import app
    client = TestClient(app)
    # No provider: on the rule floor, but the deterministic fallback is still
    # advertised as available.
    r = client.get("/llm-check").json()
    assert r["on_rule_engine_floor"] is True
    assert r["failover"]["deterministic_fallback_available"] is True
    assert r["failover"]["order"][0] == "gemini"
    # With a stubbed provider + secret key, the order shows and nothing leaks.
    monkeypatch.setenv("GEMINI_API_KEY", "SECRET_LEAK_CHECK_789")
    _stub(monkeypatch, "gemini", result="ok")
    data = client.get("/llm-check").json()
    assert "ollama" in data["failover"]["order"]
    assert data["failover"]["deterministic_fallback_available"] is True
    assert "SECRET_LEAK_CHECK_789" not in str(data)
