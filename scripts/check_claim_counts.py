"""Fail when a published test-count claim drifts from the collected reality.

The repo's history shows hand-synced counts rotting repeatedly (647 → 665 →
666 → 678 → 847 → 858 while the suite actually held 885): every judge-facing
surface carries a number, and each new test silently stales all of them. This
gate makes the drift loud: it collects the real backend test count with pytest
and verifies every registered claim surface against it.

Rules
-----
- Exact backend claims (docs, claims.ts ``backendTests``) must equal the
  collected count.
- Floor claims (README's "700+ tests" badge/prose) must not exceed it.
- Frontend claims can't be collected from Python, so every surface must agree
  with ``frontend/lib/claims.ts`` (single source of truth); pass
  ``--frontend N`` (e.g. from a vitest run) to verify the truth itself.

Usage: python scripts/check_claim_counts.py [--backend N] [--frontend N]
(--backend skips the pytest collection subprocess when the count is known.)
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Every judge-facing surface that states a BACKEND test count, with the exact
# pattern that carries the number. Adding a count to a new document means
# registering it here — an unregistered stale number is what this gate exists
# to prevent.
EXACT_BACKEND_SURFACES: tuple[tuple[str, str], ...] = (
    ("frontend/lib/claims.ts", r"backendTests:\s*(\d+)"),
    ("docs/QUALITY_GATES.md", r"Backend:\s*(\d+) tests"),
    ("docs/UNSTOP_SUBMISSION.md", r"(\d{3,}) (?:automated )?tests"),
    ("docs/detailed_submission.html", r"(\d{3,}) (?:automated )?tests"),
    ("presentation.html", r"card-value purple\">(\d+)</div><div class=\"card-label\">automated tests"),
    ("docs/DECK.md", r"\*\*(\d+)\*\* tests"),
    ("docs/CHECKLISTS.md", r"\*\*Tests\*\*.*?(\d+) passed"),
)

FLOOR_BACKEND_SURFACES: tuple[tuple[str, str], ...] = (
    ("README.md", r"tests-(\d+)%2B"),
    ("README.md", r"(\d+)\+ (?:reproducible )?tests"),
    ("README.md", r"More than (\d+) tests"),
)

FRONTEND_SURFACES: tuple[tuple[str, str], ...] = (
    ("frontend/lib/claims.ts", r"frontendTests:\s*(\d+)"),
)


def collect_backend_count() -> int:
    """Collect the suite exactly as CI runs it and parse pytest's own total."""
    out = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "--collect-only", "-q"],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
        errors="replace", check=True,
    ).stdout
    match = re.search(r"(\d+) tests collected", out)
    if not match:
        raise SystemExit(f"could not parse pytest collection output:\n{out[-500:]}")
    return int(match.group(1))


def claims(surfaces: tuple[tuple[str, str], ...]) -> list[tuple[str, int]]:
    found: list[tuple[str, int]] = []
    for rel_path, pattern in surfaces:
        text = (ROOT / rel_path).read_text(encoding="utf-8")
        matches = re.findall(pattern, text)
        if not matches:
            raise SystemExit(
                f"{rel_path}: expected a test-count claim matching {pattern!r} "
                "but found none — update the registry in scripts/check_claim_counts.py"
            )
        found.extend((rel_path, int(value)) for value in matches)
    return found


def check(backend_actual: int, frontend_actual: int | None) -> list[str]:
    failures: list[str] = []
    for path, value in claims(EXACT_BACKEND_SURFACES):
        if value != backend_actual:
            failures.append(
                f"{path}: claims {value} backend tests, suite collects {backend_actual}"
            )
    for path, value in claims(FLOOR_BACKEND_SURFACES):
        if value > backend_actual:
            failures.append(
                f"{path}: floor claim {value}+ exceeds collected count {backend_actual}"
            )
    frontend_claims = claims(FRONTEND_SURFACES)
    truth = frontend_actual if frontend_actual is not None else frontend_claims[0][1]
    for path, value in frontend_claims:
        if value != truth:
            failures.append(
                f"{path}: claims {value} frontend tests, expected {truth}"
            )
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", type=int, default=None,
                        help="known backend test count (skips pytest collection)")
    parser.add_argument("--frontend", type=int, default=None,
                        help="known frontend test count (verifies claims.ts itself)")
    args = parser.parse_args()

    backend_actual = args.backend if args.backend is not None else collect_backend_count()
    failures = check(backend_actual, args.frontend)
    if failures:
        print("Test-count claims have drifted from the collected suite:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"Claim counts verified: backend={backend_actual} on every registered surface.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
