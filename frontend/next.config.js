/** @type {import('next').NextConfig} */
module.exports = {
  reactStrictMode: true,
  // Dev-server-only (no effect on `next build`/production): the Playwright
  // E2E suite (frontend/playwright.config.ts) drives the dev server via
  // 127.0.0.1 explicitly so it matches the backend's default bind address;
  // without this, Next.js blocks that origin's HMR websocket by default,
  // which can cascade into broken client-side interactivity under test.
  allowedDevOrigins: ["127.0.0.1"],
};
