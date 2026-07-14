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


def _cpm_forward(
    graph: nx.DiGraph, order: list[str], tasks: dict[str, dict], durations: dict[str, float]
) -> tuple[dict[str, float], dict[str, float]]:
    starts: dict[str, float] = {}
    finishes: dict[str, float] = {}
    for task_id in order:
        floor = float(tasks[task_id].get("delivery_constraint_week") or 0.0)
        predecessors = list(graph.predecessors(task_id))
        dependency_start = max(
            [finishes[pred] + graph[pred][task_id]["lag"] for pred in predecessors],
            default=0.0,
        )
        starts[task_id] = max(dependency_start, floor)
        finishes[task_id] = starts[task_id] + durations[task_id]
    return starts, finishes


def _cpm_backward(
    graph: nx.DiGraph, order: list[str], durations: dict[str, float], project: float
) -> tuple[dict[str, float], dict[str, float]]:
    late_finishes: dict[str, float] = {}
    late_starts: dict[str, float] = {}
    for task_id in reversed(order):
        successors = list(graph.successors(task_id))
        late_finishes[task_id] = min(
            [late_starts[successor] - graph[task_id][successor]["lag"] for successor in successors],
            default=project,
        )
        late_starts[task_id] = late_finishes[task_id] - durations[task_id]
    return late_starts, late_finishes


def _cpm_rows(
    graph: nx.DiGraph,
    order: list[str],
    tasks: dict[str, dict],
    starts: dict[str, float],
    finishes: dict[str, float],
    late_starts: dict[str, float],
    late_finishes: dict[str, float],
    project: float,
) -> dict[str, dict]:
    rows = {}
    for task_id in order:
        total_float = late_starts[task_id] - starts[task_id]
        successors = list(graph.successors(task_id))
        free_float = min([starts[successor] for successor in successors], default=project) - finishes[task_id]
        rows[task_id] = {
            "name": tasks[task_id].get("name", task_id),
            "is_milestone": tasks[task_id].get("is_milestone", False),
            "cx_level": tasks[task_id].get("cx_level"),
            "es": round(starts[task_id], 3),
            "ef": round(finishes[task_id], 3),
            "ls": round(late_starts[task_id], 3),
            "lf": round(late_finishes[task_id], 3),
            "total_float": round(total_float, 3),
            "free_float": round(free_float, 3),
            "critical": abs(total_float) < _EPS,
        }
    return rows


def cpm(tasks: list[dict]) -> dict:
    """Deterministic Critical Path Method on expected durations.

    Returns per-task early/late start & finish, total & free float, the critical
    flag, plus the project duration and the critical path (zero-float chain).
    """
    g = _build_dag(tasks)
    order = list(nx.topological_sort(g))
    by_id = {t["id"]: t for t in tasks}
    dur = {tid: _te(by_id[tid]["duration"]) for tid in order}

    es, ef = _cpm_forward(g, order, by_id, dur)
    project = max(ef.values(), default=0.0)
    ls, lf = _cpm_backward(g, order, dur, project)
    out = _cpm_rows(g, order, by_id, es, ef, ls, lf, project)
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


def _initial_trials(
    tasks: list[dict], n: int, rng: np.random.Generator
) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray]]:
    durations = {
        task["id"]: _sample(task["duration"], n, rng, float(task.get("lambda", CLASSIC_LAMBDA)))
        for task in tasks
    }
    floors = {
        task["id"]: np.full(n, float(task.get("delivery_constraint_week") or 0.0))
        for task in tasks
    }
    return durations, floors


def _apply_risks(
    durations: dict[str, np.ndarray],
    floors: dict[str, np.ndarray],
    risks: list[dict],
    n: int,
    rng: np.random.Generator,
) -> None:
    for risk in risks:
        occurs = rng.random(n) < float(risk.get("probability", 1.0))
        targets = risk.get("applies_to", [])
        if risk["type"] == "rework":
            impact = _sample(risk["impact"], n, rng)
            for task_id in targets:
                if task_id in durations:
                    durations[task_id] += np.where(occurs, impact, 0.0)
        elif risk["type"] == "delivery_delay":
            delay = _sample(risk["delay"], n, rng)
            for task_id in targets:
                if task_id in floors:
                    floors[task_id] += np.where(occurs, delay, 0.0)


