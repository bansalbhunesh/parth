import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    environment: "jsdom",
    include: ["__tests__/**/*.test.{ts,tsx}"],
    setupFiles: ["./__tests__/setup.ts"],
    restoreMocks: true,
    testTimeout: 15_000,
    coverage: {
      provider: "v8",
      reporter: ["text", "json-summary"],
      include: [
        "components/AnalyzePanel.tsx",
        "components/analyze/**/*.{ts,tsx}",
        "components/ResolutionWorkflow.tsx",
        "components/ThemeToggle.tsx",
      ],
      thresholds: {
        statements: 95,
        branches: 90,
        functions: 90,
        lines: 95,
      },
    },
  },
});
