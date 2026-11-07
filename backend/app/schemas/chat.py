"""Schemas for Chat interactions."""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ChatMessageSchema(BaseModel):
    role: str = Field(..., description="Role of the author: system, user, assistant")
    content: str = Field(..., description="Content of the message")
    timestamp: datetime = Field(default_factory=utc_now)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000, description="User prompt message")
    conversation_id: Optional[str] = Field(None, description="Optional conversation UUID")
    provider: Optional[str] = Field(None, description="Specific provider override (e.g. 'mock')")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0)


class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    provider: str
    model: str
    is_mock: bool
    claimed_actions_executed: bool = Field(
        False,
        description="Strict safety flag: indicates whether consequential external actions were executed",
    )
    timestamp: datetime = Field(default_factory=utc_now)
    intent: Optional[str] = Field(None, description="Classified intent from agent state graph")
    routed_agent: Optional[str] = Field(None, description="Target agent routed by graph")
    requires_approval: bool = Field(False, description="True if action was gated for human approval")
    approval_id: Optional[str] = Field(None, description="ID of generated approval request")
    steps: List[str] = Field(default_factory=list, description="Execution step trace through state graph")
    metadata: Dict[str, Any] = Field(default_factory=dict)
