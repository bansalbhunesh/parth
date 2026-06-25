"""
Orchestrator — LangGraph pipeline with conditional routing:
  [ingest, load_standards] -> validate -> reconcile -> cx_predict -> format_output
                                       └─(no docs)─> END (skip reconciliation)
Falls back to sequential runner if langgraph is not installed.
"""

import logging
import time
from typing import List, Literal, Optional, TypedDict

from backend.agents.ingestion import ingest_system
from backend.agents.reconciliation import reconcile_system, _all_standards_text
from backend.agents.commissioning import predict_cx_impact, compute_risk_score
from backend.paths import CORPUS

log = logging.getLogger("pramaan.orchestrator")


class PipelineState(TypedDict):
    system_id: str
    standards_text: str
    spec_text: Optional[str]
    submittal_text: Optional[str]
    ingestion_meta: Optional[dict]
    extracted_triples: Optional[List[dict]]
    deviations: List[dict]
    elapsed_ms: float


def node_ingest(state: PipelineState) -> PipelineState:
    sys_id = state["system_id"]
    result = ingest_system(sys_id)
    state["ingestion_meta"] = {
        "total_documents": result["total_documents"],
        "total_words": result["total_words"],
    }
    for doc in result["documents"]:
        if doc.get("doc_type") == "spec":
            state["spec_text"] = doc.get("text", "")
        elif doc.get("doc_type") == "submittal":
            state["submittal_text"] = doc.get("text", "")
    log.info("Ingested %s: %d docs, %d words",
             sys_id, result["total_documents"], result["total_words"])
    return state


def node_load_standards(state: PipelineState) -> PipelineState:
    state["standards_text"] = _all_standards_text()
    return state


def node_validate(state: PipelineState) -> PipelineState:
    return state


def route_after_validate(state: PipelineState) -> Literal["reconcile", "format_output"]:
    if not state.get("spec_text") or not state.get("submittal_text"):
        log.warning("System %s: missing spec or submittal, skipping reconciliation",
                    state["system_id"])
        return "format_output"
    return "reconcile"


def node_reconcile(state: PipelineState) -> PipelineState:
    state["deviations"] = reconcile_system(state["system_id"],
                                           state["standards_text"])
    return state


def node_cx_predict(state: PipelineState) -> PipelineState:
    for d in state["deviations"]:
        if not d.get("predicted_cx_test"):
            cx = predict_cx_impact(d)
            d.update(cx)
        d["risk_score"] = compute_risk_score(d)
    return state


def node_format_output(state: PipelineState) -> PipelineState:
    for d in state["deviations"]:
        d["system"] = state["system_id"]
        d.setdefault("week_caught", 11)
    return state


def build_graph():
    try:
        from langgraph.graph import StateGraph, END
    except ImportError:
        return None

    g = StateGraph(PipelineState)
    g.add_node("ingest", node_ingest)
    g.add_node("load_standards", node_load_standards)
    g.add_node("validate", node_validate)
    g.add_node("reconcile", node_reconcile)
    g.add_node("cx_predict", node_cx_predict)
    g.add_node("format_output", node_format_output)

    g.set_entry_point("ingest")
    g.add_edge("ingest", "load_standards")
    g.add_edge("load_standards", "validate")
    g.add_conditional_edges("validate", route_after_validate, {
        "reconcile": "reconcile",
        "format_output": "format_output",
    })
    g.add_edge("reconcile", "cx_predict")
    g.add_edge("cx_predict", "format_output")
    g.add_edge("format_output", END)
    return g.compile()


def _init_state(system_id: str) -> PipelineState:
    return {
        "system_id": system_id,
        "standards_text": "",
        "spec_text": None,
        "submittal_text": None,
        "ingestion_meta": None,
        "extracted_triples": None,
        "deviations": [],
        "elapsed_ms": 0,
    }


def run_pipeline(system_id: str) -> List[dict]:
    t0 = time.time()
    graph = build_graph()
    state = _init_state(system_id)
    if graph is not None:
        log.info("Running LangGraph 5-node pipeline for %s", system_id)
        result = graph.invoke(state)
        devs = result["deviations"]
    else:
        log.info("Running sequential pipeline for %s", system_id)
        state = node_ingest(state)
        state = node_load_standards(state)
        if route_after_validate(state) == "reconcile":
            state = node_reconcile(state)
            state = node_cx_predict(state)
        state = node_format_output(state)
        devs = state["deviations"]
    elapsed = round((time.time() - t0) * 1000)
    log.info("Pipeline for %s: %d deviations in %dms", system_id, len(devs), elapsed)
    return devs


def run_full_pipeline() -> dict:
    t0 = time.time()
    specs_dir = CORPUS / "specs"
    if not specs_dir.exists():
        return {"deviations": [], "systems": 0, "elapsed_ms": 0}

    all_devs = []
    system_results = {}
    for p in sorted(specs_dir.glob("*.md")):
        sys_id = p.stem
        devs = run_pipeline(sys_id)
        system_results[sys_id] = len(devs)
        all_devs.extend(devs)

    elapsed = round((time.time() - t0) * 1000)
    return {
        "deviations": all_devs,
        "systems_scanned": len(system_results),
        "per_system": system_results,
        "elapsed_ms": elapsed,
    }
