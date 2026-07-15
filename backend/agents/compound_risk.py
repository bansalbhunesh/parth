"""Compound Risk Layer — deterministic project-level risk aggregation.

Pramaan scores each spec deviation's commissioning risk in isolation. On a real
project the danger is rarely one finding; it is *convergence* — several
deviations that all fail the same commissioning test, sit in the same system, or
land on the same milestone week. Fixing one of a converged set does not clear the
gate, and a week where several failures stack is a schedule cliff, not a queue.

This module turns a list of already-Cx-enriched deviations into a systemic-risk
report. It is pure and deterministic (no LLM, no I/O): the compound score is the
probabilistic-OR of the per-deviation commissioning risk, ``1 - prod(1 - r_i)``,
which stays in ``[0, 1]`` and rises as correlated findings stack. It aggregates
scores that already exist; it makes no new field-accuracy claim.

Adapted from the "compound risk" idea seen across industrial-safety entries
(fire before any single threshold breaches) into Pramaan's commissioning domain.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Iterable

from backend.agents.commissioning import compute_risk_score

_BANDS: tuple[tuple[str, float], ...] = (("Critical", 0.85), ("High", 0.60), ("Moderate", 0.35))


def _clamp01(value: float) -> float:
    return 0.0 if value < 0.0 else 1.0 if value > 1.0 else value


def _deviation_risk(dev: dict) -> float:
    """Per-deviation commissioning risk in ``[0, 1]``, robust to messy output."""
    try:
        return _clamp01(float(compute_risk_score(dev)))
    except (TypeError, ValueError):
        return 0.0


def _combine(risks: Iterable[float]) -> float:
    """Probabilistic-OR: the chance that at least one converged finding fails."""
    product = 1.0
    for risk in risks:
        product *= 1.0 - _clamp01(risk)
    return round(_clamp01(1.0 - product), 4)


def _band(score: float) -> str:
    for name, floor in _BANDS:
        if score >= floor:
            return name
    return "Low"


def _int_or_none(value: object) -> int | None:
    try:
        return None if value is None else int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _label(dev: dict) -> str:
    return f"{dev.get('component') or '?'}/{dev.get('parameter') or '?'}"


def _summarize_cluster(kind: str, key: object, members: list[dict]) -> dict:
    weeks = [w for w in (_int_or_none(d.get("week_fail")) for d in members) if w is not None]
    return {
        "kind": kind,
        "key": key,
        "member_count": len(members),
        "members": sorted(_label(d) for d in members),
        "compound_risk": _combine(_deviation_risk(d) for d in members),
        "earliest_week_fail": min(weeks) if weeks else None,
    }


def _cluster(deviations: list[dict], kind: str, key_of: Callable[[dict], object]) -> list[dict]:
    """Group deviations by a shared key; keep only clusters with >= 2 members."""
    groups: dict[object, list[dict]] = defaultdict(list)
    for dev in deviations:
        key = key_of(dev)
        if key not in (None, "", "?"):
            groups[key].append(dev)

    clusters = [
        _summarize_cluster(kind, key, members)
        for key, members in groups.items()
        if len(members) >= 2
    ]
    clusters.sort(key=lambda c: (-c["compound_risk"], -c["member_count"], str(c["key"])))
    return clusters


def analyze_compound_risk(deviations: list[dict]) -> dict:
    """Aggregate per-deviation commissioning risk into a systemic-risk report.

    Returns the project-level compound risk, its band, the convergence clusters
    (over commissioning test / system / milestone week), and the *schedule
    cliff*: the soonest week where two or more deviations fail together.
    """
    devs = [d for d in (deviations or []) if isinstance(d, dict)]
    project = _combine(_deviation_risk(d) for d in devs)

    cx_clusters = _cluster(devs, "cx_test", lambda d: d.get("predicted_cx_test"))
    system_clusters = _cluster(devs, "system", lambda d: d.get("system"))
    week_clusters = _cluster(devs, "milestone_week", lambda d: _int_or_none(d.get("week_fail")))

    cliff: dict | None = None
    dated = [c for c in week_clusters if c["earliest_week_fail"] is not None]
    if dated:
        soonest = min(dated, key=lambda c: (c["earliest_week_fail"], -c["compound_risk"]))
        cliff = {
            "week_fail": soonest["earliest_week_fail"],
            "converging_deviations": soonest["member_count"],
            "compound_risk": soonest["compound_risk"],
            "deviations": soonest["members"],
        }

    clusters = cx_clusters + system_clusters + week_clusters
    clusters.sort(key=lambda c: (-c["compound_risk"], -c["member_count"]))
    return {
        "project_compound_risk": project,
        "risk_band": _band(project),
        "deviation_count": len(devs),
        "converged_cx_tests": [c["key"] for c in cx_clusters],
        "schedule_cliff": cliff,
        "clusters": clusters,
        "method": (
            "deterministic compound-risk aggregation: probabilistic-OR of per-deviation "
            "commissioning risk over cx-test / system / milestone-week convergence; no LLM"
        ),
    }
