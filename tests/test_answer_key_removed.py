"""P0-3 — user-facing analysis must never silently substitute the answer key.

Before this fix, /ingest, /deviations, and the copilot fallback returned the
seeded ground-truth deviations verbatim when the LLM pipeline came back empty
(no key / throttled). A judge who disconnected the model still saw the seeded
"correct" answers, presented as if they were inference.

Contract now enforced here:
  - With no LLM key, the pipeline returns empty, so the corpus endpoints degrade
    to the INDEPENDENT rule engine (analysis_mode="rule") or report
    analysis_mode="unavailable" — never the seeded answer key. Seeded
    deviations carry an "id"; rule findings never do, so the absence of "id"
    proves no answer-key substitution.
  - The seeded fixture is reachable ONLY via the explicit ?seeded_demo=true
    opt-in, and is stamped analysis_mode="seeded_demo" with a disclaimer.
  - The copilot offline fallback is labelled mode="offline-fallback" and says so
    in the answer text, rather than posing as a live model reply.
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)

_KEYS = ("GEMINI_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GROQ_API_KEY",
         "PRAMAAN_LLM")


@pytest.fixture()
def no_llm_key(monkeypatch):
    """Force the empty-pipeline branch: no provider key configured."""
    for k in _KEYS:
        monkeypatch.delenv(k, raising=False)
    yield


def _seeded_ids():
    import json
    import pathlib
    gt = json.loads((pathlib.Path(__file__).parent.parent
                     / "data" / "corpus" / "ground_truth.json").read_text())
    return {d["id"] for d in gt["seeded_deviations"]}


# ── /ingest ──────────────────────────────────────────────────────────

def test_ingest_empty_pipeline_never_returns_answer_key(no_llm_key):
    r = client.post("/ingest/UPS")  # UPS is a seeded system
    assert r.status_code == 200
    data = r.json()
    # Honest degradation, not the fixture.
    assert data["analysis_mode"] in {"rule", "unavailable", "pipeline"}
    assert data["analysis_mode"] != "seeded_demo"
    # No returned deviation is a seeded ground-truth label (those carry "id").
    assert all("id" not in d for d in data["deviations"]), \
        "answer-key (seeded) labels leaked into default /ingest output"


def test_ingest_seeded_demo_is_explicit_and_labelled(no_llm_key):
    r = client.post("/ingest/UPS?seeded_demo=true")
    assert r.status_code == 200
    data = r.json()
    assert data["analysis_mode"] == "seeded_demo"
    assert "disclaimer" in data and "not live inference" in data["disclaimer"]
    # This path (and only this path) may surface the seeded labels.
    assert data["deviations"], "seeded fixture should return the UPS answer key"
    assert all("id" in d for d in data["deviations"])
    assert _seeded_ids() & {d["id"] for d in data["deviations"]}


# ── /deviations ──────────────────────────────────────────────────────

def test_deviations_empty_pipeline_never_returns_answer_key(no_llm_key):
    r = client.get("/deviations")
    assert r.status_code == 200
    data = r.json()
    assert "register" in data and "count" in data
    assert data["analysis_mode"] in {"rule", "unavailable", "pipeline"}
    assert data["analysis_mode"] != "seeded_demo"
    assert all("id" not in d for d in data["register"]), \
        "answer-key (seeded) labels leaked into default /deviations register"


def test_deviations_seeded_demo_is_explicit_and_labelled(no_llm_key):
    r = client.get("/deviations?seeded_demo=true")
    assert r.status_code == 200
    data = r.json()
    assert data["analysis_mode"] == "seeded_demo"
    assert "disclaimer" in data
    assert data["count"] == len(data["register"]) and data["count"] > 0
    assert all("id" in d for d in data["register"])


# ── copilot fallback ────────────────────────────────────────────────

def test_copilot_fallback_is_labelled_not_inference():
    from backend.agents.rfi_copilot import ask_fallback
    seeded = [{"component": "UPS-02", "parameter": "battery_runtime_min",
               "provided_value": "7", "required_value": "10", "severity": "Critical",
               "lead_time_weeks": 27, "system": "UPS", "spec_clause": "DB-4.3"}]
    fb = ask_fallback("What is the UPS battery runtime?", seeded)
    assert fb["mode"] == "offline-fallback"
    assert "Offline reference" in fb["answer"]
    assert "not a live model" in fb["answer"]


def test_ingest_unknown_system_still_404(no_llm_key):
    assert client.post("/ingest/NOT_A_REAL_SYSTEM").status_code == 404
