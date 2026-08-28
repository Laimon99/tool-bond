import "./globals.css";
import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "BondFX — Explainable TRY bond valuation in USD",
  description: "An educational, auditable proof of concept for valuing TRY bond cash flows in USD with FX forwards.",
  icons: {
    icon: "/images/bondfx-logo.png",
    apple: "/images/bondfx-logo.png",
  },
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
