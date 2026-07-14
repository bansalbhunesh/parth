import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

const ROUTES = ["/", "/judge", "/evidence", "/war-room"];

for (const route of ROUTES) {
  test(`${route} has no serious or critical automated accessibility violations`, async ({ page }) => {
    await page.goto(route, { waitUntil: "networkidle" });
    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"])
      .analyze();
    const releaseBlocking = results.violations.filter(
      (violation) => violation.impact === "serious" || violation.impact === "critical",
    );
    expect(releaseBlocking, JSON.stringify(releaseBlocking, null, 2)).toEqual([]);
  });
}

test("primary routes reflow at the WCAG 400 percent equivalent width", async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 800 });
  for (const route of ROUTES) {
    await page.goto(route, { waitUntil: "domcontentloaded" });
    const dimensions = await page.evaluate(() => ({
      clientWidth: document.documentElement.clientWidth,
      scrollWidth: document.documentElement.scrollWidth,
    }));
    expect(dimensions.scrollWidth, `${route} overflows at 320 CSS pixels`).toBeLessThanOrEqual(dimensions.clientWidth + 2);
  }
});

test("forced-colors mode preserves focus and status text", async ({ page }) => {
  await page.emulateMedia({ forcedColors: "active" });
  await page.goto("/judge", { waitUntil: "domcontentloaded" });
  await page.keyboard.press("Tab");
  await expect(page.getByRole("link", { name: "Skip to main content" })).toBeFocused();
  await expect(page.getByText("No result is relabelled as live when the API or model is unavailable.")).toBeVisible();
});
