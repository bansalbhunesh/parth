"""Tests for the predictive schedule-risk engine (CPM + Monte Carlo)."""

import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from backend.agents.schedule_risk import analyze_schedule, cpm, monte_carlo, simulate_finish

# Classic CPM case: A->B->D and A->C->D. Durations A3 B4 C2 D5.
# Hand-computed: ES A0/B3/C3/D7; project=12; critical A,B,D; C has total float 2.
KNOWN = [
    {"id": "A", "name": "A", "duration": {"fixed": 3}},
    {"id": "B", "name": "B", "duration": {"fixed": 4}, "predecessors": ["A"]},
    {"id": "C", "name": "C", "duration": {"fixed": 2}, "predecessors": ["A"]},
    {"id": "D", "name": "D", "duration": {"fixed": 5}, "predecessors": ["B", "C"], "is_milestone": True},
]


class TestCPM:
    def test_project_duration_and_critical_path(self):
        r = cpm(KNOWN)
        assert r["project_duration"] == 12
        assert set(r["critical_path"]) == {"A", "B", "D"}

    def test_floats(self):
        r = cpm(KNOWN)["tasks"]
        assert r["A"]["es"] == 0 and r["A"]["ef"] == 3
        assert r["D"]["es"] == 7 and r["D"]["ef"] == 12
        assert r["C"]["total_float"] == 2  # C has slack; B/A/D are critical
        assert r["B"]["total_float"] == 0
        assert r["C"]["critical"] is False

    def test_cycle_is_rejected(self):
        cyclic = [
            {"id": "X", "duration": {"fixed": 1}, "predecessors": ["Y"]},
            {"id": "Y", "duration": {"fixed": 1}, "predecessors": ["X"]},
        ]
        with pytest.raises(ValueError):
            cpm(cyclic)

    def test_unknown_predecessor_rejected(self):
        bad = [{"id": "A", "duration": {"fixed": 1}, "predecessors": ["NOPE"]}]
        with pytest.raises(ValueError):
            cpm(bad)


THREE_POINT = [
    {"id": "A", "name": "A", "duration": {"optimistic": 2, "most_likely": 3, "pessimistic": 6}},
    {"id": "B", "name": "B", "duration": {"optimistic": 3, "most_likely": 4, "pessimistic": 9},
     "predecessors": ["A"], "is_milestone": True, "cx_level": 5},
]


class TestMonteCarlo:
    def test_reproducible_with_seed(self):
        a = monte_carlo(THREE_POINT, seed=42, n=5000)
        b = monte_carlo(THREE_POINT, seed=42, n=5000)
        assert a["p80"] == b["p80"]
        assert a["p50"] == b["p50"]

    def test_percentile_ordering(self):
        r = monte_carlo(THREE_POINT, seed=1, n=10000)
        assert r["p50"] <= r["p80"] <= r["p90"]

    def test_histogram_covers_all_trials(self):
        r = monte_carlo(THREE_POINT, seed=1, n=10000)
        assert sum(b["count"] for b in r["histogram"]) == 10000

    def test_rework_risk_pushes_p80_later(self):
        base = monte_carlo(THREE_POINT, risks=[], seed=7, n=10000)
        risk = [{"id": "R", "type": "rework", "applies_to": ["B"], "probability": 1.0,
                 "impact": {"optimistic": 2, "most_likely": 4, "pessimistic": 8}}]
        worse = monte_carlo(THREE_POINT, risks=risk, seed=7, n=10000)
        assert worse["p80"] > base["p80"]

    def test_on_time_probability_drops_under_risk(self):
        base = monte_carlo(THREE_POINT, risks=[], deadline_week=10, seed=7, n=10000)
        risk = [{"id": "R", "type": "delivery_delay", "applies_to": ["B"], "probability": 1.0,
                 "delay": {"optimistic": 2, "most_likely": 4, "pessimistic": 8}}]
        worse = monte_carlo(THREE_POINT, risks=risk, deadline_week=10, seed=7, n=10000)
        assert worse["on_time_probability"] < base["on_time_probability"]


class TestAnalyzeSchedule:
    def test_deviation_impact_quantified(self):
        schedule = {
            "project_id": "test",
            "deadline_week": 10,
            "tasks": THREE_POINT,
            "risks": [{"id": "R", "type": "rework", "applies_to": ["B"], "probability": 1.0,
                       "impact": {"optimistic": 2, "most_likely": 4, "pessimistic": 8}}],
        }
        out = analyze_schedule(schedule, n=10000, seed=3)
        imp = out["deviation_impact"]
        assert imp["milestone"] == "B"
        assert imp["slip_weeks"] > 0  # the deviation pushes the headline milestone later
        assert imp["at_risk_on_time"] <= imp["baseline_on_time"]
        assert out["cpm"]["project_duration"] > 0


class TestCalibration:
    def test_p80_is_self_calibrated(self):
        # The P80 finish should contain ~80% of independently-sampled outcomes —
        # i.e. the Monte-Carlo machinery is internally calibrated.
        pred = simulate_finish(THREE_POINT, n=20000, seed=1)
        p80 = float(np.percentile(pred, 80))
        actual = simulate_finish(THREE_POINT, n=20000, seed=2)
        coverage = float(np.mean(actual <= p80))
        assert abs(coverage - 0.80) < 0.03
