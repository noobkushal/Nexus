"""Deterministic Mock AI Provider for Offline / Standalone Operation."""
from typing import Any, List, Optional
from app.providers.base import (
    BaseLLMProvider,
    ChatMessage,
    LLMResponse,
    ProviderStatus,
)


class MockProvider(BaseLLMProvider):
    """Deterministic mock provider that requires zero external models or APIs."""

    def __init__(self, model_name: str = "nexus-mock-engine-v1"):
        self._model_name = model_name

    @property
    def name(self) -> str:
        return "mock"

    @property
    def is_mock(self) -> bool:
        return True

    @property
    def model_name(self) -> str:
        return self._model_name

    async def check_status(self) -> ProviderStatus:
        return ProviderStatus(
            name=self.name,
            is_available=True,
            is_mock=True,
            details={
                "model": self._model_name,
                "mode": "deterministic_mock",
                "notes": "Running in offline standalone mode. No LLM hardware or API key required.",
            },
        )

    async def generate_chat_response(
        self,
        messages: List[ChatMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        last_message = messages[-1].content if messages else "Hello"
        lower_msg = last_message.lower()

        # Deterministic context-aware responses
        if any(w in lower_msg for w in ["status", "health", "system", "state"]):
            content = (
                "[MOCK RESPONSE — NEXUS Foundation]\n"
                "System Status: Operational.\n"
                "- Backend: FastAPI (Active)\n"
                "- AI Provider: Mock Engine (Offline Mode)\n"
                "- Database: In-memory fallback (Ready)\n"
                "- Automation: n8n Interface (Standby)"
            )
        elif any(w in lower_msg for w in ["agent", "agents", "who are you"]):
            content = (
                "[MOCK RESPONSE — NEXUS Assistant]\n"
                "I am NEXUS AI, your personal automation and digital operations assistant.\n"
                "I am currently operating using the deterministic foundation provider."
            )
        elif any(w in lower_msg for w in ["task", "tasks", "schedule", "reminder"]):
            content = (
                "[MOCK RESPONSE — Task Service]\n"
                f"Acknowledged request regarding tasks: '{last_message}'.\n"
                "Your task management module is operational and ready to track work items."
            )
        else:
            content = (
                f"[MOCK RESPONSE] Received prompt: \"{last_message}\".\n"
                "NEXUS AI foundation is running smoothly in deterministic mock mode. "
                "No external LLM or GPU resources were utilized."
            )

        return LLMResponse(
            content=content,
            provider_name=self.name,
            model_name=self._model_name,
            is_mock=True,
            tokens_used=len(content.split()),
            finish_reason="stop",
            raw_response={"mock": True, "prompt_length": len(last_message)},
        )
