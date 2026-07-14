import { expect, test } from "@playwright/test";

test("homepage renders the judge journey without runtime errors", async ({ page }) => {
  const errors: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text());
  });
  page.on("pageerror", (error) => errors.push(error.message));

  await page.goto("/");
  await expect(
    page.getByRole("heading", {
      level: 1,
      name: /Find the deviation.*Prove the consequence.*Close it before commissioning/i,
    }),
  ).toBeVisible();
  await expect(page.getByText(/reference snapshot|deterministic project snapshot/i).first()).toBeVisible();
  await expect(page.locator("[data-nextjs-dialog]"), "Next error overlay").toHaveCount(0);
  expect(errors).toEqual([]);
});

test("theme preference is usable and survives reload", async ({ page }) => {
  await page.goto("/");
  const toggle = page.getByRole("button", { name: /Switch to (dark|light) theme/ });
  await expect(toggle).toBeVisible();
  await toggle.click();
  const selected = await page.locator("html").getAttribute("data-theme");
  expect(["light", "dark"]).toContain(selected);
  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("data-theme", selected!);
});

test("finding advances through the real resolution API", async ({ page }) => {
  test.setTimeout(60_000);
  await page.goto("/#resolve");

  await page.getByRole("button", { name: "Open a protected case" }).click();
  await expect(page.getByRole("button", { name: "Assign and accept" })).toBeVisible();

  await page.getByRole("button", { name: "Assign and accept" }).click();
  await expect(page.getByRole("button", { name: "Draft and issue RFI" })).toBeVisible();

  await page.getByRole("button", { name: "Draft and issue RFI" }).click();
  await expect(page.getByRole("button", { name: "Record response and close" })).toBeVisible();

  await page.getByRole("button", { name: "Record response and close" }).click();
  await expect(page.getByText("Closed with evidence.")).toBeVisible();
  await expect(page.getByText(/audit events recorded/)).toBeVisible();
});
