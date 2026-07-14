"""Platform-independent branch contracts for corpus and reference-data routes."""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from backend.api_context import CopilotQuery
from backend.routers import data


def test_system_and_corpus_loaders_handle_absent_documents(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(data, "CORPUS", tmp_path)
    assert data.systems() == {"systems": []}
    assert data._corpus_texts("UPS") == (None, None)


def test_ingest_rejects_unknown_system_and_reports_unavailable_analysis(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(data, "_get_valid_systems", lambda: {"UPS"})
    with pytest.raises(HTTPException) as unknown:
        data.ingest("UNKNOWN")
    assert unknown.value.status_code == 404

    monkeypatch.setattr(data, "run_pipeline", lambda _system_id: [])
    monkeypatch.setattr(data, "_corpus_texts", lambda _system_id: (None, None))
    result = data.ingest("UPS")
    assert result["analysis_mode"] == "unavailable"
    assert result["deviations"] == []


def test_seeded_ingest_and_deviation_register_are_explicitly_labeled(monkeypatch: pytest.MonkeyPatch) -> None:
    seeded = [
        {"system": "UPS", "severity": "Critical", "lead_time_weeks": 4},
        {"system": "BMS", "severity": "Major", "lead_time_weeks": None},
    ]
    monkeypatch.setattr(data, "_get_valid_systems", lambda: {"UPS"})
    monkeypatch.setattr(data, "_load_json", lambda _name: {"seeded_deviations": seeded})

    ingested = data.ingest("UPS", seeded_demo=True)
    assert ingested["analysis_mode"] == "seeded_demo"
    assert ingested["deviations"] == [seeded[0]]

    register = data.deviations(seeded_demo=True)
    assert register["analysis_mode"] == "seeded_demo"
    assert register["critical"] == 1
    assert register["major"] == 1
    assert register["mean_lead_time_weeks"] == 4.0


def test_deterministic_register_distinguishes_missing_and_incomplete_corpus(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(data, "CORPUS", tmp_path / "missing")
    missing = data._deterministic_register()
    assert missing["analysis_mode"] == "unavailable"
    assert missing["provenance"]["source_documents"] == 0

    corpus = tmp_path / "corpus"
    specs = corpus / "specs"
    specs.mkdir(parents=True)
    (specs / "UPS.md").write_text("owner document only", encoding="utf-8")
    monkeypatch.setattr(data, "CORPUS", corpus)
    incomplete = data._deterministic_register()
    assert incomplete["analysis_mode"] == "unavailable"
    assert incomplete["provenance"]["label"] == "No deterministic findings available"


def test_copilot_and_metrics_fail_closed_to_safe_fallbacks(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(data, "ask", lambda _query: (_ for _ in ()).throw(RuntimeError("provider failed")))
    monkeypatch.setattr(data, "_load_json", lambda _name: {"seeded_deviations": [{"id": "D-1"}]})
    monkeypatch.setattr(
        data,
        "ask_fallback",
        lambda query, devs: {"answer": query, "sources": [], "prior_rfis": [], "deviations": devs},
    )
    fallback = data.copilot(CopilotQuery(query="What failed?"))
    assert fallback["answer"] == "What failed?"
    assert fallback["deviations"] == [{"id": "D-1"}]

    monkeypatch.setattr(data, "_compute_metrics", lambda: (_ for _ in ()).throw(RuntimeError("metrics failed")))
    metrics = data.metrics()
    assert metrics["error"] == "metrics temporarily unavailable"
    assert metrics["citation_faithfulness"] is None


def test_benchmark_headline_handles_missing_evidence_file(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(data, "CORPUS", tmp_path / "data" / "corpus")
    assert data._benchmark_headline() == {"note": "benchmark card unavailable"}
