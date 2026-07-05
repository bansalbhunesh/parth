import "./globals.css";
import type { Metadata, Viewport } from "next";

export const metadata: Metadata = {
  title: "Pramaan — EPC Deviation Intelligence",
  description:
    "Spec-to-Site Deviation Sentinel + Commissioning Risk Twin for hyperscale data-centre EPC delivery. Catches deviations 27 weeks before commissioning failure.",
  icons: { icon: "/icon.svg" },
};

// Correct mobile scaling so the layout is honestly responsive down to ~360px
// (no forced desktop width, no user-scaling lockout for accessibility).
export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#0a0d11",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700;800&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
