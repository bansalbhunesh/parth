"""Project Knowledge Graph — the unifying 'living project intelligence' twin.

Assembles ONE networkx graph from the artifacts Pramaan already produces
(deviations, governing standards, commissioning tests/levels) plus, when present,
the new schedule and supply-chain layers. A single spec deviation then propagates
across four normally-siloed domains:

    compliance (standard violated)
      -> commissioning (which Cx test, which level)
        -> schedule (which milestone slips, by how many weeks)
          -> procurement (which supplier is the long pole of the fix)

`blast_radius(dev)` walks the impact edges and reports exactly that chain. The
deviation -> standard -> Cx-test edges carry standard citations; the structural,
schedule, and supply edges are deterministic data relationships (not standards-
derived). Every number comes from the data — the graph is fully deterministic and
runs offline; the language model (elsewhere) never draws an edge and never moves a
date, it only narrates the blast radius.

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


def _node(g: nx.MultiDiGraph, node_id: str, kind: str, label: str, **attrs) -> str:
    if node_id not in g:
        g.add_node(node_id, kind=kind, label=label, **attrs)
    return node_id


def _add_deviation(g: nx.MultiDiGraph, deviation: dict, cx_tests: dict, rfs_week: float) -> None:
    dev = _node(
        g,
        f"DEV:{deviation['id']}",
        "deviation",
        deviation["id"],
        component=deviation.get("component"),
        parameter=deviation.get("parameter"),
        severity=deviation.get("severity"),
        week_caught=deviation.get("week_caught"),
        week_fail=deviation.get("week_fail"),
        lead_time_weeks=deviation.get("lead_time_weeks"),
        predicted_cx_level=deviation.get("predicted_cx_level"),
    )
    component = deviation.get("component")
    if component:
        equipment = _node(g, f"EQ:{component}", "equipment", component)
        g.add_edge(dev, equipment, rel="about")
        system = component.split("-")[0]
        if system and system != component:
            g.add_edge(equipment, _node(g, f"EQ:{system}", "equipment", system), rel="part-of")
    standard = deviation.get("standard_ref")
    if standard:
        g.add_edge(
            dev,
            _node(g, f"STD:{standard}", "standard", standard),
            rel="violates",
            basis=deviation.get("spec_clause"),
        )
    cx_id = deviation.get("predicted_cx_test")
    if cx_id:
        test = cx_tests.get(cx_id, {})
        scheduled = test.get("scheduled_week")
        if not isinstance(scheduled, (int, float)):
            scheduled = deviation.get("week_fail")
        cx_node = _node(
            g,
            f"CX:{cx_id}",
            "cx_test",
            test.get("name", cx_id),
            level=deviation.get("predicted_cx_level") or test.get("level"),
            scheduled_week=scheduled,
        )
        g.add_edge(dev, cx_node, rel="predicts-failure-of", basis=deviation.get("standard_ref"))
        milestone = _node(g, _RFS, "milestone", "Ready-for-service (integrated systems test)", planned_week=rfs_week)
        g.add_edge(cx_node, milestone, rel="verified-at")


def _add_supply_item(g: nx.MultiDiGraph, item: dict) -> None:
    component = item.get("component")
    vendor = item.get("vendor") or item.get("supplier")
    if not component or not vendor:
        return
    equipment = _node(g, f"EQ:{component}", "equipment", component)
    supplier = _node(
        g,
        f"SUP:{vendor}",
        "supplier",
        vendor,
        lead_time_weeks=item.get("lead_time_weeks"),
        single_source=item.get("single_source", False),
        country=item.get("country") or item.get("origin_country"),
    )
    g.add_edge(equipment, supplier, rel="supplied-by", lead_time_weeks=item.get("lead_time_weeks"))
    if _RFS in g:
        g.add_edge(supplier, _RFS, rel="blocks", lead_time_weeks=item.get("lead_time_weeks"))


def _add_schedule_task(g: nx.MultiDiGraph, task: dict) -> None:
    task_node = _node(
        g,
        f"TASK:{task['id']}",
        "schedule_task",
        task.get("name", task["id"]),
        is_milestone=task.get("is_milestone", False),
    )
    cx_id = task.get("cx_test")
    if cx_id and f"CX:{cx_id}" in g:
        g.add_edge(f"CX:{cx_id}", task_node, rel="delays")
    for predecessor in task.get("predecessors", []):
        predecessor_id = predecessor["pred"] if isinstance(predecessor, dict) else predecessor
        if f"TASK:{predecessor_id}" in g:
            g.add_edge(task_node, f"TASK:{predecessor_id}", rel="depends-on")


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

    for d in deviations:
        _add_deviation(g, d, cx_tests, rfs_week)
            # Link the specific component (UPS-02) to its system (UPS) so a
            # system-level supply item / supplier connects to component-level
            # deviations.

    if supply_chain:
        for item in supply_chain.get("items", supply_chain.get("shipments", [])):
            _add_supply_item(g, item)

    if schedule:
        for task in schedule.get("tasks", []):
            _add_schedule_task(g, task)

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


def _nodes_of_kind(g: nx.MultiDiGraph, reachable: set[str], kind: str) -> list[str]:
    return [node_id for node_id in reachable if g.nodes[node_id].get("kind") == kind]


def _fix_lead_weeks(g: nx.MultiDiGraph, suppliers: list[str], deviation: dict) -> float:
    supplier_leads = [
        g.nodes[supplier].get("lead_time_weeks")
        for supplier in suppliers
        if isinstance(g.nodes[supplier].get("lead_time_weeks"), (int, float))
    ]
    if supplier_leads:
        return float(max(supplier_leads))
    level = deviation.get("predicted_cx_level")
    if level in _LEVEL_TYPICAL_LEAD_WEEKS:
        return float(_LEVEL_TYPICAL_LEAD_WEEKS[level])
    return float(deviation.get("lead_time_weeks") or 0)


def _planned_cx_week(g: nx.MultiDiGraph, cx_nodes: list[str], deviation: dict) -> float:
    weeks = [
        g.nodes[cx_node].get("scheduled_week")
        for cx_node in cx_nodes
        if isinstance(g.nodes[cx_node].get("scheduled_week"), (int, float))
    ]
    return float(min(weeks)) if weeks else float(deviation.get("week_fail") or 0)


def _milestone_rows(g: nx.MultiDiGraph, milestones: list[str], slip: float) -> list[dict]:
    return [
        {
            "id": milestone,
            "label": g.nodes[milestone].get("label"),
            "planned_week": g.nodes[milestone].get("planned_week"),
            "slip_weeks": round(slip, 1),
        }
        for milestone in milestones
    ]


def blast_radius(g: nx.MultiDiGraph, dev_id: str) -> dict | None:
    """Compute everything a single deviation affects: the commissioning test it
    fails, the milestone(s) it slips and by how many weeks, the equipment, and the
    supplier that is the long pole of the fix. Deterministic, O(V+E)."""
    nid = dev_id if dev_id.startswith("DEV:") else f"DEV:{dev_id}"
    if nid not in g:
        return None
    reach = _typed_reach(g, nid, IMPACT_RELS) - {nid}

    cx = _nodes_of_kind(g, reach, "cx_test")
    equipment = _nodes_of_kind(g, reach, "equipment")
    suppliers = _nodes_of_kind(g, reach, "supplier")
    milestones = _nodes_of_kind(g, reach, "milestone")

    d = g.nodes[nid]
    week_caught = float(d.get("week_caught") or 0)

    # Fix lead = the long pole of remediation: the worst reachable supplier lead
    # time, else the typical lead for that Cx level, else the deviation's own
    # measured lead time. (Every value is data-sourced.)
    fix_lead = _fix_lead_weeks(g, suppliers, d)

    # Planned week of the failing commissioning test (the earliest reachable one).
    cx_planned = _planned_cx_week(g, cx, d)

    fix_complete = week_caught + fix_lead
    slip = max(0.0, fix_complete - cx_planned)

    milestone_rows = _milestone_rows(g, milestones, slip)

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


def simulate_remediation(
    g: nx.MultiDiGraph,
    dev_id: str,
    cost_per_week_lakh: float = 200.0,
    step: int = 1,
) -> dict | None:
    """What-if remediation: sweep the week the deviation is *caught* and report
    the resulting schedule slip (and its cost) at each point. Makes the core
    lead-time number causal and interactive.

    The mechanics are the same deterministic arithmetic as blast_radius:
        fix_complete(catch_week) = catch_week + fix_lead
        slip(catch_week)         = max(0, fix_complete - cx_planned_week)
    so slip is flat-zero until a *cliff* week, then climbs one-for-one. The
    cliff — `zero_slip_deadline = cx_planned - fix_lead` — is the last week you
    can still catch this deviation and take no schedule hit at all.

    Three labelled scenarios anchor the curve: caught at the design review
    (early), caught by Pramaan (on upload — `week_caught`), and caught at
    commissioning (the status quo — the test itself, too late). The headline is
    the honest, causal restatement of the lead-time metric:
        slip_avoided = slip(commissioning) - slip(pramaan)

    Cost is a transparently-stated translation (`cost_per_week_lakh`, a project
    assumption), never a hidden number: weeks are the defensible unit.
    """
    br = blast_radius(g, dev_id)
    if br is None:
        return None
    nid = dev_id if dev_id.startswith("DEV:") else f"DEV:{dev_id}"
    d = g.nodes[nid]

    fix_lead = float(br["weeks_at_risk"])
    cx_planned = float(br["cx_planned_week"])
    week_caught = float(d.get("week_caught") or 0)

    def slip_at(catch_week: float) -> float:
        return max(0.0, (catch_week + fix_lead) - cx_planned)

    def cost_of(slip_weeks: float) -> float:
        return round(slip_weeks * cost_per_week_lakh, 1)

    zero_slip_deadline = max(0.0, cx_planned - fix_lead)

    # Scenario anchors. Design review is a nominal early gate (week 4 or upload,
    # whichever is earlier); commissioning is the test week itself (status quo).
    design_week = min(4.0, week_caught)
    scenarios = {
        "design_review": design_week,
        "pramaan": week_caught,
        "commissioning": cx_planned,
    }
    scenario_rows = {
        name: {
            "catch_week": round(w, 1),
            "slip_weeks": round(slip_at(w), 1),
            "cost_lakh": cost_of(slip_at(w)),
        }
        for name, w in scenarios.items()
    }

    slip_avoided = round(slip_at(cx_planned) - slip_at(week_caught), 1)
    cost_avoided = cost_of(slip_at(cx_planned)) - cost_of(slip_at(week_caught))

    # A sweep for the interactive slider: catch_week from 0 to the commissioning
    # week, slip + cost at each step.
    hi = int(round(cx_planned))
    curve = [
        {"catch_week": w, "slip_weeks": round(slip_at(w), 1),
         "cost_lakh": cost_of(slip_at(w))}
        for w in range(0, hi + 1, max(1, step))
    ]

    return {
        "deviation": br["deviation"],
        "component": br["component"],
        "fix_lead_weeks": round(fix_lead, 1),
        "cx_planned_week": round(cx_planned, 1),
        "zero_slip_deadline_week": round(zero_slip_deadline, 1),
        "long_lead_trap": zero_slip_deadline <= week_caught and slip_at(week_caught) > 0,
        "cost_per_week_lakh": cost_per_week_lakh,
        "scenarios": scenario_rows,
        "slip_avoided_weeks": slip_avoided,
        "cost_avoided_lakh": round(cost_avoided, 1),
        "curve": curve,
        "assumption": (
            f"Slip is deterministic: catch_week + {round(fix_lead, 1)}wk fix lead "
            f"vs the week-{round(cx_planned, 1)} commissioning test. Cost translates "
            f"at {cost_per_week_lakh} lakh/week (a stated project assumption); "
            "weeks are the defensible unit."
        ),
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
