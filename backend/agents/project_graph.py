"""Project Knowledge Graph — the unifying 'living project intelligence' twin.

Assembles ONE networkx graph from the artifacts Pramaan already produces
(deviations, governing standards, commissioning tests/levels) plus, when present,
the new schedule and supply-chain layers. A single spec deviation then propagates
across four normally-siloed domains:

    compliance (standard violated)
      -> commissioning (which Cx test, which level)
        -> schedule (which milestone slips, by how many weeks)
          -> procurement (which supplier is the long pole of the fix)

`blast_radius(dev)` walks the impact edges and reports exactly that chain. Every
edge is standards-cited and every number comes from the data — the graph is fully
deterministic and runs offline; the language model (elsewhere) never draws an edge
and never moves a date, it only narrates the blast radius.

Graceful by design: missing layers are simply omitted; the deviation -> standard
-> Cx-test core always renders.
"""

from __future__ import annotations

import networkx as nx

from backend.agents.cx_graph import _LEVEL_TYPICAL_LEAD_WEEKS

# Edges the blast-radius walk follows (the causal/impact set). Structural edges
# (e.g. a label or governance link) are excluded from propagation.
IMPACT_RELS = {
    "violates", "about", "part-of", "predicts-failure-of", "verified-at",
    "supplied-by", "blocks", "delays", "depends-on",
}

_RFS = "MS:RFS"  # the headline milestone: ready-for-service / integrated systems test


def _rfs_planned_week(cx_plan: dict | None, deviations: list[dict]) -> float:
    """Planned week of the final integrated-systems-test milestone: the latest
    scheduled commissioning week, or (fallback) the latest deviation fail week."""
    weeks = [t.get("scheduled_week") for t in (cx_plan or {}).get("tests", [])
             if isinstance(t.get("scheduled_week"), (int, float))]
    if weeks:
        return float(max(weeks))
    fails = [d.get("week_fail") for d in deviations if isinstance(d.get("week_fail"), (int, float))]
    return float(max(fails)) if fails else 0.0


def assemble(
    deviations: list[dict],
    cx_plan: dict | None = None,
    supply_chain: dict | None = None,
    schedule: dict | None = None,
) -> nx.MultiDiGraph:
    """Build the unified project graph from available layers (all but `deviations`
    optional). Returns a networkx MultiDiGraph with typed nodes (`kind`) and typed
    edges (`rel`, plus a `basis` citation where applicable)."""
    g = nx.MultiDiGraph()
    cx_tests = {t["id"]: t for t in (cx_plan or {}).get("tests", [])}
    rfs_week = _rfs_planned_week(cx_plan, deviations)

    def node(nid: str, kind: str, label: str, **attrs) -> str:
        if nid not in g:
            g.add_node(nid, kind=kind, label=label, **attrs)
        return nid

    for d in deviations:
        dev = node(
            f"DEV:{d['id']}", "deviation", d["id"],
            component=d.get("component"), parameter=d.get("parameter"),
            severity=d.get("severity"), week_caught=d.get("week_caught"),
            week_fail=d.get("week_fail"), lead_time_weeks=d.get("lead_time_weeks"),
            predicted_cx_level=d.get("predicted_cx_level"),
        )
        comp = d.get("component")
        if comp:
            eq = node(f"EQ:{comp}", "equipment", comp)
            g.add_edge(dev, eq, rel="about")
            # Link the specific component (UPS-02) to its system (UPS) so a
            # system-level supply item / supplier connects to component-level
            # deviations.
            system = comp.split("-")[0]
            if system and system != comp:
                g.add_edge(eq, node(f"EQ:{system}", "equipment", system), rel="part-of")
        std = d.get("standard_ref")
        if std:
            g.add_edge(dev, node(f"STD:{std}", "standard", std),
                       rel="violates", basis=d.get("spec_clause"))
        cxid = d.get("predicted_cx_test")
        if cxid:
            t = cx_tests.get(cxid, {})
            cn = node(
                f"CX:{cxid}", "cx_test", t.get("name", cxid),
                level=d.get("predicted_cx_level") or t.get("level"),
                scheduled_week=(t.get("scheduled_week") if isinstance(t.get("scheduled_week"), (int, float))
                                else d.get("week_fail")),
            )
            g.add_edge(dev, cn, rel="predicts-failure-of", basis=d.get("standard_ref"))
            ms = node(_RFS, "milestone", "Ready-for-service (integrated systems test)",
                      planned_week=rfs_week)
            g.add_edge(cn, ms, rel="verified-at")

    if supply_chain:
        for item in supply_chain.get("items", supply_chain.get("shipments", [])):
            comp = item.get("component")
            vendor = item.get("vendor") or item.get("supplier")
            if not (comp and vendor):
                continue
            eq = node(f"EQ:{comp}", "equipment", comp)
            sup = node(f"SUP:{vendor}", "supplier", vendor,
                       lead_time_weeks=item.get("lead_time_weeks"),
                       single_source=item.get("single_source", False),
                       country=item.get("country") or item.get("origin_country"))
            g.add_edge(eq, sup, rel="supplied-by", lead_time_weeks=item.get("lead_time_weeks"))
            if _RFS in g:
                g.add_edge(sup, _RFS, rel="blocks", lead_time_weeks=item.get("lead_time_weeks"))

    if schedule:
        for task in schedule.get("tasks", []):
            tn = node(f"TASK:{task['id']}", "schedule_task", task.get("name", task["id"]),
                      is_milestone=task.get("is_milestone", False))
            cxid = task.get("cx_test")
            if cxid and f"CX:{cxid}" in g:
                g.add_edge(f"CX:{cxid}", tn, rel="delays")
            for pred in task.get("predecessors", []):
                pid = pred["pred"] if isinstance(pred, dict) else pred
                if f"TASK:{pid}" in g:
                    g.add_edge(tn, f"TASK:{pid}", rel="depends-on")

    return g


