"""AI Provider Registry."""
from typing import Dict, List, Optional
from app.core.config import settings
from app.core.logging import logger
from app.providers.base import BaseLLMProvider, ProviderStatus
from app.providers.mock_provider import MockProvider
from app.providers.ollama_provider import OllamaProvider
from app.providers.openai_compatible import OpenAICompatibleProvider


class ProviderRegistry:
    """Registry maintaining active and optional AI model providers."""

    def __init__(self):
        self._providers: Dict[str, BaseLLMProvider] = {}
        self.register_provider(MockProvider())
        self.register_provider(OllamaProvider())

        # Register a real OpenAI-compatible endpoint only when explicitly configured.
        if settings.OPENAI_COMPAT_BASE_URL and settings.OPENAI_COMPAT_MODEL:
            try:
                self.register_provider(
                    OpenAICompatibleProvider(
                        base_url=settings.OPENAI_COMPAT_BASE_URL,
                        model_name=settings.OPENAI_COMPAT_MODEL,
                        api_key=settings.OPENAI_COMPAT_API_KEY,
                        timeout=settings.OPENAI_COMPAT_TIMEOUT_SECONDS,
                    )
                )
            except ValueError as exc:
                logger.error(f"OpenAI-compatible provider configuration rejected: {exc}")

        requested_default = settings.DEFAULT_PROVIDER
        self._active_provider_name = (
            requested_default if requested_default in self._providers else "mock"
        )
        if requested_default != self._active_provider_name:
            logger.warning(
                f"Configured provider '{requested_default}' is unavailable; using safe mock provider."
            )

    def register_provider(self, provider: BaseLLMProvider) -> None:
        """Registers a provider under its unique name."""
        self._providers[provider.name] = provider
        logger.info(f"Registered AI provider: {provider.name} (is_mock={provider.is_mock})")

    def get_provider(self, name: Optional[str] = None) -> BaseLLMProvider:
        """Retrieves a provider; unknown names fail closed to mock."""
        target_name = name or self._active_provider_name
        if target_name in self._providers:
            return self._providers[target_name]
        logger.warning(f"Provider '{target_name}' not found. Falling back to 'mock'.")
        return self._providers["mock"]

    def set_active_provider(self, name: str) -> bool:
        """Sets the active default provider."""
        if name in self._providers:
            self._active_provider_name = name
            logger.info(f"Active AI provider changed to: {name}")
            return True
        logger.error(f"Cannot set active provider: '{name}' not found.")
        return False

    @property
    def active_provider(self) -> BaseLLMProvider:
        return self.get_provider(self._active_provider_name)

    async def list_statuses(self) -> List[ProviderStatus]:
        """Checks status across all registered providers."""
        statuses: List[ProviderStatus] = []
        for provider in self._providers.values():
            try:
                statuses.append(await provider.check_status())
            except Exception as exc:
                statuses.append(
                    ProviderStatus(
                        name=provider.name,
                        is_available=False,
                        is_mock=provider.is_mock,
                        error_message=str(exc),
                    )
                )
        return statuses


provider_registry = ProviderRegistry()
