import "./globals.css";
import type { Metadata, Viewport } from "next";

// metadataBase + Open Graph / Twitter cards: a pasted link (WhatsApp, LinkedIn,
// Slack, the Unstop form) unfurls as a branded card instead of a bare URL —
// the judge's first impression happens before the page is even opened.
const OG_IMAGE = {
  url: "/og.png",
  width: 1200,
  height: 630,
  alt: "Pramaan — catches the vendor deviation the day the submittal lands, and names the commissioning test it would have failed. Benchmark v1.2: recall 0.862, 0/64 false alerts, rule baseline 0.111, 605 tests.",
};

export const metadata: Metadata = {
  metadataBase: new URL("https://parth-tan.vercel.app"),
  title: "Pramaan — EPC Deviation Intelligence",
  description:
    "Spec-to-Site Deviation Sentinel + Commissioning Risk Twin for hyperscale data-centre EPC delivery. Catches deviations 27 weeks before commissioning failure.",
  icons: { icon: "/icon.svg" },
  openGraph: {
    title: "Pramaan — EPC Deviation Intelligence",
    description:
      "Catches the vendor deviation the day the submittal lands — and names the commissioning test it would have failed. Frozen benchmark v1.2: recall 0.862 · 0/64 false alerts.",
    url: "/",
    siteName: "Pramaan",
    type: "website",
    images: [OG_IMAGE],
  },
  twitter: {
    card: "summary_large_image",
    title: "Pramaan — EPC Deviation Intelligence",
    description:
      "Catches the vendor deviation the day the submittal lands — and names the commissioning test it would have failed.",
    images: ["/og.png"],
  },
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
