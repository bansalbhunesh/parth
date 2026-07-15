import { once } from "node:events";
import { readFileSync, writeFileSync } from "node:fs";
import { spawn } from "node:child_process";
import { gzipSync } from "node:zlib";

const routeManifest = JSON.parse(readFileSync(".next/server/app-paths-manifest.json", "utf8"));
const routes = Object.keys(routeManifest)
  .filter((route) => route.endsWith("/page") && !route.startsWith("/_"))
  .map((route) => (route === "/page" ? "/" : route.slice(0, -"/page".length)))
  .sort();
const dynamicRoutes = routes.filter((route) => route.includes("[") || route.includes("]"));
if (dynamicRoutes.length > 0) {
  throw new Error(`bundle budget needs concrete fixtures for dynamic routes: ${dynamicRoutes.join(", ")}`);
}
if (routes.length === 0) throw new Error("no application pages were discovered in the production build");
const budgetBytes = Number.parseInt(process.env.INITIAL_JS_BUDGET_BYTES ?? `${200 * 1024}`, 10);
const port = Number.parseInt(process.env.BUNDLE_BUDGET_PORT ?? "39019", 10);
const origin = `http://127.0.0.1:${port}`;

if (!Number.isSafeInteger(budgetBytes) || budgetBytes <= 0) {
  throw new Error("INITIAL_JS_BUDGET_BYTES must be a positive integer");
}
if (!Number.isSafeInteger(port) || port < 1024 || port > 65535) {
  throw new Error("BUNDLE_BUDGET_PORT must be an unprivileged TCP port");
}

const server = spawn(process.execPath, ["scripts/start-standalone.mjs"], {
  env: { ...process.env, HOSTNAME: "127.0.0.1", PORT: `${port}` },
  stdio: ["ignore", "pipe", "pipe"],
});
let serverOutput = "";
for (const stream of [server.stdout, server.stderr]) {
  stream.on("data", (chunk) => {
    serverOutput = `${serverOutput}${chunk}`.slice(-4_000);
  });
}

const sleep = (milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds));

async function waitUntilReady() {
  for (let attempt = 0; attempt < 60; attempt += 1) {
    if (server.exitCode !== null) {
      throw new Error(`standalone server exited before readiness:\n${serverOutput}`);
    }
    try {
      const response = await fetch(origin, { signal: AbortSignal.timeout(1_000) });
      if (response.ok) return;
    } catch {
      // Startup races are expected; the bounded loop below owns the timeout.
    }
    await sleep(250);
  }
  throw new Error(`standalone server was not ready within 15 seconds:\n${serverOutput}`);
}

async function stopServer() {
  if (server.exitCode !== null) return;
  server.kill("SIGTERM");
  await Promise.race([once(server, "exit"), sleep(3_000)]);
  if (server.exitCode === null) server.kill("SIGKILL");
}

async function measureRoute(route) {
  const pageResponse = await fetch(`${origin}${route}`);
  if (!pageResponse.ok) {
    throw new Error(`${route} returned HTTP ${pageResponse.status}`);
  }
  const html = await pageResponse.text();
  const scriptUrls = new Set(
    [...html.matchAll(/<script\b[^>]*\bsrc="([^"]+\.js(?:\?[^"]*)?)"/gu)].map((match) =>
      new URL(match[1], origin),
    ),
  );
  if (scriptUrls.size === 0) throw new Error(`${route} did not declare any initial JavaScript`);

  let rawBytes = 0;
  let gzipBytes = 0;
  for (const url of scriptUrls) {
    if (url.origin !== origin) throw new Error(`${route} loads unexpected third-party script ${url}`);
    const response = await fetch(url);
    if (!response.ok) throw new Error(`${url.pathname} returned HTTP ${response.status}`);
    const source = Buffer.from(await response.arrayBuffer());
    rawBytes += source.byteLength;
    gzipBytes += gzipSync(source, { level: 9 }).byteLength;
  }
  return { route, scripts: scriptUrls.size, rawBytes, gzipBytes };
}

let measurements;
try {
  await waitUntilReady();
  measurements = await Promise.all(routes.map(measureRoute));
} finally {
  await stopServer();
}

const result = {
  budgetBytes,
  generatedAt: new Date().toISOString(),
  routes: measurements,
};
writeFileSync(".next/bundle-budget.json", `${JSON.stringify(result, null, 2)}\n`);

for (const measurement of measurements) {
  const gzipKiB = (measurement.gzipBytes / 1024).toFixed(2);
  console.log(
    `${measurement.route}: ${measurement.scripts} scripts, ${gzipKiB} KiB gzip `
      + `(${measurement.gzipBytes}/${budgetBytes} bytes)`,
  );
}

const failures = measurements.filter(({ gzipBytes }) => gzipBytes > budgetBytes);
if (failures.length > 0) {
  const names = failures.map(({ route, gzipBytes }) => `${route}=${gzipBytes}`).join(", ");
  throw new Error(`initial JavaScript budget exceeded: ${names}; maximum=${budgetBytes} bytes`);
}
console.log(`Bundle budget passed: every discovered page is <= ${(budgetBytes / 1024).toFixed(0)} KiB gzip.`);
