"""Workflow and Automation Service Interface (n8n Bridge)."""
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.core.config import settings
from app.core.logging import logger


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class WorkflowStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    DRAFT = "draft"


class ExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class WorkflowDefinition(BaseModel):
    id: str
    name: str
    description: str
    trigger_type: str = "webhook"  # webhook, cron, event
    webhook_path: Optional[str] = None
    status: WorkflowStatus = WorkflowStatus.ACTIVE
    created_at: datetime = Field(default_factory=utc_now)


class WorkflowExecution(BaseModel):
    execution_id: str
    workflow_id: str
    status: ExecutionStatus
    triggered_at: datetime = Field(default_factory=utc_now)
    completed_at: Optional[datetime] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None


class WorkflowService:
    """Manages workflow catalog and simulated execution tracking without requiring n8n."""

    def __init__(self):
        self._workflows: Dict[str, WorkflowDefinition] = {}
        self._executions: List[WorkflowExecution] = []
        self._seed_workflows()

    def _seed_workflows(self):
        seeds = [
            (
                "daily_briefing",
                "Morning Intelligence Briefing",
                "Gathers calendar items, priority tasks, and news summary at 08:00 AM.",
                "cron",
                "/webhook/daily-briefing",
            ),
            (
                "email_inbox_triage",
                "Smart Email Triage & Drafts",
                "Labels incoming emails, flags priority senders, and pre-drafts replies for approval.",
                "webhook",
                "/webhook/email-triage",
            ),
            (
                "code_checkpoint_sync",
                "Project Git Safety Sync",
                "Automates local branch snapshots before consequential agent code edits.",
                "event",
                "/webhook/git-snapshot",
            ),
        ]
        for wid, name, desc, ttype, wpath in seeds:
            self._workflows[wid] = WorkflowDefinition(
                id=wid,
                name=name,
                description=desc,
                trigger_type=ttype,
                webhook_path=wpath,
                status=WorkflowStatus.ACTIVE,
            )

    def list_workflows(self) -> List[WorkflowDefinition]:
        return list(self._workflows.values())

    def get_workflow(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        return self._workflows.get(workflow_id)

    async def trigger_workflow(self, workflow_id: str, payload: Optional[Dict[str, Any]] = None) -> WorkflowExecution:
        wf = self.get_workflow(workflow_id)
        if not wf:
            raise ValueError(f"Workflow '{workflow_id}' does not exist.")

        exec_id = str(uuid.uuid4())[:8]
        execution = WorkflowExecution(
            execution_id=exec_id,
            workflow_id=workflow_id,
            status=ExecutionStatus.SUCCESS,
            completed_at=utc_now(),
            payload=payload or {},
            result={
                "message": f"Simulated workflow execution for '{wf.name}' completed.",
                "note": "Running in offline mode; n8n webhook invocation was simulated.",
                "target_webhook": f"{settings.N8N_WEBHOOK_URL or 'http://127.0.0.1:5678'}{wf.webhook_path}",
            },
        )
        self._executions.append(execution)
        logger.info(f"Triggered workflow '{workflow_id}' -> Execution: {exec_id}")
        return execution

    def list_executions(self, limit: int = 15) -> List[WorkflowExecution]:
        return sorted(self._executions, key=lambda e: e.triggered_at, reverse=True)[:limit]


workflow_service = WorkflowService()
