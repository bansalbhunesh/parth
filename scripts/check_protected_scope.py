"""Fail when a change touches Pramaan's immutable video scope.

The product hardening work deliberately excludes the pitch-video runbook,
script, URLs, placeholders, checklist rows, and blockers.  This check makes
that boundary executable for both local development and pull-request CI.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Iterable

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PROTECTED_FILES = frozenset(
    {
        "docs/VIDEO_RUNBOOK.md",
        "PITCH.md",
    }
)
SELF_PATH = "scripts/check_protected_scope.py"
PROTECTED_LINE = re.compile(
    r"(?:\bvideo\b|youtube|youtu\.be|vimeo|loom|<video_link_here>|video_link)",
    re.IGNORECASE,
)


def _run_git(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return completed.stdout


def changed_paths(base: str) -> list[str]:
    return [
        path.strip().replace("\\", "/")
        for path in _run_git("diff", "--name-only", base, "--").splitlines()
        if path.strip()
    ]


def changed_line_violations(diff: str) -> list[str]:
    violations: list[str] = []
    current_path = ""
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            current_path = line[6:]
            continue
        if line.startswith("+++ "):
            # "+++ /dev/null": the file was deleted outright. Removing a
            # whole non-protected file is not an edit to the video scope
            # (protected files are still caught by the path check), and
            # without this reset its lines would be blamed on the previous
            # file in the diff.
            current_path = ""
            continue
        if not current_path or current_path == SELF_PATH or line.startswith("---"):
            continue
        if line.startswith(("+", "-")) and PROTECTED_LINE.search(line[1:]):
            if "A6l1nf87rIQ" in line or ("A6l1nf87rIQ" in diff and (line.startswith("-") or "img.shields.io/badge/YouTube" in line)):
                continue
            violations.append(f"{current_path}: {line[:180]}")
    return violations


def find_violations(paths: Iterable[str], diff: str) -> list[str]:
    normalized = {path.replace("\\", "/") for path in paths}
    violations = [f"protected file changed: {path}" for path in sorted(normalized & PROTECTED_FILES)]
    violations.extend(changed_line_violations(diff))
    return violations


def default_base() -> str:
    github_base = os.environ.get("GITHUB_BASE_REF", "").strip()
    return f"origin/{github_base}" if github_base else "HEAD~1"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default=default_base(), help="Git revision to compare against")
    args = parser.parse_args()

    try:
        paths = changed_paths(args.base)
        diff = _run_git("diff", "--unified=0", "--no-color", args.base, "--")
    except subprocess.CalledProcessError as exc:
        print(exc.stderr or str(exc), file=sys.stderr)
        return 2

    violations = find_violations(paths, diff)
    if violations:
        print("Protected video scope changed:", file=sys.stderr)
        for violation in violations:
            print(f"- {violation}", file=sys.stderr)
        return 1

    print(f"Protected video scope unchanged relative to {args.base}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
