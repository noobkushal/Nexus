"""Persistent n8n webhook dispatch with honest execution outcomes."""
import json
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from urllib.parse import urlsplit

import httpx
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import logger
from app.db.models import WorkflowExecutionModel


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
    trigger_type: str = "webhook"
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


def _to_execution(row: WorkflowExecutionModel) -> WorkflowExecution:
    return WorkflowExecution(
        execution_id=row.id,
        workflow_id=row.workflow_id,
        status=ExecutionStatus(row.status),
        triggered_at=row.triggered_at,
        completed_at=row.completed_at,
        payload=json.loads(row.payload_json or "{}"),
        result=json.loads(row.result_json) if row.result_json else None,
    )


class WorkflowService:
    """Dispatches registered workflows and stores every outcome in the owner database."""

    def __init__(self):
        self._workflows: Dict[str, WorkflowDefinition] = {}
        self._seed_workflows()

    def _seed_workflows(self):
        seeds = [
            ("daily_briefing", "Morning Intelligence Briefing", "Gathers calendar items, priority tasks, and news summary.", "cron", "/webhook/daily-briefing"),
            ("email_inbox_triage", "Smart Email Triage & Drafts", "Labels incoming emails and prepares reply drafts for review.", "webhook", "/webhook/email-triage"),
            ("code_checkpoint_sync", "Project Git Safety Sync", "Triggers registered Git checkpoint automation.", "event", "/webhook/git-snapshot"),
        ]
        for wid, name, desc, trigger, path in seeds:
            self._workflows[wid] = WorkflowDefinition(id=wid, name=name, description=desc, trigger_type=trigger, webhook_path=path)

    def list_workflows(self) -> List[WorkflowDefinition]:
        return list(self._workflows.values())

    def get_workflow(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        return self._workflows.get(workflow_id)

    def list_executions(self, owner_id: str, db: Session, limit: int = 15) -> List[WorkflowExecution]:
        safe_limit = max(1, min(limit, 100))
        rows = (db.query(WorkflowExecutionModel)
            .filter(WorkflowExecutionModel.owner_id == owner_id)
            .order_by(WorkflowExecutionModel.triggered_at.desc())
            .limit(safe_limit).all())
        return [_to_execution(row) for row in rows]

    async def trigger_workflow(
        self, workflow_id: str, payload: Optional[Dict[str, Any]] = None,
        owner_id: Optional[str] = None, db: Optional[Session] = None,
    ) -> WorkflowExecution:
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow '{workflow_id}' does not exist.")
        if workflow.status != WorkflowStatus.ACTIVE:
            raise ValueError(f"Workflow '{workflow_id}' is not active.")
        base = settings.N8N_WEBHOOK_URL
        if not base:
            raise RuntimeError("n8n is not configured. Set N8N_WEBHOOK_URL before triggering workflows.")
        parsed = urlsplit(base)
        if parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username or parsed.password:
            raise RuntimeError("N8N_WEBHOOK_URL must be an absolute HTTP(S) URL without embedded credentials.")
        if parsed.scheme != "https" and parsed.hostname not in ("localhost", "127.0.0.1", "::1"):
            raise RuntimeError("Remote n8n endpoints must use HTTPS.")
        if not owner_id or db is None:
            raise RuntimeError("Workflow dispatch requires an authenticated owner and persistent database session.")

        execution_id = str(uuid.uuid4())
        triggered_at = utc_now()
        stored_payload = payload or {}
        row = WorkflowExecutionModel(
            id=execution_id, owner_id=owner_id, workflow_id=workflow_id,
            status=ExecutionStatus.RUNNING.value, triggered_at=triggered_at,
            payload_json=json.dumps(stored_payload, sort_keys=True, separators=(",", ":")),
        )
        db.add(row)
        db.commit()
        target = base.rstrip("/") + (workflow.webhook_path or "")
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(20.0), follow_redirects=False) as client:
                response = await client.post(target, json={
                    "execution_id": execution_id,
                    "workflow_id": workflow_id,
                    "triggered_at": triggered_at.isoformat(),
                    "payload": stored_payload,
                })
                response.raise_for_status()
            row.status = ExecutionStatus.SUCCESS.value
            row.result_json = json.dumps({
                "message": f"n8n accepted workflow '{workflow.name}'.",
                "http_status": response.status_code,
                "target_webhook": target,
            }, sort_keys=True)
        except httpx.HTTPError as exc:
            row.status = ExecutionStatus.FAILED.value
            row.result_json = json.dumps({
                "message": "n8n webhook dispatch failed; no successful execution is claimed.",
                "error": type(exc).__name__,
                "target_webhook": target,
            }, sort_keys=True)
            logger.warning("Workflow dispatch failed for %s: %s", workflow_id, type(exc).__name__)
        finally:
            row.completed_at = utc_now()
            db.commit()
            db.refresh(row)
        return _to_execution(row)


workflow_service = WorkflowService()
