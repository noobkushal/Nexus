"""Provider-Independent AI Interface."""
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ChatMessage(BaseModel):
    role: MessageRole
    content: str
    name: Optional[str] = None


class ProviderStatus(BaseModel):
    name: str
    is_available: bool
    is_mock: bool
    details: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None


class LLMResponse(BaseModel):
    content: str
    provider_name: str
    model_name: str
    is_mock: bool = False
    tokens_used: Optional[int] = None
    finish_reason: str = "stop"
    raw_response: Optional[Dict[str, Any]] = None


class BaseLLMProvider(ABC):
    """Abstract Base Class for all AI model providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider unique identifier."""
        pass

    @property
    @abstractmethod
    def is_mock(self) -> bool:
        """True if the provider produces synthetic/simulated outputs."""
        pass

    @abstractmethod
    async def check_status(self) -> ProviderStatus:
        """Checks connectivity and operational readiness."""
        pass

    @abstractmethod
    async def generate_chat_response(
        self,
        messages: List[ChatMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generates a conversational response asynchronously."""
        pass
