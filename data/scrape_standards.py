"""
Pramaan — Standards Data Scraper

Scrapes real technical data from public standards resources and integrates
into the corpus. Three-tier fallback: Firecrawl API → Crawl4ai → Playwright.

Usage:
    # Option 1: Firecrawl (cloud API, best success rate)
    export FIRECRAWL_API_KEY="fc-..."
    python data/scrape_standards.py

    # Option 2: No key needed (uses Crawl4ai / Playwright directly)
    python data/scrape_standards.py

Requirements:
    pip install firecrawl-py crawl4ai
    # Chromium must be available (session-start hook handles this)
"""

import asyncio
import json
import os
import pathlib
import re
import sys

SCRAPED_DIR = pathlib.Path(__file__).parent / "scraped"

# Secondary/blog sources that have real technical content and are less
# likely to block scrapers than official standards body sites.
TARGETS = [
    {
        "id": "ASHRAE-TC9.9",
        "urls": [
            "https://envigilance.com/compliance/ashrae-tc-9-9/",
            "https://www.cky.com.tw/en/insights/ashrae-tc9-datacenter-thermal-guidelines",
            "https://alliancechemical.com/blogs/articles/ashrae-tc-9-9-thermal-guidelines-ai-data-center-cooling",
            "https://www.birtech.com/en/blog/environmental-monitoring/server-room-temperature-ASHRAE-standard",
        ],
    },
    {
        "id": "UPTIME-TIER4",
        "urls": [
            "https://www.ingenious.build/blog-posts/data-center-tiers-explained",
            "https://datacenterss.com/uptime-institute-tier-certifications-what-data-centers-need-to-know/",
            "https://constructandcommission.com/data-center-uptime-tiers-explained/",
            "https://stratacore.com/uptime-institute-data-center-tiers-explained/",
        ],
    },
    {
        "id": "TIA-942",
        "urls": [
            "https://datacenterss.com/data-center-cabling-standards-guide/",
            "https://datacenterss.com/data-center-tier-classification-uptime-institute-vs-tia-942/",
            "https://thenetworkinstallers.com/blog/ansi-tia-942-c-standard/",
            "https://www.tiafotc.org/tia-standards-update/tia-942-c/",
        ],
    },
    {
        "id": "NFPA-75",
        "urls": [
            "https://www.focc-fiber.com/info/cmp-cable-explained-plenum-rating-103498029.html",
            "https://www.alphagary.com/post/understanding-nfpa-262-plenum-fire-test-requirements-for-cables",
            "https://www.zion-communication.com/NFPA-262-Explained-Flame-Travel-and-Smoke-Testing-for-Plenum-Cables-id49141455.html",
            "https://firetron.com/fire-suppression-systems/best-fire-suppression-systems-data-centers-server-rooms/",
        ],
    },
    {
        "id": "BICSI-002",
        "urls": [
            "https://constructandcommission.com/5-levels-of-commissioning-explained-data-center/",
            "https://dataxconnect.com/insights-data-centre-commissioning-levels/",
            "https://cxplanner.com/data-centers/resources/data-centers-level-testing",
            "https://karnodatacenter.com/files/ANSI-%20Bicsi%20002%202024%20Rev%20Overview.pdf",
        ],
    },
    {
        "id": "IS-1893",
        "urls": [
            "https://www.sseacademy.com/blog/seismic-load-application-as-per-is-1893-2016",
            "https://www.iitk.ac.in/nicee/IITGN-WB/EQ03.pdf",
            "https://infralens.in/maps/seismic-zones",
        ],
    },
]


def save_scraped(std_id: str, source: str, content: str):
    SCRAPED_DIR.mkdir(parents=True, exist_ok=True)
    safe_source = re.sub(r"[^a-zA-Z0-9]", "_", source)[:60]
    path = SCRAPED_DIR / f"{std_id}_{safe_source}.md"
    path.write_text(f"# Scraped: {std_id}\n\nSource: {source}\n\n{content}\n")
    print(f"  Saved: {path.name} ({len(content)} chars)")


async def scrape_firecrawl(url: str) -> str | None:
    """Scrape via Firecrawl cloud API (handles JS rendering, anti-bot)."""
    api_key = os.environ.get("FIRECRAWL_API_KEY")
    if not api_key:
        return None
    try:
        from firecrawl import FirecrawlApp
        app = FirecrawlApp(api_key=api_key)
        result = app.scrape_url(url, params={"formats": ["markdown"]})
        return result.get("markdown", "")
    except Exception as e:
        print(f"  Firecrawl error for {url}: {e}")
        return None


