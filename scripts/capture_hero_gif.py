#!/usr/bin/env python3
"""capture_hero_gif.py — record the judge-mode star scene as a clean GIF.

Drives the real UI (Load deviation demo ★ → Analyze → streamed findings)
against a running local stack and assembles the frames into docs/demo.gif
for the README hero. No overlays, no watermark — just the product.

Prereqs: backend with a working GEMINI_API_KEY on :8077, frontend dev on
:3000 (NEXT_PUBLIC_API=http://127.0.0.1:8077).

Usage: python scripts/capture_hero_gif.py [--app http://localhost:3000]
"""

import argparse
import io
import pathlib
import sys
import time

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "demo.gif"
WIDTH = 1280  # capture viewport; GIF is downscaled to 900 for size


def main() -> int:
    from PIL import Image

    ap = argparse.ArgumentParser()
    ap.add_argument("--app", default="http://localhost:3000")
    args = ap.parse_args()

    frames: list = []
    durations: list = []

    def snap(page, hold_ms=700):
        png = page.screenshot(type="png")
        img = Image.open(io.BytesIO(png)).convert("RGB")
        img.thumbnail((900, 10000))
        frames.append(img)
        durations.append(hold_ms)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": WIDTH, "height": 800})
        page.goto(f"{args.app}/judge")
        page.wait_for_timeout(2500)
        snap(page, 1100)  # hero

        panel = page.locator("text=LIVE ANALYSIS").first
        panel.scroll_into_view_if_needed()
        page.wait_for_timeout(800)
        snap(page, 900)

        page.get_by_role("button", name="Load deviation demo").click()
        page.wait_for_timeout(900)
        snap(page, 1100)  # documents loaded

        page.get_by_role("button", name="Analyze for deviations").click()
        # Stream phase: sample frames while the reasoning streams (~20-30s).
        results = page.locator("text=deviations found")
        t0 = time.time()
        while time.time() - t0 < 45:
            page.wait_for_timeout(2400)
            snap(page, 450)
            if results.count() > 0:
                break
        page.wait_for_timeout(800)
        # Results: bring the findings header into view and walk them gently —
        # the cards render below the Analyze button, so anchor on the header
        # rather than blind-scrolling (which overshoots into the next section).
        if results.count() > 0:
            results.first.scroll_into_view_if_needed()
            page.wait_for_timeout(500)
        snap(page, 1600)  # "N deviations found" header + first card
        for _ in range(2):
            page.mouse.wheel(0, 260)
            page.wait_for_timeout(600)
            snap(page, 1400)
        if results.count() > 0:
            results.first.scroll_into_view_if_needed()
            page.wait_for_timeout(500)
        snap(page, 2600)  # hold on the findings
        browser.close()

    OUT.parent.mkdir(exist_ok=True)
    frames[0].save(OUT, save_all=True, append_images=frames[1:],
                   duration=durations, loop=0, optimize=True)
    print(f"Wrote {OUT} ({len(frames)} frames, {OUT.stat().st_size/1e6:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
