"""Bundle the deterministic decision-loop blocks for an analysis response.

Every analyze surface (POST /analyze, the streaming paths, upload, vision) must
attach the same systemic layers so the Judge-Mode panel renders identically no
matter which path the demo drives. Keeping the composition in one place stops a
new endpoint from silently shipping without them.
"""

from __future__ import annotations

from backend.agents.compound_risk import analyze_compound_risk
from backend.agents.evidence_strength import evidence_report
from backend.agents.remediation import plan_remediation


def decision_blocks(deviations: list[dict]) -> dict:
    """Compound risk + optimal remediation + evidence strength for a finding set."""
    return {
        "compound_risk": analyze_compound_risk(deviations),
        "remediation": plan_remediation(deviations),
        "evidence": evidence_report(deviations),
    }
