#!/usr/bin/env python3
"""Verify public provenance links used by the real-sample evidence narrative.

This check deliberately verifies link resolvability only. It does not download
or redistribute source PDFs, and it does not turn team-authored fixtures into
externally validated documents.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import ssl
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROVENANCE = ROOT / "data" / "samples" / "real" / "PROVENANCE.md"
REPORT = ROOT / "docs" / "REAL_SOURCE_LINK_CHECK.md"
URL_RE = re.compile(r"<(https?://[^>]+)>")


@dataclass(frozen=True)
class SourceLink:
    source: str
    supports: str
    url: str
    note: str


@dataclass(frozen=True)
class LinkResult:
    link: SourceLink
    status: str
    detail: str


def parse_source_links(text: str) -> list[SourceLink]:
    links: list[SourceLink] = []
    in_table = False
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("| Source | Supports | Link | Fetch check |"):
            in_table = True
            continue
        if not in_table:
            continue
        if not line.startswith("|"):
            break
        if line.startswith("|---"):
            continue

        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 4:
            continue
        match = URL_RE.search(cells[2])
        if not match:
            continue
        links.append(SourceLink(cells[0], cells[1], match.group(1), cells[3]))
    return links


def request_once(url: str, method: str, timeout: float) -> tuple[int, str]:
    req = urllib.request.Request(
        url,
        method=method,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (compatible; PramaanSourceCheck/1.0; "
                "+https://github.com/bansalbhunesh/parth)"
            ),
            "Accept": "text/html,application/pdf,*/*;q=0.8",
        },
    )
    context = ssl.create_default_context()
    # B310 accepted risk: url is parsed from data/samples/real/PROVENANCE.md,
    # a repo-tracked, maintainer-reviewed file, not runtime/attacker-controlled
    # input; this is an offline maintainer link-check script, https(s) only.
    with urllib.request.urlopen(req, timeout=timeout, context=context) as response:  # nosec B310
        final_url = response.geturl()
        code = response.getcode()
    detail = f"HTTP {code}"
    if final_url != url:
        detail += f"; redirected to {final_url}"
    return code, detail


def check_link(link: SourceLink, timeout: float) -> LinkResult:
    last_detail = ""
    saw_timeout = False
    for method in ("HEAD", "GET"):
        try:
            code, detail = request_once(link.url, method, timeout)
            if 200 <= code < 400:
                return LinkResult(link, "ok", f"{method} {detail}")
            last_detail = f"{method} {detail}"
        except urllib.error.HTTPError as exc:
            if exc.code in {401, 403, 405, 429}:
                return LinkResult(link, "manual_check", f"{method} HTTP {exc.code}: {exc.reason}")
            last_detail = f"{method} HTTP {exc.code}: {exc.reason}"
        except TimeoutError as exc:
            saw_timeout = True
            last_detail = f"{method} TimeoutError: {exc}"
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_detail = f"{method} {type(exc).__name__}: {exc}"
    if saw_timeout:
        return LinkResult(link, "manual_check", last_detail or "automated fetch timed out")
    return LinkResult(link, "unreachable", last_detail or "no response")


def render_report(results: list[LinkResult], checked_at: dt.datetime) -> str:
    ok = sum(result.status == "ok" for result in results)
    manual = sum(result.status == "manual_check" for result in results)
    bad = sum(result.status == "unreachable" for result in results)
    lines = [
        "# Real Source Link Check",
        "",
        f"Checked at: {checked_at.strftime('%Y-%m-%dT%H:%M:%SZ')}",
        "",
        "Scope: public links listed in `data/samples/real/PROVENANCE.md`.",
        "",
        "This report verifies that the cited public provenance links are resolvable or "
        "explicitly need manual browser review. It does not store or redistribute "
        "third-party PDFs, does not validate licensed standards text, and does not "
        "convert team-authored fixtures into real customer/vendor submittals.",
        "",
        f"Summary: {ok} ok, {manual} manual browser checks, {bad} unreachable.",
        "",
        "| Source | Supports | Status | Detail |",
        "|---|---|---|---|",
    ]
    for result in results:
        lines.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(result.link.source),
                    markdown_cell(result.link.supports),
                    result.status,
                    markdown_cell(result.detail),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "Policy:",
            "- `ok` means the URL responded with a 2xx/3xx status during this run.",
            "- `manual_check` means the host blocked automated verification or requires a "
            "browser/session; the citation must remain labeled as manual-checkable.",
            "- `unreachable` means the citation should not be used for a new public claim "
            "until it is repaired or replaced.",
            "- Source values still need human engineering review before they are treated as "
            "externally validated ground truth.",
            "",
        ]
    )
    return "\n".join(lines)


def markdown_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=float, default=12.0, help="per-request timeout in seconds")
    parser.add_argument("--strict", action="store_true", help="exit non-zero on manual_check or unreachable")
    parser.add_argument("--no-write", action="store_true", help="check links without rewriting the report")
    args = parser.parse_args(argv)

    links = parse_source_links(PROVENANCE.read_text(encoding="utf-8"))
    if not links:
        print(f"FAIL: no source links found in {PROVENANCE.relative_to(ROOT).as_posix()}")
        return 1

    results = [check_link(link, args.timeout) for link in links]
    report = render_report(results, dt.datetime.now(dt.UTC))
    if not args.no_write:
        REPORT.write_text(report, encoding="utf-8")

    for result in results:
        print(f"{result.status:12} {result.link.source} - {result.detail}")

    bad = [result for result in results if result.status == "unreachable"]
    manual = [result for result in results if result.status == "manual_check"]
    if args.strict and (bad or manual):
        print(f"FAIL: {len(bad)} unreachable, {len(manual)} manual_check")
        return 1
    if bad:
        print(f"WARN: {len(bad)} unreachable, {len(manual)} manual_check")
    else:
        print(f"OK: {len(results) - len(manual)} ok, {len(manual)} manual_check")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
