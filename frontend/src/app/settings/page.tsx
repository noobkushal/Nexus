"use client";

import { useEffect, useState } from "react";
import Header from "@/components/Header";
import { Settings, Cpu, HardDrive, Shield, Database, RefreshCw, CheckCircle2 } from "lucide-react";

interface SettingsData {
  project_name: string;
  environment: string;
  debug: boolean;
  host: string;
  port: number;
  log_level: string;
  active_provider: string;
  registered_providers: { name: string; is_mock: boolean; is_available: boolean; details: any }[];
  storage_directory: string;
  database: { type: string; url_configured: boolean };
}

export default function SettingsPage() {
  const [data, setData] = useState<SettingsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedProvider, setSelectedProvider] = useState("mock");
  const [savedNotice, setSavedNotice] = useState(false);

  const loadSettings = async () => {
    try {
      setLoading(true);
      const res = await fetch("http://127.0.0.1:8000/api/v1/settings");
      if (res.ok) {
        const json = await res.json();
        setData(json);
        setSelectedProvider(json.active_provider);
      }
    } catch (err) {
      console.error("Failed to load settings", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSettings();
  }, []);

  const handleProviderSwitch = async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/api/v1/settings/provider", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ provider_name: selectedProvider }),
      });
      if (res.ok) {
        setSavedNotice(true);
        setTimeout(() => setSavedNotice(false), 3000);
        loadSettings();
      }
    } catch (err) {
      console.error("Failed to switch provider", err);
    }
  };

  return (
    <div className="flex-1 flex flex-col bg-nexus-950">
      <Header
        title="Platform Configuration & System Governance"
        subtitle="Hardware allocation, AI model providers, and security barriers"
      />

      <main className="p-8 max-w-5xl mx-auto w-full space-y-6">
        {/* Hardware Constraints Card */}
        <div className="bg-nexus-900 border border-nexus-700 rounded-xl p-5 space-y-3">
          <div className="flex items-center gap-2">
            <HardDrive className="w-5 h-5 text-cyan-400" />
            <h2 className="text-sm font-semibold text-nexus-100">Development Hardware Profile</h2>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-1 font-mono text-xs">
            <div className="p-3 rounded-lg bg-nexus-950 border border-nexus-800">
              <span className="text-[10px] text-nexus-500 uppercase block">GPU Target</span>
              <span className="text-nexus-200 font-bold">NVIDIA RTX 3050</span>
              <span className="text-[10px] text-nexus-400 block mt-0.5">4 GB VRAM Cap</span>
            </div>
            <div className="p-3 rounded-lg bg-nexus-950 border border-nexus-800">
              <span className="text-[10px] text-nexus-500 uppercase block">System RAM</span>
              <span className="text-nexus-200 font-bold">16 GB DDR4/5</span>
              <span className="text-[10px] text-nexus-400 block mt-0.5">Bounded allocations</span>
            </div>
            <div className="p-3 rounded-lg bg-nexus-950 border border-nexus-800">
              <span className="text-[10px] text-nexus-500 uppercase block">Storage Space</span>
              <span className="text-nexus-200 font-bold">512 GB SSD</span>
              <span className="text-[10px] text-nexus-400 block mt-0.5">Local storage root</span>
            </div>
            <div className="p-3 rounded-lg bg-nexus-950 border border-nexus-800">
              <span className="text-[10px] text-nexus-500 uppercase block">Host Platform</span>
              <span className="text-nexus-200 font-bold">Windows (PowerShell)</span>
              <span className="text-[10px] text-nexus-400 block mt-0.5">WSL2 / Docker ready</span>
            </div>
          </div>
        </div>

        {/* AI Provider Selector */}
        <div className="bg-nexus-900 border border-nexus-700 rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Cpu className="w-5 h-5 text-indigo-400" />
              <h2 className="text-sm font-semibold text-nexus-100">AI Model Provider Strategy</h2>
            </div>
            {savedNotice && (
              <span className="text-xs font-mono text-emerald-400 flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" /> Provider updated!
              </span>
            )}
          </div>

          <p className="text-xs text-nexus-400 leading-relaxed">
            NEXUS is engineered to be 100% provider-independent. You can run without Ollama or external models, or connect them when available.
          </p>

          <div className="flex items-center gap-4">
            <select
              value={selectedProvider}
              onChange={(e) => setSelectedProvider(e.target.value)}
              className="bg-nexus-950 border border-nexus-700 rounded-lg px-3 py-2 text-xs text-nexus-100 font-mono focus:outline-none focus:border-cyan-500"
            >
              <option value="mock">Deterministic Mock Provider (Offline Safe)</option>
            </select>
            <button
              onClick={handleProviderSwitch}
              className="px-4 py-2 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-nexus-950 font-semibold text-xs transition-colors shadow-lg shadow-cyan-500/20"
            >
              Set Active Provider
            </button>
          </div>

          <div className="p-3 rounded-lg bg-nexus-950 border border-nexus-800 text-[11px] font-mono text-nexus-400">
            Active Provider: <strong className="text-cyan-400">{data?.active_provider || "mock"}</strong> &bull; Zero external API dependencies required.
          </div>
        </div>

        {/* System Details */}
        <div className="bg-nexus-900 border border-nexus-700 rounded-xl p-5 space-y-3">
          <div className="flex items-center gap-2">
            <Settings className="w-5 h-5 text-emerald-400" />
            <h2 className="text-sm font-semibold text-nexus-100">Core Runtime Properties</h2>
          </div>

          <div className="space-y-2 text-xs font-mono">
            <div className="flex justify-between p-2 rounded bg-nexus-950 border border-nexus-850">
              <span className="text-nexus-500">PROJECT_NAME</span>
              <span className="text-nexus-200">{data?.project_name || "NEXUS AI"}</span>
            </div>
            <div className="flex justify-between p-2 rounded bg-nexus-950 border border-nexus-850">
              <span className="text-nexus-500">ENVIRONMENT</span>
              <span className="text-nexus-200">{data?.environment || "development"}</span>
            </div>
            <div className="flex justify-between p-2 rounded bg-nexus-950 border border-nexus-850">
              <span className="text-nexus-500">LOG_LEVEL</span>
              <span className="text-nexus-200">{data?.log_level || "INFO"}</span>
            </div>
            <div className="flex justify-between p-2 rounded bg-nexus-950 border border-nexus-850">
              <span className="text-nexus-500">STORAGE_DIR</span>
              <span className="text-nexus-200">{data?.storage_directory || "E:\\NEXUS\\storage"}</span>
            </div>
            <div className="flex justify-between p-2 rounded bg-nexus-950 border border-nexus-850">
              <span className="text-nexus-500">DATABASE_MODE</span>
              <span className="text-nexus-200">
                {data?.database.type === "postgresql" ? "PostgreSQL (External)" : "SQLite In-Memory (Zero Config)"}
              </span>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
