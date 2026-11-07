"""Personal Agent Implementation."""
from typing import Any, Dict, Optional
from app.agents.orchestrator import orchestrator
from app.core.logging import logger
from app.providers.registry import provider_registry
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import chat_service


class PersonalAgent:
    """Primary conversational agent for personal assistance."""

    def __init__(self, agent_id: str = "personal_agent"):
        self.agent_id = agent_id

    async def handle_prompt(self, user_prompt: str, conversation_id: Optional[str] = None) -> ChatResponse:
        logger.info(f"PersonalAgent '{self.agent_id}' handling prompt")
        orchestrator.log_activity(
            agent_id=self.agent_id,
            action="Process Prompt",
            details=f"Prompt preview: {user_prompt[:50]}...",
            status="completed",
        )
        chat_req = ChatRequest(
            message=user_prompt,
            conversation_id=conversation_id,
        )
        return await chat_service.process_chat(chat_req)


personal_agent = PersonalAgent()
