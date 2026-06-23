"""
Pramaan — Standards Data Scraper

Scrapes real technical data from public standards resources and integrates
into the corpus. Uses Firecrawl (cloud API) as primary, falls back to
Crawl4ai (Playwright + headless Chromium) for sites that block API crawlers.

Usage:
    # Set Firecrawl API key (free tier: 500 pages/month)
    export FIRECRAWL_API_KEY="fc-..."

    # Run scraper
    python data/scrape_standards.py

    # Then regenerate corpus to embed any new findings
    python data/generate_corpus.py

Requirements:
    pip install firecrawl-py crawl4ai
    crawl4ai-setup
"""

import asyncio
import json
import os
import pathlib
import re
import sys

SCRAPED_DIR = pathlib.Path(__file__).parent / "scraped"

TARGETS = [
    {
        "id": "ASHRAE-TC9.9",
        "urls": [
            "https://tc0909.ashraetcs.org/",
            "https://www.ashrae.org/technical-resources/bookstore/datacom-series",
        ],
        "search_terms": [
            "ASHRAE TC 9.9 thermal guidelines data centre temperature humidity",
            "ASHRAE TC 9.9 class A1 A2 A3 A4 allowable recommended envelope",
        ],
    },
    {
        "id": "UPTIME-TIER4",
        "urls": [
            "https://uptimeinstitute.com/tier-certification",
            "https://uptimeinstitute.com/resources/asset/tier-standard-topology",
        ],
        "search_terms": [
            "Uptime Institute Tier IV fault tolerance concurrent maintainability",
            "Uptime Tier IV 2N power N+2 cooling battery autonomy requirements",
        ],
    },
    {
        "id": "TIA-942",
        "urls": [
            "https://www.tiaonline.org/standard/tia-942-c/",
        ],
        "search_terms": [
            "TIA-942-C data centre rated 1 2 3 4 cabling requirements",
            "TIA-942 Cat6A structured cabling MDA HDA EDA pathway fill",
        ],
    },
    {
        "id": "NFPA-75",
        "urls": [
            "https://www.nfpa.org/codes-and-standards/nfpa-75-standard-development",
        ],
        "search_terms": [
            "NFPA 75 fire protection IT equipment CMP CMR plenum cable rating",
            "NFPA 262 UL 910 plenum cable test smoke density flame spread",
        ],
    },
    {
        "id": "BICSI-002",
        "urls": [
            "https://www.bicsi.org/standards/bicsi-standards/data-center-design",
        ],
        "search_terms": [
            "BICSI-002-2024 data centre design cable bundle 48 pathway fill",
            "BICSI 002 commissioning levels L1 L2 L3 L4 L5 72-hour test",
        ],
    },
    {
        "id": "IS-1893",
        "urls": [
            "https://www.bis.gov.in/product/is-1893-part-1/",
        ],
        "search_terms": [
            "IS 1893 part 1 2016 seismic zone factor India II III IV V",
            "IS 1893 importance factor data centre critical infrastructure 1.5",
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
            if result.success and result.markdown:
                return result.markdown
            print(f"  Crawl4ai failed for {url}: {result.error_message}")
            return None
    except Exception as e:
        print(f"  Crawl4ai error for {url}: {e}")
        return None


async def scrape_target(target: dict):
    std_id = target["id"]
    print(f"\n{'='*60}")
    print(f"Scraping: {std_id}")
    print(f"{'='*60}")

    for url in target["urls"]:
        print(f"\n  Trying Firecrawl: {url}")
        content = await scrape_firecrawl(url)
        if content and len(content) > 200:
            save_scraped(std_id, url, content)
            continue

        print(f"  Trying Crawl4ai: {url}")
        content = await scrape_crawl4ai(url)
        if content and len(content) > 200:
            save_scraped(std_id, url, content)


async def main():
    print("Pramaan Standards Scraper")
    print("=" * 60)

    firecrawl_key = os.environ.get("FIRECRAWL_API_KEY")
    print(f"Firecrawl API key: {'set' if firecrawl_key else 'NOT SET'}")
    print(f"Output directory: {SCRAPED_DIR}")

    if not firecrawl_key:
        print("\nWARNING: No FIRECRAWL_API_KEY set.")
        print("Get a free key at https://firecrawl.dev (500 pages/month)")
        print("Falling back to Crawl4ai only.\n")

    for target in TARGETS:
        await scrape_target(target)

    print(f"\n{'='*60}")
    print(f"Scraping complete. Check {SCRAPED_DIR}/")
    print("Run 'python data/generate_corpus.py' to regenerate corpus.")


if __name__ == "__main__":
    asyncio.run(main())