def _trial_forward(
    graph: nx.DiGraph,
    order: list[str],
    durations: dict[str, np.ndarray],
    floors: dict[str, np.ndarray],
    n: int,
) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray], np.ndarray]:
    starts: dict[str, np.ndarray] = {}
    finishes: dict[str, np.ndarray] = {}
    for task_id in order:
        predecessors = list(graph.predecessors(task_id))
        start = (
            np.maximum.reduce([finishes[pred] + graph[pred][task_id]["lag"] for pred in predecessors])
            if predecessors
            else np.zeros(n)
        )
        starts[task_id] = np.maximum(start, floors[task_id])
        finishes[task_id] = starts[task_id] + durations[task_id]
    finish = np.maximum.reduce([finishes[task_id] for task_id in order]) if order else np.zeros(n)
    return starts, finishes, finish


def _trial_backward(
    graph: nx.DiGraph,
    order: list[str],
    durations: dict[str, np.ndarray],
    finish: np.ndarray,
) -> dict[str, np.ndarray]:
    late_finishes: dict[str, np.ndarray] = {}
    late_starts: dict[str, np.ndarray] = {}
    for task_id in reversed(order):
        successors = list(graph.successors(task_id))
        late_finishes[task_id] = (
            np.minimum.reduce(
                [late_starts[successor] - graph[task_id][successor]["lag"] for successor in successors]
            )
            if successors
            else finish
        )
        late_starts[task_id] = late_finishes[task_id] - durations[task_id]
    return late_starts


def _trial_histogram(finishes: np.ndarray) -> list[dict]:
    counts, edges = np.histogram(finishes, bins=30)
    return [
        {"x0": round(float(edges[index]), 2), "x1": round(float(edges[index + 1]), 2), "count": int(count)}
        for index, count in enumerate(counts)
    ]


def _trial_milestones(tasks: list[dict], finishes: dict[str, np.ndarray]) -> dict:
    return {
        task["id"]: {
            "p50": round(float(np.percentile(finishes[task["id"]], 50)), 2),
            "p80": round(float(np.percentile(finishes[task["id"]], 80)), 2),
        }
        for task in tasks
        if task.get("is_milestone")
    }


def _finite_trials(finish: np.ndarray) -> np.ndarray:
    finite = finish[np.isfinite(finish)]
    return finite if finite.size else np.zeros(1)


def _trial_diagnostics(
    order: list[str],
    durations: dict[str, np.ndarray],
    finish: np.ndarray,
    starts: dict[str, np.ndarray],
    late_starts: dict[str, np.ndarray],
) -> tuple[dict[str, float], dict[str, float]]:
    criticality = {
        task_id: float(np.mean((late_starts[task_id] - starts[task_id]) <= _EPS))
        for task_id in order
    }
    sensitivity = {
        task_id: (
            _finite(np.corrcoef(durations[task_id], finish)[0, 1])
            if float(np.std(durations[task_id])) > 0
            else 0.0
        )
        for task_id in order
    }
    return criticality, sensitivity


def _on_time_probability(finishes: np.ndarray, deadline_week: float | None) -> float | None:
    if deadline_week is None:
        return None
    return float(np.mean(finishes <= deadline_week))


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

    dur, floor = _initial_trials(tasks, n, rng)
    _apply_risks(dur, floor, risks or [], n, rng)

    es, ef, finish = _trial_forward(g, order, dur, floor, n)
    _f = _finite_trials(finish)

    # backward pass per trial -> criticality index
    ls = _trial_backward(g, order, dur, finish)

    criticality, sensitivity = _trial_diagnostics(order, dur, finish, es, ls)

    p50, p80, p90 = (float(x) for x in np.percentile(_f, [50, 80, 90]))
    on_time = _on_time_probability(_f, deadline_week)

    histogram = _trial_histogram(_f)
    milestones = _trial_milestones(tasks, ef)

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
    durations, floors = _initial_trials(tasks, n, rng)
    _apply_risks(durations, floors, risks or [], n, rng)
    _, _, finish = _trial_forward(g, order, durations, floors, n)
    return finish


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
