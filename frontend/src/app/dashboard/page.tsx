"use client";

import { useEffect, useState } from "react";
import Header from "@/components/Header";
import Link from "next/link";
import {
  Activity,
  AlertTriangle,
  Bot,
  CheckCircle2,
  CheckSquare,
  Clock,
  Cpu,
  Database,
  Layers,
  MessageSquare,
  Play,
  ShieldCheck,
  XCircle,
  Zap,
} from "lucide-react";

interface SystemHealth {
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
  automation: {
    n8n_connected: boolean;
    mode: string;
  };
}

interface AgentItem {
  id: string;
  name: string;
  role: string;
  status: string;
  capabilities: { name: string }[];
}

interface TaskItem {
  id: string;
  title: string;
  status: string;
  priority: string;
  assigned_agent?: string;
}

interface ActivityItem {
  timestamp: string;
  agent_id: string;
  action: string;
  details: string;
  status: string;
}

interface ApprovalItem {
  id: string;
  agent_id: string;
  action_type: string;
  title: string;
  description: string;
  status: string;
}

export default function DashboardPage() {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [agents, setAgents] = useState<AgentItem[]>([]);
  const [tasks, setTasks] = useState<TaskItem[]>([]);
  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const [approvals, setApprovals] = useState<ApprovalItem[]>([]);
  const [loading, setLoading] = useState(true);

  const loadAll = async () => {
    try {
      const [hRes, aRes, tRes, actRes, appRes] = await Promise.all([
        fetch("http://127.0.0.1:8000/api/v1/health"),
        fetch("http://127.0.0.1:8000/api/v1/agents"),
        fetch("http://127.0.0.1:8000/api/v1/tasks"),
        fetch("http://127.0.0.1:8000/api/v1/agents/activities"),
        fetch("http://127.0.0.1:8000/api/v1/approvals?status=pending"),
      ]);

      if (hRes.ok) setHealth(await hRes.json());
      if (aRes.ok) setAgents(await aRes.json());
      if (tRes.ok) {
        const tData = await tRes.json();
        setTasks(tData.tasks || []);
      }
      if (actRes.ok) setActivities(await actRes.json());
      if (appRes.ok) setApprovals(await appRes.json());
    } catch (err) {
      console.error("Dashboard data load error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAll();
  }, []);

  const handleDecision = async (id: string, decision: "approved" | "rejected") => {
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/v1/approvals/${id}/decision`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ decision }),
      });
      if (res.ok) {
        loadAll();
      }
    } catch (err) {
      console.error("Failed to submit decision", err);
    }
  };

  return (
    <div className="flex-1 flex flex-col bg-nexus-950">
      <Header
        title="Mission Control Dashboard"
        subtitle="Autonomous local-first operations and multi-agent system state"
      />

      <main className="p-8 space-y-6 max-w-7xl mx-auto w-full">
        {/* Foundation Notice Banner */}
        <div className="bg-nexus-900 border border-nexus-700/80 rounded-xl p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-cyan-950 text-cyan-400 border border-cyan-800">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <div className="text-sm font-semibold text-nexus-100 flex items-center gap-2">
                <span>NEXUS Foundation Milestone Active</span>
                <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800">
                  Offline-Ready
                </span>
              </div>
              <p className="text-xs text-nexus-400">
                Running in deterministic mode without external dependencies. No Ollama, PostgreSQL, or n8n required.
              </p>
            </div>
          </div>
          <Link
            href="/chat"
            className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-nexus-950 font-semibold text-xs transition-colors shadow-lg shadow-cyan-500/20"
          >
            <MessageSquare className="w-3.5 h-3.5" />
            Test Chat
          </Link>
        </div>

        {/* Top Status Metric Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Card 1: Core System */}
          <div className="bg-nexus-900 border border-nexus-700 rounded-xl p-4 flex flex-col justify-between">
            <div className="flex items-center justify-between text-xs text-nexus-400 mb-2">
              <span className="flex items-center gap-1.5 font-medium">
                <Cpu className="w-3.5 h-3.5 text-cyan-400" />
                Backend Service
              </span>
              <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950 px-1.5 py-0.5 rounded border border-emerald-900">
                {health?.status || "ONLINE"}
              </span>
            </div>
            <div className="text-xl font-bold text-nexus-100">FastAPI Core</div>
            <div className="text-[11px] text-nexus-500 mt-1">Host: 127.0.0.1:8000 (Async)</div>
          </div>

          {/* Card 2: AI Provider */}
          <div className="bg-nexus-900 border border-nexus-700 rounded-xl p-4 flex flex-col justify-between">
            <div className="flex items-center justify-between text-xs text-nexus-400 mb-2">
              <span className="flex items-center gap-1.5 font-medium">
                <Bot className="w-3.5 h-3.5 text-indigo-400" />
                AI Inference Engine
              </span>
              <span className="text-[10px] font-mono text-cyan-400 bg-cyan-950 px-1.5 py-0.5 rounded border border-cyan-900">
                {health?.ai_provider?.name.toUpperCase() || "MOCK"}
              </span>
            </div>
            <div className="text-xl font-bold text-nexus-100">Deterministic Mock</div>
            <div className="text-[11px] text-nexus-500 mt-1">Zero GPU/RAM model overhead</div>
          </div>

          {/* Card 3: Storage & DB */}
          <div className="bg-nexus-900 border border-nexus-700 rounded-xl p-4 flex flex-col justify-between">
            <div className="flex items-center justify-between text-xs text-nexus-400 mb-2">
              <span className="flex items-center gap-1.5 font-medium">
                <Database className="w-3.5 h-3.5 text-emerald-400" />
                Persistence Layer
              </span>
              <span className="text-[10px] font-mono text-nexus-300 bg-nexus-800 px-1.5 py-0.5 rounded border border-nexus-700">
                STANDALONE
              </span>
            </div>
            <div className="text-xl font-bold text-nexus-100">SQLite In-Memory</div>
            <div className="text-[11px] text-nexus-500 mt-1">Postgres optional fallback</div>
          </div>

          {/* Card 4: Automations */}
          <div className="bg-nexus-900 border border-nexus-700 rounded-xl p-4 flex flex-col justify-between">
            <div className="flex items-center justify-between text-xs text-nexus-400 mb-2">
              <span className="flex items-center gap-1.5 font-medium">
                <Layers className="w-3.5 h-3.5 text-amber-400" />
                Workflow Orchestrator
              </span>
              <span className="text-[10px] font-mono text-amber-400 bg-amber-950 px-1.5 py-0.5 rounded border border-amber-900">
                MOCK / READY
              </span>
            </div>
            <div className="text-xl font-bold text-nexus-100">n8n Bridge</div>
            <div className="text-[11px] text-nexus-500 mt-1">Simulated webhook dispatcher</div>
          </div>
        </div>

        {/* Action Approval Gate (Human in the loop) */}
        {approvals.length > 0 && (
          <div className="bg-nexus-900 border border-amber-800/80 rounded-xl p-5 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-400" />
                <h2 className="text-sm font-semibold text-nexus-100">
                  Human Approval Gate ({approvals.length} Actions Awaiting Review)
                </h2>
              </div>
              <span className="text-[10px] font-mono text-amber-400 bg-amber-950 px-2 py-0.5 rounded border border-amber-900">
                BARRIER ACTIVE
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {approvals.map((appr) => (
                <div
                  key={appr.id}
                  className="p-3 rounded-lg bg-nexus-950 border border-nexus-800 flex flex-col justify-between space-y-2"
                >
                  <div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-semibold text-nexus-200">{appr.title}</span>
                      <span className="text-[10px] font-mono text-nexus-400 uppercase">
                        {appr.agent_id}
                      </span>
                    </div>
                    <p className="text-[11px] text-nexus-400 mt-1">{appr.description}</p>
                  </div>
                  <div className="flex justify-end gap-2 pt-2 border-t border-nexus-850">
                    <button
                      onClick={() => handleDecision(appr.id, "rejected")}
                      className="flex items-center gap-1 px-2.5 py-1 rounded border border-nexus-700 hover:bg-red-950/40 text-[11px] text-red-400 transition-colors"
                    >
                      <XCircle className="w-3 h-3" /> Reject
                    </button>
                    <button
                      onClick={() => handleDecision(appr.id, "approved")}
                      className="flex items-center gap-1 px-3 py-1 rounded bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-[11px] transition-colors"
                    >
                      <CheckCircle2 className="w-3 h-3" /> Approve
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Middle Section: Registered Agents & Quick Actions */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Registered Agents List */}
          <div className="lg:col-span-2 bg-nexus-900 border border-nexus-700 rounded-xl p-5">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Bot className="w-4 h-4 text-cyan-400" />
                <h2 className="text-sm font-semibold text-nexus-100">Registered Multi-Agent Roster</h2>
              </div>
              <Link href="/agents" className="text-xs text-cyan-400 hover:text-cyan-300 font-mono">
                View All ({agents.length}) &rarr;
              </Link>
            </div>

            <div className="space-y-3">
              {agents.map((agent) => (
                <div
                  key={agent.id}
                  className="bg-nexus-850 border border-nexus-750 p-3 rounded-lg flex items-center justify-between hover:border-nexus-600 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-nexus-800 border border-nexus-700 flex items-center justify-center font-bold text-xs text-cyan-400 font-mono">
                      {agent.name.slice(0, 2).toUpperCase()}
                    </div>
                    <div>
                      <div className="text-xs font-semibold text-nexus-100 flex items-center gap-2">
                        <span>{agent.name}</span>
                        <span className="text-[10px] text-nexus-400 font-mono">({agent.role})</span>
                      </div>
                      <div className="text-[11px] text-nexus-400 mt-0.5">
                        {agent.capabilities.map((c) => c.name).join(" • ")}
                      </div>
                    </div>
                  </div>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-nexus-800 text-nexus-300 border border-nexus-700">
                    {agent.status.toUpperCase()}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Quick Actions Panel */}
          <div className="bg-nexus-900 border border-nexus-700 rounded-xl p-5 flex flex-col justify-between">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <Zap className="w-4 h-4 text-amber-400" />
                <h2 className="text-sm font-semibold text-nexus-100">Foundation Quick Actions</h2>
              </div>
              <p className="text-xs text-nexus-400 mb-4">
                Execute core platform commands and launch test flows directly.
              </p>

              <div className="space-y-2">
                <Link
                  href="/chat"
                  className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg bg-nexus-800 hover:bg-nexus-700 border border-nexus-650 text-xs font-medium text-nexus-200 transition-colors"
                >
                  <MessageSquare className="w-4 h-4 text-cyan-400" />
                  <span>Start Chat Session</span>
                </Link>

                <Link
                  href="/tasks"
                  className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg bg-nexus-800 hover:bg-nexus-700 border border-nexus-650 text-xs font-medium text-nexus-200 transition-colors"
                >
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  <span>Create & Manage Tasks</span>
                </Link>

                <Link
                  href="/workflows"
                  className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg bg-nexus-800 hover:bg-nexus-700 border border-nexus-650 text-xs font-medium text-nexus-200 transition-colors"
                >
                  <Play className="w-4 h-4 text-indigo-400" />
                  <span>Trigger Morning Briefing (n8n Sim)</span>
                </Link>

                <Link
                  href="/settings"
                  className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg bg-nexus-800 hover:bg-nexus-700 border border-nexus-650 text-xs font-medium text-nexus-200 transition-colors"
                >
                  <Cpu className="w-4 h-4 text-nexus-400" />
                  <span>Inspect System Settings</span>
                </Link>
              </div>
            </div>

            <div className="mt-6 pt-4 border-t border-nexus-800 text-[11px] text-nexus-500 font-mono flex items-center justify-between">
              <span>Security Barrier</span>
              <span className="text-emerald-400">ENFORCED</span>
            </div>
          </div>
        </div>

        {/* Bottom Section: Active Tasks & Recent Agent Audit Logs */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Active Tasks */}
          <div className="bg-nexus-900 border border-nexus-700 rounded-xl p-5">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <CheckSquare className="w-4 h-4 text-emerald-400" />
                <h2 className="text-sm font-semibold text-nexus-100">Current Work Items ({tasks.length})</h2>
              </div>
              <Link href="/tasks" className="text-xs text-cyan-400 hover:text-cyan-300 font-mono">
                Manage &rarr;
              </Link>
            </div>

            <div className="space-y-2">
              {tasks.slice(0, 4).map((task) => (
                <div
                  key={task.id}
                  className="p-3 rounded-lg bg-nexus-850 border border-nexus-800 flex items-center justify-between text-xs"
                >
                  <div className="flex items-center gap-2.5">
                    <span
                      className={`w-2 h-2 rounded-full ${
                        task.status === "completed"
                          ? "bg-emerald-400"
                          : task.status === "in_progress"
                          ? "bg-cyan-400"
                          : "bg-amber-400"
                      }`}
                    />
                    <span className="font-medium text-nexus-200">{task.title}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-mono text-nexus-400 uppercase">
                      {task.priority}
                    </span>
                    <span
                      className={`text-[10px] font-mono px-2 py-0.5 rounded border ${
                        task.status === "completed"
                          ? "bg-emerald-950 text-emerald-400 border-emerald-800"
                          : task.status === "in_progress"
                          ? "bg-cyan-950 text-cyan-400 border-cyan-800"
                          : "bg-nexus-800 text-nexus-300 border-nexus-700"
                      }`}
                    >
                      {task.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Recent Activity Log */}
          <div className="bg-nexus-900 border border-nexus-700 rounded-xl p-5">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Activity className="w-4 h-4 text-cyan-400" />
                <h2 className="text-sm font-semibold text-nexus-100">Audit & Agent Activity Trail</h2>
              </div>
              <span className="text-[10px] font-mono text-nexus-500">LIVE FEED</span>
            </div>

            <div className="space-y-2.5 font-mono text-xs">
              {activities.slice(0, 4).map((act, i) => (
                <div
                  key={i}
                  className="p-2.5 rounded-lg bg-nexus-850/80 border border-nexus-800/80 flex items-start gap-3 text-[11px]"
                >
                  <div className="text-nexus-500 shrink-0">
                    {new Date(act.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                  </div>
                  <div className="flex-1">
                    <div className="text-nexus-200 flex items-center gap-2">
                      <span className="text-cyan-400 font-semibold">{act.agent_id}</span>
                      <span>&bull;</span>
                      <span>{act.action}</span>
                    </div>
                    <div className="text-nexus-400 text-[10px] mt-0.5">{act.details}</div>
                  </div>
                  <span className="text-[9px] px-1.5 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-900">
                    {act.status}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
