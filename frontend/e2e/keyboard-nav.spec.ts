import { test, expect } from "@playwright/test";

// Covers keyboard navigation from the audit's P2-2 ask: the live-analysis
// panel's mode toggle and dropzones are custom interactive controls (a
// <button> group and a role="button" div), not native form elements, so
// keyboard operability isn't automatic — it has to be verified.

test.describe("Keyboard navigation — analyze panel", () => {
  test("Paste Text mode is reachable and activatable by keyboard alone", async ({ page }) => {
    await page.goto("/judge");

    const pasteBtn = page.getByRole("button", { name: "Paste Text" });
    await pasteBtn.focus();
    await expect(pasteBtn).toBeFocused();

    // Space activates a focused <button>, same as a mouse click.
    await page.keyboard.press("Space");
    await expect(pasteBtn).toHaveAttribute("aria-pressed", "true");

    // The textareas should now be reachable by continuing to tab forward.
    await page.keyboard.press("Tab");
    const focused = await page.evaluate(() => document.activeElement?.tagName);
    expect(["BUTTON", "TEXTAREA"]).toContain(focused);
  });

  test("file dropzone is a real keyboard target (role=button, tabIndex=0)", async ({ page }) => {
    await page.goto("/judge");
    await page.getByRole("button", { name: "Upload PDFs" }).click();

    const specDropzone = page.getByRole("button", { name: /Spec document/ });
    await specDropzone.focus();
    await expect(specDropzone).toBeFocused();
    await expect(specDropzone).toHaveAttribute("role", "button");
    await expect(specDropzone).toHaveAttribute("tabindex", "0");
  });

  test("tabbing through the mode toggle does not trap focus", async ({ page }) => {
    await page.goto("/judge");
    const uploadBtn = page.getByRole("button", { name: "Upload PDFs" });
    await uploadBtn.focus();

    const seen = new Set<string>();
    for (let i = 0; i < 6; i++) {
      const tag = await page.evaluate(() => {
        const el = document.activeElement;
        return el ? `${el.tagName}:${el.getAttribute("aria-label") || el.textContent?.trim().slice(0, 20)}` : "none";
      });
      // A real keyboard trap would repeat the same element forever; assert
      // we keep making forward progress through at least a few distinct
      // focus targets.
      seen.add(tag);
      await page.keyboard.press("Tab");
    }
    expect(seen.size).toBeGreaterThan(2);
  });
});
