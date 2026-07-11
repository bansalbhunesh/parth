"""Tests for scripts/benchmark_calibration.py — the stratified confidence-
interval report over the frozen ps4_external_v1 benchmark (P2-4).

Covers: the Wilson score interval formula's own correctness properties, that
the script's recomputed recall matches the committed benchmark_card.json
exactly (the drift guard the script itself warns on), and that the report is
deterministic (re-running it does not change the committed file).
"""

import importlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import benchmark_calibration as C  # noqa: E402

# ── Wilson score interval — properties independent of the benchmark data ──

def test_wilson_ci_zero_n_returns_zero_not_a_crash():
    assert C.wilson_ci(0, 0) == (0.0, 0.0, 0.0)


def test_wilson_ci_bounds_stay_within_unit_interval():
    for successes, n in [(0, 5), (5, 5), (3, 5), (1, 200), (199, 200)]:
        p, lo, hi = C.wilson_ci(successes, n)
        assert 0.0 <= lo <= p <= hi <= 1.0


def test_wilson_ci_narrows_as_n_grows_at_the_same_proportion():
    # Same observed proportion (0.8), increasing sample size — a real CI must
    # narrow, not just report the same point estimate more confidently by
    # coincidence.
    _, lo_small, hi_small = C.wilson_ci(8, 10)
    _, lo_large, hi_large = C.wilson_ci(800, 1000)
    assert (hi_large - lo_large) < (hi_small - lo_small)


def test_wilson_ci_is_not_the_naive_normal_approximation_at_small_n():
    # At n=6, successes=6 (observed 100%), the normal approximation
    # (p +/- 1.96*sqrt(p(1-p)/n)) degenerates to a zero-width interval at
    # p=1 - clearly wrong for n=6. Wilson correctly reports a real interval
    # below 1.0, which is the whole reason this script uses Wilson and not
    # the normal approximation for small strata.
    _, lo, hi = C.wilson_ci(6, 6)
    assert hi == 1.0
    assert lo > 0.0
    assert (hi - lo) > 0.05  # not a degenerate zero-width interval


# ── the actual benchmark data — recomputation must match benchmark_card.json ──

def test_recomputed_recall_matches_committed_benchmark_card():
    run_dirs = C._model_runs()
    assert len(run_dirs) >= 3, "expected at least the 3 primary passes to be present"

    per_run_recall = []
    for d in run_dirs:
        rows = [r for r in C._load_labels(d) if r["label_type"] in C.POSITIVE_TYPES]
        assert len(rows) == 63, f"{d.name}: expected 63 positive labels, got {len(rows)}"
        per_run_recall.append(sum(int(r["caught_semantic"]) for r in rows) / len(rows))

    card = json.loads((C.REPORTS / "benchmark_card.json").read_text(encoding="utf-8"))
    computed_mean = round(sum(per_run_recall) / len(per_run_recall), 3)
    assert computed_mean == card["primary_result"]["recall_mean"], (
        "per_label_results.csv and benchmark_card.json have drifted apart — "
        "re-run scripts/benchmark_report.py"
    )


def test_calibration_report_is_deterministic():
    """Re-running the generator against the same committed run directories
    must reproduce byte-identical output — this is a report over frozen
    data, not a live measurement, so any diff means either the generator
    or the committed report is out of date."""
    report_path = C.REPORTS / "calibration_report.md"
    json_path = C.REPORTS / "calibration.json"
    before_report = report_path.read_text(encoding="utf-8")
    before_json = json_path.read_text(encoding="utf-8")

    importlib.reload(C)
    C.main()

    after_report = report_path.read_text(encoding="utf-8")
    after_json = json_path.read_text(encoding="utf-8")
    assert after_report == before_report, (
        "calibration_report.md changed on regeneration — commit the regenerated "
        "file (run `python scripts/benchmark_calibration.py`) or the benchmark "
        "run data changed unexpectedly"
    )
    assert after_json == before_json


def test_calibration_json_has_the_known_omission_detection_gap():
    """Regression guard, not a tautology: this pins the specific, real finding
    (omission-detection recall far below the headline) so if benchmark data
    ever changes enough to make this gap disappear or shrink dramatically,
    a test fails and a human notices — rather than the report silently
    reporting a different story than the one currently documented about it
    in docs/CLAIMS_REGISTER.md / the evidence page."""
    payload = json.loads((C.REPORTS / "calibration.json").read_text(encoding="utf-8"))
    omission = payload["by_difficulty"]["omission_detection"]
    assert omission["n"] >= 10
    assert omission["ci95_high"] < payload["overall"]["ci95_low"], (
        "omission_detection's CI no longer sits below the overall recall CI — "
        "update docs referencing this finding (or this test) to match reality"
    )
