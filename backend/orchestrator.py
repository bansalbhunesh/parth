"""
Orchestrator — LangGraph agent graph with conditional routing and TWO bounded
cycles (so this is a real agent, not a straight pipeline):

  [ingest -> load_standards -> validate] --(docs)--> reconcile -> retrieve -> critique
                                     └──(no docs)──> format_output
   retrieve --(fetched a missing cited standard)--> reconcile   <- cycle 1 (tool-call)
   critique --(self-check fails, budget left)-----> reconcile   <- cycle 2 (reflexion)
   critique --(ok / budget spent)----------------> cx_predict -> format_output

Cycle 1 (retrieval, active by default — set PRAMAAN_RETRIEVAL=0 to disable —
bounded by PRAMAAN_MAX_RETRIEVALS): when a finding cites a standard absent from
the loaded context, a tool fetches it from the local KB and the graph loops back
to re-reason with it. The fetch is a deterministic local lookup; it only fires
when the cited standard is in the KB but not yet in context, so the worst-case
cost is a single extra reconcile pass. Cycle 2 (self-
critique, bounded by PRAMAAN_MAX_REVISIONS): the reconciler's findings are verified
and, on a failed self-check (a value already meeting spec, a duplicate, or a low-
confidence finding), the graph routes back to reconcile with the critique as
feedback. The verifier never drops a value merely for not being verbatim in the
docs — the best findings are derived (4000/103 = 38.8 h) or recalled (R-410A GWP
2088). Falls back to an equivalent sequential runner if langgraph is absent.
"""

import logging
import os
import re
import time
from typing import List, Literal, Optional, TypedDict

from backend.agents.commissioning import compute_risk_score, predict_cx_impact
from backend.agents.ingestion import ingest_system
from backend.agents.reconciliation import _all_standards_text, reconcile_system
from backend.agents.retrieval import retrieve_standard
from backend.paths import CORPUS

log = logging.getLogger("pramaan.orchestrator")

# ── Self-critique / reflexion loop configuration ─────────────────────
# The reconcile node feeds into a critique node that verifies its own output;
# on a failed self-check the graph loops BACK to reconcile (a genuine cycle, not
# a straight pipeline), bounded so it always terminates.
_MAX_REVISIONS = int(os.getenv("PRAMAAN_MAX_REVISIONS", "1"))   # extra reconcile passes
_LOW_CONF = float(os.getenv("PRAMAAN_LOW_CONF", "0.45"))        # re-examine below this
_LLM_CRITIQUE = os.getenv("PRAMAAN_LLM_CRITIQUE", "0") == "1"   # opt-in deeper critic

# Retrieval tool-call loop: when a finding cites a standard not in context, fetch
# it from the local KB and loop back to re-reason. Active by default; the fetch is
# a local lookup and only fires for an in-KB-but-missing citation, so it adds at
# most one reconcile pass. Set PRAMAAN_RETRIEVAL=0 to disable on latency-sensitive
# batch runs. The node + cycle always exist in the graph either way.
_RETRIEVAL = os.getenv("PRAMAAN_RETRIEVAL", "1") != "0"
_MAX_RETRIEVALS = int(os.getenv("PRAMAAN_MAX_RETRIEVALS", "1"))

_OMISSION_TOKENS = {
    "notstated", "na", "tbd", "missing", "omitted", "none", "",
    "tobeadvised", "pending", "onrequest", "availableonrequest",
}


def _norm(s):
    return re.sub(r"[^a-z0-9]+", "", str(s).strip().lower())


def _self_check(devs: List[dict]):
    """Deterministic verifier over the reconciler's own findings. It only auto-
    drops what is provably wrong — never a value that is merely 'not verbatim in
    the docs', because the system's best findings are DERIVED (4000/103 = 38.8 h)
    or RECALLED (R-410A GWP 2088), which by design do not appear in the source.

    Catches: (1) equality false positives — a value flagged that already meets
    the spec (the documented Sakura-type bug); (2) duplicate findings. Low-
    confidence findings are kept but flagged for re-examination in the loop.

    Returns (needs_revision, feedback, keep, issues)."""
    issues, keep, seen = [], [], set()
    for d in devs:
        req = _norm(d.get("required_value"))
        prov = _norm(d.get("provided_value"))
        omission = (prov in _OMISSION_TOKENS) or ("notstated" in prov)
        label = f"{d.get('component')}/{d.get('parameter')}"
        if req and req == prov and not omission:
            issues.append(f"{label}: provided value equals required ({d.get('required_value')}) "
                          f"— compliant, not a deviation (false positive).")
            continue  # safe to drop
        sig = (_norm(d.get("component")), _norm(d.get("parameter")), req, prov)
        if sig in seen:
            issues.append(f"{label}: duplicate finding.")
            continue  # safe to drop
        seen.add(sig)
        conf = d.get("confidence")
        if isinstance(conf, (int, float)) and conf < _LOW_CONF:
            issues.append(f"{label}: low confidence ({conf}); re-verify against the documents or drop.")
        keep.append(d)
    feedback = ""
    if issues:
        feedback = (
            "A self-review of your previous findings flagged:\n- "
            + "\n- ".join(issues)
            + "\nRemove any finding where the submittal MEETS or EXCEEDS the design basis "
            "(those are compliant), remove duplicates, and re-verify each low-confidence "
            "finding — keep it only if it is a genuine non-conformance you can point to in "
            "the documents. Keep all legitimate deviations, including values you derived or "
            "recalled from domain knowledge."
        )
    return bool(issues), feedback, keep, issues


