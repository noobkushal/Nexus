"""Chat Service coordinating conversation flow and AI provider routing."""
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional
from app.core.logging import get_audit_logger, logger
from app.providers.base import ChatMessage, MessageRole
from app.providers.registry import provider_registry
from app.schemas.chat import ChatMessageSchema, ChatRequest, ChatResponse

audit_logger = get_audit_logger()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ChatService:
    """In-memory conversation manager and provider coordinator."""

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

    async def process_chat(self, request: ChatRequest) -> ChatResponse:
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

        # Select provider
        provider = provider_registry.get_provider(request.provider)

        # Convert to provider format
        provider_messages = [
            ChatMessage(
                role=MessageRole(msg.role) if msg.role in [r.value for r in MessageRole] else MessageRole.USER,
                content=msg.content,
            )
            for msg in self._conversations[cid]
        ]

        # Async provider generation
        llm_resp = await provider.generate_chat_response(
            messages=provider_messages,
            temperature=request.temperature or 0.7,
        )

        # Record assistant reply
        assistant_msg = ChatMessageSchema(
            role="assistant",
            content=llm_resp.content,
            timestamp=utc_now(),
        )
        self._conversations[cid].append(assistant_msg)

        # Strict safety verification:
        # NEXUS never claims an external action was completed just because LLM suggested it.
        return ChatResponse(
            response=llm_resp.content,
            conversation_id=cid,
            provider=llm_resp.provider_name,
            model=llm_resp.model_name,
            is_mock=llm_resp.is_mock,
            claimed_actions_executed=False,
            timestamp=utc_now(),
            metadata={
                "tokens_used": llm_resp.tokens_used,
                "history_length": len(self._conversations[cid]),
            },
        )


chat_service = ChatService()
