import { test, expect } from "@playwright/test";

// Covers "evidence links" from the audit's P2-2 ask: the /evidence page's
// job is to let a judge verify claims by following links out to the repo,
// benchmark reports, and docs. A broken link there silently defeats the
// whole page's purpose, so this checks every external link actually
// resolves (not just that it renders), and that in-page anchors land on a
// real element.

test.describe("Evidence page — links", () => {
  test("renders the core evidence sections", async ({ page }) => {
    await page.goto("/evidence");
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    await expect(page.getByRole("link", { name: "GitHub repository ↗" })).toBeVisible();
  });

  test("in-page anchor links land on an existing element", async ({ page }) => {
    await page.goto("/evidence");
    const anchorLinks = page.locator('a[href^="#"]');
    const n = await anchorLinks.count();
    expect(n).toBeGreaterThan(0);
    for (let i = 0; i < n; i++) {
      const href = await anchorLinks.nth(i).getAttribute("href");
      const id = (href || "").slice(1);
      if (!id) continue;
      await expect(page.locator(`#${id}`)).toHaveCount(1);
    }
  });

  test("external evidence/citation links resolve (not 404)", async ({ page, request }) => {
    await page.goto("/evidence");
    const external = page.locator('a[target="_blank"]');
    const n = await external.count();
    expect(n).toBeGreaterThan(5); // sanity: the page should have a real evidence trail, not a handful of links

    const hrefs = new Set<string>();
    for (let i = 0; i < n; i++) {
      const href = await external.nth(i).getAttribute("href");
      if (href && href.startsWith("http")) hrefs.add(href);
    }

    // Sequential, throttled, with a UA header and one retry on 429 — github.com's
    // bot/abuse protection rate-limits back-to-back unauthenticated requests
    // more aggressively than a real browsing session. A 429 after the retry
    // means "GitHub throttled the checker," not "the link is dead," so it is
    // reported separately rather than counted as broken.
    const broken: string[] = [];
    const throttled: string[] = [];
    const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));
    let first = true;
    for (const href of hrefs) {
      if (!first) await sleep(400);
      first = false;
      let res;
      try {
        res = await request.get(href, {
          timeout: 15_000,
          maxRedirects: 5,
          headers: { "User-Agent": "Mozilla/5.0 (compatible; PramaanE2E/1.0)" },
        });
        if (res.status() === 429) {
          await sleep(3_000);
          res = await request.get(href, {
            timeout: 15_000,
            maxRedirects: 5,
            headers: { "User-Agent": "Mozilla/5.0 (compatible; PramaanE2E/1.0)" },
          });
        }
        if (res.status() === 429) {
          throttled.push(href);
        } else if (res.status() >= 400) {
          broken.push(`${res.status()} ${href}`);
        }
      } catch (err) {
        broken.push(`ERROR ${href} (${err})`);
      }
    }
    if (throttled.length) {
      console.warn(`Evidence-link check throttled by the host, not verified this run:\n${throttled.join("\n")}`);
    }
    expect(broken, `Broken evidence links:\n${broken.join("\n")}`).toEqual([]);
  });
});
