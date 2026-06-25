"""
Tests for the eval harness — verifies that the baseline reconciler achieves
perfect precision, recall, and F1 against the ground truth corpus.

These tests prove the plumbing is correct and the eval metrics are reproducible.
"""

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from eval.baseline_reconciler import reconcile
from eval.run_eval import load_ground_truth, score, key


CORPUS = pathlib.Path(__file__).parent.parent / "data" / "corpus"


class TestGroundTruth:
    def test_ground_truth_loads(self):
        gt = load_ground_truth()
        assert isinstance(gt, list)
        assert len(gt) == 14

    def test_ground_truth_has_required_fields(self):
        gt = load_ground_truth()
        required = {"id", "system", "component", "parameter", "required_value",
                     "provided_value", "unit", "severity", "predicted_cx_test"}
        for d in gt:
            missing = required - d.keys()
            assert not missing, f"{d['id']} missing: {missing}"

    def test_all_deviations_have_lead_time(self):
        gt = load_ground_truth()
        for d in gt:
            assert d.get("lead_time_weeks") is not None, f"{d['id']} has no lead_time"
            assert d["lead_time_weeks"] > 0

    def test_severity_distribution(self):
        gt = load_ground_truth()
        sev = {d["severity"] for d in gt}
        assert "Critical" in sev
        assert "Major" in sev

    def test_unique_deviation_ids(self):
        gt = load_ground_truth()
        ids = [d["id"] for d in gt]
        assert len(ids) == len(set(ids))


class TestBaselineReconciler:
    def test_reconcile_returns_list(self):
        findings = reconcile()
        assert isinstance(findings, list)

    def test_reconcile_finds_all_deviations(self):
        findings = reconcile()
        assert len(findings) == 14

    def test_reconcile_has_required_keys(self):
        findings = reconcile()
        required = {"component", "parameter", "required_value", "provided_value",
                     "unit", "standard_ref", "spec_clause", "severity"}
        for f in findings:
            missing = required - f.keys()
            assert not missing, f"{f['component']}.{f['parameter']} missing: {missing}"

    def test_reconcile_cx_predictions(self):
        findings = reconcile()
        for f in findings:
            assert f.get("predicted_cx_test") is not None, \
                f"{f['component']}.{f['parameter']} has no cx test prediction"


class TestScoring:
    def test_perfect_precision(self):
        gt = load_ground_truth()
        findings = reconcile()
        r = score(findings, gt)
        assert r["precision"] == 1.0

    def test_perfect_recall(self):
        gt = load_ground_truth()
        findings = reconcile()
        r = score(findings, gt)
        assert r["recall"] == 1.0

    def test_perfect_f1(self):
        gt = load_ground_truth()
        findings = reconcile()
        r = score(findings, gt)
        assert r["f1"] == 1.0

    def test_cx_prediction_accuracy(self):
        gt = load_ground_truth()
        findings = reconcile()
        r = score(findings, gt)
        assert r["cx_prediction_accuracy"] == 1.0

    def test_zero_false_positives(self):
        gt = load_ground_truth()
        findings = reconcile()
        r = score(findings, gt)
        assert len(r["fp"]) == 0

    def test_zero_false_negatives(self):
        gt = load_ground_truth()
        findings = reconcile()
        r = score(findings, gt)
        assert len(r["fn"]) == 0

    def test_zero_fp_in_clean_systems(self):
        gt = load_ground_truth()
        findings = reconcile()
        r = score(findings, gt)
        assert r["false_positives_in_clean_systems"] == 0

    def test_total_lead_time(self):
        gt = load_ground_truth()
        findings = reconcile()
        r = score(findings, gt)
        assert r["total_lead_time_weeks"] == 267

    def test_max_lead_time(self):
        gt = load_ground_truth()
        findings = reconcile()
        r = score(findings, gt)
        assert r["max_lead_time_weeks"] == 33


class TestKeyFunction:
    def test_key_extracts_component_parameter(self):
        d = {"component": "UPS-02", "parameter": "battery_runtime_min"}
        assert key(d) == ("UPS-02", "battery_runtime_min")

    def test_key_raises_on_missing_component(self):
        import pytest
        with pytest.raises(ValueError):
            key({"parameter": "test"})

    def test_key_raises_on_missing_parameter(self):
        import pytest
        with pytest.raises(ValueError):
            key({"component": "X"})


class TestScoreEdgeCases:
    def test_empty_findings(self):
        gt = load_ground_truth()
        r = score([], gt)
        assert r["precision"] == 0.0
        assert r["recall"] == 0.0
        assert r["f1"] == 0.0

    def test_empty_ground_truth(self):
        findings = reconcile()
        r = score(findings, [])
        assert r["precision"] == 0.0
        assert r["recall"] == 0.0

    def test_both_empty(self):
        r = score([], [])
        assert r["precision"] == 0.0
        assert r["recall"] == 0.0
        assert r["f1"] == 0.0
