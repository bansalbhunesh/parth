import { defineConfig, devices } from "@playwright/test";

// E2E suite against the LIVE-ANALYSIS flow (upload, paste, streamed findings)
// plus evidence links, keyboard navigation, and mobile layout — the exact
// coverage the external audit's P2-2 item asked for.
//
// Runs against real local frontend + backend servers, not the deployed
// site: no bundled fallback exists for /analyze/*/stream (lib/api.ts has no
// fallback branch for it), so there is no way to exercise the live-analysis
// flow without a reachable backend. No LLM API key is set here on purpose —
// this suite tests UI/plumbing correctness against the deterministic
// rule-based fallback (same mode="rule" path the backend test suite already
// exercises with no key configured), not model accuracy.
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  // Bound process pressure so Firefox/WebKit are not starved by five browser
  // projects plus both application servers on smaller CI and developer hosts.
  workers: 2,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? "github" : "list",
  use: {
    baseURL: "http://127.0.0.1:3100",
    trace: "on-first-retry",
  },
  projects: [
    { name: "desktop-chromium", use: { ...devices["Desktop Chrome"] } },
    { name: "desktop-firefox", use: { ...devices["Desktop Firefox"] } },
    { name: "desktop-webkit", use: { ...devices["Desktop Safari"] } },
    { name: "mobile-chromium", use: { ...devices["Pixel 5"] } },
    { name: "mobile-webkit", use: { ...devices["iPhone 13"] } },
  ],
  webServer: [
    {
      // cwd is the repo root from here (frontend/../), so the venv/python on
      // PATH resolves the same backend the rest of this repo's tests use.
      command:
        "python -m uvicorn backend.main:app --host 127.0.0.1 --port 8100",
      url: "http://127.0.0.1:8100/health",
      cwd: "..",
      reuseExistingServer: !process.env.CI,
      timeout: 30_000,
      env: {
        // Explicitly spread process.env — Playwright's webServer.env is not
        // guaranteed to merge with the parent environment, and this
        // subprocess needs PATH to resolve `python` at all.
        ...process.env,
        // Force the deterministic rule-based path — explicitly cleared (not
        // just "unset in this shell"), matching how the backend test suite
        // guarantees determinism regardless of whoever's ambient env runs
        // this suite. Deterministic output makes for a non-flaky E2E
        // assertion ("N deviations found" is stable).
        GEMINI_API_KEY: "",
        OPENAI_API_KEY: "",
        QWEN_GATEWAY_API_KEY: "",
        GROQ_API_KEY: "",
        ANTHROPIC_API_KEY: "",
        CLAUDE_API_KEY: "",
        LOCAL_LLM_ENABLED: "",
        PRAMAAN_RATE_LIMIT_ENABLED: "0",
        PRAMAAN_CORS_ORIGINS: "http://127.0.0.1:3100",
      },
    },
    {
      // Exercise the deployable bundle. The development HMR client can emit
      // transient chunk-load rejections during parallel cross-browser runs,
      // which measures the dev server rather than production behavior.
      command: "npm run build && npm run start:e2e",
      url: "http://127.0.0.1:3100",
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      env: {
        ...process.env,
        HOSTNAME: "127.0.0.1",
        PORT: "3100",
        NEXT_PUBLIC_API: "http://127.0.0.1:8100",
      },
    },
  ],
});
