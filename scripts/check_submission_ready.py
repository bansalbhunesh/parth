"""Final submission guard for judge-facing placeholders.

This is intentionally separate from the normal test suite: the repository can
stay buildable before the pitch video is published, while the final Unstop gate
fails loudly if any mandatory placeholder is still present.
"""

from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]

SCANNED_FILES = [
    "README.md",
    "docs/UNSTOP_SUBMISSION.md",
    "docs/CHECKLISTS.md",
    "docs/detailed_submission.html",
]

BLOCKERS = [
    (re.compile(r"(pitch|demo)\s+video.*(<VIDEO_LINK_HERE>|placeholder|BLOCKER|link pending)", re.IGNORECASE),
     "replace the pitch-video placeholder"),
    (re.compile(r"<VIDEO_LINK_HERE>", re.IGNORECASE), "replace the pitch-video URL"),
    (re.compile(r"link lands here on submission", re.IGNORECASE), "replace the README video placeholder"),
    (re.compile(r"BLOCKER until the public link", re.IGNORECASE), "replace the README video blocker"),
    (re.compile(r"pitch video\s*\|\s*[^|\n]*placeholder", re.IGNORECASE), "mark the pitch-video row complete"),
    (re.compile(r"pitch video\s*\|[^|\n]*\|\s*[^|\n]*BLOCKER", re.IGNORECASE),
     "mark the pitch-video row complete"),
    (re.compile(r"Pitch video:</strong>\s*<span[^>]*>\s*link pending", re.IGNORECASE),
     "replace the detailed-submission video placeholder"),
]


def main() -> int:
    failures: list[str] = []
    for rel in SCANNED_FILES:
        path = ROOT / rel
        if not path.exists():
            failures.append(f"{rel}: missing scanned file")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for line_no, line in enumerate(text.splitlines(), 1):
            for rx, reason in BLOCKERS:
                if rx.search(line):
                    snippet = line.strip().encode("ascii", errors="replace").decode("ascii")
                    failures.append(f"{rel}:{line_no}: {reason}: {snippet}")
                    break

    if failures:
        print("SUBMISSION BLOCKED: mandatory judge-facing placeholders remain.\n")
        print("\n".join(failures))
        print("\nRecord/upload the demo video, paste the public logged-out URL, then rerun this check.")
        return 1

    print("Submission placeholder check passed: no mandatory video placeholders found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
