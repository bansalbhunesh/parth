import "./globals.css";
import type { Metadata, Viewport } from "next";
import { Geologica, Hanken_Grotesk } from "next/font/google";
import { PRODUCT_CLAIMS } from "../lib/claims";

const geologica = Geologica({
  subsets: ["latin"],
  variable: "--font-display",
  display: "optional",
});

const hanken = Hanken_Grotesk({
  subsets: ["latin"],
  variable: "--font-body",
  display: "optional",
});

const OG_IMAGE = {
  url: "/og.png",
  width: 1200,
  height: 630,
  alt: `Pramaan traces a vendor deviation to its commissioning consequence and resolution. Benchmark v${PRODUCT_CLAIMS.benchmark.version}: recall ${PRODUCT_CLAIMS.benchmark.recall}, ${PRODUCT_CLAIMS.benchmark.falseAlerts}/${PRODUCT_CLAIMS.benchmark.cleanNegatives} false alerts, ${PRODUCT_CLAIMS.verification.backendTests} backend tests, ${PRODUCT_CLAIMS.verification.frontendTests} frontend tests, and ${PRODUCT_CLAIMS.verification.browserJourneys} browser journeys.`,
};

export const metadata: Metadata = {
  metadataBase: new URL("https://parth-tan.vercel.app"),
  title: "Pramaan — Evidence to resolution for EPC delivery",
  description:
    "Compare specifications and submittals, trace each deviation to the commissioning test at risk, and close the finding through an auditable RFI workflow.",
  icons: { icon: "/icon.svg" },
  openGraph: {
    title: "Pramaan — Evidence to resolution for EPC delivery",
    description: `From cited deviation to owned resolution. Frozen benchmark v${PRODUCT_CLAIMS.benchmark.version}: recall ${PRODUCT_CLAIMS.benchmark.recall}; ${PRODUCT_CLAIMS.benchmark.falseAlerts}/${PRODUCT_CLAIMS.benchmark.cleanNegatives} false alerts.`,
    url: "/",
    siteName: "Pramaan",
    type: "website",
    images: [OG_IMAGE],
  },
  twitter: {
    card: "summary_large_image",
    title: "Pramaan — Evidence to resolution for EPC delivery",
    description: "From cited deviation to owned resolution, before commissioning.",
    images: ["/og.png"],
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "oklch(95.2% 0.011 89.7)" },
    { media: "(prefers-color-scheme: dark)", color: "oklch(20.7% 0.006 122)" },
  ],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={`${geologica.variable} ${hanken.variable}`}
      suppressHydrationWarning
    >
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html:
              "try{const s=localStorage.getItem('pramaan-theme');const t=s||(matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light');document.documentElement.dataset.theme=t}catch(e){}",
          }}
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
