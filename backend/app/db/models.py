"""SQLAlchemy Relational Database Models for NEXUS AI."""
from datetime import datetime, timezone
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.db.session import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class UserModel(Base):
    """User account model for local or multi-user deployment."""
    __tablename__ = "users"

    id = Column(String(64), primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=True)
    role = Column(String(50), default="operator", nullable=False)
    password_hash = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    token_version = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class ConversationModel(Base):
    """Conversational session model tracking multi-turn interactions."""
    __tablename__ = "conversations"

    id = Column(String(64), primary_key=True, index=True)
    title = Column(String(255), default="New Conversation", nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    messages = relationship("MessageModel", back_populates="conversation", cascade="all, delete-orphan")


class MessageModel(Base):
    """Message turns inside a conversation session."""
    __tablename__ = "messages"

    id = Column(String(64), primary_key=True, index=True)
    conversation_id = Column(String(64), ForeignKey("conversations.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # system, user, assistant, tool
    content = Column(Text, nullable=False)
    intent = Column(String(50), nullable=True)
    routed_agent = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    conversation = relationship("ConversationModel", back_populates="messages")


class TaskModel(Base):
    """Persistent task tracker for operator work items."""
    __tablename__ = "tasks"

    id = Column(String(64), primary_key=True, index=True)
    owner_id = Column(String(64), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="pending", nullable=False)  # pending, in_progress, completed, failed
    priority = Column(String(20), default="medium", nullable=False)  # low, medium, high, critical
    assigned_agent = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


class AgentModel(Base):
    """Registered autonomous agents in the multi-agent roster."""
    __tablename__ = "agents"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    role = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(50), default="idle", nullable=False)
    permissions = Column(Text, nullable=False)  # JSON or comma-separated list of scopes
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class AgentActivityModel(Base):
    """Historical audit log of agent operations."""
    __tablename__ = "agent_activities"

    id = Column(String(64), primary_key=True, index=True)
    agent_id = Column(String(64), nullable=False, index=True)
    action = Column(String(100), nullable=False)
    details = Column(Text, nullable=False)
    status = Column(String(50), default="completed", nullable=False)
    timestamp = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)


class MemoryRecordModel(Base):
    """Long-term personalized profile and semantic memory record."""
    __tablename__ = "memory_records"

    id = Column(String(64), primary_key=True, index=True)
    category = Column(String(50), default="profile", nullable=False, index=True)
    key = Column(String(150), nullable=False, index=True)
    content = Column(Text, nullable=False)
    importance = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class IntegrationSettingModel(Base):
    """Encrypted or plain integration configuration records."""
    __tablename__ = "integration_settings"

    id = Column(String(64), primary_key=True, index=True)
    key = Column(String(100), unique=True, index=True, nullable=False)
    value_json = Column(Text, nullable=False)
    is_secret = Column(Boolean, default=False, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


class ApprovalModel(Base):
    """Durable, payload-bound human approval request."""
    __tablename__ = "approval_requests"

    id = Column(String(64), primary_key=True, index=True)
    requester_user_id = Column(String(64), ForeignKey("users.id"), nullable=False, index=True)
    agent_id = Column(String(64), nullable=False)
    action_type = Column(String(64), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    payload_json = Column(Text, nullable=False)
    payload_hash = Column(String(64), nullable=False, index=True)
    status = Column(String(20), default="pending", nullable=False, index=True)
    requested_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    reviewer_id = Column(String(64), ForeignKey("users.id"), nullable=True)
    decided_at = Column(DateTime(timezone=True), nullable=True)
    reviewer_notes = Column(Text, nullable=True)
    consumed_at = Column(DateTime(timezone=True), nullable=True)


class AuditEventModel(Base):
    """Append-only security and approval audit event."""
    __tablename__ = "audit_events"

    id = Column(String(64), primary_key=True, index=True)
    actor_user_id = Column(String(64), nullable=True, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    resource_id = Column(String(64), nullable=True, index=True)
    payload_hash = Column(String(64), nullable=True)
    details_json = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)


class WorkflowExecutionModel(Base):
    """Durable owner-scoped record of an n8n webhook dispatch."""
    __tablename__ = "workflow_executions"

    id = Column(String(64), primary_key=True, index=True)
    owner_id = Column(String(64), ForeignKey("users.id"), nullable=False, index=True)
    workflow_id = Column(String(100), nullable=False, index=True)
    status = Column(String(20), nullable=False, index=True)
    triggered_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    payload_json = Column(Text, nullable=False, default="{}")
    result_json = Column(Text, nullable=True)
