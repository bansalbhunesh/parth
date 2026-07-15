"""Tests for the deterministic Compound Risk Layer."""

from __future__ import annotations

from backend.agents.compound_risk import _band, _combine, analyze_compound_risk


def _dev(component: str, parameter: str, **kw) -> dict:
    dev = {"component": component, "parameter": parameter, "severity": "Major"}
    dev.update(kw)
    return dev


def test_empty_input_is_low_risk_with_no_clusters() -> None:
    out = analyze_compound_risk([])
    assert out["project_compound_risk"] == 0.0
    assert out["risk_band"] == "Low"
    assert out["deviation_count"] == 0
    assert out["clusters"] == []
    assert out["schedule_cliff"] is None
    assert out["converged_cx_tests"] == []


def test_single_deviation_has_no_cluster_but_carries_project_risk() -> None:
    out = analyze_compound_risk([_dev("UPS-02", "battery_runtime_min")])
    assert out["deviation_count"] == 1
    assert out["clusters"] == []
    assert out["project_compound_risk"] == 0.6  # a lone Major
    assert out["risk_band"] == "High"


def test_two_deviations_on_same_cx_test_compound_above_each() -> None:
    devs = [
        _dev("UPS-02", "battery_runtime_min", predicted_cx_test="IST-07"),
        _dev("BATT-01", "cell_balance", predicted_cx_test="IST-07"),
    ]
    out = analyze_compound_risk(devs)
    assert "IST-07" in out["converged_cx_tests"]
    cx = [c for c in out["clusters"] if c["kind"] == "cx_test"][0]
    assert cx["member_count"] == 2
    assert cx["compound_risk"] == 0.84  # 1 - 0.4*0.4
    assert cx["compound_risk"] > 0.6  # worse than either finding alone
    assert cx["members"] == ["BATT-01/cell_balance", "UPS-02/battery_runtime_min"]


def test_system_convergence_forms_a_system_cluster() -> None:
    devs = [
        _dev("A", "x", system="COOLING"),
        _dev("B", "y", system="COOLING"),
        _dev("C", "z", system="POWER"),
    ]
    out = analyze_compound_risk(devs)
    systems = [c for c in out["clusters"] if c["kind"] == "system"]
    assert len(systems) == 1
    assert systems[0]["key"] == "COOLING"
    assert systems[0]["member_count"] == 2


def test_schedule_cliff_is_the_soonest_shared_failure_week() -> None:
    devs = [
        _dev("A", "x", week_fail=44),
        _dev("B", "y", week_fail=44),
        _dev("C", "z", week_fail=60),  # alone at 60 -> no cluster
    ]
    out = analyze_compound_risk(devs)
    cliff = out["schedule_cliff"]
    assert cliff is not None
    assert cliff["week_fail"] == 44
    assert cliff["converging_deviations"] == 2


def test_more_convergence_raises_compound_risk() -> None:
    two = analyze_compound_risk(
        [_dev("A", "x", predicted_cx_test="T1"), _dev("B", "y", predicted_cx_test="T1")]
    )
    three = analyze_compound_risk(
        [
            _dev("A", "x", predicted_cx_test="T1"),
            _dev("B", "y", predicted_cx_test="T1"),
            _dev("C", "z", predicted_cx_test="T1"),
        ]
    )
    two_r = [c for c in two["clusters"] if c["kind"] == "cx_test"][0]["compound_risk"]
    three_r = [c for c in three["clusters"] if c["kind"] == "cx_test"][0]["compound_risk"]
    assert three_r > two_r


def test_critical_deviations_saturate_to_critical_band() -> None:
    devs = [
        _dev("A", "x", severity="Critical", predicted_cx_test="T1"),
        _dev("B", "y", severity="Critical", predicted_cx_test="T1"),
    ]
    out = analyze_compound_risk(devs)
    assert out["project_compound_risk"] == 1.0
    assert out["risk_band"] == "Critical"


def test_robust_to_messy_and_non_dict_entries() -> None:
    devs = [
        {"component": "A"},  # missing parameter/severity
        _dev("B", "y", week_fail="not-a-week", predicted_cx_test="T1"),
        _dev("C", "z", week_fail="not-a-week", predicted_cx_test="T1"),
        "garbage",  # non-dict, must be ignored
        None,
    ]
    out = analyze_compound_risk(devs)  # must not raise
    assert out["deviation_count"] == 3  # two _dev plus the {"component": "A"} dict
    assert out["schedule_cliff"] is None  # non-int weeks cannot cluster
    cx = [c for c in out["clusters"] if c["kind"] == "cx_test"]
    assert cx and cx[0]["earliest_week_fail"] is None


def test_deviation_risk_survives_an_uncomputable_score() -> None:
    # A lead time the scorer cannot compare (str vs int) must degrade to 0, not crash.
    devs = [
        _dev("A", "x", lead_time_weeks="soon", predicted_cx_test="T9"),
        _dev("B", "y", lead_time_weeks="soon", predicted_cx_test="T9"),
    ]
    out = analyze_compound_risk(devs)
    cx = [c for c in out["clusters"] if c["kind"] == "cx_test"][0]
    assert cx["member_count"] == 2
    assert cx["compound_risk"] == 0.0  # both findings scored 0 from the bad lead time


def test_band_and_combine_helpers_are_consistent() -> None:
    assert _band(0.86) == "Critical"
    assert _band(0.61) == "High"
    assert _band(0.36) == "Moderate"
    assert _band(0.10) == "Low"
    assert _combine([0.5, 0.5]) == 0.75  # 1 - 0.25
    assert _combine([]) == 0.0
