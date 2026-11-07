"""Schemas for Email, Messaging, and Calendar Communications."""
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CommunicationChannel(str, Enum):
    EMAIL = "email"
    LINKEDIN = "linkedin"
    SLACK = "slack"
    CALENDAR = "calendar"


class CommunicationStatus(str, Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    DISPATCHED = "dispatched"
    REJECTED = "rejected"


class PriorityLevel(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


# --- Email Schemas ---
class EmailDraftCreate(BaseModel):
    recipient: str = Field(..., max_length=255)
    subject: str = Field(..., max_length=255)
    body: str = Field(...)
    priority: PriorityLevel = PriorityLevel.NORMAL


class EmailDraft(BaseModel):
    id: str
    sender: str
    recipient: str
    subject: str
    body: str
    status: CommunicationStatus
    priority: PriorityLevel
    approval_id: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)
    dispatched_at: Optional[datetime] = None


# --- Message Schemas ---
class MessageDraftCreate(BaseModel):
    channel: CommunicationChannel
    recipient: str = Field(..., max_length=255)
    content: str = Field(...)


class MessageDraft(BaseModel):
    id: str
    channel: CommunicationChannel
    recipient: str
    content: str
    status: CommunicationStatus
    approval_id: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)
    dispatched_at: Optional[datetime] = None


# --- Calendar Event Schemas ---
class CalendarEventCreate(BaseModel):
    title: str = Field(..., max_length=255)
    description: str = Field(default="")
    start_time: str = Field(..., description="ISO 8601 string or date time")
    end_time: str = Field(..., description="ISO 8601 string or date time")
    attendees: List[str] = Field(default_factory=list)


class CalendarEvent(BaseModel):
    id: str
    title: str
    description: str
    start_time: str
    end_time: str
    attendees: List[str]
    status: CommunicationStatus
    approval_id: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)


# --- Dispatch Response ---
class DispatchResult(BaseModel):
    id: str
    channel: str
    status: CommunicationStatus
    dispatched: bool
    message: str
    audit_logged: bool = True
