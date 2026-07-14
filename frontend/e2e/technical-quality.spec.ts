import { expect, test } from "@playwright/test";

const ROUTES = ["/", "/judge", "/evidence", "/war-room"];

test("active routes preserve the semantic and interaction contract", async ({ page }) => {
  for (const route of ROUTES) {
    const response = await page.goto(route, { waitUntil: "load" });
    expect(response?.status(), `${route}: HTTP status`).toBe(200);
    await expect(page.locator("main"), `${route}: main landmark`).toHaveCount(1);
    await expect(page.locator("h1")).toHaveCount(1);

    const audit = await page.evaluate(() => {
      const isVisible = (element: Element) => {
        const style = getComputedStyle(element);
        const rect = element.getBoundingClientRect();
        return style.display !== "none" && style.visibility !== "hidden" && rect.width > 0 && rect.height > 0;
      };

      const accessibleName = (element: Element) => {
        const labelledBy = element.getAttribute("aria-labelledby")
          ?.split(/\s+/)
          .map((id) => document.getElementById(id)?.textContent ?? "")
          .join(" ");
        const labels = element instanceof HTMLInputElement
          || element instanceof HTMLTextAreaElement
          || element instanceof HTMLSelectElement
          ? Array.from(element.labels ?? []).map((label) => label.textContent ?? "").join(" ")
          : "";
        return [
          element.getAttribute("aria-label"),
          labelledBy,
          labels,
          element.textContent,
          element.getAttribute("title"),
          element.getAttribute("alt"),
        ].find((value) => value?.trim())?.trim() ?? "";
      };

      const interactive = Array.from(document.querySelectorAll(
        "a[href], button, input, textarea, select, [role='button']",
      )).filter(isVisible);
      const unnamed = interactive
        .filter((element) => !accessibleName(element))
        .map((element) => element.outerHTML.slice(0, 180));

      const targetSelector = [
        "button",
        "input:not([type='hidden']):not([type='file']):not([type='checkbox'])",
        "textarea",
        "select",
        "[role='button']",
        ".button",
        ".site-nav a",
        ".evidence-index a",
      ].join(",");
      const undersized = Array.from(document.querySelectorAll(targetSelector))
        .filter(isVisible)
        .map((element) => {
          const rect = element.getBoundingClientRect();
          return { element: element.outerHTML.slice(0, 120), width: rect.width, height: rect.height };
        })
        .filter(({ width, height }) => width < 44 || height < 44);

      const headingLevels = Array.from(document.querySelectorAll("h1, h2, h3, h4, h5, h6"))
        .filter(isVisible)
        .map((heading) => Number(heading.tagName.slice(1)));
      const headingJumps = headingLevels
        .map((level, index) => ({ from: headingLevels[index - 1], to: level }))
        .filter(({ from, to }) => from !== undefined && to > from + 1);

      return { unnamed, undersized, headingJumps };
    });

    expect(audit.unnamed, `${route}: unnamed interactive elements`).toEqual([]);
    expect(audit.undersized, `${route}: controls below 44×44px`).toEqual([]);
    expect(audit.headingJumps, `${route}: skipped heading levels`).toEqual([]);
  }
});

test("reduced-motion preference suppresses non-essential motion", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/", { waitUntil: "domcontentloaded" });

  const animated = await page.evaluate(() => Array.from(document.querySelectorAll("body *"))
    .filter((element) => {
      const style = getComputedStyle(element);
      const durations = `${style.animationDuration},${style.transitionDuration}`
        .split(",")
        .map((value) => value.trim())
        .map((value) => value.endsWith("ms") ? Number.parseFloat(value) / 1000 : Number.parseFloat(value))
        .filter(Number.isFinite);
      return durations.some((seconds) => seconds > 0.001);
    })
    .map((element) => element.outerHTML.slice(0, 140)));

  expect(animated).toEqual([]);
});

test("the first keyboard action exposes a working skip link", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  await page.keyboard.press("Tab");

  const skipLink = page.getByRole("link", { name: "Skip to main content" });
  await expect(skipLink).toBeFocused();
  await expect(skipLink).toBeVisible();
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(/#main-content$/);
  await expect(page.locator("#main-content")).toBeInViewport();
});
