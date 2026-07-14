"""Enforce independent line and branch coverage ratchets from coverage.py JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path)
    parser.add_argument("--lines", type=float, default=86.0)
    parser.add_argument("--branches", type=float, default=75.0)
    args = parser.parse_args()
    totals = json.loads(args.report.read_text(encoding="utf-8"))["totals"]
    line_coverage = float(totals["percent_statements_covered"])
    branch_coverage = float(totals["percent_branches_covered"])
    print(f"Backend coverage: lines={line_coverage:.2f}% branches={branch_coverage:.2f}%")
    if line_coverage < args.lines or branch_coverage < args.branches:
        print(f"Required ratchet: lines>={args.lines:.2f}% branches>={args.branches:.2f}%")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
