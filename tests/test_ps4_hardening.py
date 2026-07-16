"""Adversarial hardening tests for the PS4 engines: malformed/empty/NaN inputs
must never crash and must never leak NaN/inf into the output."""

import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from backend.agents import project_graph, supply_chain
from backend.agents.schedule_risk import (
    analyze_schedule,
    cpm,
    derive_risks,
    monte_carlo,
    narrate,
    simulate_finish,
)


def _all_finite(obj) -> bool:
    if isinstance(obj, float):
        return math.isfinite(obj)
    if isinstance(obj, dict):
        return all(_all_finite(v) for v in obj.values())
    if isinstance(obj, list):
        return all(_all_finite(v) for v in obj)
    return True


class TestScheduleHardening:
    def test_empty_tasks_no_crash(self):
        out = analyze_schedule({"tasks": [], "deadline_week": 52}, n=500)
        assert math.isfinite(out["monte_carlo"]["p80"])

    def test_malformed_durations_stay_finite(self):
        tasks = [
            {"id": "A", "duration": {"optimistic": 1, "most_likely": 8, "pessimistic": 5}},  # reversed m
            {"id": "B", "duration": {}, "predecessors": ["A"]},                              # empty dur
            {"id": "C", "duration": {"fixed": float("nan")}, "predecessors": ["B"],          # NaN + null level
             "is_milestone": True, "cx_level": None},
        ]
        out = analyze_schedule({"tasks": tasks, "deadline_week": 20}, n=500)
        assert _all_finite(out["monte_carlo"])
        assert _all_finite(out["baseline"])

    def test_derive_risks_match_fallback_and_skip(self):
        sch = {"tasks": [{"id": "CX-IST-07", "cx_test": "IST-07"},
                         {"id": "INSTALL-GEN", "component": "GEN"}]}
        devs = [
            {"id": "D1", "predicted_cx_test": "IST-07", "severity": "Critical"},
            {"id": "D2", "component": "GEN-01", "severity": "Major"},   # system fallback
            {"id": "D3", "predicted_cx_test": "NOPE", "component": "ZZ"},  # no match -> skipped
        ]
        risks = derive_risks(sch, devs)
        assert {r["source_deviation"] for r in risks} == {"D1", "D2"}
        crit = next(r for r in risks if r["source_deviation"] == "D1")
        assert crit["impact"]["pessimistic"] == 8  # Critical gets the heavier impact

    def test_narrate_offline_is_rule_based(self):
        risks = [{"id": "R", "type": "rework", "applies_to": ["A"], "probability": 1.0,
                  "impact": {"optimistic": 2, "most_likely": 4, "pessimistic": 8}}]
        tasks = [{"id": "A", "duration": {"optimistic": 2, "most_likely": 3, "pessimistic": 6},
                  "is_milestone": True, "cx_level": 5}]
        out = analyze_schedule({"tasks": tasks, "deadline_week": 10, "risks": risks}, n=500)
        nr = narrate(out)
        assert nr["mode"] == "rule-based-fallback"
        assert "week" in nr["narrative"]


class TestSupplyHardening:
    def test_nan_factor_stays_finite_not_red(self):
        r = supply_chain.supplier_risk({"single_source": float("nan")})
        assert math.isfinite(r["score"]) and r["score"] == 0.0

    def test_prob_late_handles_nan_and_negative_sigma(self):
        assert 0.0 <= supply_chain.prob_late(10, float("nan"), 12) <= 1.0
        assert 0.0 <= supply_chain.prob_late(10, -3, 12) <= 1.0

    def test_malformed_shipment_does_not_crash(self):
        out = supply_chain.analyze_supply_chain({"shipments": [{"id": "X", "stages": []}]})
        assert out["summary"]["total"] == 1
        assert _all_finite(out["shipments"][0]["delivery_risk"])

    def test_narrate_offline(self):
        out = supply_chain.analyze_supply_chain({"shipments": []})
        assert supply_chain.narrate(out)["mode"] == "rule-based-fallback"


class TestGraphHardening:
    def test_malformed_deviation_no_crash(self):
        g = project_graph.assemble([{"id": "D", "component": "UPS-01"}, {"id": "E"}])
        br = project_graph.blast_radius(g, "D")
        assert br is not None and br["worst_milestone_slip"] >= 0


