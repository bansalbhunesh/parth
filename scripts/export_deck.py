#!/usr/bin/env python3
"""export_deck.py — render presentation.html to a submission-ready PDF.

The deck is a JS slide app (one .slide visible at a time), so a plain
print-to-PDF captures only the active slide. This drives headless Chromium
through every slide via the deck's own goTo(), screenshots each at 1080p,
and stitches the frames into docs/Pramaan_Deck.pdf.

Usage: python scripts/export_deck.py
"""

import io
import pathlib
import sys

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
DECK = ROOT / "presentation.html"
OUT = ROOT / "docs" / "Pramaan_Deck.pdf"


def main() -> int:
    from PIL import Image

    frames: list[Image.Image] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        # Snap animations to their final state so counters/fades are complete.
        page.emulate_media(reduced_motion="reduce")
        page.goto(DECK.as_uri())
        page.wait_for_timeout(1200)
        n = page.evaluate("document.querySelectorAll('.slide').length")
        print(f"Rendering {n} slides from {DECK.name} ...")
        for i in range(n):
            page.evaluate(f"goTo({i})")
            page.wait_for_timeout(900)  # let fade-up transitions settle
            png = page.screenshot(type="png")
            frames.append(Image.open(io.BytesIO(png)).convert("RGB"))
            print(f"  slide {i + 1}/{n}")
        browser.close()

    OUT.parent.mkdir(exist_ok=True)
    frames[0].save(OUT, save_all=True, append_images=frames[1:],
                   resolution=144.0)
    size_mb = OUT.stat().st_size / 1e6
    print(f"Wrote {OUT} ({len(frames)} pages, {size_mb:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
