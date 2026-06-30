"""Predictive Schedule Risk Engine — CPM + beta-PERT Monte Carlo, pure & offline.

Deterministic (seeded) so the no-API-key demo is byte-reproducible. The headline
figures come from Monte Carlo (the analytic single-path PERT estimate is biased
optimistic when parallel paths merge, so it is reported only as a cross-check).

Detected spec deviations are injected as schedule *risk drivers*: a rework loop
adds duration to the task that feeds the failing commissioning test; a late
equipment delivery floors that task's start. The engine then reports the shift in
the integrated-systems-test (L5) milestone and the drop in on-time probability —
the "catch it at submittal, not commissioning" money-shot, quantified.

No scipy: the normal CDF uses math.erf. numpy + networkx only.
"""

from __future__ import annotations

import math

import networkx as nx
import numpy as np

CLASSIC_LAMBDA = 4.0  # PERT shape; lower = flatter/more uncertain (modified PERT)
_EPS = 1e-6


def _phi(z: float) -> float:
    """Standard-normal CDF without scipy."""
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def _finite(x, default: float = 0.0) -> float:
    """Coerce to a finite float; non-numeric / NaN / inf -> default."""
    try:
        v = float(x)
    except (TypeError, ValueError):
        return default
    return v if math.isfinite(v) else default


def _te(dur: dict) -> float:
    """Expected duration of a task duration spec (fixed or three-point PERT).
    Robust to missing keys, non-finite values, and reversed estimates."""
    dur = dur or {}
    if "fixed" in dur:
        return max(0.0, _finite(dur.get("fixed")))
    o = max(0.0, _finite(dur.get("optimistic")))
    p = max(0.0, _finite(dur.get("pessimistic")))
    m = _finite(dur.get("most_likely"))
    m = min(max(m, o), p) if p > o else o
    return (o + 4.0 * m + p) / 6.0


def _build_dag(tasks: list[dict]) -> nx.DiGraph:
    g = nx.DiGraph()
    for t in tasks:
        g.add_node(t["id"], task=t)
    for t in tasks:
        for pred in t.get("predecessors", []):
            pid = pred["pred"] if isinstance(pred, dict) else pred
            lag = float(pred.get("lag", 0)) if isinstance(pred, dict) else 0.0
            if pid not in g:
                raise ValueError(f"Task {t['id']} depends on unknown predecessor {pid!r}")
            g.add_edge(pid, t["id"], lag=lag)
    if not nx.is_directed_acyclic_graph(g):
        raise ValueError(f"Schedule has a dependency cycle: {nx.find_cycle(g)}")
    return g


def cpm(tasks: list[dict]) -> dict:
    """Deterministic Critical Path Method on expected durations.

    Returns per-task early/late start & finish, total & free float, the critical
    flag, plus the project duration and the critical path (zero-float chain).
    """
    g = _build_dag(tasks)
    order = list(nx.topological_sort(g))
    by_id = {t["id"]: t for t in tasks}
    dur = {tid: _te(by_id[tid]["duration"]) for tid in order}

    es: dict[str, float] = {}
    ef: dict[str, float] = {}
    for v in order:
        floor = float(by_id[v].get("delivery_constraint_week") or 0.0)
        preds = list(g.predecessors(v))
        start = max([ef[u] + g[u][v]["lag"] for u in preds], default=0.0)
        es[v] = max(start, floor)
        ef[v] = es[v] + dur[v]

    project = max(ef.values(), default=0.0)

    lf: dict[str, float] = {}
    ls: dict[str, float] = {}
    for v in reversed(order):
        succs = list(g.successors(v))
        lf[v] = min([ls[w] - g[v][w]["lag"] for w in succs], default=project)
        ls[v] = lf[v] - dur[v]

    out = {}
    for v in order:
        total_float = ls[v] - es[v]
        succs = list(g.successors(v))
        free_float = min([es[w] for w in succs], default=project) - ef[v]
        out[v] = {
            "name": by_id[v].get("name", v),
            "is_milestone": by_id[v].get("is_milestone", False),
            "cx_level": by_id[v].get("cx_level"),
            "es": round(es[v], 3), "ef": round(ef[v], 3),
            "ls": round(ls[v], 3), "lf": round(lf[v], 3),
            "total_float": round(total_float, 3), "free_float": round(free_float, 3),
            "critical": abs(total_float) < _EPS,
        }
    return {
        "tasks": out,
        "project_duration": round(project, 3),
        "critical_path": [v for v in order if out[v]["critical"]],
    }


