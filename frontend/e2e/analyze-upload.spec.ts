import path from "path";
import { test, expect } from "@playwright/test";

// Covers the "upload PDFs" half of the live-analysis flow the audit asked
// for — real file inputs via setInputFiles, not just the paste-text path.
// The dropzone's file <input> is visually hidden (custom drag/drop UI) but
// still targetable directly, same as it is for a real user's file picker.

const SPEC_FIXTURE = path.join(__dirname, "fixtures", "spec.txt");
const SUBMITTAL_FIXTURE = path.join(__dirname, "fixtures", "submittal.txt");

test.describe("Live analysis — file upload", () => {
  test("uploads spec + submittal files and streams a result", async ({ page }) => {
    await page.goto("/judge");

    // "Upload PDFs" is the default mode, but assert it explicitly rather
    // than relying on default state.
    await page.getByRole("button", { name: "Upload PDFs" }).click();

    // The accessible name intentionally changes to the selected filename, so
    // keep a stable structural locator across that state transition.
    const dropzones = page.locator(".analyze-dropzone");
    const specDropzone = dropzones.nth(0);
    const subDropzone = dropzones.nth(1);

    await specDropzone.locator('input[type="file"]').setInputFiles(SPEC_FIXTURE);
    await subDropzone.locator('input[type="file"]').setInputFiles(SUBMITTAL_FIXTURE);

    // The dropzone shows the picked filename once a file is set.
    await expect(specDropzone).toContainText("spec.txt");
    await expect(subDropzone).toContainText("submittal.txt");

    await page.getByRole("button", { name: "Upload & Analyze" }).click();

    const count = page.locator(".analyze-results-count");
    await expect(count).toBeVisible({ timeout: 30_000 });
    await expect(count).toContainText(/deviation/);
  });
});
