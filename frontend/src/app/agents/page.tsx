"use client";

import { apiFetch } from "@/lib/api-client";

import { useEffect, useState } from "react";
import Header from "@/components/Header";
import { Bot, Shield, CheckCircle2, AlertTriangle, Key, Cpu, Sparkles, Lock } from "lucide-react";

interface AgentInfo {
  id: string;
  name: string;
  role: string;
  description: string;
  status: string;
  capabilities: { name: string; description: string; requires_approval: boolean }[];
  permissions: string[];
}

interface SkillInfo {
  id: string;
  name: string;
  description: string;
  required_permission: string;
  is_consequential: boolean;
  authorized_agents: string[];
}

export default function AgentsPage() {
  const [agents, setAgents] = useState<AgentInfo[]>([]);
  const [skills, setSkills] = useState<SkillInfo[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      apiFetch("http://127.0.0.1:8000/api/v1/agents").then((r) => r.json()),
      apiFetch("http://127.0.0.1:8000/api/v1/skills").then((r) => r.json()),
    ])
      .then(([agentsData, skillsData]) => {
        if (Array.isArray(agentsData)) setAgents(agentsData);
        if (Array.isArray(skillsData)) setSkills(skillsData);
      })
      .catch((err) => console.error("Failed to load agents or skills", err))
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
                  <Key className="w-3 h-3 text-cyan-400" />
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

        {/* Skills & Integrations Matrix */}
        {skills.length > 0 && (
          <div className="bg-nexus-900 border border-nexus-700 rounded-xl p-6 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <Cpu className="w-4 h-4 text-cyan-400" />
                <h2 className="text-sm font-semibold text-nexus-100">
                  Skills &amp; Integrations Registry ({skills.length} Registered)
                </h2>
              </div>
              <span className="text-[10px] font-mono text-cyan-400 bg-cyan-950 px-2 py-0.5 rounded border border-cyan-900">
                LEAST PRIVILEGE MATRIX
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {skills.map((skill) => (
                <div
                  key={skill.id}
                  className="p-3.5 rounded-lg bg-nexus-950/80 border border-nexus-800 flex flex-col justify-between space-y-3"
                >
                  <div>
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-xs text-nexus-200">{skill.name}</span>
                      {skill.is_consequential ? (
                        <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-amber-950 text-amber-400 border border-amber-900 flex items-center gap-1">
                          <Lock className="w-2.5 h-2.5" /> Gated
                        </span>
                      ) : (
                        <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-900">
                          Safe
                        </span>
                      )}
                    </div>
                    <p className="text-[11px] text-nexus-400 mt-1 leading-relaxed">{skill.description}</p>
                  </div>

                  <div className="pt-2 border-t border-nexus-850 space-y-1.5 text-[10px]">
                    <div className="flex items-center justify-between text-nexus-500 font-mono">
                      <span>Required Permission:</span>
                      <span className="text-cyan-400">{skill.required_permission}</span>
                    </div>
                    <div className="flex items-center justify-between text-nexus-500 font-mono">
                      <span>Authorized Agents:</span>
                      <span className="text-nexus-300">{skill.authorized_agents.join(", ")}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
