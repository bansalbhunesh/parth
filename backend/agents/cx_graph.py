"""Commissioning Risk Graph — the real knowledge graph behind the Cx twin.

`backend/agents/commissioning.py` keeps a project-specific scheduling table
(`_RULES`, 14 Meghdoot tuples with calendar weeks). THIS module is the
standards-grounded graph that the product's "commissioning knowledge graph"
claim actually refers to: deviation-class -> Cx-test -> Cx-level -> milestone,
where every node and edge is independently citable (ASHRAE Guideline 0 / 1.1,
BICSI-002 levels, Uptime Tier Cx, plus the specific governing standard per
failure mode). It is traversable, queryable, and extensible — adding a real
equipment class (e.g. the Tate raised floor or Schneider busway) is a single
edge with its citation, not a code change.

Graceful by design: if the JSON is missing, every function returns an empty /
None result instead of raising, so the live path never 500s on a Cx lookup.
"""

import json
import pathlib

_GRAPH_PATH = pathlib.Path(__file__).resolve().parents[2] / "data" / "commissioning_graph.json"

# How far ahead of a given Cx level a day-one submittal catch typically lands,
# in weeks. Later (integrated) tests sit further out in the schedule, so catching
# their root cause at submittal review buys more lead time. Used only for
# graph-sourced predictions (components outside the Meghdoot scheduling table).
_LEVEL_TYPICAL_LEAD_WEEKS = {1: 8, 2: 11, 3: 15, 4: 25, 5: 30}

_cache = None


def _load():
    global _cache
    if _cache is None:
        try:
            _cache = json.loads(_GRAPH_PATH.read_text(encoding="utf-8"))
        except Exception:
            _cache = {"levels": {}, "cx_tests": [], "edges": [], "meta": {}}
    return _cache


def _test_by_id(test_id):
    for t in _load().get("cx_tests", []):
        if t["id"] == test_id:
            return t
    return None


def explain(component, parameter):
    """Traverse deviation-class -> test -> level -> milestone with citations.
    Returns None if the (component, parameter) is not a node in the graph."""
    g = _load()
    edge = next((e for e in g.get("edges", [])
                 if e["component"] == component and e["parameter"] == parameter), None)
    if not edge:
        return None
    test = _test_by_id(edge["cx_test"]) or {}
    level = test.get("level")
    level_info = g.get("levels", {}).get(str(level), {})
    return {
        "component": component,
        "parameter": parameter,
        "predicted_cx_test": edge["cx_test"],
        "predicted_cx_name": test.get("name"),
        "predicted_cx_level": level,
        "cx_level_name": level_info.get("name"),
        "milestone": level_info.get("name"),
        "failure_mode": edge.get("failure_mode"),
        "standard_basis": edge.get("standard_basis"),
        "level_basis": level_info.get("basis"),
        "lead_time_weeks_typical": _LEVEL_TYPICAL_LEAD_WEEKS.get(level),
        "cx_source": "graph",
    }


def graph_stats():
    g = _load()
    edges = g.get("edges", [])
    standards = sorted({e.get("standard_basis", "") for e in edges if e.get("standard_basis")})
    return {
        "deviation_nodes": len({(e["component"], e["parameter"]) for e in edges}),
        "cx_test_nodes": len(g.get("cx_tests", [])),
        "cx_levels": len(g.get("levels", {})),
        "edges": len(edges),
        "standards_cited": len(standards),
        "version": g.get("meta", {}).get("version"),
    }


def as_graph():
    """Node/edge form for visualization (deviation, test, and level nodes)."""
    g = _load()
    nodes, seen = [], set()

    def add(node_id, kind, label):
        if node_id not in seen:
            seen.add(node_id)
            nodes.append({"id": node_id, "kind": kind, "label": label})

    for lvl, info in g.get("levels", {}).items():
        add(f"L{lvl}", "level", info.get("name", f"Level {lvl}"))
    for t in g.get("cx_tests", []):
        add(t["id"], "cx_test", t.get("name", t["id"]))
    edges = []
    for e in g.get("edges", []):
        dev_id = f'{e["component"]}/{e["parameter"]}'
        add(dev_id, "deviation", dev_id)
        test = _test_by_id(e["cx_test"]) or {}
        edges.append({"from": dev_id, "to": e["cx_test"], "basis": e.get("standard_basis")})
        if test.get("level") is not None:
            edges.append({"from": e["cx_test"], "to": f'L{test["level"]}', "basis": "Cx level"})
    return {"nodes": nodes, "edges": edges}
