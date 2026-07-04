"""No-secret-leakage guard for the status/diagnostic surfaces.

/health, /ocr-check, /llm-check, error bodies, and the security status must
never echo an API key, a demo token, a base URL bearing a secret, or an env
value — even when those secrets are present in the environment. Fake secrets are
injected here and asserted absent from every response and from the failover
report / security status payloads.
"""

from fastapi.testclient import TestClient

import backend.llm as llm
from backend.main import app

client = TestClient(app)

_FAKE = {
    "GEMINI_API_KEY": "AIzaFAKEgeminileak000000000000000000000",
    "QWEN_GATEWAY_API_KEY": "sk-or-v1-FAKEqwenleak00000000000000000000",
    "GROQ_API_KEY": "gsk_FAKEgroqleak0000000000000000000000000",
    "ANTHROPIC_API_KEY": "sk-ant-api-FAKEclaudeleak00000000000000000",
    "DEMO_AUTH_TOKEN": "FAKE-demo-token-should-never-surface-9f2a",
}


def _set_fakes(monkeypatch):
    for k, v in _FAKE.items():
        monkeypatch.setenv(k, v)


def _assert_no_secret(text: str):
    for v in _FAKE.values():
        assert v not in text, f"secret leaked into response: {v[:12]}..."


def test_health_leaks_no_secret(monkeypatch):
    _set_fakes(monkeypatch)
    _assert_no_secret(client.get("/health").text)


def test_ocr_check_leaks_no_secret(monkeypatch):
    _set_fakes(monkeypatch)
    _assert_no_secret(client.get("/ocr-check").text)


def test_llm_check_leaks_no_secret(monkeypatch):
    _set_fakes(monkeypatch)
    # stub the tiny probe so no real network call is made
    monkeypatch.setattr(llm, "complete", lambda prompt, system="", json_mode=True: "ok")
    _assert_no_secret(client.get("/llm-check").text)


def test_llm_check_error_path_leaks_no_secret(monkeypatch):
    _set_fakes(monkeypatch)

    def boom(prompt, system="", json_mode=True):
        raise llm.LLMError(f"401 invalid key {_FAKE['GEMINI_API_KEY']} rejected")
    monkeypatch.setattr(llm, "complete", boom)
    _assert_no_secret(client.get("/llm-check").text)


def test_failover_report_and_security_status_leak_no_secret(monkeypatch):
    import json

    _set_fakes(monkeypatch)
    monkeypatch.setenv("DEMO_AUTH_ENABLED", "true")
    from backend import security
    _assert_no_secret(json.dumps(llm.failover_report()))
    _assert_no_secret(json.dumps(security.security_status()))
    # security status advertises the posture without the token value
    assert security.security_status()["auth_required"] is True


def test_auth_403_body_has_no_token(monkeypatch):
    _set_fakes(monkeypatch)
    monkeypatch.setenv("DEMO_AUTH_ENABLED", "true")
    r = client.post("/analyze",
                    json={"spec_text": "x" * 20, "submittal_text": "y" * 20},
                    headers={"X-Demo-Token": "wrong-token"})
    assert r.status_code == 403
    _assert_no_secret(r.text)