async def scrape_crawl4ai(url: str) -> str | None:
    """Scrape via Crawl4ai (headless Chromium, stealth mode)."""
    try:
        from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
        config = BrowserConfig(
            headless=True,
            browser_type="chromium",
            extra_args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"],
            enable_stealth=True,
        )
        run_config = CrawlerRunConfig(
            wait_until="networkidle",
            page_timeout=30000,
        )
        async with AsyncWebCrawler(config=config) as crawler:
            result = await crawler.arun(url, config=run_config)
            if result.success and result.markdown and len(result.markdown) > 200:
                return result.markdown
            msg = getattr(result, "error_message", "unknown")
            print(f"  Crawl4ai failed for {url}: {msg}")
            return None
    except ImportError:
        print("  Crawl4ai not installed, skipping")
        return None
    except Exception as e:
        print(f"  Crawl4ai error for {url}: {e}")
        return None


async def scrape_playwright(url: str) -> str | None:
    """Direct Playwright fallback — simpler, no crawl4ai dependency."""
    chrome_bin = "/opt/chromium/chrome-linux/chrome"
    if not os.path.exists(chrome_bin):
        return None
    try:
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                executable_path=chrome_bin,
                args=["--no-sandbox", "--disable-gpu",
                      "--disable-dev-shm-usage", "--ignore-certificate-errors"],
            )
            ctx = await browser.new_context(
                ignore_https_errors=True,
                viewport={"width": 1280, "height": 900},
            )
            page = await ctx.new_page()
            resp = await page.goto(url, timeout=30000, wait_until="domcontentloaded")
            if resp and resp.status == 200:
                content = await page.content()
                if len(content) > 500:
                    from html.parser import HTMLParser
                    text_parts = []
                    class TextExtractor(HTMLParser):
                        skip = {"script", "style", "noscript"}
                        def __init__(self):
                            super().__init__()
                            self._skip = False
                        def handle_starttag(self, tag, attrs):
                            self._skip = tag.lower() in TextExtractor.skip
                        def handle_endtag(self, tag):
                            self._skip = False
                        def handle_data(self, data):
                            if not self._skip:
                                text_parts.append(data)
                    TextExtractor().feed(content)
                    text = "\n".join(
                        line.strip() for line in "".join(text_parts).splitlines()
                        if line.strip()
                    )
                    await browser.close()
                    if len(text) > 200:
                        return text
            status = resp.status if resp else "none"
            print(f"  Playwright failed for {url}: status={status}")
            await browser.close()
            return None
    except ImportError:
        print("  Playwright not installed, skipping")
        return None
    except Exception as e:
        print(f"  Playwright error for {url}: {e}")
        return None


async def scrape_target(target: dict):
    std_id = target["id"]
    print(f"\n{'='*60}")
    print(f"Scraping: {std_id}")
    print(f"{'='*60}")

    successes = 0
    for url in target["urls"]:
        content = None

        print(f"\n  [1/3] Firecrawl: {url}")
        content = await scrape_firecrawl(url)

        if not content or len(content) < 200:
            print(f"  [2/3] Crawl4ai: {url}")
            content = await scrape_crawl4ai(url)

        if not content or len(content) < 200:
            print(f"  [3/3] Playwright: {url}")
            content = await scrape_playwright(url)

        if content and len(content) > 200:
            save_scraped(std_id, url, content)
            successes += 1
        else:
            print(f"  SKIP: all methods failed for {url}")

    return successes


async def main():
    print("Pramaan Standards Scraper v2")
    print("=" * 60)

    firecrawl_key = os.environ.get("FIRECRAWL_API_KEY")
    print(f"Firecrawl API key: {'SET' if firecrawl_key else 'NOT SET (using Crawl4ai/Playwright)'}")
    print(f"Output directory:  {SCRAPED_DIR}")

    chrome_bin = "/opt/chromium/chrome-linux/chrome"
    print(f"Chromium:          {'FOUND' if os.path.exists(chrome_bin) else 'NOT FOUND'}")
    print()

    total = 0
    for target in TARGETS:
        total += await scrape_target(target)

    print(f"\n{'='*60}")
    print(f"Done. {total} pages scraped to {SCRAPED_DIR}/")
    if total > 0:
        print("Run 'python data/generate_corpus.py' to regenerate corpus.")
    else:
        print("No pages scraped — check egress allowlist or set FIRECRAWL_API_KEY.")
        print("Required domains in egress allowlist:")
        domains = set()
        for t in TARGETS:
            for u in t["urls"]:
                from urllib.parse import urlparse
                domains.add(urlparse(u).hostname)
        for d in sorted(domains):
            print(f"  {d}")


if __name__ == "__main__":
    asyncio.run(main())
