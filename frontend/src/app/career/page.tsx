"use client";

import { useState } from "react";
import Header from "@/components/Header";
import { Briefcase, FileText, Send, CheckCircle2, XCircle, AlertTriangle, UserCheck } from "lucide-react";

interface OutreachDraft {
  id: string;
  recipient: string;
  company: string;
  role: string;
  message: string;
  status: "pending_review" | "approved" | "rejected";
}

export default function CareerPage() {
  const [drafts, setDrafts] = useState<OutreachDraft[]>([
    {
      id: "out-101",
      recipient: "Sarah Jenkins",
      company: "Apex Tech Labs",
      role: "Lead Platform Architect",
      message:
        "Hi Sarah, I noticed your team is scaling distributed automation infrastructure. " +
        "I recently engineered NEXUS AI, a local-first autonomous orchestrator built with FastAPI and Next.js. " +
        "Would love to connect and share notes on safe agent architecture.",
      status: "pending_review",
    },
    {
      id: "out-102",
      recipient: "Marcus Chen",
      company: "Vector Systems",
      role: "Senior Engineering Manager",
      message:
        "Hi Marcus, I came across your work on deterministic LLM safety barriers. " +
        "My recent project implements bounded filesystem tools and human-in-the-loop validation. " +
        "Would value exchanging insights.",
      status: "pending_review",
    },
  ]);

  const handleReview = (id: string, newStatus: "approved" | "rejected") => {
    setDrafts((prev) =>
      prev.map((d) => (d.id === id ? { ...d, status: newStatus } : d))
    );
  };

  return (
    <div className="flex-1 flex flex-col bg-nexus-950">
      <Header
        title="Career Intelligence & Professional Outreach"
        subtitle="Resume tailoring and human-reviewed LinkedIn connection messages"
      />

      <main className="p-8 max-w-6xl mx-auto w-full space-y-6">
        {/* Human in the loop warning */}
        <div className="p-4 rounded-xl bg-nexus-900 border border-nexus-700 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <UserCheck className="w-5 h-5 text-amber-400" />
            <div>
              <div className="text-sm font-semibold text-nexus-100 flex items-center gap-2">
                <span>Human Approval Barrier</span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-950 text-amber-400 border border-amber-900">
                  MANDATORY
                </span>
              </div>
              <p className="text-xs text-nexus-400">
                Agent &quot;Apex&quot; is restricted from transmitting external messages automatically. Every outreach item must be manually reviewed and approved.
              </p>
            </div>
          </div>
        </div>

        {/* Outreach Review Queue */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-semibold text-nexus-400 uppercase tracking-wider">
              Outreach Approval Queue ({drafts.filter((d) => d.status === "pending_review").length} Pending)
            </h2>
          </div>

          <div className="space-y-4">
            {drafts.map((draft) => (
              <div
                key={draft.id}
                className="bg-nexus-900 border border-nexus-700 rounded-xl p-5 space-y-3"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-nexus-850 border border-nexus-700 flex items-center justify-center font-bold text-xs text-indigo-400 font-mono">
                      {draft.recipient.slice(0, 2).toUpperCase()}
                    </div>
                    <div>
                      <h3 className="text-sm font-semibold text-nexus-100">{draft.recipient}</h3>
                      <p className="text-xs text-nexus-400 font-mono">
                        {draft.role} @ <strong className="text-nexus-200">{draft.company}</strong>
                      </p>
                    </div>
                  </div>

                  <span
                    className={`text-[10px] font-mono px-2 py-0.5 rounded border uppercase ${
                      draft.status === "approved"
                        ? "bg-emerald-950 text-emerald-400 border-emerald-800"
                        : draft.status === "rejected"
                        ? "bg-red-950 text-red-400 border-red-800"
                        : "bg-amber-950 text-amber-400 border-amber-800"
                    }`}
                  >
                    {draft.status.replace("_", " ")}
                  </span>
                </div>

                <div className="p-3 rounded-lg bg-nexus-950 border border-nexus-800 text-xs text-nexus-300 font-mono leading-relaxed">
                  &ldquo;{draft.message}&rdquo;
                </div>

                {draft.status === "pending_review" && (
                  <div className="pt-2 flex justify-end gap-2">
                    <button
                      onClick={() => handleReview(draft.id, "rejected")}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-nexus-700 hover:bg-red-950/40 text-xs text-red-400 transition-colors"
                    >
                      <XCircle className="w-3.5 h-3.5" />
                      Reject Draft
                    </button>
                    <button
                      onClick={() => handleReview(draft.id, "approved")}
                      className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs transition-colors shadow-md shadow-emerald-600/20"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      Approve &amp; Queue Transmission
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