def _sample(dur: dict, n: int, rng: np.random.Generator, lam: float = CLASSIC_LAMBDA) -> np.ndarray:
    """Sample n durations from a fixed value or a beta-PERT distribution."""
    dur = dur or {}
    if "fixed" in dur:
        return np.full(n, max(0.0, _finite(dur.get("fixed"))))
    o = max(0.0, _finite(dur.get("optimistic")))
    p = max(0.0, _finite(dur.get("pessimistic")))
    m = _finite(dur.get("most_likely"))
    if p <= o:  # degenerate range -> constant (np.random.beta undefined for zero range)
        return np.full(n, o)
    m = min(max(m, o), p)  # clamp most-likely into [o, p] so beta params stay valid
    a = 1.0 + lam * (m - o) / (p - o)
    b = 1.0 + lam * (p - m) / (p - o)
    return o + (p - o) * rng.beta(a, b, size=n)


def monte_carlo(
    tasks: list[dict],
    risks: list[dict] | None = None,
    deadline_week: float | None = None,
    n: int = 10_000,
    seed: int = 42,
) -> dict:
    """Vectorized beta-PERT Monte Carlo over the schedule DAG.

    Risks are injected as correlated drivers (one shared occurrence draw per risk,
    applied across every task it hits). Returns P50/P80/P90 finish, on-time
    probability, a pre-binned histogram (for the frontend), per-task criticality
    index and duration-sensitivity, and P50/P80 dates for milestone tasks.
    """
    rng = np.random.default_rng(seed)
    g = _build_dag(tasks)
    order = list(nx.topological_sort(g))

    dur = {t["id"]: _sample(t["duration"], n, rng, float(t.get("lambda", CLASSIC_LAMBDA))) for t in tasks}
    floor = {t["id"]: np.full(n, float(t.get("delivery_constraint_week") or 0.0)) for t in tasks}

    for r in risks or []:
        occur = rng.random(n) < float(r.get("probability", 1.0))  # one shared draw per risk
        targets = r.get("applies_to", [])
        if r["type"] == "rework":
            add = _sample(r["impact"], n, rng)
            for tid in targets:
                if tid in dur:
                    dur[tid] = dur[tid] + np.where(occur, add, 0.0)
        elif r["type"] == "delivery_delay":
            delay = _sample(r["delay"], n, rng)
            for tid in targets:
                if tid in floor:
                    floor[tid] = floor[tid] + np.where(occur, delay, 0.0)

    es: dict[str, np.ndarray] = {}
    ef: dict[str, np.ndarray] = {}
    for v in order:
        preds = list(g.predecessors(v))
        start = (np.maximum.reduce([ef[u] + g[u][v]["lag"] for u in preds])
                 if preds else np.zeros(n))
        es[v] = np.maximum(start, floor[v])
        ef[v] = es[v] + dur[v]

    finish = np.maximum.reduce([ef[v] for v in order]) if order else np.zeros(n)
    _f = finish[np.isfinite(finish)]
    if _f.size == 0:
        _f = np.zeros(1)

    # backward pass per trial -> criticality index
    lf: dict[str, np.ndarray] = {}
    ls: dict[str, np.ndarray] = {}
    for v in reversed(order):
        succs = list(g.successors(v))
        lf[v] = (np.minimum.reduce([ls[w] - g[v][w]["lag"] for w in succs])
                 if succs else finish)
        ls[v] = lf[v] - dur[v]

    criticality = {v: float(np.mean((ls[v] - es[v]) <= _EPS)) for v in order}
    sensitivity = {
        v: (_finite(np.corrcoef(dur[v], finish)[0, 1]) if float(np.std(dur[v])) > 0 else 0.0)
        for v in order
    }

    p50, p80, p90 = (float(x) for x in np.percentile(_f, [50, 80, 90]))
    on_time = float(np.mean(_f <= deadline_week)) if deadline_week is not None else None

    counts, edges = np.histogram(_f, bins=30)
    histogram = [
        {"x0": round(float(edges[i]), 2), "x1": round(float(edges[i + 1]), 2), "count": int(counts[i])}
        for i in range(len(counts))
    ]

    milestones = {
        t["id"]: {
            "p50": round(float(np.percentile(ef[t["id"]], 50)), 2),
            "p80": round(float(np.percentile(ef[t["id"]], 80)), 2),
        }
        for t in tasks if t.get("is_milestone")
    }

    return {
        "n_trials": n, "seed": seed,
        "p50": round(p50, 2), "p80": round(p80, 2), "p90": round(p90, 2),
        "mean_finish": round(float(np.mean(finish)), 2),
        "on_time_probability": (round(on_time, 4) if on_time is not None else None),
        "deadline_week": deadline_week,
        "histogram": histogram,
        "criticality_index": {k: round(v, 4) for k, v in criticality.items()},
        "sensitivity": {k: round(v, 4) for k, v in sensitivity.items()},
        "milestones": milestones,
    }


