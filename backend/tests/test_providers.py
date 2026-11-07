"""Test AI Providers and Model Status Non-Blocking Endpoint."""
import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.providers.registry import provider_registry


@pytest.mark.asyncio
async def test_provider_registry_contains_mock_and_ollama():
    mock_prov = provider_registry.get_provider("mock")
    assert mock_prov.is_mock is True
    assert mock_prov.name == "mock"

    ollama_prov = provider_registry.get_provider("ollama")
    assert ollama_prov.is_mock is False
    assert ollama_prov.name == "ollama"

    # Default active must remain 'mock'
    assert provider_registry.active_provider.name == "mock"


@pytest.mark.asyncio
async def test_model_status_endpoint_non_blocking():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/model-status")
        assert res.status_code == 200
        data = res.json()
        assert "target_model" in data
        assert "connectivity" in data
        assert data["active_system_provider"] == "mock"
