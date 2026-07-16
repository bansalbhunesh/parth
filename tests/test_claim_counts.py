"""Every judge-facing surface must state the same test counts.

The full equality gate against the *collected* suite runs in CI and demo-gate
(scripts/check_claim_counts.py collects with pytest there); this in-suite check
is the fast subset — all registered surfaces must agree with each other — so a
half-synced edit fails locally without a subprocess collection pass.
"""

from scripts.check_claim_counts import (
    EXACT_BACKEND_SURFACES,
    FLOOR_BACKEND_SURFACES,
    check,
    claims,
)


def test_every_surface_agrees_with_claims_ts():
    backend_claims = claims(EXACT_BACKEND_SURFACES)
    declared = dict(backend_claims)["frontend/lib/claims.ts"]

    assert check(backend_actual=declared, frontend_actual=None) == []


def test_floor_claims_do_not_exceed_declared_count():
    declared = dict(claims(EXACT_BACKEND_SURFACES))["frontend/lib/claims.ts"]

    for path, floor in claims(FLOOR_BACKEND_SURFACES):
        assert floor <= declared, f"{path} floor {floor}+ exceeds declared {declared}"


def test_gate_reports_a_drifted_surface():
    declared = dict(claims(EXACT_BACKEND_SURFACES))["frontend/lib/claims.ts"]

    failures = check(backend_actual=declared + 1, frontend_actual=None)

    assert failures, "gate must flag every exact claim when the suite grows"
    assert any("claims.ts" in failure for failure in failures)
