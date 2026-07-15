"""Evidence-strength scoring — deterministic per-finding trust signals.

Each deviation carries observable, checkable signals: whether the numeric
mismatch is exact, whether the commissioning mapping came from the deterministic
rule/graph (not an LLM guess), whether a governing standard and spec clause are
cited, and whether the citation was verified faithful. This module composes
those into a transparent 0-1 strength score and a band.

It is *evidence strength*, not a probability of correctness: a high score means
"this finding rests on strong, checkable signals," never "this finding is 92%
likely true." Pure and deterministic (no LLM). Fuses the confidence-scored-answer
idea from the knowledge-intelligence field into an auditable, non-probabilistic
form that matches Pramaan's claims discipline.
"""

from __future__ import annotations

import re
from collections.abc import Callable

_NUMBER = re.compile(r"-?\d+(?:\.\d+)?")
_BANDS: tuple[tuple[str, float], ...] = (("Strong", 0.80), ("Moderate", 0.50), ("Weak", 0.25))


def _number(value: object) -> float | None:
    match = _NUMBER.search(str(value if value is not None else ""))
    return float(match.group()) if match else None


def _numeric_mismatch(dev: dict) -> bool:
    required = _number(dev.get("required_value"))
    provided = _number(dev.get("provided_value"))
    return required is not None and provided is not None and required != provided


def _nonempty(dev: dict, field: str) -> bool:
    return bool(str(dev.get(field) or "").strip())


# label, weight, predicate. Weights sum to exactly 1.0 at full strength.
_SIGNALS: tuple[tuple[str, float, Callable[[dict], bool]], ...] = (
    ("exact numeric mismatch", 0.30, _numeric_mismatch),
    ("deterministic rule/graph mapping", 0.25, lambda d: str(d.get("cx_source") or "") in {"rule", "graph"}),
    ("governing standard cited", 0.20, lambda d: _nonempty(d, "standard_ref")),
    ("spec clause cited", 0.15, lambda d: _nonempty(d, "spec_clause")),
    ("citation verified faithful", 0.10, lambda d: d.get("citation_faithful") is True),
)


def _label(dev: dict) -> str:
    return f"{dev.get('component') or '?'}/{dev.get('parameter') or '?'}"


def _band(score: float) -> str:
    for name, floor in _BANDS:
        if score >= floor:
            return name
    return "Thin"


def score_evidence(deviation: dict) -> dict:
    """Score one finding's evidence strength from its checkable signals."""
    present: list[str] = []
    missing: list[str] = []
    total = 0.0
    for label, weight, predicate in _SIGNALS:
        if predicate(deviation):
            present.append(label)
            total += weight
        else:
            missing.append(label)
    score = round(min(total, 1.0), 2)
    return {
        "target": _label(deviation),
        "score": score,
        "band": _band(score),
        "signals": present,
        "missing": missing,
    }


def evidence_report(deviations: list[dict]) -> dict:
    """Score every finding and summarise the evidence profile of the analysis."""
    devs = [d for d in (deviations or []) if isinstance(d, dict)]
    findings = [score_evidence(d) for d in devs]
    return {
        "findings": findings,
        "count": len(findings),
        "strong_count": sum(1 for f in findings if f["band"] == "Strong"),
        "thin_count": sum(1 for f in findings if f["band"] == "Thin"),
        "basis": (
            "deterministic evidence-strength composite of observable signals "
            "(numeric exactness, rule/graph grounding, standard and clause citation, "
            "citation faithfulness); not a probability of correctness"
        ),
    }
