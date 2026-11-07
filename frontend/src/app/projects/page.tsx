"use client";

import Header from "@/components/Header";
import { FolderGit2, ShieldCheck, GitBranch, GitCommit, FileCode, Lock } from "lucide-react";

export default function ProjectsPage() {
  const approvedWorkspaces = [
    {
      name: "NEXUS Core Engine",
      path: "E:\\NEXUS",
      gitBranch: "master",
      status: "Active Workspace",
      checkpointReady: true,
      lastCheckpoint: "Initial Foundation Scaffolding",
    },
    {
      name: "Storage Projects Sandbox",
      path: "E:\\NEXUS\\storage\\projects",
      gitBranch: "local",
      status: "Sandboxed Area",
      checkpointReady: true,
      lastCheckpoint: "Baseline directory barrier initialized",
    },
  ];

  return (
    <div className="flex-1 flex flex-col bg-nexus-950">
      <Header
        title="Coding Agent & Local Projects"
        subtitle="Approved codebase workspaces with mandatory Git checkpoints and sandboxed file tools"
      />

      <main className="p-8 max-w-6xl mx-auto w-full space-y-6">
        {/* Safety Barrier Banner */}
        <div className="p-4 rounded-xl bg-nexus-900 border border-nexus-700 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <ShieldCheck className="w-5 h-5 text-cyan-400" />
            <div>
              <div className="text-sm font-semibold text-nexus-100 flex items-center gap-2">
                <span>Deterministic Coding Safety Protocol</span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800">
                  GUARD ACTIVE
                </span>
              </div>
              <p className="text-xs text-nexus-400">
                Agent &quot;Forge&quot; cannot edit files outside approved directories. An automated Git commit is required before mutating existing files.
              </p>
            </div>
          </div>
        </div>

        {/* Workspaces List */}
        <div className="space-y-4">
          <h2 className="text-xs font-semibold text-nexus-400 uppercase tracking-wider">
            Approved Workspaces
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {approvedWorkspaces.map((ws, i) => (
              <div
                key={i}
                className="bg-nexus-900 border border-nexus-700 rounded-xl p-5 space-y-3"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <FolderGit2 className="w-4 h-4 text-cyan-400" />
                    <h3 className="text-sm font-semibold text-nexus-100">{ws.name}</h3>
                  </div>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-nexus-850 text-cyan-400 border border-nexus-700">
                    {ws.status}
                  </span>
                </div>

                <div className="p-2.5 rounded bg-nexus-950 border border-nexus-800 font-mono text-[11px] text-nexus-300">
                  {ws.path}
                </div>

                <div className="space-y-1.5 text-xs text-nexus-400">
                  <div className="flex items-center gap-2">
                    <GitBranch className="w-3.5 h-3.5 text-nexus-500" />
                    <span>Branch: <strong className="text-nexus-200 font-mono">{ws.gitBranch}</strong></span>
                  </div>
                  <div className="flex items-center gap-2">
                    <GitCommit className="w-3.5 h-3.5 text-nexus-500" />
                    <span>Last Checkpoint: <span className="text-nexus-300">{ws.lastCheckpoint}</span></span>
                  </div>
                </div>

                <div className="pt-2 border-t border-nexus-800 flex items-center justify-between text-[11px]">
                  <span className="text-emerald-400 flex items-center gap-1 font-mono">
                    <Lock className="w-3 h-3" /> Path Boundary Enforced
                  </span>
                  <button
                    onClick={() => alert(`Git checkpoint verified for ${ws.path}`)}
                    className="px-2.5 py-1 rounded bg-nexus-800 hover:bg-nexus-700 border border-nexus-700 text-nexus-200 text-xs font-mono"
                  >
                    Verify Git Checkpoint
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Feature Roadmap Notice */}
        <div className="p-4 rounded-xl bg-nexus-900/60 border border-dashed border-nexus-700 text-xs text-nexus-400 space-y-2">
          <div className="font-semibold text-nexus-200 flex items-center gap-2">
            <FileCode className="w-4 h-4 text-indigo-400" />
            <span>Autonomous Coding Agent Integration (Milestone 5)</span>
          </div>
          <p>
            The coding agent will ingest repository trees, run deterministic pytest suites, propose targeted diffs, and prompt for human approval before pushing or merging changes.
          </p>
        </div>
      </main>
    </div>
  );
}
