"""Enforce a transparent mutation-score floor from ``mutmut results --all``."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

KNOWN_STATUSES = {
    "killed",
    "survived",
    "no tests",
    "timeout",
    "suspicious",
    "skipped",
    "caught by type check",
    "check was interrupted by user",
    "not checked",
    "segfault",
}
KILLED_STATUSES = {"killed", "caught by type check"}
INCOMPLETE_STATUSES = {"check was interrupted by user", "not checked"}
EXCLUDED_STATUSES = {"skipped"}


def parse_results(text: str) -> Counter[str]:
    """Parse Mutmut's stable ``<mutant>: <status>`` result lines."""
    counts: Counter[str] = Counter()
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or ": " not in line:
            continue
        status = line.rsplit(": ", 1)[1]
        if status not in KNOWN_STATUSES:
            raise ValueError(f"unknown mutation status: {status!r}")
        counts[status] += 1
    if not counts:
        raise ValueError("no mutation results found")
    return counts


def mutation_summary(counts: Counter[str]) -> dict[str, object]:
    """Calculate a conservative score; only explicit kills count as success."""
    incomplete = sum(counts[status] for status in INCOMPLETE_STATUSES)
    if incomplete:
        raise ValueError(f"mutation run is incomplete: {incomplete} result(s) were not checked")
    scored = sum(count for status, count in counts.items() if status not in EXCLUDED_STATUSES)
    if scored == 0:
        raise ValueError("mutation run produced no scored mutants")
    killed = sum(counts[status] for status in KILLED_STATUSES)
    return {
        "score": round(100 * killed / scored, 2),
        "killed": killed,
        "scored": scored,
        "excluded": sum(counts[status] for status in EXCLUDED_STATUSES),
        "statuses": dict(sorted(counts.items())),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("results", type=Path)
    parser.add_argument("--minimum", type=float, default=85.0)
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args()
    try:
        summary = mutation_summary(parse_results(args.results.read_text(encoding="utf-8")))
    except (OSError, ValueError) as exc:
        print(f"Mutation score unavailable: {exc}")
        return 2
    rendered = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    if args.json_output:
        args.json_output.write_text(rendered, encoding="utf-8", newline="\n")
    score = float(summary["score"])
    print(f"Mutation score: {score:.2f}% ({summary['killed']}/{summary['scored']} killed)")
    if score < args.minimum:
        print(f"Mutation score gate failed: required >= {args.minimum:.2f}%")
        return 1
    print(f"Mutation score gate passed: required >= {args.minimum:.2f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
