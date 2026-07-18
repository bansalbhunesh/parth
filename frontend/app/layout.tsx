import "./globals.css";
import type { Metadata, Viewport } from "next";
import { IBM_Plex_Mono, IBM_Plex_Sans, IBM_Plex_Serif } from "next/font/google";
import SiteHeader from "../components/SiteHeader";
import SiteFooter from "../components/SiteFooter";
import { PRODUCT_CLAIMS } from "../lib/claims";

const plexSerif = IBM_Plex_Serif({
  subsets: ["latin"],
  weight: ["300", "400", "500"],
  variable: "--font-display",
  display: "swap",
});

const plexSans = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-body",
  display: "swap",
});

const plexMono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500"],
  variable: "--font-mono",
  display: "swap",
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
    { media: "(prefers-color-scheme: light)", color: "oklch(96.6% 0.004 240)" },
    { media: "(prefers-color-scheme: dark)", color: "oklch(17.5% 0.014 255)" },
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
      className={`${plexSerif.variable} ${plexSans.variable} ${plexMono.variable}`}
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
      <body>
        <a className="skip-link" href="#main-content">Skip to main content</a>
        <SiteHeader />
        {children}
        <SiteFooter />
      </body>
    </html>
  );
}
