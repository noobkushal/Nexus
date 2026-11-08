"use client";

import { apiFetch } from "@/lib/api-client";

import { useState } from "react";
import Header from "@/components/Header";
import { Send, Bot, User, ShieldAlert, Sparkles, ChevronDown, ChevronRight, Activity, GitFork } from "lucide-react";

interface ChatMessage {
  role: "user" | "assistant" | "system";
  content: string;
  is_mock?: boolean;
  claimed_actions_executed?: boolean;
  intent?: string;
  routed_agent?: string;
  steps?: string[];
  requires_approval?: boolean;
  approval_id?: string;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content:
        "[MOCK RESPONSE — NEXUS Foundation]\n" +
        "Greetings! I am NEXUS AI operating in standalone foundation mode. " +
        "You can query system status, explore agent capabilities, or discuss upcoming automation workflows.",
      is_mock: true,
      claimed_actions_executed: false,
      intent: "general_dialogue",
      routed_agent: "personal_agent",
      steps: [
        "Intent Classification -> 'general_dialogue'",
        "Graph Router -> Assigned to Agent 'Aura' (personal_agent)",
        "Safety Guard -> Read-only / Non-consequential query (Autonomous execution permitted)",
        "Synthesis -> Completed via Provider 'mock'",
      ],
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [expandedTraceIdx, setExpandedTraceIdx] = useState<number | null>(0);

