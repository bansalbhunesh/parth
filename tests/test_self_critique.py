"""Tests for the orchestrator self-critique / reflexion loop.

The loop must (1) genuinely improve output by removing the documented false-
positive class, (2) NEVER drop a legitimate derived/recalled finding, and
(3) always terminate (bounded revisions).
"""

import backend.orchestrator as orch
from backend.orchestrator import (
    _self_check, node_reconcile, node_critique, route_after_critique,
    route_after_validate, build_graph, _init_state,
)


def _dev(comp, param, req, prov, conf=0.9):
    return {"component": comp, "parameter": param, "required_value": req,
            "provided_value": prov, "confidence": conf}


def test_self_check_drops_equality_false_positive():
    devs = [_dev("COOL-01", "redundancy", "N+1", "N+1")]  # provided meets spec
    needs, fb, keep, issues = _self_check(devs)
    assert needs is True
    assert keep == []          # the false positive is removed
    assert "compliant" in fb.lower()


def test_self_check_keeps_derived_and_recalled_findings():
    """The crown-jewel findings are NOT verbatim in the docs — must be kept."""
    devs = [
        _dev("GEN-FUEL", "onsite_fuel_hours", "48", "38.8"),   # derived arithmetic
        _dev("COOL-01", "refrigerant_gwp", "750", "2088"),     # recalled GWP
    ]
    needs, fb, keep, issues = _self_check(devs)
    assert needs is False
    assert len(keep) == 2


def test_self_check_drops_duplicates():
    devs = [_dev("UPS-02", "battery_runtime_min", "10", "7"),
            _dev("UPS-02", "battery_runtime_min", "10", "7")]
    _, _, keep, _ = _self_check(devs)
    assert len(keep) == 1


def test_self_check_flags_low_confidence_but_keeps():
    devs = [_dev("X", "y", "10", "7", conf=0.2)]
    needs, fb, keep, issues = _self_check(devs)
    assert needs is True          # triggers re-examination
    assert len(keep) == 1         # but not auto-dropped
    assert "low confidence" in fb.lower()


def test_loop_removes_false_positive_and_terminates(monkeypatch):
    """End-to-end: first pass emits a false positive; the loop feeds a critique
    back, the revised pass drops it, and the loop stops. Proves the cycle works."""
    calls = {"n": 0}

    def fake_reconcile(sys_id, standards_text, feedback=None):
        calls["n"] += 1
        if feedback:  # revised pass — the model corrected itself
            return [_dev("GEN-01", "start_time_sec", "10", "15")]
        return [_dev("COOL-01", "redundancy", "N+1", "N+1"),    # false positive
                _dev("GEN-01", "start_time_sec", "10", "15")]   # real deviation

    monkeypatch.setattr(orch, "reconcile_system", fake_reconcile)
    monkeypatch.setattr(orch, "_MAX_REVISIONS", 1)

    state = _init_state("HELIOS")
    state["spec_text"], state["submittal_text"] = "spec", "sub"
    while True:
        state = node_reconcile(state)
        state = node_critique(state)
        if route_after_critique(state) != "reconcile":
            break

    comps = {d["component"] for d in state["deviations"]}
    assert comps == {"GEN-01"}          # false positive gone, real one kept
    assert calls["n"] == 2              # exactly one revision pass
    assert state["iteration"] == 2


def test_loop_is_bounded_even_if_model_never_fixes(monkeypatch):
    """If revision never clears the issue, the loop must still terminate."""
    def stubborn(sys_id, standards_text, feedback=None):
        return [_dev("COOL-01", "redundancy", "N+1", "N+1")]  # always a FP

    monkeypatch.setattr(orch, "reconcile_system", stubborn)
    monkeypatch.setattr(orch, "_MAX_REVISIONS", 2)

    state = _init_state("X")
    state["spec_text"], state["submittal_text"] = "s", "u"
    passes = 0
    while True:
        state = node_reconcile(state)
        state = node_critique(state)
        passes += 1
        if route_after_critique(state) != "reconcile":
            break
        assert passes <= 5, "loop failed to terminate"
    assert state["iteration"] <= 3            # 1 initial + up to 2 revisions
    assert state["deviations"] == []          # final cleanup still drops the FP


def test_graph_has_critique_cycle():
    g = build_graph()
    if g is not None:
        assert hasattr(g, "invoke")
    # router returns both legs
    assert route_after_critique({"critique": {"needs_revision": True}}) == "reconcile"
    assert route_after_critique({"critique": {"needs_revision": False}}) == "cx_predict"
