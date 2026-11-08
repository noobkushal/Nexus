"""Chat Service coordinating conversation flow and AI provider routing."""
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.agents.graph import agent_graph
from app.core.logging import get_audit_logger, logger
from app.providers.base import ChatMessage, MessageRole
from app.providers.registry import provider_registry
from app.schemas.chat import ChatMessageSchema, ChatRequest, ChatResponse

audit_logger = get_audit_logger()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ChatService:
    """In-memory conversation manager and provider coordinator with state graph execution."""

    def __init__(self):
        # Maps conversation_id -> List[ChatMessageSchema]
        self._conversations: Dict[str, List[ChatMessageSchema]] = {}

    def get_or_create_conversation(self, conversation_id: Optional[str] = None) -> str:
        cid = conversation_id or str(uuid.uuid4())
        if cid not in self._conversations:
            self._conversations[cid] = [
                ChatMessageSchema(
                    role="system",
                    content=(
                        "You are NEXUS AI, a modular, local-first personal AI automation platform. "
                        "You operate under strict deterministic safety rules. You must never claim "
                        "an external action was executed unless verified."
                    ),
                    timestamp=utc_now(),
                )
            ]
        return cid

    def get_conversation_history(self, conversation_id: str) -> List[ChatMessageSchema]:
        return self._conversations.get(conversation_id, [])

    async def process_chat(self, request: ChatRequest, owner_user_id: str, db: Session) -> ChatResponse:
        cid = self.get_or_create_conversation(request.conversation_id)

        # Record user message
        user_msg = ChatMessageSchema(
            role="user",
            content=request.message,
            timestamp=utc_now(),
        )
        self._conversations[cid].append(user_msg)

        # Audit log user request
        audit_logger.info(f"Chat request | conv={cid} | user_msg_len={len(request.message)}")

        # Execute Multi-Agent State Graph
        graph_result = await agent_graph.execute(
            user_prompt=request.message,
            conversation_id=cid,
            owner_user_id=owner_user_id,
            db=db,
        )

        # Record assistant reply
        assistant_msg = ChatMessageSchema(
            role="assistant",
            content=graph_result.response_content,
            timestamp=utc_now(),
        )
        self._conversations[cid].append(assistant_msg)

        provider = provider_registry.active_provider

        # Strict safety verification:
        # NEXUS never claims an external action was completed just because LLM suggested it.
        return ChatResponse(
            response=graph_result.response_content,
            conversation_id=cid,
            provider=provider.name,
            model=graph_result.metadata.get("model", "nexus-mock-engine-v1"),
            is_mock=provider.is_mock,
            claimed_actions_executed=False,
            timestamp=utc_now(),
            intent=graph_result.intent,
            routed_agent=graph_result.target_agent_id,
            requires_approval=graph_result.requires_approval,
            approval_id=graph_result.approval_id,
            steps=graph_result.steps,
            metadata={
                "history_length": len(self._conversations[cid]),
            },
        )


chat_service = ChatService()
