"""Tests for the provider-neutral OpenAI-compatible adapter."""
import pytest

from app.providers.base import ChatMessage, MessageRole
from app.providers.openai_compatible import OpenAICompatibleProvider


def test_rejects_non_https_remote_endpoint():
    with pytest.raises(ValueError, match="HTTPS"):
        OpenAICompatibleProvider(
            base_url="http://api.example.com/v1",
            model_name="example-model",
        )


def test_allows_loopback_http_endpoint():
    provider = OpenAICompatibleProvider(
        base_url="http://127.0.0.1:1234/v1/",
        model_name="local-compatible-model",
    )
    assert provider.name == "openai_compatible"
    assert provider.is_mock is False


def test_rejects_invalid_endpoint_and_timeout():
    with pytest.raises(ValueError):
        OpenAICompatibleProvider(base_url="not-a-url", model_name="model")
    with pytest.raises(ValueError):
        OpenAICompatibleProvider(
            base_url="https://api.example.com/v1",
            model_name="model",
            timeout=0,
        )


@pytest.mark.asyncio
async def test_generation_uses_chat_completions_payload(monkeypatch):
    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "choices": [
                    {
                        "message": {"content": "Hello from test provider"},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"total_tokens": 12},
            }

    class FakeAsyncClient:
        def __init__(self, timeout):
            captured["timeout"] = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def post(self, url, headers, json):
            captured.update({"url": url, "headers": headers, "payload": json})
            return FakeResponse()

    monkeypatch.setattr("app.providers.openai_compatible.httpx.AsyncClient", FakeAsyncClient)

    provider = OpenAICompatibleProvider(
        base_url="https://api.example.com/v1",
        model_name="test-model",
        api_key="test-secret",
    )
    result = await provider.generate_chat_response(
        [ChatMessage(role=MessageRole.USER, content="Say hello")],
        temperature=0.2,
        max_tokens=64,
    )

    assert result.content == "Hello from test provider"
    assert result.provider_name == "openai_compatible"
    assert result.model_name == "test-model"
    assert result.tokens_used == 12
    assert captured["url"] == "https://api.example.com/v1/chat/completions"
    assert captured["headers"]["Authorization"] == "Bearer test-secret"
    assert captured["payload"]["messages"] == [{"role": "user", "content": "Say hello"}]
    assert captured["payload"]["max_tokens"] == 64


@pytest.mark.asyncio
async def test_status_checks_models_endpoint(monkeypatch):
    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

    class FakeAsyncClient:
        def __init__(self, timeout):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def get(self, url, headers):
            captured["url"] = url
            return FakeResponse()

    monkeypatch.setattr("app.providers.openai_compatible.httpx.AsyncClient", FakeAsyncClient)
    provider = OpenAICompatibleProvider(
        base_url="https://api.example.com/v1",
        model_name="test-model",
    )
    status = await provider.check_status()

    assert status.is_available is True
    assert captured["url"] == "https://api.example.com/v1/models"
