"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { ShieldCheck, LockKeyhole } from "lucide-react";
import { apiFetch, getApiBase } from "@/lib/api-client";

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      const response = await apiFetch(`${getApiBase()}/api/v1/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      const data = await response.json();
      if (!response.ok) {
        setError(data.detail || "Unable to sign in. Check your credentials.");
        return;
      }
      router.replace("/dashboard");
      router.refresh();
    } catch {
      setError("Cannot reach the NEXUS backend. Make sure it is running.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen w-full flex items-center justify-center bg-nexus-950 px-6">
      <section className="w-full max-w-md rounded-2xl border border-nexus-800 bg-nexus-900 p-8 shadow-2xl">
        <div className="flex items-center gap-3 mb-8">
          <div className="rounded-xl border border-cyan-800 bg-cyan-950 p-3 text-cyan-300">
            <ShieldCheck className="h-6 w-6" />
          </div>
          <div>
            <h1 className="text-xl font-semibold text-white tracking-wide">NEXUS</h1>
            <p className="text-xs text-nexus-400">Private personal operating system</p>
          </div>
        </div>
        <div className="mb-6">
          <h2 className="text-lg font-semibold text-white">Owner sign in</h2>
          <p className="mt-1 text-sm text-nexus-400">Authenticate to access your private workspace.</p>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <label className="block">
            <span className="mb-2 block text-xs font-medium uppercase tracking-wider text-nexus-400">Username</span>
            <input value={username} onChange={(event) => setUsername(event.target.value)} autoComplete="username" required minLength={3} className="w-full rounded-lg border border-nexus-700 bg-nexus-950 px-4 py-3 text-sm text-white outline-none focus:border-cyan-500" />
          </label>
          <label className="block">
            <span className="mb-2 block text-xs font-medium uppercase tracking-wider text-nexus-400">Password</span>
            <div className="relative">
              <LockKeyhole className="absolute left-3 top-3.5 h-4 w-4 text-nexus-500" />
              <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="current-password" required className="w-full rounded-lg border border-nexus-700 bg-nexus-950 py-3 pl-10 pr-4 text-sm text-white outline-none focus:border-cyan-500" />
            </div>
          </label>
          {error && <p role="alert" className="rounded-lg border border-red-900 bg-red-950/40 px-3 py-2 text-sm text-red-300">{error}</p>}
          <button type="submit" disabled={loading} className="w-full rounded-lg bg-cyan-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-cyan-500 disabled:cursor-not-allowed disabled:opacity-50">
            {loading ? "Authenticating…" : "Sign in securely"}
          </button>
        </form>
        <p className="mt-6 text-center text-[11px] leading-5 text-nexus-500">Session credentials are held in an HttpOnly cookie. No browser localStorage token is used.</p>
      </section>
    </main>
  );
}