def _llm_critique(devs, spec, submittal, standards):
    """Opt-in deeper critic (PRAMAAN_LLM_CRITIQUE=1): a second model pass that
    looks for subtle false positives and missed deviations the deterministic
    check cannot see. Returns {needs_revision, feedback} or {} on any failure."""
    import json as _json

    from backend.llm import complete_json
    prompt = (
        "You are a senior CxA peer-reviewing another reviewer's deviation findings.\n"
        f"DESIGN BASIS:\n{spec}\n\nSUBMITTAL:\n{submittal}\n\n"
        f"FINDINGS TO REVIEW:\n{_json.dumps(devs, indent=2)}\n\n"
        "Identify (a) any finding that is actually compliant (false positive) and "
        "(b) any genuine deviation that was MISSED. Return JSON: "
        '{"needs_revision": <bool>, "feedback": "<concise, specific guidance>"}.'
    )
    try:
        r = complete_json(prompt, system="You are a meticulous commissioning peer reviewer.")
        if isinstance(r, dict) and r.get("needs_revision"):
            return {"needs_revision": True, "feedback": str(r.get("feedback", ""))}
    except Exception as exc:
        log.info("LLM critique skipped: %s", exc)
    return {}


class PipelineState(TypedDict):
    system_id: str
    standards_text: str
    spec_text: Optional[str]
    submittal_text: Optional[str]
    ingestion_meta: Optional[dict]
    extracted_triples: Optional[List[dict]]
    deviations: List[dict]
    elapsed_ms: float
    iteration: int
    critique: Optional[dict]
    revision_count: int
    retrieval_count: int
    retrieved: List[str]
    retrieval_log: List[str]
    # Routing flag for the retrieval cycle. Declared as a real channel so it
    # survives state reduction on every pinned langgraph version (rather than
    # relying on the conditional-edge seeing the node's returned dict).
    _retrieve_again: bool


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
    state["iteration"] = state.get("iteration", 0) + 1
    feedback = (state.get("critique") or {}).get("feedback")
    prior = state.get("deviations") or []
    if feedback:
        log.info("Reconcile pass %d for %s (revising on self-critique)",
                 state["iteration"], state["system_id"])
    revised = reconcile_system(state["system_id"],
                               state["standards_text"],
                               feedback=feedback)
    # Best-so-far retention: a revision pass must refine, never regress. If the
    # second pass throttles to [] or returns fewer findings than the prior pass
    # (e.g. LLMError swallowed -> []), keep the prior result rather than letting a
    # degraded retry silently erase legitimate findings.
    if feedback and len(revised) < len(prior):
        log.warning("Revision for %s returned %d < prior %d; keeping prior findings",
                    state["system_id"], len(revised), len(prior))
        state["deviations"] = prior
    else:
        state["deviations"] = revised
    return state


def _retrieve_missing_standards(
    deviations: list[dict], standards: str, already: set[str]
) -> tuple[list[str], list[str]]:
    additions: list[str] = []
    fetched: list[str] = []
    normalized_standards = _norm(standards)
    for deviation in deviations:
        reference = str(deviation.get("standard_ref") or "").strip()
        ignored = not reference or reference.upper() == "DESIGN-BASIS" or reference in already
        if ignored or _norm(reference) in normalized_standards:
            continue
        text = retrieve_standard(reference)
        if text:
            additions.append(f"\n\n=== RETRIEVED STANDARD: {reference} ===\n{text}")
            fetched.append(reference)
    return additions, fetched


def _apply_retrieved_standards(
    state: PipelineState,
    standards: str,
    already: set[str],
    additions: list[str],
    fetched: list[str],
) -> None:
    state["standards_text"] = standards + "".join(additions)
    state["retrieved"] = sorted(already | set(fetched))
    state["retrieval_count"] = state.get("retrieval_count", 0) + 1
    state["retrieval_log"] = fetched
    log.info("Retrieved %d standard(s) for %s %s; re-reconciling", len(fetched), state["system_id"], fetched)