def _typed_reach(g: nx.MultiDiGraph, start: str, rels: set[str]) -> set[str]:
    """Set of nodes reachable from `start` following only edges whose rel is in
    `rels` (typed forward reachability)."""
    seen = {start}
    stack = [start]
    while stack:
        u = stack.pop()
        for _, v, data in g.out_edges(u, data=True):
            if data.get("rel") in rels and v not in seen:
                seen.add(v)
                stack.append(v)
    return seen


def blast_radius(g: nx.MultiDiGraph, dev_id: str) -> dict | None:
    """Compute everything a single deviation affects: the commissioning test it
    fails, the milestone(s) it slips and by how many weeks, the equipment, and the
    supplier that is the long pole of the fix. Deterministic, O(V+E)."""
    nid = dev_id if dev_id.startswith("DEV:") else f"DEV:{dev_id}"
    if nid not in g:
        return None
    reach = _typed_reach(g, nid, IMPACT_RELS) - {nid}

    def of_kind(kind: str) -> list[str]:
        return [n for n in reach if g.nodes[n].get("kind") == kind]

    cx = of_kind("cx_test")
    equipment = of_kind("equipment")
    suppliers = of_kind("supplier")
    milestones = of_kind("milestone")

    d = g.nodes[nid]
    week_caught = float(d.get("week_caught") or 0)
    level = d.get("predicted_cx_level")

    # Fix lead = the long pole of remediation: the worst reachable supplier lead
    # time, else the typical lead for that Cx level, else the deviation's own
    # measured lead time. (Every value is data-sourced.)
    sup_leads = [g.nodes[s].get("lead_time_weeks") for s in suppliers
                 if isinstance(g.nodes[s].get("lead_time_weeks"), (int, float))]
    if sup_leads:
        fix_lead = float(max(sup_leads))
    elif level in _LEVEL_TYPICAL_LEAD_WEEKS:
        fix_lead = float(_LEVEL_TYPICAL_LEAD_WEEKS[level])
    else:
        fix_lead = float(d.get("lead_time_weeks") or 0)

    # Planned week of the failing commissioning test (the earliest reachable one).
    cx_weeks = [g.nodes[c].get("scheduled_week") for c in cx
                if isinstance(g.nodes[c].get("scheduled_week"), (int, float))]
    cx_planned = float(min(cx_weeks)) if cx_weeks else float(d.get("week_fail") or 0)

    fix_complete = week_caught + fix_lead
    slip = max(0.0, fix_complete - cx_planned)

    milestone_rows = []
    for m in milestones:
        planned = g.nodes[m].get("planned_week")
        milestone_rows.append({
            "id": m, "label": g.nodes[m].get("label"),
            "planned_week": planned, "slip_weeks": round(slip, 1),
        })

    return {
        "deviation": d.get("label"),
        "component": d.get("component"),
        "cx_tests_at_risk": [{"id": c, "label": g.nodes[c].get("label")} for c in cx],
        "equipment": [g.nodes[e].get("label") for e in equipment],
        "suppliers": [{"id": s, "label": g.nodes[s].get("label"),
                       "lead_time_weeks": g.nodes[s].get("lead_time_weeks")} for s in suppliers],
        "milestones": milestone_rows,
        "weeks_at_risk": round(fix_lead, 1),
        "cx_planned_week": cx_planned,
        "fix_complete_week": round(fix_complete, 1),
        "worst_milestone_slip": round(slip, 1),
        "caught_in_time": slip <= 0,
        "reach_size": len(reach),
    }


def as_graph(g: nx.MultiDiGraph) -> dict:
    """Node/edge form for visualization, mirroring cx_graph.as_graph()."""
    nodes = [{"id": n, "kind": g.nodes[n].get("kind"), "label": g.nodes[n].get("label")}
             for n in g.nodes]
    edges = [{"from": u, "to": v, "rel": data.get("rel"), "basis": data.get("basis")}
             for u, v, data in g.edges(data=True)]
    return {"nodes": nodes, "edges": edges}


def graph_stats(g: nx.MultiDiGraph) -> dict:
    """Counts by node kind plus edge/relationship totals."""
    by_kind: dict[str, int] = {}
    for n in g.nodes:
        k = g.nodes[n].get("kind", "?")
        by_kind[k] = by_kind.get(k, 0) + 1
    rels = sorted({data.get("rel") for _, _, data in g.edges(data=True) if data.get("rel")})
    return {
        "nodes": g.number_of_nodes(),
        "edges": g.number_of_edges(),
        "by_kind": by_kind,
        "relationship_types": rels,
    }
