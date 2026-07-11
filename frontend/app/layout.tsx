import "./globals.css";
import type { Metadata, Viewport } from "next";
import { Sora, JetBrains_Mono } from "next/font/google";

// next/font self-hosts these (no runtime request to fonts.gstatic.com) and
// computes fallback-font metric overrides (ascent/descent/size-adjust) so the
// page doesn't reflow when the webfont swaps in — this is what actually fixes
// the layout shift a <link>-based Google Fonts import causes, not just speed.
const sora = Sora({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800"],
  variable: "--font-sora",
  display: "swap",
});
const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800"],
  variable: "--font-jetbrains-mono",
  display: "swap",
});

// metadataBase + Open Graph / Twitter cards: a pasted link (WhatsApp, LinkedIn,
// Slack, the Unstop form) unfurls as a branded card instead of a bare URL —
// the judge's first impression happens before the page is even opened.
const OG_IMAGE = {
  url: "/og.png",
  width: 1200,
  height: 630,
  alt: "Pramaan — catches the vendor deviation the day the submittal lands, and names the commissioning test it would have failed. Benchmark v1.2: recall 0.862, 0/64 false alerts, rule baseline 0.111, 644 tests.",
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
    <html lang="en" className={`${sora.variable} ${jetbrainsMono.variable}`}>
      <body>{children}</body>
    </html>
  );
}
