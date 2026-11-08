"use client";

import { apiFetch } from "@/lib/api-client";

import { useEffect, useState } from "react";
import Header from "@/components/Header";
import { Workflow, Play, CheckCircle2, AlertCircle, RefreshCw, ExternalLink } from "lucide-react";

interface WorkflowItem {
  id: string;
  name: string;
  description: string;
  trigger_type: string;
  webhook_path: string;
  status: string;
}

interface ExecutionItem {
  execution_id: string;
  workflow_id: string;
  status: string;
  triggered_at: string;
  result?: { message: string; note: string; target_webhook: string };
}

export default function WorkflowsPage() {
  const [workflows, setWorkflows] = useState<WorkflowItem[]>([]);
  const [executions, setExecutions] = useState<ExecutionItem[]>([]);
  const [triggering, setTriggering] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const loadData = async () => {
    try {
      const [wRes, eRes] = await Promise.all([
        apiFetch("http://127.0.0.1:8000/api/v1/workflows"),
        apiFetch("http://127.0.0.1:8000/api/v1/workflows/executions"),
      ]);
      if (wRes.ok) setWorkflows(await wRes.json());
      if (eRes.ok) setExecutions(await eRes.json());
    } catch (err) {
      console.error("Failed to load workflows", err);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const triggerWorkflow = async (workflowId: string) => {
    try {
      setTriggering(workflowId);
      setActionError(null);
      const res = await apiFetch(`http://127.0.0.1:8000/api/v1/workflows/${workflowId}/trigger`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ payload: { source: "frontend_dashboard" } }),
      });
      if (res.ok) {
        await loadData();
      } else {
        const detail = await res.json().catch(() => ({}));
        setActionError(detail.detail || `Workflow dispatch failed (${res.status}). Configure n8n and check its webhook.`);
      }
    } catch (err) {
      console.error("Failed to trigger workflow", err);
    } finally {
      setTriggering(null);
    }
  };

  return (
    <div className="flex-1 flex flex-col bg-nexus-950">
      <Header
        title="Workflow Automation & n8n Bridge"
        subtitle="Event dispatchers, webhook pipelines, and external integrations"
      />

      <main className="p-8 max-w-6xl mx-auto w-full space-y-6">
        <div className="p-4 rounded-xl bg-nexus-900 border border-nexus-700 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Workflow className="w-5 h-5 text-indigo-400" />
            <div>
              <div className="text-sm font-semibold text-nexus-100 flex items-center gap-2">
                <span>n8n Integration Architecture</span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-nexus-800 text-nexus-300 border border-nexus-700">
                  LIVE WEBHOOK
                </span>
              </div>
              <p className="text-xs text-nexus-400">
                Dispatches real webhook requests to your configured n8n instance. No simulated success.
              </p>
            </div>
          </div>
          <button
            onClick={loadData}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-nexus-700 text-xs text-nexus-300 hover:bg-nexus-800"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Refresh
          </button>
        </div>

        {actionError && <div role="alert" className="p-3 rounded-lg border border-rose-800 bg-rose-950/40 text-xs text-rose-300">{actionError}</div>}

        {/* Workflow Catalog */}
        <div className="space-y-4">
          <h2 className="text-xs font-semibold text-nexus-400 uppercase tracking-wider">
            Registered Pipeline Catalog
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {workflows.map((wf) => (
              <div
                key={wf.id}
                className="bg-nexus-900 border border-nexus-700 rounded-xl p-5 flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-950 text-indigo-400 border border-indigo-900 uppercase">
                      {wf.trigger_type}
                    </span>
                    <span className="text-[10px] font-mono text-emerald-400">{wf.status.toUpperCase()}</span>
                  </div>
                  <h3 className="text-sm font-semibold text-nexus-100 mb-1">{wf.name}</h3>
                  <p className="text-xs text-nexus-400 leading-relaxed mb-3">{wf.description}</p>
                  <div className="text-[10px] font-mono text-nexus-500 bg-nexus-950 p-2 rounded border border-nexus-800 break-all mb-4">
                    {wf.webhook_path}
                  </div>
                </div>

                <button
                  onClick={() => triggerWorkflow(wf.id)}
                  disabled={triggering === wf.id}
                  className="w-full flex items-center justify-center gap-2 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-semibold text-xs transition-colors shadow-md shadow-indigo-600/20"
                >
                  <Play className={`w-3.5 h-3.5 ${triggering === wf.id ? "animate-spin" : ""}`} />
                  {triggering === wf.id ? "Triggering..." : "Trigger Workflow"}
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Execution Log */}
        <div className="bg-nexus-900 border border-nexus-700 rounded-xl p-5 space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-semibold text-nexus-100 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              Pipeline Execution History
            </h2>
            <span className="text-[10px] font-mono text-nexus-500">{executions.length} runs</span>
          </div>

          {executions.length === 0 ? (
            <p className="text-xs text-nexus-500 py-4 text-center">
              No executions yet. Click &quot;Simulate Trigger&quot; above to run a workflow.
            </p>
          ) : (
            <div className="space-y-2 font-mono text-xs">
              {executions.map((exec) => (
                <div
                  key={exec.execution_id}
                  className="p-3 rounded-lg bg-nexus-850 border border-nexus-800 text-[11px] space-y-1"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 text-nexus-200">
                      <span className="text-cyan-400 font-bold">{exec.workflow_id}</span>
                      <span className="text-nexus-500">#{exec.execution_id}</span>
                    </div>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-900 uppercase">
                      {exec.status}
                    </span>
                  </div>
                  {exec.result && (
                    <div className="text-[10px] text-nexus-400 pt-1">
                      <div>&bull; {exec.result.message}</div>
                      <div className="text-nexus-500">&bull; {exec.result.note}</div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