class TestNarrateGuard:
    """The narrate() LLM path may only restate computed numbers; an invented or
    re-rounded figure must be rejected so it never reaches a judge."""

    def test_numbers_grounded_accepts_exact_quote(self):
        from backend.llm import numbers_grounded
        src = "Baseline P80 finish is week 67.4 (on-time probability 0.82)."
        assert numbers_grounded("P80 lands week 67.4, on-time prob 0.82.", src)

    def test_numbers_grounded_rejects_invented_and_rerounded(self):
        from backend.llm import numbers_grounded
        src = "2 of 4 long-lead shipments are at risk (worst 61.9/100)."
        assert not numbers_grounded("Risk is 62/100 over 13 weeks.", src)  # invented
        assert not numbers_grounded("worst 62/100", src)                   # re-rounded
        assert numbers_grounded("All shipments tracking well.", src)       # no figures

    def test_restate_falls_back_to_template_offline(self):
        # No API key in the test env -> complete() raises -> template verbatim.
        from backend.llm import restate
        tmpl = "2 of 4 long-lead shipments are at risk (worst 61.9/100)."
        out = restate(tmpl, "Rewrite crisply.", "analyst")
        assert out["narrative"] == tmpl and out["mode"] == "rule-based-fallback"


_CHAIN = [
    {"id": "A", "duration": {"optimistic": 2, "most_likely": 3, "pessimistic": 6}},
    {"id": "B", "duration": {"optimistic": 3, "most_likely": 4, "pessimistic": 9}, "predecessors": ["A"]},
]


class TestProperties:
    def test_simulate_finish_matches_monte_carlo(self):
        # Lock the duplicate MC model against silent drift.
        mc = monte_carlo(_CHAIN, n=20000, seed=5)
        fin = simulate_finish(_CHAIN, n=20000, seed=5)
        p = [round(float(x), 2) for x in np.percentile(fin, [50, 80, 90])]
        assert (p[0], p[1], p[2]) == (mc["p50"], mc["p80"], mc["p90"])

    def test_cpm_mc_consistency_all_fixed(self):
        tasks = [{"id": "A", "duration": {"fixed": 3}},
                 {"id": "B", "duration": {"fixed": 4}, "predecessors": ["A"]}]
        assert abs(monte_carlo(tasks, n=2000, seed=1)["p50"] - cpm(tasks)["project_duration"]) < 1e-6

    def test_rework_risk_monotonic(self):
        base = monte_carlo(_CHAIN, risks=[], n=10000, seed=3)
        risk = [{"id": "R", "type": "rework", "applies_to": ["B"], "probability": 1.0,
                 "impact": {"optimistic": 2, "most_likely": 4, "pessimistic": 8}}]
        assert monte_carlo(_CHAIN, risks=risk, n=10000, seed=3)["p80"] >= base["p80"]

    def test_supplier_risk_bounded(self):
        r = supply_chain.supplier_risk({"single_source": 1.0, "geo": 0.5})
        assert 0 <= r["score"] <= 100

    def test_blast_radius_monotonic_in_supplier_lead(self):
        devs = [{"id": "D", "component": "UPS-02", "predicted_cx_test": "IST-07",
                 "predicted_cx_level": 4, "week_caught": 11, "week_fail": 38, "lead_time_weeks": 27}]
        cx = {"tests": [{"id": "IST-07", "level": 4, "scheduled_week": 38}]}
        sc = lambda lead: {"items": [{"component": "UPS", "vendor": "V", "lead_time_weeks": lead}]}  # noqa: E731
        g1 = project_graph.assemble(devs, cx, supply_chain=sc(30))
        g2 = project_graph.assemble(devs, cx, supply_chain=sc(45))
        b1 = project_graph.blast_radius(g1, "D")
        b2 = project_graph.blast_radius(g2, "D")
        assert b2["worst_milestone_slip"] >= b1["worst_milestone_slip"]

    def test_as_graph_roundtrips_counts(self):
        g = project_graph.assemble(
            [{"id": "D", "component": "UPS-02", "standard_ref": "X", "predicted_cx_test": "T"}],
            {"tests": [{"id": "T", "level": 4, "scheduled_week": 38}]})
        gg = project_graph.as_graph(g)
        st = project_graph.graph_stats(g)
        assert len(gg["nodes"]) == st["nodes"] and len(gg["edges"]) == st["edges"]
