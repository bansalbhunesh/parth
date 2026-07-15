"""Enforce independent line and branch coverage ratchets from coverage.py JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _normalized_files(report: dict) -> dict[str, dict]:
    return {name.replace("\\", "/"): details for name, details in report.get("files", {}).items()}


def _per_file_failures(
    files: dict[str, dict], min_lines: float, min_branches: float, exempt: list[str]
) -> list[tuple[str, float, float]]:
    """Return (name, line%, branch%) for every file under the per-file floor.

    The floor is off unless a positive minimum is supplied, so existing callers
    are unaffected. Exempt paths (e.g. modules whose coverage depends on an
    optional system binary) are skipped by their normalized path.
    """
    if min_lines <= 0 and min_branches <= 0:
        return []
    exempt_set = {name.replace("\\", "/") for name in exempt}
    failures = []
    for name, details in sorted(files.items()):
        if name in exempt_set:
            continue
        summary = details["summary"]
        lines = float(summary["percent_statements_covered"])
        branches = float(summary["percent_branches_covered"])
        if lines < min_lines or branches < min_branches:
            failures.append((name, lines, branches))
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path)
    parser.add_argument("--lines", type=float, default=86.0)
    parser.add_argument("--branches", type=float, default=75.0)
    parser.add_argument(
        "--critical",
        action="append",
        default=[],
        help="Source file that must retain 100%% statement and branch coverage (repeatable).",
    )
    parser.add_argument("--min-file-lines", type=float, default=0.0)
    parser.add_argument("--min-file-branches", type=float, default=0.0)
    parser.add_argument(
        "--exempt",
        action="append",
        default=[],
        help="File exempt from the per-file coverage floor (repeatable).",
    )
    args = parser.parse_args(argv)
    report = json.loads(args.report.read_text(encoding="utf-8"))
    totals = report["totals"]
    line_coverage = float(totals["percent_statements_covered"])
    branch_coverage = float(totals["percent_branches_covered"])
    print(f"Backend coverage: lines={line_coverage:.2f}% branches={branch_coverage:.2f}%")
    if line_coverage < args.lines or branch_coverage < args.branches:
        print(f"Required ratchet: lines>={args.lines:.2f}% branches>={args.branches:.2f}%")
        return 1
    files = _normalized_files(report)
    failed = False
    for requested in args.critical:
        name = requested.replace("\\", "/")
        details = files.get(name)
        if details is None:
            print(f"Critical coverage target missing from report: {name}")
            failed = True
            continue
        summary = details["summary"]
        lines = float(summary["percent_statements_covered"])
        branches = float(summary["percent_branches_covered"])
        print(f"Critical coverage: {name} lines={lines:.2f}% branches={branches:.2f}%")
        if lines < 100.0 or branches < 100.0:
            failed = True
    if failed:
        print("Every critical coverage target must remain at 100% lines and branches.")

    floor_failures = _per_file_failures(files, args.min_file_lines, args.min_file_branches, args.exempt)
    for name, lines, branches in floor_failures:
        print(f"Per-file coverage below floor: {name} lines={lines:.2f}% branches={branches:.2f}%")
    if floor_failures:
        print(
            f"Every source file must reach lines>={args.min_file_lines:.2f}% "
            f"branches>={args.min_file_branches:.2f}% (or be explicitly exempted)."
        )
        failed = True

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
