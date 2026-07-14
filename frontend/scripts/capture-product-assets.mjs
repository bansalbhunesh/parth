import { chromium } from "@playwright/test";
import { mkdir, unlink } from "node:fs/promises";
import path from "node:path";

const baseUrl = process.env.PRAMAAN_CAPTURE_URL ?? "http://127.0.0.1:3000";
const publicDir = path.resolve("public");
const screenshotDir = path.join(publicDir, "screenshots");

const retiredAssets = [
  "architecture.png",
  "copilot.png",
  "eval.png",
  "graph.png",
  "hero-full.png",
  "pipeline.png",
  "refs.png",
  "register.png",
  "risk.png",
  "roi.png",
  "scale.png",
  "schedule.png",
  "sentinel.png",
  "standards.png",
  "supply.png",
  "systems.png",
  "twin.png",
  "workflow.png",
];

const captures = [
  { file: "overview.png", route: "/", selector: ".hero" },
  { file: "trace.png", route: "/#proof", selector: "#proof" },
  { file: "resolution.png", route: "/#resolve", selector: "#resolve" },
  { file: "analysis.png", route: "/judge", selector: ".analysis-stage" },
  { file: "evidence.png", route: "/evidence#benchmark", selector: "#benchmark" },
  { file: "interventions.png", route: "/war-room", selector: ".intervention-brief" },
];

await mkdir(screenshotDir, { recursive: true });
for (const name of retiredAssets) {
  await unlink(path.join(screenshotDir, name)).catch((error) => {
    if (error.code !== "ENOENT") throw error;
  });
}

const browser = await chromium.launch();
try {
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 }, colorScheme: "light" });
  await page.addInitScript(() => localStorage.setItem("pramaan-theme", "light"));

  for (const capture of captures) {
    await page.goto(`${baseUrl}${capture.route}`, { waitUntil: "networkidle" });
    await page.evaluate(() => {
      document.querySelectorAll("nextjs-portal").forEach((node) => node.remove());
    });
    const target = page.locator(capture.selector).first();
    await target.waitFor({ state: "visible" });
    await target.scrollIntoViewIfNeeded();
    await page.waitForTimeout(250);
    await page.screenshot({ path: path.join(screenshotDir, capture.file) });
  }

  await page.setViewportSize({ width: 1200, height: 630 });
  await page.goto(baseUrl, { waitUntil: "networkidle" });
  await page.evaluate(() => {
    document.querySelectorAll("nextjs-portal").forEach((node) => node.remove());
  });
  await page.locator(".hero").waitFor({ state: "visible" });
  await page.screenshot({ path: path.join(publicDir, "og.png") });
} finally {
  await browser.close();
}

console.log(`Captured ${captures.length} current product screenshots and og.png from ${baseUrl}.`);
