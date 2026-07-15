"""Enforce a transparent mutation-score floor from Mutmut results or metadata.

Mutants that make the selected tests exceed Mutmut's bounded timeout are
detected mutants: the altered behavior cannot pass CI. This matches the
standard mutation-score definition (explicit test failures plus timeouts),
while still reporting explicit kills and timeouts separately. Incomplete,
untested, suspicious, crashed, and surviving mutants never count as detected.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Iterable

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
DETECTED_STATUSES = {"killed", "caught by type check", "timeout"}
INCOMPLETE_STATUSES = {"check was interrupted by user", "not checked"}
EXCLUDED_STATUSES = {"skipped"}

EXIT_CODE_STATUS = {
    0: "survived",
    1: "killed",
    2: "check was interrupted by user",
    3: "killed",
    5: "no tests",
    24: "timeout",
    33: "no tests",
    34: "skipped",
    35: "suspicious",
    36: "timeout",
    37: "caught by type check",
    152: "timeout",
    255: "timeout",
    -24: "timeout",
    -11: "segfault",
    -9: "segfault",
    None: "not checked",
}


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


def metadata_results(root: Path) -> list[tuple[str, str]]:
    """Read Mutmut 3's durable ``*.py.meta`` files without fragile CLI flags."""
    results: list[tuple[str, str]] = []
    for metadata_path in sorted(root.rglob("*.py.meta")):
        try:
            payload = json.loads(metadata_path.read_text(encoding="utf-8"))
            exit_codes = payload["exit_code_by_key"]
        except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
            raise ValueError(f"invalid mutation metadata: {metadata_path}") from exc
        if not isinstance(exit_codes, dict):
            raise ValueError(f"invalid mutation metadata: {metadata_path}")
        for mutant_name, exit_code in sorted(exit_codes.items()):
            valid_exit_code = exit_code is None or type(exit_code) is int
            if (
                not isinstance(mutant_name, str)
                or not valid_exit_code
                or exit_code not in EXIT_CODE_STATUS
            ):
                raise ValueError(
                    f"unknown mutation result in {metadata_path}: {mutant_name!r}={exit_code!r}"
                )
            results.append((mutant_name, EXIT_CODE_STATUS[exit_code]))
    if not results:
        raise ValueError(f"no mutation metadata found under {root}")
    return results


def render_results(results: Iterable[tuple[str, str]]) -> str:
    return "".join(f"    {mutant_name}: {status}\n" for mutant_name, status in results)


def mutation_summary(counts: Counter[str]) -> dict[str, object]:
    """Calculate the detected-mutant score and expose every component."""
    incomplete = sum(counts[status] for status in INCOMPLETE_STATUSES)
    if incomplete:
        raise ValueError(f"mutation run is incomplete: {incomplete} result(s) were not checked")
    scored = sum(count for status, count in counts.items() if status not in EXCLUDED_STATUSES)
    if scored == 0:
        raise ValueError("mutation run produced no scored mutants")
    detected = sum(counts[status] for status in DETECTED_STATUSES)
    explicitly_killed = counts["killed"] + counts["caught by type check"]
    return {
        "score": round(100 * detected / scored, 2),
        "detected": detected,
        "explicitly_killed": explicitly_killed,
        "timed_out": counts["timeout"],
        "scored": scored,
        "excluded": sum(counts[status] for status in EXCLUDED_STATUSES),
        "statuses": dict(sorted(counts.items())),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("results", type=Path)
    parser.add_argument("--minimum", type=float, default=85.0)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--results-output", type=Path)
    args = parser.parse_args()
    try:
        if args.results.is_dir():
            rendered_results = render_results(metadata_results(args.results))
        else:
            rendered_results = args.results.read_text(encoding="utf-8")
        summary = mutation_summary(parse_results(rendered_results))
    except (OSError, ValueError) as exc:
        print(f"Mutation score unavailable: {exc}")
        return 2
    if args.results_output:
        args.results_output.write_text(rendered_results, encoding="utf-8", newline="\n")
    rendered = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    if args.json_output:
        args.json_output.write_text(rendered, encoding="utf-8", newline="\n")
    score = float(summary["score"])
    print(
        f"Mutation score: {score:.2f}% "
        f"({summary['detected']}/{summary['scored']} detected; "
        f"{summary['explicitly_killed']} explicit kills, {summary['timed_out']} timeouts)"
    )
    if score < args.minimum:
        print(f"Mutation score gate failed: required >= {args.minimum:.2f}%")
        return 1
    print(f"Mutation score gate passed: required >= {args.minimum:.2f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
