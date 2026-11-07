"""AI Provider Registry."""
from typing import Dict, List, Optional
from app.core.config import settings
from app.core.logging import logger
from app.providers.base import BaseLLMProvider, ProviderStatus
from app.providers.mock_provider import MockProvider
from app.providers.ollama_provider import OllamaProvider


class ProviderRegistry:
    """Registry maintaining active and optional AI model providers."""

    def __init__(self):
        self._providers: Dict[str, BaseLLMProvider] = {}
        # Always register the deterministic mock provider first
        self.register_provider(MockProvider())
        # Register optional Ollama provider (does not execute or block at startup)
        self.register_provider(OllamaProvider())
        # Default active provider is always 'mock' for standalone safety
        self._active_provider_name: str = settings.DEFAULT_PROVIDER if settings.DEFAULT_PROVIDER in ["mock"] else "mock"

    def register_provider(self, provider: BaseLLMProvider) -> None:
        """Registers a new provider."""
        self._providers[provider.name] = provider
        logger.info(f"Registered AI provider: {provider.name} (is_mock={provider.is_mock})")

    def get_provider(self, name: Optional[str] = None) -> BaseLLMProvider:
        """Retrieves a provider by name, or falls back to active provider or mock."""
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
                status = await provider.check_status()
                statuses.append(status)
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


# Global singleton provider registry
provider_registry = ProviderRegistry()
