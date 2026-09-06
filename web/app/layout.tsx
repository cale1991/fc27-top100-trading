import type { Metadata, Viewport } from "next";
import "./globals.css";
import { AppShell } from "@/components/AppShell";

export const metadata: Metadata = {
  title: "FC27 Trading Terminal",
  description: "PC Ultimate Team trading decision terminal",
  manifest: "/manifest.webmanifest",
  appleWebApp: { capable: true, title: "FC27 Trader", statusBarStyle: "black-translucent" },
};
export const viewport: Viewport = { themeColor: "#0b0d10", width: "device-width", initialScale: 1 };

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body><AppShell>{children}</AppShell></body></html>;
}
