"""Enforce independent line and branch coverage ratchets from coverage.py JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _normalized_files(report: dict) -> dict[str, dict]:
    return {name.replace("\\", "/"): details for name, details in report.get("files", {}).items()}


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
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