def simulate_finish(tasks: list[dict], risks: list[dict] | None = None,
                    n: int = 10_000, seed: int = 42) -> np.ndarray:
    """Raw (n,) array of simulated project-finish weeks — same model as
    monte_carlo(), exposed for calibration analysis."""
    rng = np.random.default_rng(seed)
    g = _build_dag(tasks)
    order = list(nx.topological_sort(g))
    dur = {t["id"]: _sample(t["duration"], n, rng, float(t.get("lambda", CLASSIC_LAMBDA))) for t in tasks}
    floor = {t["id"]: np.full(n, float(t.get("delivery_constraint_week") or 0.0)) for t in tasks}
    for r in risks or []:
        occur = rng.random(n) < float(r.get("probability", 1.0))
        if r["type"] == "rework":
            add = _sample(r["impact"], n, rng)
            for tid in r.get("applies_to", []):
                if tid in dur:
                    dur[tid] = dur[tid] + np.where(occur, add, 0.0)
        elif r["type"] == "delivery_delay":
            delay = _sample(r["delay"], n, rng)
            for tid in r.get("applies_to", []):
                if tid in floor:
                    floor[tid] = floor[tid] + np.where(occur, delay, 0.0)
    ef: dict[str, np.ndarray] = {}
    for v in order:
        preds = list(g.predecessors(v))
        start = (np.maximum.reduce([ef[u] + g[u][v]["lag"] for u in preds])
                 if preds else np.zeros(n))
        ef[v] = np.maximum(start, floor[v]) + dur[v]
    return np.maximum.reduce([ef[v] for v in order]) if order else np.zeros(n)


