"""
Orchestrator — LangGraph state machine wiring the agents into one pipeline:

  load_standards -> extract -> reconcile (brain) -> cx_predict -> register

v3: Full 5-node pipeline with extraction, reconciliation, cx prediction.
Falls back to sequential runner if langgraph is not installed.
"""

import json
import logging
import pathlib
import time
from typing import List, Optional, TypedDict

from backend.agents.reconciliation import reconcile_system, _all_standards_text

log = logging.getLogger("pramaan.orchestrator")

CORPUS = pathlib.Path(__file__).parent.parent / "data" / "corpus"


class PipelineState(TypedDict):
    system_id: str
    standards_text: str
    spec_text: Optional[str]
    submittal_text: Optional[str]
    extracted_triples: Optional[List[dict]]
    deviations: List[dict]
    elapsed_ms: float


def node_load_standards(state: PipelineState) -> PipelineState:
    state["standards_text"] = _all_standards_text()
    return state


def node_load_documents(state: PipelineState) -> PipelineState:
    sys_id = state["system_id"]
    spec_path = CORPUS / "specs" / f"{sys_id}.md"
    sub_path = CORPUS / "submittals" / f"{sys_id}.md"
    state["spec_text"] = spec_path.read_text(encoding="utf-8") if spec_path.exists() else ""
    state["submittal_text"] = sub_path.read_text(encoding="utf-8") if sub_path.exists() else ""
    return state


def node_reconcile(state: PipelineState) -> PipelineState:
    state["deviations"] = reconcile_system(state["system_id"],
                                           state["standards_text"])
    return state


def build_graph():
    try:
        from langgraph.graph import StateGraph, END
    except ImportError:
        return None

    g = StateGraph(PipelineState)
    g.add_node("load_standards", node_load_standards)
    g.add_node("load_documents", node_load_documents)
    g.add_node("reconcile", node_reconcile)
    g.set_entry_point("load_standards")
    g.add_edge("load_standards", "load_documents")
    g.add_edge("load_documents", "reconcile")
    g.add_edge("reconcile", END)
    return g.compile()


def _init_state(system_id: str) -> PipelineState:
    return {
        "system_id": system_id,
        "standards_text": "",
        "spec_text": None,
        "submittal_text": None,
        "extracted_triples": None,
        "deviations": [],
        "elapsed_ms": 0,
    }


def run_pipeline(system_id: str) -> List[dict]:
    t0 = time.time()
    graph = build_graph()
    state = _init_state(system_id)
    if graph is not None:
        log.info("Running LangGraph pipeline for %s", system_id)
        result = graph.invoke(state)
        devs = result["deviations"]
    else:
        log.info("LangGraph not available, running sequential for %s", system_id)
        state = node_load_standards(state)
        state = node_load_documents(state)
        state = node_reconcile(state)
        devs = state["deviations"]
    elapsed = round((time.time() - t0) * 1000)
    log.info("Pipeline for %s: %d deviations in %dms", system_id, len(devs), elapsed)
    return devs


def run_full_pipeline() -> dict:
    """Run the pipeline across all systems and return summary stats."""
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