def node_retrieve(state: PipelineState) -> PipelineState:
    """Retrieval tool-call node. If a finding cites a governing standard that is
    not already in the loaded context, fetch it from the local KB, append it to
    the standards, and signal a loop back to reconcile so the model can re-reason
    with the new context. Bounded by _MAX_RETRIEVALS; a no-op unless enabled."""
    if not _RETRIEVAL:
        state["_retrieve_again"] = False
        return state
    devs = state.get("deviations") or []
    standards = state.get("standards_text") or ""
    already = set(state.get("retrieved") or [])
    additions, fetched = _retrieve_missing_standards(devs, standards, already)
    can_loop = bool(fetched) and state.get("retrieval_count", 0) < _MAX_RETRIEVALS
    if can_loop:
        _apply_retrieved_standards(state, standards, already, additions, fetched)
    state["_retrieve_again"] = can_loop
    return state


def route_after_retrieve(state: PipelineState) -> Literal["reconcile", "critique"]:
    return "reconcile" if state.get("_retrieve_again") else "critique"


def node_critique(state: PipelineState) -> PipelineState:
    """Self-critique node — the reflexion step. Verifies the reconciler's own
    findings; if the check fails and revision budget remains, marks the state so
    the graph loops BACK to reconcile. On the final pass it applies the safe
    deterministic cleanup (drop equality false-positives / duplicates)."""
    devs = state.get("deviations") or []
    spec = state.get("spec_text") or ""
    sub = state.get("submittal_text") or ""
    needs, feedback, keep, issues = _self_check(devs)

    if _LLM_CRITIQUE and devs:
        deeper = _llm_critique(devs, spec, sub, state.get("standards_text", ""))
        if deeper.get("needs_revision"):
            needs = True
            feedback = (feedback + "\n" + deeper.get("feedback", "")).strip()
            issues = issues + ["peer-review: " + deeper.get("feedback", "")]

    rev = state.get("revision_count", 0)
    revise = bool(needs and rev < _MAX_REVISIONS)
    state["critique"] = {
        "needs_revision": revise,
        "revision_count": rev,
        "issues": issues,
        "feedback": feedback,
        "dropped": 0,
    }
    if revise:
        state["revision_count"] = rev + 1
    else:
        if len(keep) != len(devs):
            state["critique"]["dropped"] = len(devs) - len(keep)
            log.info("Self-critique cleaned %d finding(s) for %s",
                     len(devs) - len(keep), state["system_id"])
        state["deviations"] = keep
    return state


def route_after_critique(state: PipelineState) -> Literal["reconcile", "cx_predict"]:
    return "reconcile" if (state.get("critique") or {}).get("needs_revision") else "cx_predict"


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
        from langgraph.graph import END, StateGraph
    except ImportError:
        return None

    g = StateGraph(PipelineState)
    g.add_node("ingest", node_ingest)
    g.add_node("load_standards", node_load_standards)
    g.add_node("validate", node_validate)
    g.add_node("reconcile", node_reconcile)
    g.add_node("retrieve", node_retrieve)
    g.add_node("critique", node_critique)
    g.add_node("cx_predict", node_cx_predict)
    g.add_node("format_output", node_format_output)

    g.set_entry_point("ingest")
    g.add_edge("ingest", "load_standards")
    g.add_edge("load_standards", "validate")
    g.add_conditional_edges("validate", route_after_validate, {
        "reconcile": "reconcile",
        "format_output": "format_output",
    })
    g.add_edge("reconcile", "retrieve")
    # Cycle 1 — retrieval tool-call: if a cited standard was missing from context
    # and got fetched, loop back to reconcile (bounded by _MAX_RETRIEVALS).
    g.add_conditional_edges("retrieve", route_after_retrieve, {
        "reconcile": "reconcile",
        "critique": "critique",
    })
    # Cycle 2 — self-critique: route back to reconcile on a failed self-check
    # (bounded by _MAX_REVISIONS), else forward to cx_predict.
    g.add_conditional_edges("critique", route_after_critique, {
        "reconcile": "reconcile",
        "cx_predict": "cx_predict",
    })
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
        "iteration": 0,
        "critique": None,
        "revision_count": 0,
        "retrieval_count": 0,
        "retrieved": [],
        "retrieval_log": [],
        "_retrieve_again": False,
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
            while True:  # retrieval + reflexion cycles, both bounded
                state = node_reconcile(state)
                state = node_retrieve(state)
                if route_after_retrieve(state) == "reconcile":
                    continue
                state = node_critique(state)
                if route_after_critique(state) == "reconcile":
                    continue
                break
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
