"use client";

import { useEffect, useState } from "react";
import Header from "@/components/Header";
import { CheckSquare, Plus, Trash2, Clock, CheckCircle2, AlertCircle } from "lucide-react";

interface TaskItem {
  id: string;
  title: string;
  description?: string;
  status: "pending" | "in_progress" | "completed" | "failed";
  priority: "low" | "medium" | "high" | "critical";
  assigned_agent?: string;
  created_at: string;
}

export default function TasksPage() {
  const [tasks, setTasks] = useState<TaskItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddForm, setShowAddForm] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [newPriority, setNewPriority] = useState<"low" | "medium" | "high" | "critical">("medium");
  const [newAgent, setNewAgent] = useState("personal_agent");

  const loadTasks = async () => {
    try {
      setLoading(true);
      const res = await fetch("http://127.0.0.1:8000/api/v1/tasks");
      if (res.ok) {
        const data = await res.json();
        setTasks(data.tasks || []);
      }
    } catch (err) {
      console.error("Failed to load tasks", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTasks();
  }, []);

  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim()) return;

    try {
      const res = await fetch("http://127.0.0.1:8000/api/v1/tasks", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: newTitle,
          description: newDesc || undefined,
          priority: newPriority,
          assigned_agent: newAgent,
        }),
      });

      if (res.ok) {
        setNewTitle("");
        setNewDesc("");
        setShowAddForm(false);
        loadTasks();
      }
    } catch (err) {
      console.error("Failed to create task", err);
    }
  };

  const updateStatus = async (taskId: string, newStatus: string) => {
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/v1/tasks/${taskId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus }),
      });
      if (res.ok) {
        loadTasks();
      }
    } catch (err) {
      console.error("Failed to update task", err);
    }
  };

  const deleteTask = async (taskId: string) => {
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/v1/tasks/${taskId}`, {
        method: "DELETE",
      });
      if (res.ok) {
        loadTasks();
      }
    } catch (err) {
      console.error("Failed to delete task", err);
    }
  };

  return (
    <div className="flex-1 flex flex-col bg-nexus-950">
      <Header
        title="Tasks & Autonomous Job Dispatch"
        subtitle="Operational work items assigned to NEXUS multi-agent workers"
      />

      <main className="p-8 max-w-6xl mx-auto w-full space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckSquare className="w-5 h-5 text-cyan-400" />
            <h2 className="text-sm font-semibold text-nexus-100">
              Work Items Overview ({tasks.length})
            </h2>
          </div>
          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-nexus-950 font-semibold text-xs transition-colors shadow-lg shadow-cyan-500/20"
          >
            <Plus className="w-3.5 h-3.5" />
            {showAddForm ? "Cancel" : "Add Task"}
          </button>
        </div>

        {/* Add Task Form Modal/Inline */}
        {showAddForm && (
          <form
            onSubmit={handleCreateTask}
            className="p-5 rounded-xl bg-nexus-900 border border-nexus-700 space-y-4"
          >
            <div className="text-xs font-semibold text-nexus-100">Create New Action Item</div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-[11px] text-nexus-400 block mb-1">Task Title *</label>
                <input
                  type="text"
                  required
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  placeholder="e.g. Scrape technical specifications for Next.js"
                  className="w-full bg-nexus-950 border border-nexus-700 rounded-lg px-3 py-2 text-xs text-nexus-100 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="text-[11px] text-nexus-400 block mb-1">Assign Agent</label>
                <select
                  value={newAgent}
                  onChange={(e) => setNewAgent(e.target.value)}
                  className="w-full bg-nexus-950 border border-nexus-700 rounded-lg px-3 py-2 text-xs text-nexus-100 focus:outline-none focus:border-cyan-500"
                >
                  <option value="personal_agent">Aura (Personal Assistant)</option>
                  <option value="coding_agent">Forge (Developer)</option>
                  <option value="research_agent">Scout (Researcher)</option>
                  <option value="workflow_agent">Conduit (Workflow)</option>
                  <option value="career_agent">Apex (Career)</option>
                </select>
              </div>

              <div className="md:col-span-2">
                <label className="text-[11px] text-nexus-400 block mb-1">Description</label>
                <textarea
                  rows={2}
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                  placeholder="Additional context or execution constraints..."
                  className="w-full bg-nexus-950 border border-nexus-700 rounded-lg px-3 py-2 text-xs text-nexus-100 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="text-[11px] text-nexus-400 block mb-1">Priority</label>
                <select
                  value={newPriority}
                  onChange={(e) => setNewPriority(e.target.value as any)}
                  className="w-full bg-nexus-950 border border-nexus-700 rounded-lg px-3 py-2 text-xs text-nexus-100 focus:outline-none focus:border-cyan-500"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="critical">Critical</option>
                </select>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setShowAddForm(false)}
                className="px-3 py-1.5 rounded-lg border border-nexus-700 text-xs text-nexus-400 hover:text-nexus-200"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-1.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-nexus-950 font-semibold text-xs"
              >
                Save Task
              </button>
            </div>
          </form>
        )}

        {/* Task Cards */}
        <div className="space-y-3">
          {tasks.map((task) => (
            <div
              key={task.id}
              className="bg-nexus-900 border border-nexus-700 rounded-xl p-4 flex items-center justify-between hover:border-nexus-600 transition-colors"
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span
                    className={`w-2 h-2 rounded-full ${
                      task.status === "completed"
                        ? "bg-emerald-400"
                        : task.status === "in_progress"
                        ? "bg-cyan-400"
                        : "bg-amber-400"
                    }`}
                  />
                  <h3 className="text-xs font-semibold text-nexus-100">{task.title}</h3>
                  <span className="text-[10px] font-mono text-nexus-500">#{task.id}</span>
                </div>
                {task.description && (
                  <p className="text-[11px] text-nexus-400 pl-4">{task.description}</p>
                )}
                <div className="flex items-center gap-3 pl-4 text-[10px] text-nexus-500 font-mono">
                  <span>Agent: {task.assigned_agent || "unassigned"}</span>
                  <span>&bull;</span>
                  <span className="uppercase">Priority: {task.priority}</span>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <select
                  value={task.status}
                  onChange={(e) => updateStatus(task.id, e.target.value)}
                  className="bg-nexus-850 border border-nexus-700 rounded-lg px-2.5 py-1 text-[11px] text-nexus-200 font-mono focus:outline-none"
                >
                  <option value="pending">Pending</option>
                  <option value="in_progress">In Progress</option>
                  <option value="completed">Completed</option>
                  <option value="failed">Failed</option>
                </select>

                <button
                  onClick={() => deleteTask(task.id)}
                  title="Delete Task"
                  className="p-1.5 rounded-lg border border-nexus-700 hover:bg-red-950/40 text-nexus-400 hover:text-red-400 transition-colors"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
