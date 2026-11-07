"""Schemas for Human-in-the-Loop Action Approval."""
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ActionType(str, Enum):
    FILESYSTEM_WRITE = "filesystem_write"
    FILESYSTEM_DELETE = "filesystem_delete"
    EXTERNAL_MESSAGE = "external_message"
    WORKFLOW_TRIGGER = "workflow_trigger"
    CODE_MODIFICATION = "code_modification"
    SYSTEM_CONFIG = "system_config"


class ApprovalRequestCreate(BaseModel):
    agent_id: str = Field(..., description="ID of requesting agent")
    action_type: ActionType
    title: str = Field(..., max_length=200)
    description: str = Field(..., max_length=2000)
    payload: Dict[str, Any] = Field(default_factory=dict)


class ApprovalDecision(BaseModel):
    decision: ApprovalStatus = Field(..., description="'approved' or 'rejected'")
    reviewer_notes: Optional[str] = Field(None, max_length=1000)


class ApprovalResponse(BaseModel):
    id: str
    agent_id: str
    action_type: ActionType
    title: str
    description: str
    payload: Dict[str, Any]
    status: ApprovalStatus
    requested_at: datetime
    decided_at: Optional[datetime] = None
    reviewer_notes: Optional[str] = None
