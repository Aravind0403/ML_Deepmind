import type { Metadata } from "next";
import "./globals.css";
import { NavShell } from "@/components/NavShell";

export const metadata: Metadata = {
  title: "ML Command Center — Deep-Path & Interview Studio",
  description: "Private local-first ML Mastery Engine & 4-Stage Staff Interview Studio",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-zinc-950 text-zinc-100 antialiased">
        <NavShell />
        <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">{children}</main>
      </body>
    </html>
  );
}
