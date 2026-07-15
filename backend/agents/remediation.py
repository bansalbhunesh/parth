"""Remediation Intelligence — optimal fix sequencing over compound risk.

The Compound Risk Layer says how bad the convergence is; this says what to do
about it first. For every candidate action -- resolve one deviation, or clear a
whole convergence cluster -- it computes the marginal drop in project compound
risk and whether the action clears the soonest schedule cliff, then ranks them.

The non-obvious payoff is cluster-awareness: when several findings fail the same
commissioning test, resolving one alone barely moves the number because its
siblings still fail the gate, so the planner surfaces the cluster-level fix as
the higher-leverage action. Pure and deterministic (no LLM): it optimises over
the existing probabilistic-OR risk model in ``compound_risk``.
"""

from __future__ import annotations

from backend.agents.compound_risk import analyze_compound_risk


def _coerce_week(value: object) -> int | None:
    try:
        return None if value is None else int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _label(dev: dict) -> str:
    return f"{dev.get('component') or '?'}/{dev.get('parameter') or '?'}"


def _cliff_week(report: dict) -> int | None:
    cliff = report.get("schedule_cliff")
    return cliff["week_fail"] if cliff else None


def _cluster_members(deviations: list[dict], kind: str, key: object) -> list[dict]:
    if kind == "cx_test":
        return [d for d in deviations if d.get("predicted_cx_test") == key]
    if kind == "system":
        return [d for d in deviations if d.get("system") == key]
    return [d for d in deviations if _coerce_week(d.get("week_fail")) == key]


def _action(kind: str, target: str, base_risk: float, base_cliff: int | None,
            remaining: list[dict], resolves: list[str]) -> dict:
    residual = analyze_compound_risk(remaining)
    residual_risk = residual["project_compound_risk"]
    new_cliff = _cliff_week(residual)
    return {
        "kind": kind,
        "target": target,
        "resolves": sorted(resolves),
        "risk_reduction": round(base_risk - residual_risk, 4),
        "residual_project_risk": residual_risk,
        "clears_schedule_cliff": base_cliff is not None and new_cliff != base_cliff,
        "new_schedule_cliff_week": new_cliff,
    }


def _individual_actions(devs: list[dict], base_risk: float, base_cliff: int | None) -> list[dict]:
    actions = []
    for index, dev in enumerate(devs):
        remaining = devs[:index] + devs[index + 1 :]
        actions.append(_action("fix_deviation", _label(dev), base_risk, base_cliff, remaining, [_label(dev)]))
    return actions


def _cluster_actions(devs: list[dict], clusters: list[dict], base_risk: float,
                     base_cliff: int | None) -> list[dict]:
    actions = []
    for cluster in clusters:
        members = _cluster_members(devs, cluster["kind"], cluster["key"])
        member_ids = {id(m) for m in members}
        remaining = [d for d in devs if id(d) not in member_ids]
        target = f"{cluster['key']} ({cluster['kind']})"
        actions.append(_action("clear_cluster", target, base_risk, base_cliff, remaining, [_label(m) for m in members]))
    return actions


def plan_remediation(deviations: list[dict]) -> dict:
    """Rank remediation actions by marginal reduction in project compound risk.

    Emits both single-deviation fixes and cluster-clearing actions; the ranking
    naturally floats a cluster fix above its members when they converge on one
    commissioning gate.
    """
    devs = [d for d in (deviations or []) if isinstance(d, dict)]
    base = analyze_compound_risk(devs)
    base_risk = base["project_compound_risk"]
    base_cliff = _cliff_week(base)

    actions = _individual_actions(devs, base_risk, base_cliff) + _cluster_actions(
        devs, base["clusters"], base_risk, base_cliff
    )
    actions.sort(key=lambda a: (-a["risk_reduction"], -len(a["resolves"]), a["target"]))
    converged = any(a["kind"] == "clear_cluster" for a in actions)
    return {
        "actions": actions,
        "highest_leverage": actions[0] if actions else None,
        "has_convergence": converged,
        "note": (
            "Converged findings share a commissioning gate: clearing the whole cluster "
            "reduces risk more than any single fix, which leaves the gate failing."
            if converged
            else "No convergence: fixes are independent, so resolve the highest-risk findings first."
        ),
        "method": "deterministic marginal-risk optimisation over the compound-risk model; no LLM",
    }
