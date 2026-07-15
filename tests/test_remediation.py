"""Tests for the deterministic Remediation Intelligence planner."""

from __future__ import annotations

from backend.agents.remediation import plan_remediation


def _dev(component: str, parameter: str, **kw) -> dict:
    dev = {"component": component, "parameter": parameter, "severity": "Major"}
    dev.update(kw)
    return dev


def test_empty_input_has_no_actions() -> None:
    out = plan_remediation([])
    assert out["actions"] == []
    assert out["highest_leverage"] is None
    assert out["has_convergence"] is False
    assert "independent" in out["note"]


def test_independent_findings_are_ranked_without_clusters() -> None:
    out = plan_remediation([_dev("A", "x"), _dev("B", "y")])
    kinds = {a["kind"] for a in out["actions"]}
    assert kinds == {"fix_deviation"}
    assert out["has_convergence"] is False
    # two lone Majors: base 0.84, fixing one leaves 0.6 -> reduction 0.24
    assert all(a["risk_reduction"] == 0.24 for a in out["actions"])


def test_converged_gate_makes_the_cluster_fix_dominant() -> None:
    # Two Critical findings both fail commissioning test T1.
    devs = [
        _dev("A", "x", severity="Critical", predicted_cx_test="T1"),
        _dev("B", "y", severity="Critical", predicted_cx_test="T1"),
    ]
    out = plan_remediation(devs)
    assert out["has_convergence"] is True
    top = out["highest_leverage"]
    assert top["kind"] == "clear_cluster"
    assert top["risk_reduction"] == 1.0
    # The killer insight: fixing ONE of a converged set moves the number by nothing,
    # because its sibling still fails the same gate.
    solo = [a for a in out["actions"] if a["kind"] == "fix_deviation"]
    assert solo and all(a["risk_reduction"] == 0.0 for a in solo)
    assert "cluster" in out["note"]


def test_cluster_fix_beats_solo_fix_for_major_convergence() -> None:
    devs = [
        _dev("A", "x", predicted_cx_test="T1"),
        _dev("B", "y", predicted_cx_test="T1"),
    ]
    out = plan_remediation(devs)
    cluster = [a for a in out["actions"] if a["kind"] == "clear_cluster"][0]
    solo = [a for a in out["actions"] if a["kind"] == "fix_deviation"][0]
    assert cluster["risk_reduction"] == 0.84  # clears the whole gate
    assert solo["risk_reduction"] == 0.24  # sibling remains
    assert cluster["risk_reduction"] > solo["risk_reduction"]


def test_clearing_a_week_cluster_clears_the_schedule_cliff() -> None:
    devs = [
        _dev("A", "x", week_fail=44),
        _dev("B", "y", week_fail=44),
    ]
    out = plan_remediation(devs)
    cluster = [a for a in out["actions"] if a["kind"] == "clear_cluster"][0]
    assert cluster["clears_schedule_cliff"] is True
    assert cluster["new_schedule_cliff_week"] is None


def test_actions_are_sorted_by_leverage() -> None:
    out = plan_remediation(
        [
            _dev("A", "x", severity="Critical", predicted_cx_test="T1"),
            _dev("B", "y", severity="Critical", predicted_cx_test="T1"),
            _dev("C", "z", severity="Minor"),
        ]
    )
    reductions = [a["risk_reduction"] for a in out["actions"]]
    assert reductions == sorted(reductions, reverse=True)
    assert out["highest_leverage"] is out["actions"][0]


def test_system_convergence_yields_a_cluster_fix() -> None:
    devs = [
        _dev("A", "x", system="COOLING"),
        _dev("B", "y", system="COOLING"),
        _dev("C", "z", system="POWER"),
    ]
    out = plan_remediation(devs)
    cluster = [a for a in out["actions"] if a["kind"] == "clear_cluster"]
    assert cluster and cluster[0]["target"] == "COOLING (system)"
    assert cluster[0]["resolves"] == ["A/x", "B/y"]


def test_robust_to_messy_weeks_and_non_dict_entries() -> None:
    devs = [
        _dev("A", "x", week_fail=30),
        _dev("B", "y", week_fail=30),
        _dev("C", "z", week_fail="soon"),  # uncoercible week
        "garbage",
        None,
    ]
    out = plan_remediation(devs)  # must not raise
    assert out["has_convergence"] is True  # A,B converge at week 30
    assert any(a["kind"] == "clear_cluster" for a in out["actions"])
