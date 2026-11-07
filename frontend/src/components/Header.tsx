"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Activity, Shield, Sparkles, RefreshCw, AlertTriangle } from "lucide-react";

interface HealthData {
  status: string;
  ai_provider: {
    name: string;
    is_mock: boolean;
    is_available: boolean;
  };
  database: {
    type: string;
    is_available: boolean;
  };
}

export default function Header({ title, subtitle }: { title: string; subtitle?: string }) {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [pendingApprovalsCount, setPendingApprovalsCount] = useState<number>(0);
  const [loading, setLoading] = useState(false);

  const fetchHealthAndApprovals = async () => {
    try {
      setLoading(true);
      const [hRes, aRes] = await Promise.all([
        fetch("http://127.0.0.1:8000/api/v1/health", { cache: "no-store" }),
        fetch("http://127.0.0.1:8000/api/v1/approvals?status=pending", { cache: "no-store" }),
      ]);
      if (hRes.ok) {
        const data = await hRes.json();
        setHealth(data);
      }
      if (aRes.ok) {
        const aData = await aRes.json();
        setPendingApprovalsCount(aData.length || 0);
      }
    } catch {
      setHealth(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealthAndApprovals();
    const interval = setInterval(fetchHealthAndApprovals, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="h-16 border-b border-nexus-700 bg-nexus-900/80 backdrop-blur-md px-8 flex items-center justify-between sticky top-0 z-20">
      <div>
        <h1 className="text-lg font-semibold text-nexus-100 flex items-center gap-2">
          {title}
        </h1>
        {subtitle && <p className="text-xs text-nexus-400">{subtitle}</p>}
      </div>

      <div className="flex items-center gap-3">
        {/* Pending Approvals Pill */}
        {pendingApprovalsCount > 0 && (
          <Link
            href="/career"
            className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-950/80 border border-amber-800 text-amber-300 text-xs font-mono hover:bg-amber-900 transition-colors animate-pulse"
          >
            <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
            <span>{pendingApprovalsCount} Approval{pendingApprovalsCount > 1 ? "s" : ""} Pending</span>
          </Link>
        )}

        {/* Backend Connectivity Status */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-nexus-800 border border-nexus-700 text-xs">
          <span
            className={`w-2 h-2 rounded-full ${
              health ? "bg-emerald-400 shadow-sm shadow-emerald-400/50" : "bg-amber-500 animate-pulse"
            }`}
          />
          <span className="text-nexus-300 font-mono text-[11px]">
            {health ? "Backend: Online" : "Backend: Connecting..."}
          </span>
        </div>

        {/* Active Provider Tag */}
        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-nexus-850 border border-nexus-700 text-xs text-nexus-300">
          <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
          <span className="text-[11px] font-mono">
            Provider: <strong className="text-nexus-100">{health?.ai_provider?.name || "mock"}</strong>
          </span>
        </div>

        {/* Refresh Button */}
        <button
          onClick={fetchHealthAndApprovals}
          title="Refresh health status"
          className="p-1.5 rounded-lg border border-nexus-700 hover:bg-nexus-800 text-nexus-400 hover:text-nexus-200 transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
        </button>
      </div>
    </header>
  );
}
