import "./globals.css";
import type { Metadata } from "next";
import AuthGate from "@/components/AuthGate";

export const metadata: Metadata = {
  title: "NEXUS AI — Personal AI Operating System",
  description: "Modular, local-first, multi-agent personal automation platform.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-nexus-950 text-nexus-100 min-h-screen antialiased flex">
        <AuthGate>{children}</AuthGate>
      </body>
    </html>
  );
}
