"""Optional Ollama Provider for Local Model Execution."""
from typing import Any, List, Optional
from app.core.config import settings
from app.core.logging import logger
from app.providers.base import (
    BaseLLMProvider,
    ChatMessage,
    LLMResponse,
    ProviderStatus,
)
from app.tools.ollama import OllamaClient


class OllamaProvider(BaseLLMProvider):
    """Integrates local Ollama models via asynchronous client."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout: Optional[float] = None,
    ):
        self._model_name = model_name or settings.OLLAMA_MODEL
        self._client = OllamaClient(
            base_url=base_url or settings.OLLAMA_BASE_URL,
            model=self._model_name,
            timeout=timeout or settings.OLLAMA_TIMEOUT_SECONDS,
        )

    @property
    def name(self) -> str:
        return "ollama"

    @property
    def is_mock(self) -> bool:
        return False

    async def check_status(self) -> ProviderStatus:
        info = await self._client.check_connectivity()
        is_avail = info.get("connected", False) and info.get("model_available", False)
        return ProviderStatus(
            name=self.name,
            is_available=is_avail,
            is_mock=False,
            details=info,
            error_message=info.get("error"),
        )

    async def generate_chat_response(
        self,
        messages: List[ChatMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        formatted = [{"role": m.role.value, "content": m.content} for m in messages]
        try:
            raw = await self._client.chat(messages=formatted, temperature=temperature)
            content = raw.get("message", {}).get("content", "")
            return LLMResponse(
                content=content,
                provider_name=self.name,
                model_name=self._model_name,
                is_mock=False,
                tokens_used=raw.get("eval_count"),
                finish_reason="stop",
                raw_response=raw,
            )
        except Exception as exc:
            logger.error(f"Ollama generation failed: {exc}")
            raise RuntimeError(f"Ollama generation failed: {exc}")
