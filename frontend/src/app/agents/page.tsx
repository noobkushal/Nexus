"use client";

import { useEffect, useState } from "react";
import Header from "@/components/Header";
import { Bot, Shield, CheckCircle2, AlertTriangle, Key } from "lucide-react";

interface AgentInfo {
  id: string;
  name: string;
  role: string;
  description: string;
  status: string;
  capabilities: { name: string; description: string; requires_approval: boolean }[];
  permissions: string[];
}

export default function AgentsPage() {
  const [agents, setAgents] = useState<AgentInfo[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("http://127.0.0.1:8000/api/v1/agents")
      .then((r) => r.json())
      .then((data) => setAgents(data))
      .catch((err) => console.error("Failed to load agents", err))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="flex-1 flex flex-col bg-nexus-950">
      <Header
        title="Multi-Agent Roster & Security Governance"
        subtitle="Specialized autonomous agents, capability scopes, and permission boundaries"
      />

      <main className="p-8 max-w-7xl mx-auto w-full space-y-6">
        {/* Governance banner */}
        <div className="p-4 rounded-xl bg-nexus-900 border border-nexus-700 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Shield className="w-5 h-5 text-cyan-400" />
            <div>
              <div className="text-sm font-semibold text-nexus-100">Zero Trust Agent Sandbox</div>
              <p className="text-xs text-nexus-400">
                Agents operate with bounded least-privilege permissions. External mutations strictly require human sign-off.
              </p>
            </div>
          </div>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800">
            ENFORCED
          </span>
        </div>

        {/* Agent Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {agents.map((agent) => (
            <div
              key={agent.id}
              className="bg-nexus-900 border border-nexus-700 hover:border-nexus-600 rounded-xl p-5 flex flex-col justify-between transition-all"
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2.5">
                    <div className="w-9 h-9 rounded-lg bg-nexus-800 border border-nexus-700 flex items-center justify-center font-bold text-sm text-cyan-400 font-mono">
                      {agent.name.slice(0, 2).toUpperCase()}
                    </div>
                    <div>
                      <h3 className="text-sm font-semibold text-nexus-100">{agent.name}</h3>
                      <p className="text-[10px] text-cyan-400 font-mono">{agent.role}</p>
                    </div>
                  </div>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-nexus-850 text-emerald-400 border border-nexus-700">
                    {agent.status.toUpperCase()}
                  </span>
                </div>

                <p className="text-xs text-nexus-300 leading-relaxed mb-4">
                  {agent.description}
                </p>

                {/* Capabilities */}
                <div className="space-y-1.5 mb-4">
                  <div className="text-[10px] font-semibold text-nexus-500 uppercase tracking-wider">
                    Declared Capabilities
                  </div>
                  {agent.capabilities.map((cap, i) => (
                    <div
                      key={i}
                      className="p-2 rounded-md bg-nexus-850 border border-nexus-800 flex items-center justify-between text-[11px]"
                    >
                      <span className="text-nexus-200">{cap.name}</span>
                      {cap.requires_approval ? (
                        <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-amber-950 text-amber-400 border border-amber-900 flex items-center gap-1">
                          <AlertTriangle className="w-2.5 h-2.5" />
                          Needs Approval
                        </span>
                      ) : (
                        <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-nexus-800 text-nexus-400">
                          Autonomous
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Permissions */}
              <div className="pt-3 border-t border-nexus-800">
                <div className="text-[10px] font-semibold text-nexus-500 uppercase tracking-wider mb-2 flex items-center gap-1">
                  <Key className="w-3 h-3" />
                  Active Permissions
                </div>
                <div className="flex flex-wrap gap-1">
                  {agent.permissions.map((perm, idx) => (
                    <span
                      key={idx}
                      className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-nexus-950 text-nexus-400 border border-nexus-800"
                    >
                      {perm}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
