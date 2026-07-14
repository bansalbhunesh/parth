"""The project overview is a cheap, provenance-labelled read model.

It must never launch one LLM pipeline per system during a page refresh. Fresh
reasoning belongs to /ingest and /analyze; /deviations remains deterministic so
an abandoned server-render fetch cannot continue burning provider quota.
"""

from fastapi.testclient import TestClient

from backend import main
from backend.routers import data

client = TestClient(main.app)


def test_register_never_invokes_llm_pipeline(monkeypatch):
    monkeypatch.setattr(
        data,
        "run_pipeline",
        lambda _system: (_ for _ in ()).throw(
            AssertionError("overview must not invoke run_pipeline")
        ),
    )

    response = client.get("/deviations")

    assert response.status_code == 200
    payload = response.json()
    assert payload["analysis_mode"] in {"rule", "unavailable"}
    assert payload["provenance"]["live"] is False
    assert payload["provenance"]["kind"] in {"deterministic", "unavailable"}
    assert payload["provenance"]["source_documents"] >= 0


def test_seeded_demo_remains_explicit_opt_in():
    payload = client.get("/deviations?seeded_demo=true").json()

    assert payload["analysis_mode"] == "seeded_demo"
    assert "SEEDED DEMO FIXTURE" in payload["disclaimer"]
    assert payload["register"]
