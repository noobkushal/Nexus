"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import Sidebar from "@/components/Sidebar";
import { apiFetch, getApiBase } from "@/lib/api-client";

export default function AuthGate({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [authorized, setAuthorized] = useState(false);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    let active = true;
    if (pathname === "/login") {
      setAuthorized(false);
      setChecking(false);
      return () => { active = false; };
    }
    setChecking(true);
    apiFetch(`${getApiBase()}/api/v1/auth/me`)
      .then((response) => {
        if (!active) return;
        if (response.ok) {
          setAuthorized(true);
          setChecking(false);
        } else {
          router.replace("/login");
        }
      })
      .catch(() => {
        if (active) router.replace("/login");
      });
    return () => { active = false; };
  }, [pathname, router]);

  if (pathname === "/login") return <>{children}</>;
  if (checking || !authorized) {
    return (
      <main className="min-h-screen flex flex-1 items-center justify-center bg-nexus-950 text-nexus-300">
        <div className="text-sm font-mono">Verifying secure NEXUS session…</div>
      </main>
    );
  }

  return (
    <>
      <Sidebar />
      <div className="flex-1 ml-64 flex flex-col min-h-screen">{children}</div>
    </>
  );
}
