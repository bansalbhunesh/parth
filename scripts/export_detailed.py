#!/usr/bin/env python3
"""export_detailed.py — render docs/detailed_submission.html to a native PDF.

Unlike the deck (a JS slide app screenshotted frame-by-frame), the detailed
submission is a single flowing document. We use Chromium's own print-to-PDF
(`page.pdf()`), which preserves selectable/searchable text and honours the
document's `@page A4` + print-color-adjust CSS.

Usage: python scripts/export_detailed.py
"""

import pathlib
import sys

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "docs" / "detailed_submission.html"
OUT = ROOT / "docs" / "Pramaan_Detailed_Submission.pdf"


def main() -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.emulate_media(media="print", reduced_motion="reduce")
        page.goto(SRC.as_uri())
        page.wait_for_timeout(800)
        OUT.parent.mkdir(exist_ok=True)
        page.pdf(
            path=str(OUT),
            format="A4",
            print_background=True,
            margin={"top": "12mm", "bottom": "14mm", "left": "12mm", "right": "12mm"},
        )
        browser.close()

    size_mb = OUT.stat().st_size / 1e6
    print(f"Wrote {OUT} ({size_mb:.2f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
