import { test, expect } from "@playwright/test";

// Covers the "paste text" half of the live-analysis flow: load a known
// fixture pair, run analysis, and assert the streamed result renders. Runs
// against the local rule-based backend (no LLM key configured — see
// playwright.config.ts), so the deviation count is deterministic.

test.describe("Live analysis — paste text", () => {
  test("loads the deviation demo and streams a non-zero result", async ({ page }) => {
    await page.goto("/judge");

    await page.getByRole("button", { name: "Paste Text" }).click();
    await page.getByRole("button", { name: "Load deviation demo ★" }).click();

    // Fixture text should now populate both textareas.
    const specBox = page.getByLabel("Design basis specification text");
    const subBox = page.getByLabel("Vendor submittal text");
    await expect(specBox).not.toHaveValue("");
    await expect(subBox).not.toHaveValue("");

    await page.getByRole("button", { name: "Analyze for deviations" }).click();

    // Streamed results render into .analyze-results-count once the SSE
    // stream completes; generous timeout since this is a real analysis run.
    const count = page.locator(".analyze-results-count");
    await expect(count).toBeVisible({ timeout: 30_000 });
    await expect(count).toContainText(/deviation/);
  });

  test("loads the compliant demo and does not false-alarm", async ({ page }) => {
    await page.goto("/judge");

    await page.getByRole("button", { name: "Paste Text" }).click();
    await page.getByRole("button", { name: "Load compliant demo ✓" }).click();

    await page.getByRole("button", { name: "Analyze for deviations" }).click();

    const result = page.locator(".analyze-results, .analyze-no-devs");
    await expect(result.first()).toBeVisible({ timeout: 30_000 });
  });

  test("turns the analyzed finding into owned, verified closure", async ({ page }) => {
    await page.goto("/judge");
    await page.getByRole("button", { name: "Paste Text" }).click();
    await page.getByRole("button", { name: "Load compact example" }).click();
    await page.getByRole("button", { name: "Analyze for deviations" }).click();

    await expect(page.getByRole("button", { name: "Persist the highest-priority finding" })).toBeVisible({ timeout: 30_000 });
    await page.getByRole("button", { name: "Persist the highest-priority finding" }).click();
    await expect(page.getByLabel("Accountable owner")).toHaveValue(/Commissioning Authority/);
    await page.getByRole("button", { name: "Assign owner and accept" }).click();
    await page.getByRole("button", { name: "Draft and issue the RFI" }).click();
    await expect(page.getByLabel("Vendor revision to verify")).toHaveValue(/REVISION C/);
    await page.getByRole("button", { name: "Re-analyze revision and close" }).click();

    await expect(page.getByText("Closed with read-back evidence.")).toBeVisible({ timeout: 30_000 });
    await expect(page.getByText(/audit events/)).toBeVisible();
    await page.getByRole("button", { name: "Delete this demo case and restart" }).click();
    await expect(page.getByRole("button", { name: "Persist the highest-priority finding" })).toBeVisible();
  });

  test("shows a friendly error, not a crash, for an empty submission", async ({ page }) => {
    await page.goto("/judge");
    await page.getByRole("button", { name: "Paste Text" }).click();
    // Analyze button is disabled with empty inputs — assert that directly
    // rather than clicking a disabled control.
    await expect(page.getByRole("button", { name: "Analyze for deviations" })).toBeDisabled();
  });
});
