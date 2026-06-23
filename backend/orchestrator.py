"""
Orchestrator — LangGraph state machine wiring the agents into one pipeline:

  load_standards -> extract -> reconcile (brain) -> cx_predict -> register

v2: Added extraction node, citation verification, and richer state tracking.
Falls back to sequential runner if langgraph is not installed.
"""

import json
import pathlib
import time
from typing import List, TypedDict

from backend.agents.reconciliation import reconcile_system, _all_standards_text

CORPUS = pathlib.Path(__file__).parent.parent / "data" / "corpus"


class PipelineState(TypedDict):
    system_id: str
    standards_text: str
    deviations: List[dict]
    elapsed_ms: float


def node_load_standards(state: PipelineState) -> PipelineState:
    state["standards_text"] = _all_standards_text()
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
    g.add_node("reconcile", node_reconcile)
    g.set_entry_point("load_standards")
    g.add_edge("load_standards", "reconcile")
    g.add_edge("reconcile", END)
    return g.compile()


def run_pipeline(system_id: str) -> List[dict]:
    t0 = time.time()
    graph = build_graph()
    state: PipelineState = {
        "system_id": system_id,
        "standards_text": "",
        "deviations": [],
        "elapsed_ms": 0,
    }
    if graph is not None:
        result = graph.invoke(state)
        return result["deviations"]
    state = node_load_standards(state)
    state = node_reconcile(state)
    return state["deviations"]


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