def analyze_schedule(schedule: dict, n: int = 10_000, seed: int = 42) -> dict:
    """Full analysis of a schedule dict: deterministic CPM + Monte Carlo, and —
    when the schedule carries deviation-driven risks — the baseline-vs-risk delta
    on the headline milestone and on-time probability (the deviation's schedule
    blast radius)."""
    tasks = schedule["tasks"]
    deadline = schedule.get("deadline_week")
    risks = schedule.get("risks", [])

    base = monte_carlo(tasks, risks=[], deadline_week=deadline, n=n, seed=seed)
    withrisk = monte_carlo(tasks, risks=risks, deadline_week=deadline, n=n, seed=seed)

    headline = _headline_milestone(tasks)
    impact = None
    if headline:
        b = base["milestones"].get(headline, {})
        w = withrisk["milestones"].get(headline, {})
        impact = {
            "milestone": headline,
            "baseline_p80": b.get("p80"),
            "at_risk_p80": w.get("p80"),
            "slip_weeks": (round(w.get("p80", 0) - b.get("p80", 0), 2)
                           if b.get("p80") is not None and w.get("p80") is not None else None),
            "baseline_on_time": base["on_time_probability"],
            "at_risk_on_time": withrisk["on_time_probability"],
        }

    return {
        "project_id": schedule.get("project_id"),
        "time_unit": schedule.get("time_unit", "weeks"),
        "deadline_week": deadline,
        "cpm": cpm(tasks),
        "monte_carlo": withrisk,
        "baseline": {"p50": base["p50"], "p80": base["p80"], "p90": base["p90"],
                     "on_time_probability": base["on_time_probability"]},
        "deviation_impact": impact,
        "n_risks": len(risks),
    }


def _headline_milestone(tasks: list[dict]) -> str | None:
    """The 'final' milestone = the latest-level / last milestone task (the L5
    integrated systems test / energization)."""
    ms = [t for t in tasks if t.get("is_milestone")]
    if not ms:
        return None
    ms.sort(key=lambda t: (t.get("cx_level") or 0))
    return ms[-1]["id"]


def derive_risks(schedule: dict, deviations: list[dict]) -> list[dict]:
    """Turn detected spec deviations into schedule risk drivers: a rework loop on
    the task that feeds the commissioning test the deviation is predicted to fail
    (fallback: a task on the same system). Critical deviations carry a heavier
    rework impact."""
    by_cx: dict[str, str] = {}
    by_comp: dict[str, str] = {}
    for t in schedule.get("tasks", []):
        if t.get("cx_test"):
            by_cx.setdefault(t["cx_test"], t["id"])
        if t.get("component"):
            by_comp.setdefault(t["component"], t["id"])
    risks = []
    for d in deviations:
        tid = by_cx.get(d.get("predicted_cx_test"))
        if not tid:
            tid = by_comp.get((d.get("component") or "").split("-")[0]) or by_comp.get(d.get("component"))
        if not tid:
            continue
        crit = d.get("severity") == "Critical"
        risks.append({
            "id": f"R-{d.get('id')}", "type": "rework", "applies_to": [tid],
            "probability": 1.0, "source_deviation": d.get("id"),
            "impact": ({"optimistic": 2, "most_likely": 4, "pessimistic": 8} if crit
                       else {"optimistic": 1, "most_likely": 2, "pessimistic": 4}),
        })
    return risks


def narrate(analysis: dict) -> dict:
    """Plain-language schedule-risk briefing. The rule-based template is filled
    only from computed numbers (always works offline); the LLM, if reachable, may
    restate those numbers more fluently but never invents a figure."""
    b = analysis.get("baseline", {})
    imp = analysis.get("deviation_impact") or {}
    parts = [f"Baseline P80 finish is week {b.get('p80')} "
             f"(on-time probability {b.get('on_time_probability')})."]
    if imp.get("slip_weeks"):
        parts.append(
            f"If the {analysis.get('n_risks', 0)} detected deviations are left uncaught, the "
            f"{imp.get('milestone')} milestone slips {imp.get('slip_weeks')} weeks "
            f"(P80 week {imp.get('at_risk_p80')}) and on-time probability falls to "
            f"{imp.get('at_risk_on_time')}; catching them at submittal review protects the date.")
    template = " ".join(parts)
    try:
        from backend.llm import restate
        return restate(
            template,
            "Rewrite as a crisp two-sentence schedule-risk briefing for an EPC director.",
            system="You are an EPC schedule-risk analyst. Use only the provided numbers.",
        )
    except Exception:
        return {"narrative": template, "mode": "rule-based-fallback"}
