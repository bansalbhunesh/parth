"""Demo-hardening: optional token auth + process-local rate limiting.

Proves the reliability/abuse contract: expensive endpoints refuse without a
token when auth is on, accept with the right token in a header,
stay open when auth is off, and a caller that exceeds the per-hour cap gets a
clean 429 with Retry-After — while the public/static data endpoints and the
whole suite's default posture stay open. No secret ever appears in a response.
"""

import io

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)

_SPEC = "**UPS-02** - battery runtime: shall be **10 min** at full load."
_SUB = "**UPS-02** - battery runtime: **7 min**."


def _no_llm(monkeypatch):
    """Force the instant deterministic path so status-code tests don't wait on
    (or spend) any real LLM call."""
    for k in ("GEMINI_API_KEY", "OPENAI_API_KEY", "QWEN_GATEWAY_API_KEY",
              "GROQ_API_KEY", "ANTHROPIC_API_KEY", "CLAUDE_API_KEY",
              "LOCAL_LLM_ENABLED"):
        monkeypatch.delenv(k, raising=False)


def _analyze(**kwargs):
    return client.post("/analyze",
                       json={"spec_text": _SPEC, "submittal_text": _SUB,
                             "system_id": "UPS"}, **kwargs)


# ── auth ────────────────────────────────────────────────────────────

def _enable_auth(monkeypatch, token="s3cr3t-demo-token"):
    monkeypatch.setenv("DEMO_AUTH_ENABLED", "true")
    monkeypatch.setenv("DEMO_AUTH_TOKEN", token)
    return token


def test_protected_endpoint_without_token_401(monkeypatch):
    _no_llm(monkeypatch)
    _enable_auth(monkeypatch)
    r = _analyze()
    assert r.status_code == 401
    assert "token" in r.json()["detail"].lower()


def test_protected_endpoint_wrong_token_403(monkeypatch):
    _no_llm(monkeypatch)
    _enable_auth(monkeypatch)
    r = _analyze(headers={"X-Demo-Token": "WRONG"})
    assert r.status_code == 403


def test_protected_endpoint_correct_token_allowed(monkeypatch):
    _no_llm(monkeypatch)
    tok = _enable_auth(monkeypatch)
    # Header and bearer authentication are accepted; query-string tokens are
    # rejected because URLs leak into history, referrers, and access logs.
    assert _analyze(headers={"X-Demo-Token": tok}).status_code == 200
    assert _analyze(headers={"Authorization": f"Bearer {tok}"}).status_code == 200
    assert client.post(f"/analyze?token={tok}",
                       json={"spec_text": _SPEC, "submittal_text": _SUB}).status_code == 401


def test_auth_off_is_open(monkeypatch):
    _no_llm(monkeypatch)
    monkeypatch.setenv("DEMO_AUTH_ENABLED", "false")
    assert _analyze().status_code == 200


def test_auth_enabled_without_token_fails_closed(monkeypatch):
    """A broken auth configuration must never reopen protected analysis."""
    _no_llm(monkeypatch)
    monkeypatch.setenv("DEMO_AUTH_ENABLED", "true")
    monkeypatch.delenv("DEMO_AUTH_TOKEN", raising=False)
    response = _analyze()
    assert response.status_code == 503
    assert "access control" in response.json()["detail"].lower()


def test_public_endpoints_open_even_when_auth_on(monkeypatch):
    _enable_auth(monkeypatch)
    for path in ("/health", "/ocr-check", "/systems", "/export/audit"):
        assert client.get(path).status_code == 200, path


def test_upload_protected_by_auth(monkeypatch):
    _enable_auth(monkeypatch)
    files = [("spec_file", ("s.txt", io.BytesIO(_SPEC.encode()), "text/plain")),
             ("submittal_file", ("u.txt", io.BytesIO(_SUB.encode()), "text/plain"))]
    assert client.post("/analyze/upload", files=files).status_code == 401


