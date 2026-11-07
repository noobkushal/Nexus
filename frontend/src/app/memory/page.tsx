"use client";

import { useEffect, useState } from "react";
import Header from "@/components/Header";
import { Brain, Database, Plus, Search, ShieldCheck } from "lucide-react";

interface MemoryItem {
  id: string;
  category: string;
  key: string;
  content: string;
  importance: number;
}

export default function MemoryPage() {
  const [memories, setMemories] = useState<MemoryItem[]>([]);
  const [categoryFilter, setCategoryFilter] = useState<string | null>(null);
  const [showAdd, setShowAdd] = useState(false);
  const [newCat, setNewCat] = useState("profile");
  const [newKey, setNewKey] = useState("");
  const [newContent, setNewContent] = useState("");
  const [newImportance, setNewImportance] = useState(2);

  const loadMemories = async () => {
    try {
      const url = categoryFilter
        ? `http://127.0.0.1:8000/api/v1/memory?category=${categoryFilter}`
        : "http://127.0.0.1:8000/api/v1/memory";
      const res = await fetch(url);
      if (res.ok) setMemories(await res.json());
    } catch (err) {
      console.error("Failed to load memory", err);
    }
  };

  useEffect(() => {
    loadMemories();
  }, [categoryFilter]);

  const handleAddMemory = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newKey.trim() || !newContent.trim()) return;

    try {
      const res = await fetch("http://127.0.0.1:8000/api/v1/memory", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          category: newCat,
          key: newKey,
          content: newContent,
          importance: newImportance,
        }),
      });

      if (res.ok) {
        setNewKey("");
        setNewContent("");
        setShowAdd(false);
        loadMemories();
      }
    } catch (err) {
      console.error("Failed to store memory", err);
    }
  };

  const categories = ["all", "profile", "system", "preferences"];

  return (
    <div className="flex-1 flex flex-col bg-nexus-950">
      <Header
        title="Long-Term Memory & User Profile"
        subtitle="Semantic knowledge store and personalized operational context"
      />

      <main className="p-8 max-w-6xl mx-auto w-full space-y-6">
        <div className="p-4 rounded-xl bg-nexus-900 border border-nexus-700 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Database className="w-5 h-5 text-emerald-400" />
            <div>
              <div className="text-sm font-semibold text-nexus-100 flex items-center gap-2">
                <span>Memory Backend: In-Memory / SQLite Fallback</span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800">
                  READY
                </span>
              </div>
              <p className="text-xs text-nexus-400">
                Future milestone: PostgreSQL + pgvector embeddings for semantic similarity retrieval.
              </p>
            </div>
          </div>

          <button
            onClick={() => setShowAdd(!showAdd)}
            className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-nexus-950 font-semibold text-xs transition-colors shadow-lg shadow-cyan-500/20"
          >
            <Plus className="w-3.5 h-3.5" />
            {showAdd ? "Cancel" : "Add Memory"}
          </button>
        </div>

        {/* Add Memory Modal/Form */}
        {showAdd && (
          <form
            onSubmit={handleAddMemory}
            className="p-5 rounded-xl bg-nexus-900 border border-nexus-700 space-y-4"
          >
            <div className="text-xs font-semibold text-nexus-100">Store Context Item</div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="text-[11px] text-nexus-400 block mb-1">Category</label>
                <select
                  value={newCat}
                  onChange={(e) => setNewCat(e.target.value)}
                  className="w-full bg-nexus-950 border border-nexus-700 rounded-lg px-3 py-2 text-xs text-nexus-100"
                >
                  <option value="profile">Profile</option>
                  <option value="preferences">Preferences</option>
                  <option value="system">System</option>
                  <option value="projects">Projects</option>
                </select>
              </div>

              <div>
                <label className="text-[11px] text-nexus-400 block mb-1">Key Identifier *</label>
                <input
                  type="text"
                  required
                  value={newKey}
                  onChange={(e) => setNewKey(e.target.value)}
                  placeholder="e.g. primary_editor"
                  className="w-full bg-nexus-950 border border-nexus-700 rounded-lg px-3 py-2 text-xs text-nexus-100"
                />
              </div>

              <div>
                <label className="text-[11px] text-nexus-400 block mb-1">Importance (1-5)</label>
                <input
                  type="number"
                  min={1}
                  max={5}
                  value={newImportance}
                  onChange={(e) => setNewImportance(Number(e.target.value))}
                  className="w-full bg-nexus-950 border border-nexus-700 rounded-lg px-3 py-2 text-xs text-nexus-100"
                />
              </div>

              <div className="md:col-span-3">
                <label className="text-[11px] text-nexus-400 block mb-1">Memory Content *</label>
                <textarea
                  rows={2}
                  required
                  value={newContent}
                  onChange={(e) => setNewContent(e.target.value)}
                  placeholder="Fact, user preference, or permanent context..."
                  className="w-full bg-nexus-950 border border-nexus-700 rounded-lg px-3 py-2 text-xs text-nexus-100"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setShowAdd(false)}
                className="px-3 py-1.5 rounded-lg border border-nexus-700 text-xs text-nexus-400"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-1.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-nexus-950 font-semibold text-xs"
              >
                Save Record
              </button>
            </div>
          </form>
        )}

        {/* Filter Pills */}
        <div className="flex items-center gap-2">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setCategoryFilter(cat === "all" ? null : cat)}
              className={`px-3 py-1 rounded-lg text-xs font-mono transition-colors ${
                (cat === "all" && categoryFilter === null) || categoryFilter === cat
                  ? "bg-nexus-700 text-nexus-100 border border-nexus-500 font-semibold"
                  : "bg-nexus-900 text-nexus-400 hover:text-nexus-200 border border-nexus-800"
              }`}
            >
              {cat.toUpperCase()}
            </button>
          ))}
        </div>

        {/* Memory Items Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {memories.map((mem) => (
            <div
              key={mem.id}
              className="bg-nexus-900 border border-nexus-700 rounded-xl p-4 flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-nexus-800 text-cyan-400 border border-nexus-700 uppercase">
                    {mem.category}
                  </span>
                  <span className="text-[10px] font-mono text-nexus-400">
                    Priority: {mem.importance}★
                  </span>
                </div>
                <h3 className="text-xs font-semibold text-nexus-100 font-mono mb-1">{mem.key}</h3>
                <p className="text-xs text-nexus-300 leading-relaxed">{mem.content}</p>
              </div>

              <div className="mt-3 pt-2 border-t border-nexus-800 text-[10px] text-nexus-500 font-mono">
                Store ID: {mem.id}
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
