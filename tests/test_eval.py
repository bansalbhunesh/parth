"""
Tests for the eval harness — verifies that the baseline reconciler achieves
perfect precision, recall, and F1 against the ground truth corpus.

These tests prove the plumbing is correct and the eval metrics are reproducible.
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from eval.baseline_reconciler import reconcile
from eval.run_eval import key, load_ground_truth, score

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


class TestSemanticMatching:
    """Semantic scoring credits a detection regardless of the label the model
    chose, while strict scoring still reports exact-label divergence."""

    def _gt_by_key(self):
        gt = load_ground_truth()
        return gt, {(d["component"], d["parameter"]): d for d in gt}

    def test_renamed_parameter_still_counts(self):
        # "delta_t_c" reported as "delta t c" — same system, same transition.
        gt, by_key = self._gt_by_key()
        findings = [dict(d) for d in gt]
        for f in findings:
            if f["parameter"] == "delta_t_c":
                f["parameter"] = "delta t c"
        r = score(findings, gt)
        assert r["recall"] == 1.0
        assert r["f1"] == 1.0
        # strict penalizes the rename
        assert r["strict_f1"] < 1.0
        assert ("COOL-LOOP", "delta_t_c") in r["strict_fn"]

    def test_renamed_component_still_counts(self):
        # "FLOOR/height_mm" reported as "Raised Floor System/finished_floor_height"
        gt, by_key = self._gt_by_key()
        findings = [dict(d) for d in gt]
        for f in findings:
            if (f["component"], f["parameter"]) == ("FLOOR", "height_mm"):
                f["component"] = "Raised Floor System"
                f["parameter"] = "finished_floor_height"
        r = score(findings, gt)
        assert r["recall"] == 1.0
        assert r["strict_recall"] < 1.0

    def test_hallucination_is_still_false_positive(self):
        # A finding with a value transition that exists in NO ground-truth
        # deviation must remain a false positive — semantic match is not lenient.
        gt, by_key = self._gt_by_key()
        findings = [dict(d) for d in gt]
        findings.append({
            "component": "MADE-UP", "parameter": "imaginary_param",
            "required_value": "999", "provided_value": "111",
        })
        r = score(findings, gt)
        assert r["recall"] == 1.0
        assert r["precision"] < 1.0
        assert ("MADE-UP", "imaginary_param") in r["fp"]

    def test_value_collision_disambiguated_by_system(self):
        # Two deviations share the 10->7 transition (UPS battery, COOL delta).
        # A 10->7 finding on UPS must NOT be credited as the COOL deviation.
        gt, _ = self._gt_by_key()
        # Only report the UPS one; COOL/delta_t_c should remain a miss.
        findings = [dict(d) for d in gt
                    if (d["component"], d["parameter"]) != ("COOL-LOOP", "delta_t_c")]
        r = score(findings, gt)
        assert ("COOL-LOOP", "delta_t_c") in r["fn"]
        assert r["recall"] < 1.0

    def test_baseline_perfect_in_both_modes(self):
        gt = load_ground_truth()
        r = score(reconcile(), gt)
        assert r["f1"] == 1.0
        assert r["strict_f1"] == 1.0