def test_no_token_leak_in_responses_or_health(monkeypatch):
    secret = "TOKEN_SHOULD_NEVER_APPEAR_9f2a"
    _enable_auth(monkeypatch, token=secret)
    bodies = [
        client.get("/health").text,
        client.post("/analyze", json={"spec_text": _SPEC, "submittal_text": _SUB}).text,
        client.post("/analyze", json={"spec_text": _SPEC, "submittal_text": _SUB},
                    headers={"X-Demo-Token": "WRONG"}).text,
    ]
    for b in bodies:
        assert secret not in b
    # /health advertises the posture without the value
    sec = client.get("/health").json()["security"]
    assert sec["auth_required"] is True
    assert secret not in str(sec)


# ── rate limiting ───────────────────────────────────────────────────

def test_rate_limit_exceeded_429(monkeypatch):
    _no_llm(monkeypatch)
    monkeypatch.setenv("PRAMAAN_RATE_LIMIT_ENABLED", "1")
    monkeypatch.setenv("PRAMAAN_ANALYSIS_LIMIT_PER_HOUR", "2")
    assert _analyze().status_code == 200
    assert _analyze().status_code == 200
    r = _analyze()
    assert r.status_code == 429
    assert "Retry-After" in r.headers
    assert int(r.headers["Retry-After"]) > 0
    assert "retry" in r.json()["detail"].lower()


def test_rate_limit_disabled_never_429(monkeypatch):
    _no_llm(monkeypatch)
    monkeypatch.setenv("PRAMAAN_RATE_LIMIT_ENABLED", "0")
    monkeypatch.setenv("PRAMAAN_ANALYSIS_LIMIT_PER_HOUR", "1")
    for _ in range(5):
        assert _analyze().status_code == 200


def test_rate_limit_buckets_by_forwarded_ip(monkeypatch):
    _no_llm(monkeypatch)
    monkeypatch.setenv("PRAMAAN_RATE_LIMIT_ENABLED", "1")
    monkeypatch.setenv("PRAMAAN_ANALYSIS_LIMIT_PER_HOUR", "1")
    monkeypatch.setenv("PRAMAAN_TRUST_PROXY_HEADERS", "true")
    h1 = {"X-Forwarded-For": "1.1.1.1"}
    h2 = {"X-Forwarded-For": "2.2.2.2"}
    assert _analyze(headers=h1).status_code == 200
    assert _analyze(headers=h1).status_code == 429   # same IP, over cap
    assert _analyze(headers=h2).status_code == 200    # different IP, own bucket


def test_untrusted_forwarded_ip_cannot_evade_rate_limit(monkeypatch):
    _no_llm(monkeypatch)
    monkeypatch.setenv("PRAMAAN_RATE_LIMIT_ENABLED", "1")
    monkeypatch.setenv("PRAMAAN_ANALYSIS_LIMIT_PER_HOUR", "1")
    monkeypatch.setenv("PRAMAAN_TRUST_PROXY_HEADERS", "false")

    assert _analyze(headers={"X-Forwarded-For": "1.1.1.1"}).status_code == 200
    assert _analyze(headers={"X-Forwarded-For": "2.2.2.2"}).status_code == 429


def test_deep_probe_has_its_own_tight_limit(monkeypatch):
    monkeypatch.setenv("PRAMAAN_RATE_LIMIT_ENABLED", "1")
    monkeypatch.setenv("PRAMAAN_DEEP_PROBE_LIMIT_PER_HOUR", "1")
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr("backend.agents.reconciliation.complete_json", lambda prompt, system="": [])
    assert client.get("/llm-check?deep=1").status_code == 200
    assert client.get("/llm-check?deep=1").status_code == 429


def test_health_security_block_shape(monkeypatch):
    monkeypatch.setenv("PRAMAAN_RATE_LIMIT_ENABLED", "1")
    monkeypatch.setenv("PRAMAAN_MAX_UPLOAD_MB", "20")
    sec = client.get("/health").json()["security"]
    for k in ("auth_required", "rate_limit_enabled", "max_upload_mb",
              "max_pdf_pages", "max_image_pixels", "ocr_available",
              "deterministic_fallback_available"):
        assert k in sec, k
    assert sec["rate_limit_enabled"] is True
    assert sec["max_upload_mb"] == 20
