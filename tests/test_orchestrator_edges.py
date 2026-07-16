"""Failure, cycle, and fallback contracts for the bounded agent orchestrator."""

from __future__ import annotations

import builtins

import pytest

from backend import orchestrator


def test_llm_critique_accepts_only_explicit_revision_and_fails_open(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "backend.llm.complete_json",
        lambda *_args, **_kwargs: {"needs_revision": True, "feedback": "Check the rating"},
    )
    assert orchestrator._llm_critique([], "spec", "submittal", "standard") == {
        "needs_revision": True,
        "feedback": "Check the rating",
    }

    monkeypatch.setattr("backend.llm.complete_json", lambda *_args, **_kwargs: ["unexpected shape"])
    assert orchestrator._llm_critique([], "spec", "submittal", "standard") == {}

    monkeypatch.setattr(
        "backend.llm.complete_json",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("provider unavailable")),
    )
    assert orchestrator._llm_critique([], "spec", "submittal", "standard") == {}


def test_ingest_classifies_documents_without_trusting_unknown_types(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        orchestrator,
        "ingest_system",
        lambda _system: {
            "total_documents": 3,
            "total_words": 6,
            "documents": [
                {"doc_type": "spec", "text": "owner"},
                {"doc_type": "submittal", "text": "vendor"},
                {"doc_type": "unknown", "text": "ignored"},
            ],
        },
    )
    state = orchestrator._init_state("UPS")

    result = orchestrator.node_ingest(state)

    assert result["spec_text"] == "owner"
    assert result["submittal_text"] == "vendor"
    assert result["ingestion_meta"] == {"total_documents": 3, "total_words": 6}


def test_optional_peer_critique_merges_feedback_and_respects_noop(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(orchestrator, "_LLM_CRITIQUE", True)
    monkeypatch.setattr(orchestrator, "_MAX_REVISIONS", 1)
    monkeypatch.setattr(orchestrator, "_self_check", lambda devs: (False, "", devs, []))
    monkeypatch.setattr(
        orchestrator,
        "_llm_critique",
        lambda *_args: {"needs_revision": True, "feedback": "Peer found an omission"},
    )
    state = orchestrator._init_state("UPS")
    state["deviations"] = [{"component": "UPS-1"}]

    revised = orchestrator.node_critique(state)

    assert revised["critique"]["needs_revision"] is True
    assert revised["critique"]["feedback"] == "Peer found an omission"
    assert revised["critique"]["issues"] == ["peer-review: Peer found an omission"]
    assert revised["revision_count"] == 1

    monkeypatch.setattr(orchestrator, "_llm_critique", lambda *_args: {})
    noop = orchestrator._init_state("UPS")
    noop["deviations"] = [{"component": "UPS-1"}]
    assert orchestrator.node_critique(noop)["critique"]["needs_revision"] is False


def test_cx_and_output_nodes_fill_only_missing_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        orchestrator,
        "predict_cx_impact",
        lambda finding: {"predicted_cx_test": f"test-{finding['id']}"},
    )
    monkeypatch.setattr(orchestrator, "compute_risk_score", lambda finding: 10 + finding["id"])
    state = orchestrator._init_state("UPS")
    state["deviations"] = [
        {"id": 1},
        {"id": 2, "predicted_cx_test": "preserved", "week_caught": 4},
    ]

    orchestrator.node_cx_predict(state)
    orchestrator.node_format_output(state)

    assert state["deviations"][0] == {
        "id": 1,
        "predicted_cx_test": "test-1",
        "risk_score": 11,
        "system": "UPS",
        "week_caught": 11,
    }
    assert state["deviations"][1]["predicted_cx_test"] == "preserved"
    assert state["deviations"][1]["risk_score"] == 12
    assert state["deviations"][1]["week_caught"] == 4


def test_build_graph_returns_none_when_langgraph_is_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    real_import = builtins.__import__

    def import_without_langgraph(name, *args, **kwargs):  # noqa: ANN001, ANN002, ANN003, ANN202
        if name == "langgraph.graph":
            raise ImportError("langgraph unavailable")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", import_without_langgraph)
    assert orchestrator.build_graph() is None


def test_sequential_pipeline_skips_reconciliation_when_documents_are_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(orchestrator, "build_graph", lambda: None)
    monkeypatch.setattr(orchestrator, "node_ingest", lambda state: state)
    monkeypatch.setattr(orchestrator, "node_load_standards", lambda state: state)
    monkeypatch.setattr(orchestrator, "route_after_validate", lambda _state: "format_output")
    assert orchestrator.run_pipeline("MISSING") == []


def test_sequential_pipeline_exercises_retrieval_and_reflexion_cycles(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(orchestrator, "build_graph", lambda: None)
    monkeypatch.setattr(orchestrator, "node_ingest", lambda state: state)
    monkeypatch.setattr(orchestrator, "node_load_standards", lambda state: state)
    monkeypatch.setattr(orchestrator, "route_after_validate", lambda _state: "reconcile")
    passes = {"reconcile": 0}

    def reconcile(state):  # noqa: ANN001, ANN202
        passes["reconcile"] += 1
        state["deviations"] = [{"component": "UPS-1"}]
        return state

    retrieve_routes = iter(("reconcile", "critique", "critique"))
    critique_routes = iter(("reconcile", "cx_predict"))
    monkeypatch.setattr(orchestrator, "node_reconcile", reconcile)
    monkeypatch.setattr(orchestrator, "node_retrieve", lambda state: state)
    monkeypatch.setattr(orchestrator, "route_after_retrieve", lambda _state: next(retrieve_routes))
    monkeypatch.setattr(orchestrator, "node_critique", lambda state: state)
    monkeypatch.setattr(orchestrator, "route_after_critique", lambda _state: next(critique_routes))
    monkeypatch.setattr(orchestrator, "node_cx_predict", lambda state: state)

    result = orchestrator.run_pipeline("UPS")

    assert passes["reconcile"] == 3
    assert result == [{"component": "UPS-1", "system": "UPS", "week_caught": 11}]
