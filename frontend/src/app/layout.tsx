import "./globals.css";
import type { Metadata } from "next";
import Sidebar from "@/components/Sidebar";

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
        <Sidebar />
        <div className="flex-1 ml-64 flex flex-col min-h-screen">
          {children}
        </div>
      </body>
    </html>
  );
}