  const sendMessage = async (textToSend?: string) => {
    const messageText = textToSend || input;
    if (!messageText.trim() || loading) return;

    const userMsg: ChatMessage = { role: "user", content: messageText };
    setMessages((prev) => [...prev, userMsg]);
    if (!textToSend) setInput("");
    setLoading(true);

    try {
      const res = await apiFetch("http://127.0.0.1:8000/api/v1/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: messageText,
          conversation_id: conversationId,
        }),
      });

      if (!res.ok) {
        throw new Error(`Server returned HTTP ${res.status}`);
      }

      const data = await res.json();
      setConversationId(data.conversation_id);
      const newIdx = messages.length + 1;
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.response,
          is_mock: data.is_mock,
          claimed_actions_executed: data.claimed_actions_executed,
          intent: data.intent,
          routed_agent: data.routed_agent,
          steps: data.steps,
          requires_approval: data.requires_approval,
          approval_id: data.approval_id,
        },
      ]);
      setExpandedTraceIdx(newIdx);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `[Error: Failed to reach backend at http://127.0.0.1:8000] - ${err.message}`,
          is_mock: true,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const samplePrompts = [
    "Check system status",
    "Can you check git commit and fix a bug in the code?",
    "Please research the web for latest AI papers",
    "Please delete old files in storage directory",
  ];

  return (
    <div className="flex-1 flex flex-col bg-nexus-950 h-screen">
      <Header
        title="Conversational Assistant & Orchestration Graph"
        subtitle="Multi-agent state graph routing with human approval intercept"
      />

      {/* Main Chat Stream */}
      <div className="flex-1 overflow-y-auto p-6 max-w-4xl mx-auto w-full space-y-4">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex gap-3.5 ${
              msg.role === "user" ? "justify-end" : "justify-start"
            }`}
          >
            {msg.role === "assistant" && (
              <div className="w-8 h-8 rounded-lg bg-cyan-950 border border-cyan-800 text-cyan-400 flex items-center justify-center shrink-0">
                <Bot className="w-4 h-4" />
              </div>
            )}

            <div
              className={`max-w-2xl rounded-xl p-4 text-xs leading-relaxed space-y-2.5 ${
                msg.role === "user"
                  ? "bg-cyan-600 text-white rounded-br-none shadow-md"
                  : "bg-nexus-900 border border-nexus-700 text-nexus-200 rounded-bl-none shadow-md"
              }`}
            >
              {msg.role === "assistant" && (
                <div className="flex items-center justify-between pb-1 border-b border-nexus-800 text-[10px] text-nexus-400 font-mono">
                  <div className="flex items-center gap-1.5">
                    <Sparkles className="w-3 h-3 text-cyan-400" />
                    <span>Agent: <strong className="text-nexus-200">{msg.routed_agent || "personal_agent"}</strong></span>
                  </div>
                  {msg.requires_approval ? (
                    <span className="text-amber-400 font-bold bg-amber-950/60 px-1.5 py-0.5 rounded border border-amber-900">
                      Approval #{msg.approval_id} Queued
                    </span>
                  ) : (
                    <span className="text-emerald-400 font-bold">• Safe Read-Only</span>
                  )}
                </div>
              )}

              {/* Expandable State Graph Trace */}
              {msg.role === "assistant" && msg.steps && msg.steps.length > 0 && (
                <div className="bg-nexus-950/80 border border-nexus-800 rounded-lg p-2.5">
                  <button
                    onClick={() => setExpandedTraceIdx(expandedTraceIdx === idx ? null : idx)}
                    className="flex items-center justify-between w-full text-[10px] font-mono text-cyan-400 hover:text-cyan-300"
                  >
                    <span className="flex items-center gap-1.5">
                      <GitFork className="w-3 h-3 text-indigo-400" />
                      State Graph Execution Trace ({msg.steps.length} Nodes)
                    </span>
                    {expandedTraceIdx === idx ? (
                      <ChevronDown className="w-3 h-3" />
                    ) : (
                      <ChevronRight className="w-3 h-3" />
                    )}
                  </button>

                  {expandedTraceIdx === idx && (
                    <div className="mt-2 pt-2 border-t border-nexus-850 space-y-1 font-mono text-[10px] text-nexus-400">
                      {msg.steps.map((step, sIdx) => (
                        <div key={sIdx} className="flex items-start gap-1.5">
                          <span className="text-indigo-400 shrink-0">&rarr;</span>
                          <span className="text-nexus-300">{step}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              <p className="whitespace-pre-line font-mono text-[11px]">{msg.content}</p>

              {msg.role === "assistant" && (
                <div className="pt-1 flex items-center justify-between text-[10px] text-nexus-500 font-mono">
                  <span className="flex items-center gap-1">
                    <ShieldAlert className="w-3 h-3 text-emerald-400" />
                    Side-Effects: None
                  </span>
                  <span>Intent: {msg.intent || "general"}</span>
                </div>
              )}
            </div>

            {msg.role === "user" && (
              <div className="w-8 h-8 rounded-lg bg-nexus-800 border border-nexus-700 text-nexus-300 flex items-center justify-center shrink-0">
                <User className="w-4 h-4" />
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="flex gap-3.5 justify-start">
            <div className="w-8 h-8 rounded-lg bg-cyan-950 border border-cyan-800 text-cyan-400 flex items-center justify-center shrink-0 animate-pulse">
              <Bot className="w-4 h-4" />
            </div>
            <div className="bg-nexus-900 border border-nexus-700 rounded-xl p-4 text-xs text-nexus-400 font-mono flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
              Routing prompt through agent state graph...
            </div>
          </div>
        )}
      </div>

      {/* Suggested Quick Prompts */}
      <div className="p-3 border-t border-nexus-800/80 bg-nexus-900/50 max-w-4xl mx-auto w-full">
        <div className="flex items-center gap-2 overflow-x-auto pb-1 text-[11px]">
          <span className="text-nexus-500 font-mono shrink-0">Sample Prompts:</span>
          {samplePrompts.map((p, i) => (
            <button
              key={i}
              onClick={() => sendMessage(p)}
              className="px-2.5 py-1 rounded-md bg-nexus-850 hover:bg-nexus-800 border border-nexus-700 text-nexus-300 hover:text-cyan-400 whitespace-nowrap transition-colors"
            >
              {p}
            </button>
          ))}
        </div>
      </div>

      {/* Chat Input Bar */}
      <div className="p-4 border-t border-nexus-700 bg-nexus-900">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            sendMessage();
          }}
          className="max-w-4xl mx-auto flex gap-3"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type a request (e.g. 'Can you check git code?', 'Delete files', 'Research AI papers')..."
            className="flex-1 bg-nexus-950 border border-nexus-700 rounded-xl px-4 py-2.5 text-xs text-nexus-100 placeholder-nexus-500 focus:outline-none focus:border-cyan-500 transition-colors"
          />
          <button
            type="submit"
            disabled={!input.trim() || loading}
            className="px-4 py-2.5 bg-cyan-500 hover:bg-cyan-400 disabled:opacity-50 disabled:cursor-not-allowed text-nexus-950 rounded-xl font-semibold text-xs flex items-center gap-2 transition-colors shadow-lg shadow-cyan-500/20"
          >
            <Send className="w-3.5 h-3.5" />
            Send
          </button>
        </form>
      </div>
    </div>
  );
}
