"use client";

import { useState } from "react";
import Header from "@/components/Header";
import { Monitor, RefreshCw, Folder, FileCode2, Save, ShieldCheck, Wifi, WifiOff } from "lucide-react";

type Entry = { name: string; type: "file" | "directory"; size?: number };

const COMPANION = "http://127.0.0.1:8765";

export default function CompanionPage() {
  const [token, setToken] = useState("");
  const [connected, setConnected] = useState(false);
  const [workspace, setWorkspace] = useState("");
  const [path, setPath] = useState("");
  const [entries, setEntries] = useState<Entry[]>([]);
  const [selectedFile, setSelectedFile] = useState("");
  const [content, setContent] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const request = async (url: string, init: RequestInit = {}) => {
    if (!token.trim()) throw new Error("Paste the local companion token first.");
    const response = await fetch(url, {
      ...init,
      headers: {
        Authorization: \`Bearer \${token.trim()}\`,
        ...(init.headers || {}),
      },
    });
    const body = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(body.error || body.detail || \`Local companion returned \${response.status}\`);
    return body;
  };

  const connect = async () => {
    setBusy(true); setError(""); setNotice("");
    try {
      const status = await request(\`\${COMPANION}/v1/status\`);
      setWorkspace(status.workspace || "");
      setConnected(true);
      await loadDirectory("");
      setNotice("Connected to the local Windows companion.");
    } catch (err) {
      setConnected(false);
      setError(err instanceof Error ? err.message : "Could not connect to the local companion.");
    } finally { setBusy(false); }
  };

  const loadDirectory = async (nextPath: string) => {
    setBusy(true); setError("");
    try {
      const data = await request(\`\${COMPANION}/v1/files?path=\${encodeURIComponent(nextPath)}\`);
      setPath(nextPath);
      setEntries(data.entries || []);
      setSelectedFile("");
      setContent("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not list this directory.");
    } finally { setBusy(false); }
  };

  const openFile = async (relativePath: string) => {
    setBusy(true); setError("");
    try {
      const data = await request(\`\${COMPANION}/v1/files/read?path=\${encodeURIComponent(relativePath)}\`);
      setSelectedFile(relativePath);
      setContent(data.content || "");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not read this file.");
    } finally { setBusy(false); }
  };

  const saveFile = async () => {
    if (!selectedFile) return;
    if (!window.confirm(\`Save changes to \${selectedFile} on this PC?\`)) return;
    setBusy(true); setError(""); setNotice("");
    try {
      await request(\`\${COMPANION}/v1/files/write\`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-NEXUS-LOCAL-CONFIRM": "true" },
        body: JSON.stringify({ path: selectedFile, content }),
      });
      setNotice("File saved on the connected PC.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save this file.");
    } finally { setBusy(false); }
  };

  const parentPath = path.includes("/") ? path.split("/").slice(0, -1).join("/") : "";

  return (
    <div className="flex-1 flex flex-col bg-nexus-950">
      <Header title="Windows Computer Companion" subtitle="Local workspace access with explicit write confirmation" />
      <main className="p-8 max-w-6xl mx-auto w-full space-y-6">
        <section className="rounded-xl border border-nexus-700 bg-nexus-900 p-5 space-y-4">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <Monitor className="w-5 h-5 text-cyan-400" />
              <div>
                <h2 className="text-sm font-semibold text-nexus-100">Local device connection</h2>
                <p className="text-xs text-nexus-400">Runs only on the PC where this browser and companion are running.</p>
              </div>
            </div>
            <span className={\`text-[10px] px-2 py-1 rounded border \${connected ? "text-emerald-400 border-emerald-800 bg-emerald-950" : "text-nexus-400 border-nexus-700 bg-nexus-950"}\`}>
              {connected ? "CONNECTED" : "DISCONNECTED"}
            </span>
          </div>
          <div className="flex flex-col md:flex-row gap-3">
            <input
              type="password"
              value={token}
              onChange={(e) => setToken(e.target.value)}
              placeholder="Paste token from %LOCALAPPDATA%\\Nexus\\companion.token"
              autoComplete="off"
              className="flex-1 rounded-lg border border-nexus-700 bg-nexus-950 px-3 py-2 text-xs text-nexus-100 font-mono"
            />
            <button onClick={connect} disabled={busy || !token.trim()} className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white text-xs font-semibold flex items-center justify-center gap-2">
              <Wifi className="w-4 h-4" /> Connect
            </button>
          </div>
          {workspace && <p className="text-[11px] text-nexus-500 font-mono break-all">Workspace: {workspace}</p>}
          <p className="text-[11px] text-amber-300">The token is kept only in this page's memory and is not saved to browser storage. Never paste it into a shared or public browser.</p>
        </section>

        {error && <div role="alert" className="rounded-lg border border-rose-800 bg-rose-950/40 p-3 text-xs text-rose-300">{error}</div>}
        {notice && <div role="status" className="rounded-lg border border-emerald-800 bg-emerald-950/30 p-3 text-xs text-emerald-300">{notice}</div>}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          <section className="rounded-xl border border-nexus-700 bg-nexus-900 p-4 space-y-3 min-h-96">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-semibold text-nexus-100 flex items-center gap-2"><Folder className="w-4 h-4 text-cyan-400" /> Workspace files</h3>
              <button onClick={() => loadDirectory(path)} disabled={!connected || busy} className="text-xs text-nexus-400 hover:text-white disabled:opacity-40"><RefreshCw className="w-4 h-4" /></button>
            </div>
            <div className="text-[11px] font-mono text-nexus-500 break-all">/{path || ""}</div>
            {path && <button onClick={() => loadDirectory(parentPath)} disabled={busy} className="text-xs text-cyan-400 hover:underline">.. Up one level</button>}
            <div className="space-y-1">
              {entries.map((entry) => {
                const childPath = path ? \`\${path}/\${entry.name}\` : entry.name;
                return (
                  <button key={childPath} onClick={() => entry.type === "directory" ? loadDirectory(childPath) : openFile(childPath)} disabled={busy} className={\`w-full flex items-center justify-between gap-2 rounded-lg px-3 py-2 text-left text-xs hover:bg-nexus-800 \${selectedFile === childPath ? "bg-nexus-800 text-cyan-300" : "text-nexus-300"}\`}>
                    <span className="flex items-center gap-2 min-w-0">{entry.type === "directory" ? <Folder className="w-4 h-4 shrink-0 text-amber-400" /> : <FileCode2 className="w-4 h-4 shrink-0 text-cyan-400" />}<span className="truncate">{entry.name}</span></span>
                    {entry.type === "file" && <span className="text-[10px] text-nexus-500">{entry.size || 0} B</span>}
                  </button>
                );
              })}
              {connected && entries.length === 0 && <p className="py-6 text-center text-xs text-nexus-500">No permitted files in this directory.</p>}
              {!connected && <p className="py-6 text-center text-xs text-nexus-500">Connect the companion to browse files.</p>}
            </div>
          </section>

          <section className="rounded-xl border border-nexus-700 bg-nexus-900 p-4 space-y-3 min-h-96">
            <div className="flex items-center justify-between gap-2">
              <h3 className="text-xs font-semibold text-nexus-100">Text editor</h3>
              <button onClick={saveFile} disabled={!connected || !selectedFile || busy} className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 text-white text-xs font-semibold flex items-center gap-2"><Save className="w-3.5 h-3.5" /> Save with confirmation</button>
            </div>
            <p className="text-[11px] text-nexus-500 font-mono break-all">{selectedFile || "Select a permitted text file"}</p>
            <textarea value={content} onChange={(e) => setContent(e.target.value)} disabled={!selectedFile || busy} spellCheck={false} className="w-full min-h-80 resize-y rounded-lg border border-nexus-800 bg-nexus-950 p-3 font-mono text-xs text-nexus-200 outline-none focus:border-cyan-700 disabled:opacity-50" placeholder="File content appears here..." />
            <div className="text-[10px] text-nexus-500 flex items-center gap-2"><ShieldCheck className="w-3.5 h-3.5 text-emerald-400" /> Writes are limited to approved text formats, 1 MB, and the configured workspace.</div>
          </section>
        </div>

        <section className="rounded-xl border border-nexus-800 bg-nexus-950 p-4 text-xs text-nexus-400 space-y-1">
          <div className="flex items-center gap-2 text-nexus-200"><WifiOff className="w-4 h-4" /> Current security boundary</div>
          <p>Localhost only. No shell commands, app launching, process control, browser sessions, or Android remote relay. Browser local-network permission may be requested by your browser. Do not expose port 8765 to the internet.</p>
        </section>
      </main>
    </div>
  );
}
