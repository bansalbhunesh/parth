"""Tests for the supply-chain visibility & risk engine."""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from backend.agents.supply_chain import (
    analyze_shipment,
    analyze_supply_chain,
    delivery_risk,
    prob_late,
    project_eta,
    supplier_risk,
)

# today_week = 0. Remaining means 4+6+2 = 12; var 1+4+0.25 = 5.25; sigma ~2.291.
SHIPMENT = {
    "id": "SHP-UPS-01", "equipment_type": "UPS", "description": "1.25MW modular UPS",
    "supplier": "Vertiv", "origin_country": "US", "destination_site": "Ashburn",
    "current_stage": "MANUFACTURING", "required_on_site_week": 10,
    "on_critical_path": True, "linked_task_id": "T-UPS-INSTALL",
    "supplier_risk_factors": {"single_source": 1.0, "subtier_shortage": 1.0},
    "stages": [
        {"name": "PO_PLACED", "status": "done", "planned_mean_weeks": 0, "planned_std_weeks": 0},
        {"name": "MANUFACTURING", "status": "active", "planned_mean_weeks": 4,
         "planned_std_weeks": 1, "actual_start_week": 0},
        {"name": "OCEAN_FREIGHT", "status": "pending", "planned_mean_weeks": 6, "planned_std_weeks": 2},
        {"name": "INLAND_TRANSPORT", "status": "pending", "planned_mean_weeks": 2, "planned_std_weeks": 0.5},
    ],
}


class TestETA:
    def test_eta_sums_remaining_means(self):
        eta = project_eta(SHIPMENT, today_week=0)
        assert eta["eta_p50"] == 12  # 4 + 6 + 2
        assert abs(eta["sigma"] - (5.25 ** 0.5)) < 1e-3
        assert eta["eta_p80"] > eta["eta_p50"]

    def test_prob_late_monotonic(self):
        eta = project_eta(SHIPMENT, today_week=0)
        late_tight = prob_late(eta["eta_p50"], eta["sigma"], required_on_site_week=10)
        late_loose = prob_late(eta["eta_p50"], eta["sigma"], required_on_site_week=20)
        assert late_tight > 0.5  # ETA 12 vs ROS 10 -> likely late
        assert late_loose < 0.05  # ETA 12 vs ROS 20 -> safe
        assert late_tight > late_loose


class TestSupplierRisk:
    def test_single_source_weight(self):
        r = supplier_risk({"single_source": 1.0})
        assert r["score"] == 30.0  # weight 0.30 * 100
        assert r["contributions"]["single_source"] == 30.0

    def test_all_factors_max_is_red(self):
        r = supplier_risk({k: 1.0 for k in
                           ["single_source", "concentration", "geo",
                            "port_congestion", "subtier_shortage", "backlog"]})
        assert r["score"] == 100.0
        assert r["band"] == "red"


class TestDeliveryRisk:
    def test_critical_path_raises_risk(self):
        on = delivery_risk(p_late=0.8, on_critical_path=True, supplier_risk_norm=0.3)
        off = delivery_risk(p_late=0.8, on_critical_path=False, supplier_risk_norm=0.3)
        assert on["score"] > off["score"]
        assert on["consequence"] == 1.0 and off["consequence"] == 0.5


class TestAnalyzeShipment:
    def test_at_risk_flagged_when_late(self):
        a = analyze_shipment(SHIPMENT, today_week=0)
        assert a["slack_weeks"] == -2  # ROS 10 - ETA 12
        assert a["p_late"] > 0.5
        assert a["at_risk"] is True
        assert a["delivery_risk"]["band"] in ("amber", "red")

    def test_not_at_risk_with_ample_slack(self):
        s = {**SHIPMENT, "required_on_site_week": 30, "supplier_risk_factors": {}}
        a = analyze_shipment(s, today_week=0)
        assert a["slack_weeks"] > 0
        assert a["at_risk"] is False


class TestAnalyzeSupplyChain:
    def test_summary_counts(self):
        data = {"project_id": "test", "current_week": 0, "shipments": [SHIPMENT]}
        out = analyze_supply_chain(data)
        assert out["summary"]["total"] == 1
        assert out["summary"]["at_risk"] == 1
        assert out["summary"]["worst_item"] == "SHP-UPS-01"
        assert sum(out["summary"]["by_band"].values()) == 1
