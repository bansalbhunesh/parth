import { test, expect } from "@playwright/test";

// Covers "mobile layout" from the audit's P2-2 ask. layout.tsx's viewport
// comment claims the app is "honestly responsive down to ~360px" — this
// test checks that claim directly instead of taking the comment's word for
// it, on the exact width it names plus the judge page (the one an actual
// judge is most likely to open first on a phone).

const PAGES = ["/", "/judge", "/evidence"];

test.describe("Mobile layout — no horizontal overflow", () => {
  for (const path of PAGES) {
    test(`${path} has no horizontal scroll at 360px width`, async ({ page }) => {
      await page.setViewportSize({ width: 360, height: 800 });
      await page.goto(path, { waitUntil: "domcontentloaded" });
      await expect(page.locator("main")).toBeVisible();

      const overflow = await page.evaluate(() => ({
        scrollWidth: document.documentElement.scrollWidth,
        clientWidth: document.documentElement.clientWidth,
        offenders: Array.from(document.querySelectorAll<HTMLElement>("body *"))
          .map((element) => {
            const rect = element.getBoundingClientRect();
            return {
              selector: `${element.tagName.toLowerCase()}.${Array.from(element.classList).join(".")}`,
              left: Math.round(rect.left),
              right: Math.round(rect.right),
              width: Math.round(rect.width),
            };
          })
          .filter((rect) => rect.left < -2 || rect.right > document.documentElement.clientWidth + 2)
          .slice(0, 12),
      }));

      // A few px of slack for scrollbar-gutter rendering quirks across
      // engines; a real horizontal-spill bug overflows by tens/hundreds of
      // px, not 1-2.
      expect(
        overflow.scrollWidth,
        `Overflowing elements: ${JSON.stringify(overflow.offenders)}`,
      ).toBeLessThanOrEqual(overflow.clientWidth + 2);
    });
  }

  test("judge page nav is usable (not clipped) at 360px", async ({ page }) => {
    await page.setViewportSize({ width: 360, height: 800 });
    await page.goto("/judge");
    const nav = page.locator("nav.jm-topnav");
    await expect(nav).toBeVisible();
    const box = await nav.boundingBox();
    expect(box).not.toBeNull();
    expect(box!.width).toBeLessThanOrEqual(360);
  });
});
