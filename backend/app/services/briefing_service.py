"""Task Scheduling, Reminders, and Daily Briefings Service.

Synthesizes system state, agent activity, pending safety approvals, high-priority tasks,
and communication drafts into an executive Markdown briefing saved in storage/generated/.
"""
import glob
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.agents.orchestrator import orchestrator
from app.core.config import settings
from app.core.logging import get_audit_logger, logger
from app.providers.registry import provider_registry
from app.schemas.approval import ApprovalStatus
from app.schemas.communication import CommunicationStatus
from app.schemas.task import TaskPriority, TaskStatus
from app.services.approval_service import approval_service
from app.services.communication_service import communication_service
from app.services.task_service import task_service
from app.tools.filesystem import sandboxed_fs

audit_logger = get_audit_logger()


class BriefingService:
    """Compiles daily operational summaries and reminders for the human operator."""

    def generate_daily_briefing(self) -> Dict[str, Any]:
        """Gathers runtime diagnostics, tasks, approvals, and generates a structured briefing."""
        now = datetime.now(timezone.utc)
        date_str = now.strftime("%Y-%m-%d")
        timestamp_str = now.strftime("%Y%m%d_%H%M%S")

        # 1. System & Provider State
        active_provider = provider_registry.active_provider
        provider_name = active_provider.name
        model_name = getattr(active_provider, "model_name", "nexus-mock-engine-v1")

        # 2. Tasks Summary
        all_tasks = task_service.list_tasks()
        pending_tasks = [t for t in all_tasks if t.status in (TaskStatus.PENDING, TaskStatus.IN_PROGRESS)]
        high_priority_tasks = [t for t in pending_tasks if t.priority in (TaskPriority.HIGH, TaskPriority.CRITICAL)]

        # 3. Safety Approval Gate
        pending_approvals = approval_service.list_approvals(status=ApprovalStatus.PENDING)

        # 4. Multi-Agent Roster & Activity
        agents = orchestrator.list_agents()
        recent_activity = orchestrator.list_activities(limit=5)

        # 5. Communications Drafts
        pending_emails = communication_service.list_emails(status=CommunicationStatus.PENDING_APPROVAL)
        draft_emails = communication_service.list_emails(status=CommunicationStatus.DRAFT)

        # Assemble Markdown Briefing
        md_lines = [
            f"# NEXUS Daily Operator Briefing — {date_str}",
            f"",
            f"> **Generated**: {now.isoformat()}  ",
            f"> **Active AI Engine**: `{provider_name}` (`{model_name}`)  ",
            f"> **Environment**: Local-First Autonomous Operations",
            f"",
            f"---",
            f"",
            f"## 1. Safety & Human-in-the-Loop Barrier",
        ]

        if pending_approvals:
            md_lines.append(f"**Attention**: There are **{len(pending_approvals)}** pending actions awaiting your explicit authorization:")
            for app in pending_approvals:
                md_lines.append(f"- `[{app.id}]` **{app.action_type.value}**: {app.title} (Agent: `{app.agent_id}`)")
        else:
            md_lines.append("All safety gates clear. No unreviewed consequential actions in queue.")

        md_lines.extend([
            f"",
            f"## 2. Priority Tasks & Work Items",
            f"- **Total Tasks Tracked**: {len(all_tasks)}",
            f"- **Active / In-Progress**: {len(pending_tasks)}",
            f"- **High / Critical Priority**: {len(high_priority_tasks)}",
            f"",
        ])

        if high_priority_tasks:
            md_lines.append("### Urgent Attention:")
            for t in high_priority_tasks:
                md_lines.append(f"- **{t.title}** [`{t.priority.value.upper()}`] — Status: *{t.status.value}*")
            md_lines.append("")

        md_lines.extend([
            f"## 3. Communication & Outbound Pipeline",
            f"- **Emails Pending Operator Approval**: {len(pending_emails)}",
            f"- **Emails in Draft**: {len(draft_emails)}",
            f"",
            f"## 4. Multi-Agent System Roster ({len(agents)} Registered)",
        ])

        for a in agents:
            md_lines.append(f"- **{a.name}** (`{a.id}`): {a.role} — Status: *{a.status}*")

        md_lines.extend([
            f"",
            f"## 5. Recent Agent Audit Trail",
        ])

        if recent_activity:
            for act in recent_activity:
                time_fmt = act.timestamp.strftime("%H:%M:%S")
                md_lines.append(f"- `[{time_fmt}]` **{act.agent_id}**: {act.action} — *{act.details}*")
        else:
            md_lines.append("- No recent agent actions logged.")

        md_lines.extend([
            f"",
            f"---",
            f"*NEXUS Personal AI Operating System — Sandboxed Local Generation*",
        ])

        briefing_text = "\n".join(md_lines)
        relative_filename = f"generated/daily_briefing_{timestamp_str}.md"

        # Save to sandboxed storage
        sandboxed_fs.write_text_file(relative_filename, briefing_text, requires_approval=False)

        # Log activity
        orchestrator.log_activity(
            agent_id="personal_agent",
            action="Briefing Generated",
            details=f"Saved daily briefing to {relative_filename}",
            status="completed",
        )
        audit_logger.info(f"Daily briefing compiled and saved: {relative_filename}")

        return {
            "filename": Path(relative_filename).name,
            "path": relative_filename,
            "generated_at": now.isoformat(),
            "content": briefing_text,
            "stats": {
                "pending_tasks": len(pending_tasks),
                "pending_approvals": len(pending_approvals),
                "active_agents": len(agents),
            },
        }

    def get_latest_briefing(self) -> Dict[str, Any]:
        """Returns the most recently generated briefing or creates a fresh one."""
        storage_base = Path(settings.STORAGE_DIR).resolve()
        generated_dir = storage_base / "generated"
        briefing_files = sorted(generated_dir.glob("daily_briefing_*.md"), key=lambda p: p.stat().st_mtime, reverse=True)

        if not briefing_files:
            return self.generate_daily_briefing()

        latest = briefing_files[0]
        content = latest.read_text(encoding="utf-8")
        rel_path = f"generated/{latest.name}"

        return {
            "filename": latest.name,
            "path": rel_path,
            "generated_at": datetime.fromtimestamp(latest.stat().st_mtime, tz=timezone.utc).isoformat(),
            "content": content,
        }

    def list_reminders(self) -> List[Dict[str, Any]]:
        """Synthesizes high-priority reminders across tasks, approvals, and communications."""
        reminders = []

        # 1. Pending approvals needing decision
        for app in approval_service.list_approvals(status=ApprovalStatus.PENDING):
            reminders.append({
                "type": "approval_required",
                "priority": "urgent",
                "title": f"Approval Needed: {app.title}",
                "description": f"Agent '{app.agent_id}' requested '{app.action_type.value}'.",
                "reference_id": app.id,
            })

        # 2. Urgent / High priority tasks
        all_tasks = task_service.list_tasks()
        for t in all_tasks:
            if t.status in (TaskStatus.PENDING, TaskStatus.IN_PROGRESS) and t.priority in (TaskPriority.HIGH, TaskPriority.CRITICAL):
                reminders.append({
                    "type": "urgent_task",
                    "priority": t.priority.value,
                    "title": f"Task: {t.title}",
                    "description": t.description or "High priority action item.",
                    "reference_id": t.id,
                })

        # 3. Communications pending dispatch
        for em in communication_service.list_emails(status=CommunicationStatus.PENDING_APPROVAL):
            reminders.append({
                "type": "pending_communication",
                "priority": "high",
                "title": f"Email Pending: {em.subject}",
                "description": f"Recipient: {em.recipient}",
                "reference_id": em.id,
            })

        return reminders


briefing_service = BriefingService()
