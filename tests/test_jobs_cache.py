"""Prototype scalability proof: input-hash caching/idempotency + job flow.

These prove the reliability contract: an identical analysis is computed once and
reused (cached=true, same input_hash), the hash changes with the model/prompt
version, the async job flow (submit -> poll -> result) completes, unknown ids
404, /health advertises the counters, and no secret leaks through the job path.
"""

import time

from fastapi.testclient import TestClient

from backend import jobs
from backend.main import app

client = TestClient(app)

_SPEC = "**UPS-02** - battery runtime: shall be **10 min** at full load."
_SUB = "**UPS-02** - battery runtime: **7 min**."
_PAYLOAD = {"spec_text": _SPEC, "submittal_text": _SUB, "system_id": "UPS"}


def _no_llm(monkeypatch):
    for k in ("GEMINI_API_KEY", "OPENAI_API_KEY", "QWEN_GATEWAY_API_KEY",
              "GROQ_API_KEY", "ANTHROPIC_API_KEY", "CLAUDE_API_KEY",
              "LOCAL_LLM_ENABLED"):
        monkeypatch.delenv(k, raising=False)


def _poll(job_id, timeout_s=5.0):
    deadline = time.time() + timeout_s
    st = {}
    while time.time() < deadline:
        st = client.get(f"/jobs/{job_id}").json()
        if st["status"] in ("done", "error"):
            return st
        time.sleep(0.02)
    return st


# ── caching / idempotency ───────────────────────────────────────────

def test_analyze_returns_traceability_metadata(monkeypatch):
    _no_llm(monkeypatch)
    d = client.post("/analyze", json=_PAYLOAD).json()
    assert len(d["input_hash"]) == 64      # sha256 hex
    assert d["cached"] is False
    assert len(d["request_id"]) == 32


def test_analyze_is_idempotent(monkeypatch):
    _no_llm(monkeypatch)
    r1 = client.post("/analyze", json=_PAYLOAD).json()
    r2 = client.post("/analyze", json=_PAYLOAD).json()
    assert r1["input_hash"] == r2["input_hash"]
    assert r1["cached"] is False and r2["cached"] is True
    assert r1["deviations"] == r2["deviations"]      # reused, identical result
    assert r1["request_id"] != r2["request_id"]      # but distinct request ids


def test_different_input_different_hash(monkeypatch):
    _no_llm(monkeypatch)
    h1 = client.post("/analyze", json=_PAYLOAD).json()["input_hash"]
    other = {**_PAYLOAD, "submittal_text": "**UPS-02** - battery runtime: **9 min**."}
    h2 = client.post("/analyze", json=other).json()["input_hash"]
    assert h1 != h2


def test_input_hash_folds_in_model_and_prompt_version(monkeypatch):
    _no_llm(monkeypatch)
    h1 = jobs.compute_input_hash("a", "b", "UPS")
    monkeypatch.setenv("GEMINI_MODEL", "some-other-model")
    h2 = jobs.compute_input_hash("a", "b", "UPS")
    assert h1 != h2  # a model change invalidates cached results


def test_single_flight_computes_once(monkeypatch):
    """Concurrent identical requests coalesce to a single compute."""
    _no_llm(monkeypatch)
    calls = {"n": 0}
    import backend.analyze as az
    real = az.run_analysis

    def counting(spec, sub, sid="CUSTOM"):
        calls["n"] += 1
        return real(spec, sub, sid)
    monkeypatch.setattr(jobs, "run_analysis", counting)

    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=8) as ex:
        views = list(ex.map(lambda _: jobs.analyze_cached(_SPEC, _SUB, "UPS"), range(8)))
    assert calls["n"] == 1                       # single-flight: computed once
    assert sum(1 for v in views if v["cached"]) >= 1


def test_degraded_result_does_not_pin_the_cache(monkeypatch):
    """A rule-floor (non-LLM) result must not occupy the cache for the full
    TTL: the demo pair is a fixed input, so one transient 429 during warm-up
    would otherwise serve every subsequent judge the degraded fallback for up
    to an hour after the provider recovered. Degraded entries expire fast;
    within their short TTL they are still reused (idempotency preserved)."""
    _no_llm(monkeypatch)
    monkeypatch.setattr(jobs, "_DEGRADED_TTL_S", 0.05)
    v1 = jobs.analyze_cached(_SPEC, _SUB, "UPS")
    assert v1["mode"] != "llm" and v1["cached"] is False
    v2 = jobs.analyze_cached(_SPEC, _SUB, "UPS")
    assert v2["cached"] is True            # reused within the short TTL
    time.sleep(0.06)
    v3 = jobs.analyze_cached(_SPEC, _SUB, "UPS")
    assert v3["cached"] is False           # degraded entry expired quickly


# ── job flow ────────────────────────────────────────────────────────

def test_job_flow_submit_poll_result(monkeypatch):
    _no_llm(monkeypatch)
    sub = client.post("/jobs/analyze", json=_PAYLOAD)
    assert sub.status_code == 202
    body = sub.json()
    jid = body["job_id"]
    assert body["status"] == "queued" and len(jid) == 32
    st = _poll(jid)
    assert st["status"] == "done"
    assert st["latency_ms"] is not None and st["count"] >= 1
    res = client.get(f"/jobs/{jid}/result")
    assert res.status_code == 200
    rb = res.json()
    assert rb["status"] == "done"
    assert any(d["parameter"] == "battery_runtime_min" for d in rb["deviations"])
    assert rb["input_hash"] == body["input_hash"]


def test_job_result_while_running_or_unknown(monkeypatch):
    _no_llm(monkeypatch)
    assert client.get("/jobs/" + "a" * 32).status_code == 404       # unknown
    assert client.get("/jobs/not-valid").status_code == 404          # bad format
    assert client.get("/jobs/" + "a" * 32 + "/result").status_code == 404


def test_job_reuses_cache(monkeypatch):
    _no_llm(monkeypatch)
    client.post("/analyze", json=_PAYLOAD)          # warms the cache
    sub = client.post("/jobs/analyze", json=_PAYLOAD).json()
    st = _poll(sub["job_id"])
    assert st["status"] == "done"
    assert st["cached"] is True                     # job reused the cached result


# ── status + no-leak ────────────────────────────────────────────────

def test_health_scalability_block():
    sc = client.get("/health").json()["scalability"]
    for k in ("cache_entries", "cache_max", "jobs_tracked", "job_workers",
              "pipeline_signature"):
        assert k in sc


def test_job_path_leaks_no_secret(monkeypatch):
    secret = "AIzaFAKEjobleak0000000000000000000000000"
    monkeypatch.setenv("GEMINI_API_KEY", secret)
    import backend.llm as llm
    # fast-fail the LLM so the job degrades to the deterministic path instantly
    monkeypatch.setattr(llm, "complete_json",
                        lambda p, system="": (_ for _ in ()).throw(llm.LLMError("boom")))
    sub = client.post("/jobs/analyze", json=_PAYLOAD).json()
    st = _poll(sub["job_id"])
    res = client.get(f"/jobs/{sub['job_id']}/result").text
    assert secret not in st.get("input_hash", "") and secret not in res
    assert secret not in client.get("/health").text


def test_job_endpoints_auth_protected(monkeypatch):
    monkeypatch.setenv("DEMO_AUTH_ENABLED", "true")
    monkeypatch.setenv("DEMO_AUTH_TOKEN", "tok")
    assert client.post("/jobs/analyze", json=_PAYLOAD).status_code == 401
    assert client.get("/jobs/" + "a" * 32).status_code == 401
