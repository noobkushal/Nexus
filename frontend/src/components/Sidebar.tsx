"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { apiFetch, getApiBase } from "@/lib/api-client";
import {
  LayoutDashboard,
  MessageSquare,
  Bot,
  CheckSquare,
  Workflow,
  Brain,
  FolderGit2,
  Briefcase,
  Settings,
  ShieldCheck,
  Cpu,
  Monitor,
} from "lucide-react";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/chat", label: "Chat Assistant", icon: MessageSquare },
  { href: "/agents", label: "Agents Registry", icon: Bot },
  { href: "/tasks", label: "Tasks & Jobs", icon: CheckSquare },
  { href: "/workflows", label: "Workflows (n8n)", icon: Workflow },
  { href: "/memory", label: "Memory & Profile", icon: Brain },
  { href: "/projects", label: "Projects & Code", icon: FolderGit2 },
  { href: "/career", label: "Career & Outreach", icon: Briefcase },
  { href: "/companion", label: "Windows Companion", icon: Monitor },
  { href: "/settings", label: "System Settings", icon: Settings },
];

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();

  const handleLogout = async () => {
    try {
      await apiFetch(`${getApiBase()}/api/v1/auth/logout`, { method: "POST" });
    } finally {
      router.replace("/login");
      router.refresh();
    }
  };

  return (
    <aside className="w-64 bg-nexus-900 border-r border-nexus-700 flex flex-col h-screen fixed left-0 top-0 select-none z-30">
      {/* Brand Header */}
      <div className="p-5 border-b border-nexus-700 flex items-center justify-between">
        <Link href="/dashboard" className="flex items-center gap-3 group">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-cyan-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-cyan-500/20 group-hover:scale-105 transition-transform">
            <Cpu className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="font-bold tracking-wider text-nexus-100 flex items-center gap-1.5 text-sm">
              <span>NEXUS</span>
              <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800">
                AI OS
              </span>
            </div>
            <div className="text-[11px] text-nexus-400 font-mono">v0.1.0 • Foundation</div>
          </div>
        </Link>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
        <div className="px-3 py-2 text-[10px] font-semibold text-nexus-500 uppercase tracking-wider">
          Platform Navigation
        </div>
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href || (item.href !== "/dashboard" && pathname?.startsWith(item.href));
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-150 ${
                isActive
                  ? "bg-nexus-800 text-nexus-100 font-medium border border-nexus-600 shadow-sm"
                  : "text-nexus-400 hover:text-nexus-200 hover:bg-nexus-850"
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? "text-accent-cyan" : "text-nexus-400"}`} />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      {/* Session and System Status Footer */}
      <div className="p-4 border-t border-nexus-700 bg-nexus-950/60">
        <button onClick={handleLogout} className="mb-3 w-full rounded-lg border border-nexus-700 px-3 py-2 text-xs font-medium text-nexus-300 hover:border-red-800 hover:text-red-300 transition-colors">Sign out</button>
        <div className="flex items-center justify-between text-xs mb-2">
          <span className="text-nexus-400 flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            Local Safe Mode
          </span>
          <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/50 border border-emerald-800 px-1.5 py-0.5 rounded">
            ACTIVE
          </span>
        </div>
        <p className="text-[11px] text-nexus-500 leading-tight">
          Operating independently of external LLMs and cloud APIs.
        </p>
      </div>
    </aside>
  );
}
