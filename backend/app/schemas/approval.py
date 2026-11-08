"""Schemas for durable, payload-bound human approval."""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CONSUMED = "consumed"
    FAILED = "failed"


class ActionType(str, Enum):
    FILESYSTEM_WRITE = "filesystem_write"
    FILESYSTEM_DELETE = "filesystem_delete"
    EXTERNAL_MESSAGE = "external_message"
    APPLICATION_SUBMISSION = "application_submission"
    PRODUCTION_DEPLOYMENT = "production_deployment"
    WORKFLOW_TRIGGER = "workflow_trigger"
    CODE_MODIFICATION = "code_modification"
    SYSTEM_CONFIG = "system_config"


class ApprovalRequestCreate(BaseModel):
    agent_id: str = Field(..., min_length=1, max_length=64, description="Requesting agent identity label")
    action_type: ActionType
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=2000)
    payload: Dict[str, Any] = Field(default_factory=dict)


class ApprovalDecision(BaseModel):
    decision: ApprovalStatus = Field(..., description="Only approved or rejected are valid decisions")
    payload_hash: str = Field(..., min_length=64, max_length=64, pattern=r"^[a-f0-9]{64}$")
    reviewer_notes: Optional[str] = Field(None, max_length=1000)


class ApprovalResponse(BaseModel):
    id: str
    agent_id: str
    action_type: ActionType
    title: str
    description: str
    payload: Dict[str, Any]
    payload_hash: str
    status: ApprovalStatus
    requested_at: datetime
    expires_at: datetime
    decided_at: Optional[datetime] = None
    reviewer_id: Optional[str] = None
    reviewer_notes: Optional[str] = None
    consumed_at: Optional[datetime] = None
