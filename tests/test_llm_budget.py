"""Per-provider hourly call budget — the spend guard for paid failover legs.

A funded gateway leg (aicredits/OpenRouter) must not be drainable by demo
abuse or a failover storm. Contract: an exhausted budget makes that leg raise
LLMError, which the chain treats as a provider failure — the next configured
leg (or the free rule floor) answers instead. 0/unset = unlimited, so free
legs and existing deployments are unchanged. Counters are process-local
(single-instance demo, same trade-off as the per-IP rate limiter) and count
ATTEMPTS, conservatively.
"""

import pytest

import backend.llm as L


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for k in ("GEMINI_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY",
              "PRAMAAN_LLM", "OPENAI_BASE_URL", "OPENAI_MODEL",
              "GEMINI_BUDGET_PER_HOUR", "OPENAI_BUDGET_PER_HOUR",
              "QWEN_GATEWAY_BUDGET_PER_HOUR", "GROQ_BUDGET_PER_HOUR"):
        monkeypatch.delenv(k, raising=False)
    L.FAILOVER_STATUS["last_successful_provider"] = None
    L.FAILOVER_STATUS["last_failover"] = None
    L.reset_budgets()
    yield
    L.reset_budgets()


def _stub(monkeypatch, provider, result=None, exc=None):
    def fn(prompt, system, json_mode):
        if exc:
            raise exc
        return result
    monkeypatch.setitem(L._DISPATCH, provider, fn)


def test_unset_budget_is_unlimited(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "g")
    _stub(monkeypatch, "gemini", result="ok")
    for _ in range(25):
        assert L.complete("p") == "ok"
    assert L.provider_budget("gemini") == 0


def test_exhausted_budget_fails_over_to_next_leg(monkeypatch):
    # Realistic-length fake keys: a 1-char key would make _redact() mangle
    # every occurrence of that letter in the recorded failover reason.
    monkeypatch.setenv("GEMINI_API_KEY", "FAKEgemini0000000000")
    monkeypatch.setenv("OPENAI_API_KEY", "FAKEgateway000000000")
    monkeypatch.setenv("GEMINI_BUDGET_PER_HOUR", "2")
    _stub(monkeypatch, "gemini", result="from-gemini")
    _stub(monkeypatch, "openai", result="from-gateway")
    assert L.complete("p") == "from-gemini"
    assert L.complete("p") == "from-gemini"
    # Third call: gemini budget spent -> gateway answers, failover recorded.
    assert L.complete("p") == "from-gateway"
    assert L.FAILOVER_STATUS["last_successful_provider"] == "openai"
    assert "budget" in L.FAILOVER_STATUS["last_failover"]["reason"]


def test_gateway_budget_guards_the_paid_leg(monkeypatch):
    """The canonical scenario: the paid gateway is capped; once spent, the
    chain raises and callers degrade to the free rule floor."""
    monkeypatch.setenv("OPENAI_API_KEY", "o")
    monkeypatch.setenv("PRAMAAN_LLM", "qwen")
    monkeypatch.setenv("QWEN_GATEWAY_BUDGET_PER_HOUR", "1")
    _stub(monkeypatch, "openai", result="paid-answer")
    assert L.complete("p") == "paid-answer"
    with pytest.raises(L.LLMError):
        L.complete("p")                      # budget spent, no other leg


def test_budget_applies_to_json_path(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "g")
    monkeypatch.setenv("GEMINI_BUDGET_PER_HOUR", "1")
    _stub(monkeypatch, "gemini", result='{"a": 1}')
    assert L.complete_json("p") == {"a": 1}
    with pytest.raises(L.LLMError):
        L.complete_json("p")


def test_budget_applies_to_stream_path(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "g")
    monkeypatch.setenv("GEMINI_BUDGET_PER_HOUR", "1")

    def stream(prompt, system):
        yield "tok"
    monkeypatch.setitem(L._STREAM_DISPATCH, "gemini", stream)
    assert list(L.complete_stream("p")) == ["tok"]
    with pytest.raises(L.LLMError):
        list(L.complete_stream("p"))


def test_probe_counts_against_budget_and_report_shows_usage(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "SECRET_BUDGET_KEY")
    monkeypatch.setenv("GEMINI_BUDGET_PER_HOUR", "3")
    _stub(monkeypatch, "gemini", result="ok")
    assert L.probe_provider("gemini")["ok"] is True
    report = L.failover_report()
    meta = report["providers"]["gemini"]
    assert meta["budget_per_hour"] == 3
    assert meta["budget_used_last_hour"] == 1
    assert "SECRET_BUDGET_KEY" not in str(report)


def test_budget_never_blocks_the_rule_floor(monkeypatch):
    """An exhausted budget degrades exactly like any provider failure — the
    analyze path still answers from the deterministic engine."""
    monkeypatch.setenv("GEMINI_API_KEY", "g")
    monkeypatch.setenv("GEMINI_BUDGET_PER_HOUR", "1")
    finding = ('[{"component": "UPS-02", "parameter": "battery_runtime_min", '
               '"required_value": "10", "provided_value": "7"}]')
    _stub(monkeypatch, "gemini", result=finding)
    from backend.analyze import run_analysis
    spec = "**UPS-02** - battery runtime: shall be **10 min** at full load."
    sub = "**UPS-02** - battery runtime: **7 min**."
    r1 = run_analysis(spec, sub, "UPS")
    assert r1.mode == "llm"
    r2 = run_analysis(spec, sub, "UPS")      # budget spent -> rule floor
    assert r2.mode == "deterministic"
    assert any(d["parameter"] == "battery_runtime_min" for d in r2.deviations)
