"""Tests for deterministic evidence-strength scoring."""

from __future__ import annotations

from backend.agents.evidence_strength import _band, evidence_report, score_evidence


def test_full_signal_finding_scores_strong() -> None:
    dev = {
        "component": "UPS-02",
        "parameter": "battery_runtime_min",
        "required_value": "10 min",
        "provided_value": "7 min",
        "cx_source": "rule",
        "standard_ref": "Uptime Tier IV",
        "spec_clause": "DB-1.1",
        "citation_faithful": True,
    }
    out = score_evidence(dev)
    assert out["score"] == 1.0
    assert out["band"] == "Strong"
    assert out["missing"] == []
    assert "exact numeric mismatch" in out["signals"]
    assert out["target"] == "UPS-02/battery_runtime_min"


def test_llm_only_textual_finding_scores_thin() -> None:
    dev = {
        "component": "BMS",
        "parameter": "notes",
        "required_value": "compliant",
        "provided_value": "unclear",
        "cx_source": "llm",
    }
    out = score_evidence(dev)
    assert out["score"] == 0.0  # no numeric, not rule-grounded, no citations
    assert out["band"] == "Thin"
    assert "exact numeric mismatch" in out["missing"]


def test_partial_signals_land_in_moderate_band() -> None:
    dev = {
        "component": "SWGR",
        "parameter": "rating",
        "required_value": 65,
        "provided_value": 50,
        "cx_source": "graph",
        "standard_ref": "IEC 61439",
    }
    # 0.30 numeric + 0.25 graph + 0.20 standard = 0.75 -> Moderate
    out = score_evidence(dev)
    assert out["score"] == 0.75
    assert out["band"] == "Moderate"


def test_numeric_mismatch_requires_two_parseable_and_different_numbers() -> None:
    same = {"component": "A", "parameter": "x", "required_value": "5 m", "provided_value": "5 m"}
    assert "exact numeric mismatch" in score_evidence(same)["missing"]
    one_missing = {"component": "A", "parameter": "x", "required_value": "N+1", "provided_value": "N"}
    assert "exact numeric mismatch" in score_evidence(one_missing)["missing"]
    differ = {"component": "A", "parameter": "x", "required_value": "400 V", "provided_value": "380 V"}
    assert "exact numeric mismatch" in score_evidence(differ)["signals"]


def test_band_thresholds() -> None:
    assert _band(0.80) == "Strong"
    assert _band(0.50) == "Moderate"
    assert _band(0.25) == "Weak"
    assert _band(0.10) == "Thin"


def test_report_summarises_and_ignores_non_dicts() -> None:
    devs = [
        {"component": "A", "parameter": "x", "required_value": 10, "provided_value": 7,
         "cx_source": "rule", "standard_ref": "S", "spec_clause": "C", "citation_faithful": True},
        {"component": "B", "parameter": "y", "required_value": "n/a", "provided_value": "n/a", "cx_source": "llm"},
        "garbage",
        None,
    ]
    report = evidence_report(devs)
    assert report["count"] == 2
    assert report["strong_count"] == 1
    assert report["thin_count"] == 1
    assert len(report["findings"]) == 2
    assert "not a probability of correctness" in report["basis"]


def test_empty_report_is_well_formed() -> None:
    report = evidence_report([])
    assert report["count"] == 0
    assert report["findings"] == []
    assert report["strong_count"] == 0
    assert report["thin_count"] == 0
