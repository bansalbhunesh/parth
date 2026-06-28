"""Tests for the standards-grounded commissioning knowledge graph."""

import pathlib

from backend.agents import cx_graph
from backend.agents.commissioning import predict_cx_impact, _RULES
from backend.analyze import _resilient_fallback

REAL = pathlib.Path(__file__).parent.parent / "data" / "samples" / "real"


def test_graph_is_real_and_cited():
    stats = cx_graph.graph_stats()
    assert stats["edges"] >= 16
    assert stats["cx_test_nodes"] >= 14
    assert stats["cx_levels"] == 5
    assert stats["standards_cited"] >= 8  # genuine provenance, not a flat lookup


def test_every_edge_resolves_to_a_test_and_level():
    g = cx_graph._load()
    test_ids = {t["id"] for t in g["cx_tests"]}
    for e in g["edges"]:
        assert e["cx_test"] in test_ids, f"dangling edge {e}"
        assert e.get("standard_basis"), f"uncited edge {e}"


def test_explain_returns_cited_path():
    path = cx_graph.explain("BUSWAY-01", "short_time_withstand_ka")
    assert path is not None
    assert path["predicted_cx_test"] == "FAT-03"
    assert path["predicted_cx_level"] == 3
    assert "IEC 61439-6" in path["standard_basis"]
    assert path["lead_time_weeks_typical"]  # non-zero estimate


def test_explain_unknown_is_none():
    assert cx_graph.explain("NOPE", "nope") is None


def test_as_graph_has_nodes_and_edges():
    gv = cx_graph.as_graph()
    kinds = {n["kind"] for n in gv["nodes"]}
    assert {"level", "cx_test", "deviation"} <= kinds
    assert len(gv["edges"]) > len(gv["nodes"]) // 2


def test_rules_table_still_resolves_as_rule():
    """Regression guard: the 14 Meghdoot entries must still come from the table,
    not the graph (preserves committed lead-time numbers)."""
    dev = {"component": "UPS-02", "parameter": "battery_runtime_min", "severity": "Critical"}
    out = predict_cx_impact(dev)
    assert out["cx_source"] == "rule"
    assert out["lead_time_weeks"] == 27


def test_new_real_components_get_graph_cx():
    dev = {"component": "BUSWAY-01", "parameter": "short_time_withstand_ka", "severity": "Critical"}
    out = predict_cx_impact(dev)
    assert out["cx_source"] == "graph"
    assert out["predicted_cx_test"] == "FAT-03"
    assert out["lead_time_weeks"]
    assert "IEC 61439-6" in out["standard_basis"]


def test_floor_busway_findings_enriched_end_to_end():
    for spec, sub, comp in [
        ("design_basis_floor.md", "submittal_floor_concore1250.md", "FLOOR-01"),
        ("design_basis_busway.md", "submittal_busway_canalis.md", "BUSWAY-01"),
    ]:
        s = (REAL / spec).read_text(encoding="utf-8")
        u = (REAL / sub).read_text(encoding="utf-8")
        devs = _resilient_fallback(s, u, comp)
        d = next(x for x in devs if x["component"] == comp)
        assert d.get("predicted_cx_test"), "real finding should carry a Cx test from the graph"
        assert d.get("cx_source") == "graph"
