"""Test Health Check Endpoints."""
import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_health_check_operational():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "operational"
        assert data["ai_provider"]["is_mock"] is True
        assert data["ai_provider"]["is_available"] is True
        assert data["dependencies"]["ollama_required"] is False
        assert data["dependencies"]["postgres_required"] is False


@pytest.mark.asyncio
async def test_api_v1_health_matches():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "operational"
