"""OpenAI-compatible chat-completions provider.

Works with hosted APIs and self-hosted OpenAI-compatible gateways. Ollama is
not required; a compatible server is configured explicitly by the operator.
"""
from typing import Any, List, Optional
from urllib.parse import urlsplit

import httpx

from app.providers.base import (
    BaseLLMProvider,
    ChatMessage,
    LLMResponse,
    ProviderStatus,
)


class OpenAICompatibleProvider(BaseLLMProvider):
    def __init__(
        self,
        base_url: str,
        model_name: str,
        api_key: Optional[str] = None,
        timeout: float = 45.0,
        provider_name: str = "openai_compatible",
    ):
        parsed = urlsplit(base_url)
        if parsed.scheme not in ("https", "http") or not parsed.netloc:
            raise ValueError("Provider base_url must be an absolute HTTP(S) URL.")
        if parsed.scheme != "https" and parsed.hostname not in ("localhost", "127.0.0.1", "::1"):
            raise ValueError("Non-local provider endpoints must use HTTPS.")
        if not model_name.strip():
            raise ValueError("Provider model_name cannot be empty.")
        if timeout <= 0:
            raise ValueError("Provider timeout must be positive.")

        self._base_url = base_url.rstrip("/")
        self._model_name = model_name
        self._api_key = api_key
        self._timeout = timeout
        self._name = provider_name

    @property
    def name(self) -> str:
        return self._name

    @property
    def is_mock(self) -> bool:
        return False

    @property
    def model_name(self) -> str:
        return self._model_name

    def _headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return headers

    async def check_status(self) -> ProviderStatus:
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(
                    f"{self._base_url}/models",
                    headers=self._headers(),
                )
                response.raise_for_status()
            return ProviderStatus(
                name=self.name,
                is_available=True,
                is_mock=False,
                details={"model": self._model_name, "endpoint_reachable": True},
            )
        except (httpx.HTTPError, ValueError) as exc:
            return ProviderStatus(
                name=self.name,
                is_available=False,
                is_mock=False,
                details={"model": self._model_name},
                error_message=str(exc),
            )

    async def generate_chat_response(
        self,
        messages: List[ChatMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        payload: dict[str, Any] = {
            "model": self._model_name,
            "messages": [
                {"role": message.role.value, "content": message.content}
                for message in messages
            ],
            "temperature": temperature,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    f"{self._base_url}/chat/completions",
                    headers=self._headers(),
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
            choices = data.get("choices") or []
            if not choices or not isinstance(choices[0].get("message"), dict):
                raise RuntimeError("Provider returned no chat completion choice.")
            content = choices[0]["message"].get("content")
            if not isinstance(content, str):
                raise RuntimeError("Provider returned a non-text completion.")
            usage = data.get("usage") or {}
            return LLMResponse(
                content=content,
                provider_name=self.name,
                model_name=self._model_name,
                is_mock=False,
                tokens_used=usage.get("total_tokens"),
                finish_reason=choices[0].get("finish_reason") or "stop",
            )
        except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
            raise RuntimeError(f"{self.name} generation failed: {exc}") from exc
