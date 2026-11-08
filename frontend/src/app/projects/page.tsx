"use client";

import { apiFetch } from "@/lib/api-client";

import { useEffect, useState } from "react";
import Header from "@/components/Header";
import {
  FolderGit2,
  ShieldCheck,
  GitBranch,
  GitCommit,
  FileCode,
  Lock,
  Plus,
  RefreshCw,
  FileText,
  Eye,
  CheckCircle2,
} from "lucide-react";

interface GitStatus {
  is_git_repo: boolean;
  repo_path: string;
  current_branch: string;
  latest_commit: string;
  last_commit_message: string;
  clean_working_tree: boolean;
  uncommitted_changes_count: number;
  uncommitted_files: string[];
}

interface GitCheckpoint {
  hash: string;
  author: string;
  date: string;
  message: string;
}

interface StorageFile {
  path: string;
  name: string;
  size_bytes: number;
  extension: string;
  modified_at: string;
}

export default function ProjectsPage() {
  const [gitStatus, setGitStatus] = useState<GitStatus | null>(null);
  const [checkpoints, setCheckpoints] = useState<GitCheckpoint[]>([]);
  const [files, setFiles] = useState<StorageFile[]>([]);
  const [selectedCompartment, setSelectedCompartment] = useState<string>("documents");
  const [loading, setLoading] = useState(true);
  const [previewContent, setPreviewContent] = useState<{ path: string; text: string } | null>(null);
  const [checkpointDesc, setCheckpointDesc] = useState("");
  const [checkpointLoading, setCheckpointLoading] = useState(false);
  const [checkpointNotice, setCheckpointNotice] = useState<string | null>(null);

  const loadAll = async () => {
    try {
      setLoading(true);
      const [gRes, cRes, fRes] = await Promise.all([
        apiFetch("http://127.0.0.1:8000/api/v1/storage/git/status"),
        apiFetch("http://127.0.0.1:8000/api/v1/storage/git/checkpoints?limit=5"),
        apiFetch(`http://127.0.0.1:8000/api/v1/storage/files?compartment=${selectedCompartment}`),
      ]);
      if (gRes.ok) setGitStatus(await gRes.json());
      if (cRes.ok) setCheckpoints(await cRes.json());
      if (fRes.ok) setFiles(await fRes.json());
    } catch (err) {
      console.error("Failed to load project state", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAll();
  }, [selectedCompartment]);

  const handleCreateCheckpoint = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!checkpointDesc.trim()) return;

    try {
      setCheckpointLoading(true);
      const res = await apiFetch("http://127.0.0.1:8000/api/v1/storage/git/checkpoint", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          description: checkpointDesc,
          author_agent: "coding_agent",
        }),
      });

      if (res.ok) {
        setCheckpointDesc("");
        setCheckpointNotice("Safety checkpoint created successfully!");
        setTimeout(() => setCheckpointNotice(null), 3500);
        await loadAll();
      }
    } catch (err: any) {
      alert(`Checkpoint creation failed: ${err.message}`);
    } finally {
      setCheckpointLoading(false);
    }
  };

  const handlePreviewFile = async (filePath: string) => {
    try {
      const res = await apiFetch(`http://127.0.0.1:8000/api/v1/storage/read?path=${encodeURIComponent(filePath)}`);
      if (res.ok) {
        const data = await res.json();
        setPreviewContent({ path: filePath, text: data.content });
      }
    } catch (err) {
      console.error("Preview failed", err);
    }
  };

  const compartments = ["documents", "profile", "projects", "generated"];

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
                Agent &quot;Forge&quot; cannot modify files outside approved directories. An automated Git commit is required before mutating existing files.
              </p>
            </div>
          </div>
          <button
            onClick={loadAll}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-nexus-700 text-xs text-nexus-300 hover:bg-nexus-800"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>

        {/* Live Git Workspace Status */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="md:col-span-2 bg-nexus-900 border border-nexus-700 rounded-xl p-5 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <FolderGit2 className="w-4 h-4 text-cyan-400" />
                <h2 className="text-sm font-semibold text-nexus-100">Live Workspace Status</h2>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-nexus-800 text-nexus-300 border border-nexus-700">
                BRANCH: {gitStatus?.current_branch || "master"}
              </span>
            </div>

            <div className="p-3 rounded-lg bg-nexus-950 border border-nexus-800 font-mono text-xs space-y-2">
              <div className="flex justify-between text-nexus-400">
                <span>Repository Root:</span>
                <span className="text-nexus-200">{gitStatus?.repo_path || "E:\\NEXUS"}</span>
              </div>
              <div className="flex justify-between text-nexus-400">
                <span>Latest Checkpoint Hash:</span>
                <span className="text-cyan-400 font-bold">{gitStatus?.latest_commit || "HEAD"}</span>
              </div>
              <div className="flex justify-between text-nexus-400">
                <span>Working Tree:</span>
                <span className={gitStatus?.clean_working_tree ? "text-emerald-400" : "text-amber-400 font-bold"}>
                  {gitStatus?.clean_working_tree ? "CLEAN" : `${gitStatus?.uncommitted_changes_count} Uncommitted Change(s)`}
                </span>
              </div>
              <div className="pt-2 border-t border-nexus-850 text-nexus-300 text-[11px]">
                Last Commit: &ldquo;{gitStatus?.last_commit_message}&rdquo;
              </div>
            </div>

            {/* Create Checkpoint Form */}
            <form onSubmit={handleCreateCheckpoint} className="space-y-2 pt-2 border-t border-nexus-800">
              <div className="flex items-center justify-between">
                <label className="text-xs font-semibold text-nexus-200">
                  Trigger Manual Git Safety Checkpoint
                </label>
                {checkpointNotice && (
                  <span className="text-[11px] font-mono text-emerald-400 flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5" /> {checkpointNotice}
                  </span>
                )}
              </div>
              <div className="flex gap-2">
                <input
                  type="text"
                  required
                  value={checkpointDesc}
                  onChange={(e) => setCheckpointDesc(e.target.value)}
                  placeholder="e.g. Pre-flight snapshot before refactoring router..."
                  className="flex-1 bg-nexus-950 border border-nexus-700 rounded-lg px-3 py-2 text-xs text-nexus-100 placeholder-nexus-500 focus:outline-none focus:border-cyan-500"
                />
                <button
                  type="submit"
                  disabled={checkpointLoading || !checkpointDesc.trim()}
                  className="px-3.5 py-2 rounded-lg bg-cyan-500 hover:bg-cyan-400 disabled:opacity-50 text-nexus-950 font-semibold text-xs transition-colors shrink-0 shadow-md shadow-cyan-500/20"
                >
                  {checkpointLoading ? "Committing..." : "Commit Checkpoint"}
                </button>
              </div>
            </form>
          </div>

          {/* Recent Git Checkpoints */}
          <div className="bg-nexus-900 border border-nexus-700 rounded-xl p-5 space-y-3 flex flex-col justify-between">
            <div>
              <div className="flex items-center gap-2 mb-3">
                <GitCommit className="w-4 h-4 text-indigo-400" />
                <h2 className="text-sm font-semibold text-nexus-100">Recent Checkpoints</h2>
              </div>
              <div className="space-y-2 font-mono text-xs">
                {checkpoints.map((cp) => (
                  <div key={cp.hash} className="p-2.5 rounded-lg bg-nexus-950 border border-nexus-850 space-y-1">
                    <div className="flex items-center justify-between text-[10px]">
                      <span className="text-cyan-400 font-bold">{cp.hash}</span>
                      <span className="text-nexus-500">{cp.date}</span>
                    </div>
                    <div className="text-[11px] text-nexus-200 line-clamp-1">{cp.message}</div>
                  </div>
                ))}
              </div>
            </div>

            <div className="pt-2 text-[10px] text-nexus-500 font-mono flex items-center justify-between">
              <span>Automated Rollback Barrier</span>
              <span className="text-emerald-400">ARMED</span>
            </div>
          </div>
        </div>

        {/* Sandboxed Storage Explorer */}
        <div className="bg-nexus-900 border border-nexus-700 rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <FileCode className="w-4 h-4 text-emerald-400" />
              <h2 className="text-sm font-semibold text-nexus-100">Approved Storage Compartment Browser</h2>
            </div>
            <span className="text-[10px] font-mono text-nexus-500">SANDBOX ROOT: E:\NEXUS\storage</span>
          </div>

          {/* Compartment Tabs */}
          <div className="flex gap-2">
            {compartments.map((comp) => (
              <button
                key={comp}
                onClick={() => setSelectedCompartment(comp)}
                className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-colors ${
                  selectedCompartment === comp
                    ? "bg-nexus-700 text-nexus-100 border border-nexus-500 font-semibold"
                    : "bg-nexus-950 text-nexus-400 hover:text-nexus-200 border border-nexus-800"
                }`}
              >
                /{comp}
              </button>
            ))}
          </div>

          {/* Files List */}
          <div className="space-y-2">
            {files.length === 0 ? (
              <div className="p-4 rounded-lg bg-nexus-950 border border-nexus-850 text-center text-xs text-nexus-500">
                No files in compartment &quot;/{selectedCompartment}&quot; yet.
              </div>
            ) : (
              files.map((file) => (
                <div
                  key={file.path}
                  className="p-3 rounded-lg bg-nexus-950 border border-nexus-800 flex items-center justify-between text-xs hover:border-nexus-700 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <FileText className="w-4 h-4 text-cyan-400 shrink-0" />
                    <div>
                      <div className="font-mono font-medium text-nexus-200">{file.name}</div>
                      <div className="text-[10px] text-nexus-500 font-mono">
                        {file.path} &bull; {(file.size_bytes / 1024).toFixed(1)} KB
                      </div>
                    </div>
                  </div>

                  <button
                    onClick={() => handlePreviewFile(file.path)}
                    className="flex items-center gap-1 px-2.5 py-1 rounded bg-nexus-850 hover:bg-nexus-800 border border-nexus-700 text-[11px] text-nexus-300 font-mono transition-colors"
                  >
                    <Eye className="w-3.5 h-3.5 text-indigo-400" /> Preview
                  </button>
                </div>
              ))
            )}
          </div>

          {/* File Preview Drawer */}
          {previewContent && (
            <div className="mt-4 p-4 rounded-xl bg-nexus-950 border border-cyan-900/60 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono font-bold text-cyan-400">{previewContent.path}</span>
                <button
                  onClick={() => setPreviewContent(null)}
                  className="text-xs text-nexus-500 hover:text-nexus-300 font-mono"
                >
                  Close &times;
                </button>
              </div>
              <pre className="p-3 rounded-lg bg-nexus-900 border border-nexus-800 text-[11px] font-mono text-nexus-200 overflow-x-auto whitespace-pre-wrap max-h-60">
                {previewContent.text}
              </pre>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
