"use client";

import { apiFetch } from "@/lib/api-client";

import { useEffect, useState } from "react";
import Header from "@/components/Header";
import {
  Briefcase,
  FileText,
  Send,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  UserCheck,
  Mail,
  MessageSquare,
  Plus,
  Clock,
  ShieldAlert,
  Sparkles,
  Copy,
  Check,
  X,
  Eye,
  RefreshCw,
} from "lucide-react";

interface EmailDraft {
  id: string;
  sender: string;
  recipient: string;
  subject: string;
  body: string;
  status: "draft" | "pending_approval" | "approved" | "dispatched" | "rejected";
  priority: string;
  approval_id?: string;
  created_at: string;
}

interface MessageDraft {
  id: string;
  channel: string;
  recipient: string;
  content: string;
  status: "draft" | "pending_approval" | "approved" | "dispatched" | "rejected";
  approval_id?: string;
  created_at: string;
}

interface JobOpportunity {
  id: string;
  title: string;
  company: string;
  location: string;
  skills_required: string[];
  description: string;
  match_score: number;
  status: string;
}

interface ResumeData {
  id: string;
  target_role: string;
  target_company: string;
  match_score: number;
  tailored_summary: string;
  matched_skills: string[];
  relative_path: string;
  content: string;
}

export default function CareerPage() {
  const [activeTab, setActiveTab] = useState<"jobs" | "emails" | "outreach">("jobs");
  const [emails, setEmails] = useState<EmailDraft[]>([]);
  const [messages, setMessages] = useState<MessageDraft[]>([]);
  const [jobs, setJobs] = useState<JobOpportunity[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  // Resume Modal & Generation State
  const [tailoringJobId, setTailoringJobId] = useState<string | null>(null);
  const [activeResume, setActiveResume] = useState<ResumeData | null>(null);
  const [copiedResume, setCopiedResume] = useState(false);

  // New Draft Modal
  const [showDraftModal, setShowDraftModal] = useState(false);
  const [recipient, setRecipient] = useState("");
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [priority, setPriority] = useState("normal");

  const loadData = async () => {
    try {
      const [eRes, mRes, jRes] = await Promise.all([
        apiFetch("http://127.0.0.1:8000/api/v1/communications/emails"),
        apiFetch("http://127.0.0.1:8000/api/v1/communications/messages"),
        apiFetch("http://127.0.0.1:8000/api/v1/career/jobs"),
      ]);
      if (eRes.ok) setEmails(await eRes.json());
      if (mRes.ok) setMessages(await mRes.json());
      if (jRes.ok) setJobs(await jRes.json());
    } catch (err) {
      console.error("Failed to load communications and career data", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleTailorResume = async (job: JobOpportunity) => {
    setTailoringJobId(job.id);
    try {
      const res = await apiFetch("http://127.0.0.1:8000/api/v1/career/tailor-resume", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          job_id: job.id,
          target_role: job.title,
          target_company: job.company,
          job_description: job.description,
          focus_skills: job.skills_required,
        }),
      });
      if (res.ok) {
        const resume: ResumeData = await res.json();
        setActiveResume(resume);
        setActionMessage(`Resume customized for ${job.company} (${Math.round(resume.match_score * 100)}% match)`);
        loadData();
      }
    } catch (err) {
      console.error("Failed to tailor resume", err);
    } finally {
      setTailoringJobId(null);
    }
  };

  const handleCopyResume = () => {
    if (!activeResume) return;
    navigator.clipboard.writeText(activeResume.content);
    setCopiedResume(true);
    setTimeout(() => setCopiedResume(false), 2000);
  };

  const handleRequestEmailApproval = async (id: string) => {
    try {
      const res = await apiFetch(`http://127.0.0.1:8000/api/v1/communications/emails/${id}/request-dispatch`, {
        method: "POST",
      });
      if (res.ok) {
        setActionMessage(`Email ${id} submitted to Human Approval Gate!`);
        loadData();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleDispatchEmail = async (id: string) => {
    try {
      const res = await apiFetch(`http://127.0.0.1:8000/api/v1/communications/emails/${id}/dispatch`, {
        method: "POST",
      });
      if (res.ok) {
        const data = await res.json();
        setActionMessage(data.message);
        loadData();
      } else {
        const err = await res.json();
        setActionMessage(`Security Guardrail: ${err.detail || "Dispatch blocked"}`);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleCreateDraft = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!recipient || !subject || !body) return;

    try {
      const res = await apiFetch("http://127.0.0.1:8000/api/v1/communications/emails", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ recipient, subject, body, priority }),
      });
      if (res.ok) {
        setShowDraftModal(false);
        setRecipient("");
        setSubject("");
        setBody("");
        loadData();
        setActionMessage("New email draft created safely in quarantine.");
      }
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="flex-1 flex flex-col bg-nexus-950">
      <Header
        title="Career Intelligence, Job Discovery & Outreach Engine"
        subtitle="Autonomous opportunity matching, CV tailoring, and human-verified outreach"
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
                  MANDATORY ENFORCEMENT
                </span>
              </div>
              <p className="text-xs text-nexus-400">
                Agent &quot;Apex&quot; is prohibited from transmitting outbound outreach autonomously.
                Every communication must be approved in Mission Control before dispatch.
              </p>
            </div>
          </div>
          <button
            onClick={() => setShowDraftModal(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-semibold text-xs transition-colors shadow-md shadow-cyan-900/30"
          >
            <Plus className="w-3.5 h-3.5" /> Compose Email
          </button>
        </div>

        {actionMessage && (
          <div className="p-3 rounded-lg bg-nexus-900 border border-cyan-800 text-xs text-cyan-300 flex items-center justify-between animate-in fade-in duration-150">
            <span>{actionMessage}</span>
            <button onClick={() => setActionMessage(null)} className="text-nexus-400 hover:text-nexus-200">
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        )}

        {/* Tab Controls */}
        <div className="flex items-center gap-3 border-b border-nexus-800 pb-2">
          <button
            onClick={() => setActiveTab("jobs")}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
              activeTab === "jobs"
                ? "bg-nexus-800 text-cyan-400 border border-nexus-700"
                : "text-nexus-400 hover:text-nexus-200"
            }`}
          >
            <Briefcase className="w-3.5 h-3.5" />
            <span>Discovered Opportunities ({jobs.length})</span>
          </button>
          <button
            onClick={() => setActiveTab("emails")}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
              activeTab === "emails"
                ? "bg-nexus-800 text-cyan-400 border border-nexus-700"
                : "text-nexus-400 hover:text-nexus-200"
            }`}
          >
            <Mail className="w-3.5 h-3.5" />
            <span>Email Communication Queue ({emails.length})</span>
          </button>
          <button
            onClick={() => setActiveTab("outreach")}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
              activeTab === "outreach"
                ? "bg-nexus-800 text-cyan-400 border border-nexus-700"
                : "text-nexus-400 hover:text-nexus-200"
            }`}
          >
            <MessageSquare className="w-3.5 h-3.5" />
            <span>LinkedIn &amp; Messaging ({messages.length})</span>
          </button>
        </div>

        {/* Jobs Tab Content */}
        {activeTab === "jobs" && (
          <div className="space-y-4">
            {jobs.map((job) => (
              <div
                key={job.id}
                className="bg-nexus-900 border border-nexus-700 rounded-xl p-5 space-y-3"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div>
                    <div className="flex items-center gap-2.5">
                      <h3 className="text-sm font-semibold text-nexus-100">{job.title}</h3>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800">
                        {Math.round(job.match_score * 100)}% MATCH
                      </span>
                    </div>
                    <p className="text-xs text-nexus-400 font-mono mt-0.5">
                      {job.company} &bull; <span className="text-nexus-300">{job.location}</span>
                    </p>
                  </div>
                  <button
                    onClick={() => handleTailorResume(job)}
                    disabled={tailoringJobId === job.id}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs transition-colors shadow-md shadow-indigo-900/30 disabled:opacity-50"
                  >
                    <Sparkles className={`w-3.5 h-3.5 ${tailoringJobId === job.id ? "animate-spin" : ""}`} />
                    <span>{tailoringJobId === job.id ? "Tailoring CV..." : "Tailor Resume"}</span>
                  </button>
                </div>

                <p className="text-xs text-nexus-300 leading-relaxed">{job.description}</p>

                <div className="flex flex-wrap items-center gap-1.5 pt-1">
                  <span className="text-[10px] font-mono text-nexus-500 mr-1">Skills:</span>
                  {job.skills_required.map((skill, idx) => (
                    <span
                      key={idx}
                      className="text-[10px] font-mono px-2 py-0.5 rounded bg-nexus-850 text-cyan-300 border border-nexus-750"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Emails Tab Content */}
        {activeTab === "emails" && (
          <div className="space-y-4">
            {emails.map((em) => (
              <div
                key={em.id}
                className="bg-nexus-900 border border-nexus-700 rounded-xl p-5 space-y-3"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-nexus-850 border border-nexus-700 flex items-center justify-center font-bold text-xs text-cyan-400 font-mono">
                      EM
                    </div>
                    <div>
                      <h3 className="text-sm font-semibold text-nexus-100">{em.subject}</h3>
                      <p className="text-xs text-nexus-400 font-mono">
                        To: <strong className="text-nexus-200">{em.recipient}</strong> &bull; From: {em.sender}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-nexus-800 text-nexus-300 border border-nexus-700 uppercase">
                      {em.priority}
                    </span>
                    <span
                      className={`text-[10px] font-mono px-2 py-0.5 rounded border uppercase ${
                        em.status === "dispatched"
                          ? "bg-emerald-950 text-emerald-400 border-emerald-800"
                          : em.status === "pending_approval"
                          ? "bg-amber-950 text-amber-400 border-amber-800"
                          : "bg-nexus-800 text-nexus-300 border-nexus-700"
                      }`}
                    >
                      {em.status.replace("_", " ")}
                    </span>
                  </div>
                </div>

                <div className="p-3.5 rounded-lg bg-nexus-950 border border-nexus-800 text-xs text-nexus-300 whitespace-pre-wrap leading-relaxed font-mono">
                  {em.body}
                </div>

                <div className="pt-2 border-t border-nexus-850 flex items-center justify-between">
                  <span className="text-[10px] text-nexus-500 font-mono">
                    ID: {em.id} {em.approval_id && `• Approval #${em.approval_id}`}
                  </span>
                  <div className="flex items-center gap-2">
                    {em.status === "draft" && (
                      <button
                        onClick={() => handleRequestEmailApproval(em.id)}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-500 text-white font-semibold text-xs transition-colors shadow-md shadow-amber-900/30"
                      >
                        <ShieldAlert className="w-3.5 h-3.5" />
                        Request Dispatch Approval
                      </button>
                    )}
                    {em.status === "pending_approval" && (
                      <button
                        onClick={() => handleDispatchEmail(em.id)}
                        className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs transition-colors shadow-md shadow-emerald-900/30"
                      >
                        <Send className="w-3.5 h-3.5" />
                        Execute Dispatch
                      </button>
                    )}
                    {em.status === "dispatched" && (
                      <span className="text-xs text-emerald-400 flex items-center gap-1 font-mono">
                        <CheckCircle2 className="w-3.5 h-3.5" /> Sent &amp; Logged to Audit
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Outreach Tab Content */}
        {activeTab === "outreach" && (
          <div className="space-y-4">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className="bg-nexus-900 border border-nexus-700 rounded-xl p-5 space-y-3"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-nexus-850 border border-nexus-700 flex items-center justify-center font-bold text-xs text-indigo-400 font-mono">
                      LI
                    </div>
                    <div>
                      <h3 className="text-sm font-semibold text-nexus-100">{msg.recipient}</h3>
                      <p className="text-xs text-nexus-400 font-mono">
                        Channel: <span className="text-indigo-400 uppercase">{msg.channel}</span>
                      </p>
                    </div>
                  </div>

                  <span
                    className={`text-[10px] font-mono px-2 py-0.5 rounded border uppercase ${
                      msg.status === "dispatched"
                        ? "bg-emerald-950 text-emerald-400 border-emerald-800"
                        : msg.status === "pending_approval"
                        ? "bg-amber-950 text-amber-400 border-amber-800"
                        : "bg-nexus-800 text-nexus-300 border-nexus-700"
                    }`}
                  >
                    {msg.status.replace("_", " ")}
                  </span>
                </div>

                <div className="p-3.5 rounded-lg bg-nexus-950 border border-nexus-800 text-xs text-nexus-300 font-mono leading-relaxed">
                  &ldquo;{msg.content}&rdquo;
                </div>

                <div className="pt-2 border-t border-nexus-850 flex items-center justify-between">
                  <span className="text-[10px] text-nexus-500 font-mono">
                    ID: {msg.id} {msg.approval_id && `• Approval #${msg.approval_id}`}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Tailored Resume Inspection Modal */}
        {activeResume && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
            <div className="bg-nexus-900 border border-nexus-700 rounded-2xl w-full max-w-4xl max-h-[85vh] flex flex-col shadow-2xl overflow-hidden">
              <div className="p-4 border-b border-nexus-700 flex items-center justify-between bg-nexus-950/60">
                <div className="flex items-center gap-2.5">
                  <FileText className="w-4 h-4 text-indigo-400" />
                  <span className="text-sm font-semibold text-nexus-100">
                    Tailored CV: {activeResume.target_role} @ {activeResume.target_company}
                  </span>
                  <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800">
                    {Math.round(activeResume.match_score * 100)}% Match
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleCopyResume}
                    className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-nexus-800 hover:bg-nexus-750 border border-nexus-700 text-xs text-nexus-200 transition-colors"
                  >
                    {copiedResume ? (
                      <>
                        <Check className="w-3.5 h-3.5 text-emerald-400" />
                        <span className="text-emerald-400">Copied</span>
                      </>
                    ) : (
                      <>
                        <Copy className="w-3.5 h-3.5" />
                        <span>Copy Markdown</span>
                      </>
                    )}
                  </button>
                  <button
                    onClick={() => setActiveResume(null)}
                    className="p-1 rounded-lg hover:bg-nexus-800 text-nexus-400 hover:text-nexus-200 transition-colors"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              </div>
              <div className="p-6 overflow-y-auto flex-1 font-mono text-xs text-nexus-200 bg-nexus-950/40 whitespace-pre-wrap leading-relaxed">
                {activeResume.content}
              </div>
              <div className="p-3 border-t border-nexus-800 bg-nexus-950/80 text-[11px] text-nexus-500 flex justify-between">
                <span>Quarantined in storage/{activeResume.relative_path}</span>
                <span>Generated via NEXUS Apex Agent</span>
              </div>
            </div>
          </div>
        )}

        {/* Compose Email Modal */}
        {showDraftModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
            <div className="bg-nexus-900 border border-nexus-700 rounded-2xl w-full max-w-xl p-6 shadow-2xl space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-nexus-800">
                <h3 className="text-base font-semibold text-nexus-100 flex items-center gap-2">
                  <Mail className="w-4 h-4 text-cyan-400" />
                  Compose Quarantined Email Draft
                </h3>
                <button
                  onClick={() => setShowDraftModal(false)}
                  className="p-1 rounded-lg text-nexus-400 hover:text-nexus-200 transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <form onSubmit={handleCreateDraft} className="space-y-3.5 text-xs">
                <div>
                  <label className="block text-nexus-400 font-semibold mb-1">Recipient Email</label>
                  <input
                    type="email"
                    required
                    value={recipient}
                    onChange={(e) => setRecipient(e.target.value)}
                    placeholder="recruiter@techinnovations.io"
                    className="w-full px-3 py-2 rounded-lg bg-nexus-950 border border-nexus-750 text-nexus-100 focus:outline-none focus:border-cyan-500"
                  />
                </div>

                <div>
                  <label className="block text-nexus-400 font-semibold mb-1">Subject</label>
                  <input
                    type="text"
                    required
                    value={subject}
                    onChange={(e) => setSubject(e.target.value)}
                    placeholder="Collaboration Opportunity"
                    className="w-full px-3 py-2 rounded-lg bg-nexus-950 border border-nexus-750 text-nexus-100 focus:outline-none focus:border-cyan-500"
                  />
                </div>

                <div>
                  <label className="block text-nexus-400 font-semibold mb-1">Priority</label>
                  <select
                    value={priority}
                    onChange={(e) => setPriority(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg bg-nexus-950 border border-nexus-750 text-nexus-200 focus:outline-none focus:border-cyan-500"
                  >
                    <option value="low">Low</option>
                    <option value="normal">Normal</option>
                    <option value="high">High</option>
                    <option value="urgent">Urgent</option>
                  </select>
                </div>

                <div>
                  <label className="block text-nexus-400 font-semibold mb-1">Email Body</label>
                  <textarea
                    rows={4}
                    required
                    value={body}
                    onChange={(e) => setBody(e.target.value)}
                    placeholder="Write your email contents here..."
                    className="w-full px-3 py-2 rounded-lg bg-nexus-950 border border-nexus-750 text-nexus-100 focus:outline-none focus:border-cyan-500 font-mono"
                  />
                </div>

                <div className="flex justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setShowDraftModal(false)}
                    className="px-3 py-1.5 rounded-lg border border-nexus-750 text-nexus-400 hover:text-nexus-200"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-semibold transition-colors shadow-md shadow-cyan-900/30"
                  >
                    Save Draft (Quarantined)
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
