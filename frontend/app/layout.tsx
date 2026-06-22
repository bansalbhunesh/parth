import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Pramaan — EPC Deviation Intelligence",
  description:
    "Catch spec-to-submittal deviations before they fail in commissioning.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
