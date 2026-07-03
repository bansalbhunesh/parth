"""Tests for the unified project knowledge graph + blast-radius propagation."""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from backend.agents.project_graph import (
    as_graph,
    assemble,
    blast_radius,
    graph_stats,
    simulate_remediation,
)

DEVS = [{
    "id": "DEV-001", "component": "UPS-02", "parameter": "battery_runtime_min",
    "severity": "Critical", "standard_ref": "UPTIME-TIER4", "spec_clause": "DB-4.3",
    "predicted_cx_test": "IST-07", "predicted_cx_level": 4,
    "week_caught": 11, "week_fail": 38, "lead_time_weeks": 27,
}]
CX_PLAN = {"tests": [
    {"id": "IST-07", "level": 4, "name": "Battery autonomy", "scheduled_week": 38},
    {"id": "SAT-01", "level": 5, "name": "Integrated systems test", "scheduled_week": 50},
]}
SUPPLY_OK = {"items": [{"component": "UPS-02", "vendor": "Vertiv", "lead_time_weeks": 27,
                        "single_source": True, "country": "US"}]}
SUPPLY_LATE = {"items": [{"component": "UPS-02", "vendor": "Vertiv", "lead_time_weeks": 35,
                          "single_source": True, "country": "US"}]}


class TestAssembly:
    def test_core_nodes_and_edges(self):
        g = assemble(DEVS, CX_PLAN)
        kinds = {g.nodes[n]["kind"] for n in g.nodes}
        assert {"deviation", "equipment", "standard", "cx_test", "milestone"} <= kinds
        graph = as_graph(g)
        assert any(e["rel"] == "predicts-failure-of" for e in graph["edges"])
        assert any(e["rel"] == "violates" for e in graph["edges"])

    def test_supply_layer_adds_supplier(self):
        g = assemble(DEVS, CX_PLAN, supply_chain=SUPPLY_OK)
        assert "SUP:Vertiv" in g
        assert any(d.get("rel") == "supplied-by" for _, _, d in g.edges(data=True))

    def test_stats(self):
        g = assemble(DEVS, CX_PLAN, supply_chain=SUPPLY_OK)
        s = graph_stats(g)
        assert s["by_kind"]["deviation"] == 1
        assert s["by_kind"]["supplier"] == 1
        assert "predicts-failure-of" in s["relationship_types"]


class TestBlastRadius:
    def test_caught_in_time_when_supplier_lead_fits(self):
        # fix_complete = week_caught 11 + lead 27 = 38 == cx planned 38 -> no slip
        g = assemble(DEVS, CX_PLAN, supply_chain=SUPPLY_OK)
        br = blast_radius(g, "DEV-001")
        assert br["weeks_at_risk"] == 27
        assert br["worst_milestone_slip"] == 0
        assert br["caught_in_time"] is True
        assert any(c["id"] == "CX:IST-07" for c in br["cx_tests_at_risk"])
        assert any(s["label"] == "Vertiv" for s in br["suppliers"])

    def test_slips_when_supplier_lead_too_long(self):
        # fix_complete = 11 + 35 = 46 > cx planned 38 -> slip 8 weeks
        g = assemble(DEVS, CX_PLAN, supply_chain=SUPPLY_LATE)
        br = blast_radius(g, "DEV-001")
        assert br["worst_milestone_slip"] == 8
        assert br["caught_in_time"] is False
        assert br["milestones"][0]["slip_weeks"] == 8

    def test_falls_back_to_level_lead_without_supply(self):
        # level 4 typical lead = 25; fix_complete = 11 + 25 = 36 < 38 -> caught
        g = assemble(DEVS, CX_PLAN)
        br = blast_radius(g, "DEV-001")
        assert br["weeks_at_risk"] == 25
        assert br["caught_in_time"] is True

    def test_system_level_supply_connects_to_component_deviation(self):
        # deviation component "UPS-02"; supply item for the system "UPS" must still
        # connect via the part-of edge (UPS-02 -> UPS -> supplier).
        supply_sys = {"items": [{"component": "UPS", "vendor": "Vertiv",
                                 "lead_time_weeks": 40, "single_source": True}]}
        g = assemble(DEVS, CX_PLAN, supply_chain=supply_sys)
        br = blast_radius(g, "DEV-001")
        assert any(s["label"] == "Vertiv" for s in br["suppliers"])
        assert br["weeks_at_risk"] == 40

    def test_unknown_deviation_returns_none(self):
        g = assemble(DEVS, CX_PLAN)
        assert blast_radius(g, "DEV-999") is None


class TestRemediationSimulator:
    def test_slip_avoided_equals_lead_time(self):
        """The causal payoff: catching on upload (week 11) vs at commissioning
        (week 38) avoids exactly the deviation's lead time. Long-lead item:
        fix_lead 40 > cx 38, so slip never zeroes but early catch cuts it."""
        g = assemble(DEVS, CX_PLAN, supply_chain={"items": [
            {"component": "UPS-02", "vendor": "Vertiv", "lead_time_weeks": 40}]})
        sim = simulate_remediation(g, "DEV-001")
        assert sim["fix_lead_weeks"] == 40
        assert sim["cx_planned_week"] == 38
        # pramaan slip 11+40-38=13; commissioning slip 38+40-38=40; avoided 27
        assert sim["scenarios"]["pramaan"]["slip_weeks"] == 13
        assert sim["scenarios"]["commissioning"]["slip_weeks"] == 40
        assert sim["slip_avoided_weeks"] == 27
        assert sim["long_lead_trap"] is True

    def test_short_lead_has_zero_slip_region_and_cliff(self):
        """A short-lead deviation is flat-zero until the cliff, then climbs."""
        g = assemble(DEVS, CX_PLAN)  # level-4 typical lead = 25
        sim = simulate_remediation(g, "DEV-001")
        assert sim["fix_lead_weeks"] == 25
        # cliff = cx 38 - lead 25 = 13; catching by week 13 => zero slip
        assert sim["zero_slip_deadline_week"] == 13
        assert sim["long_lead_trap"] is False
        early = [p for p in sim["curve"] if p["catch_week"] <= 13]
        assert all(p["slip_weeks"] == 0 for p in early)
        assert sim["curve"][-1]["slip_weeks"] > 0  # climbs after the cliff

    def test_cost_translates_and_is_labelled(self):
        g = assemble(DEVS, CX_PLAN)
        sim = simulate_remediation(g, "DEV-001", cost_per_week_lakh=100.0)
        s = sim["scenarios"]["commissioning"]
        assert s["cost_lakh"] == round(s["slip_weeks"] * 100.0, 1)
        assert "assumption" in sim and "defensible unit" in sim["assumption"]

    def test_unknown_deviation_returns_none(self):
        g = assemble(DEVS, CX_PLAN)
        assert simulate_remediation(g, "DEV-999") is None


class TestGraceful:
    def test_deviation_without_cx_still_builds(self):
        devs = [{"id": "DEV-X", "component": "GEN-01", "standard_ref": "NFPA-110"}]
        g = assemble(devs)  # no cx_plan, no supply
        assert "DEV:DEV-X" in g
        assert "EQ:GEN-01" in g
        br = blast_radius(g, "DEV-X")
        assert br is not None
        assert br["cx_tests_at_risk"] == []
        assert br["milestones"] == []
