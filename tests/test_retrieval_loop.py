"""Tests for the standards retrieval tool and the retrieval tool-call loop."""

import backend.orchestrator as orch
from backend.agents.retrieval import available_standards, retrieve_standard
from backend.orchestrator import (
    _init_state,
    build_graph,
    node_retrieve,
    route_after_retrieve,
)


# ── the retrieval tool ───────────────────────────────────────────────
def test_retrieve_known_standard_by_key():
    txt = retrieve_standard("UPTIME-TIER4")
    assert txt and len(txt) > 50


def test_retrieve_known_standard_by_alias():
    assert retrieve_standard("Uptime Tier IV") is not None
    assert retrieve_standard("TIA-942") is not None


def test_retrieve_unknown_standard_returns_none():
    # Not in the scraped KB — the tool must say "no", not return a wrong sibling.
    assert retrieve_standard("IEC 61439-6") is None
    assert retrieve_standard("NFPA 110") is None  # must NOT resolve to NFPA-75
    assert retrieve_standard("") is None


def test_available_standards_nonempty():
    assert len(available_standards()) >= 5


# ── the loop node ────────────────────────────────────────────────────
def test_retrieval_active_by_default():
    # The second cycle must be live on the default path (no env override),
    # otherwise the "two bounded cycles" claim is only true behind a flag.
    import os
    if os.getenv("PRAMAAN_RETRIEVAL") == "0":
        return  # caller explicitly opted out; default-on is the shipped behaviour
    assert orch._RETRIEVAL is True


def test_retrieve_node_loops_on_default(monkeypatch):
    # With the shipped default (no flag flip), an in-KB-but-missing citation
    # should fetch and loop back to reconcile.
    monkeypatch.setattr(orch, "_MAX_RETRIEVALS", 1)
    state = _init_state("X")
    state["deviations"] = [{"standard_ref": "UPTIME-TIER4", "required_value": "10", "provided_value": "7"}]
    state["standards_text"] = "unrelated standards text"
    state = node_retrieve(state)
    assert route_after_retrieve(state) == "reconcile"
    assert state["retrieval_count"] == 1


def test_retrieve_node_is_noop_when_disabled(monkeypatch):
    monkeypatch.setattr(orch, "_RETRIEVAL", False)
    state = _init_state("X")
    state["deviations"] = [{"standard_ref": "UPTIME-TIER4", "required_value": "10", "provided_value": "7"}]
    state["standards_text"] = ""
    state = node_retrieve(state)
    assert route_after_retrieve(state) == "critique"   # no loop by default
    assert state.get("retrieval_count", 0) == 0


def test_retrieve_node_loops_when_standard_missing(monkeypatch):
    monkeypatch.setattr(orch, "_RETRIEVAL", True)
    monkeypatch.setattr(orch, "_MAX_RETRIEVALS", 1)
    state = _init_state("X")
    state["deviations"] = [{"standard_ref": "UPTIME-TIER4", "required_value": "10", "provided_value": "7"}]
    state["standards_text"] = "some other standards text without the cited one"

    state = node_retrieve(state)
    assert route_after_retrieve(state) == "reconcile"          # fetched -> loop back
    assert state["retrieval_count"] == 1
    assert "UPTIME-TIER4" in state["retrieved"]
    assert "RETRIEVED STANDARD: UPTIME-TIER4" in state["standards_text"]

    # Second pass: budget spent / already in context -> no more looping.
    state = node_retrieve(state)
    assert route_after_retrieve(state) == "critique"


def test_retrieve_node_no_loop_for_unknown_standard(monkeypatch):
    monkeypatch.setattr(orch, "_RETRIEVAL", True)
    state = _init_state("X")
    state["deviations"] = [{"standard_ref": "IEC 61439-6", "required_value": "65", "provided_value": "50"}]
    state["standards_text"] = ""
    state = node_retrieve(state)
    assert route_after_retrieve(state) == "critique"   # not in KB -> no fetch, no loop


def test_retrieve_skips_when_standard_already_in_context(monkeypatch):
    monkeypatch.setattr(orch, "_RETRIEVAL", True)
    state = _init_state("X")
    state["deviations"] = [{"standard_ref": "TIA-942", "required_value": "x", "provided_value": "y"}]
    state["standards_text"] = "... governing standard TIA-942 cabling ..."
    state = node_retrieve(state)
    assert route_after_retrieve(state) == "critique"   # already loaded -> nothing to fetch


def test_graph_has_retrieve_cycle():
    g = build_graph()
    if g is not None:
        assert hasattr(g, "invoke")
    assert route_after_retrieve({"_retrieve_again": True}) == "reconcile"
    assert route_after_retrieve({"_retrieve_again": False}) == "critique"
