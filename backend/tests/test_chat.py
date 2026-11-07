"""Test Chat Interactions and Safety Flags."""
import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_chat_mock_response():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {"message": "Hello NEXUS, check system status"}
        response = await client.post("/api/v1/chat", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["is_mock"] is True
        assert data["provider"] == "mock"
        assert data["claimed_actions_executed"] is False
        assert "[MOCK RESPONSE" in data["response"]
        assert "conversation_id" in data


@pytest.mark.asyncio
async def test_chat_validation_error():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Empty message should fail Pydantic validation
        response = await client.post("/api/v1/chat", json={"message": ""})
        assert response.status_code == 422


@pytest.mark.asyncio
async def test_chat_history_retrieval():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # First message
        resp1 = await client.post("/api/v1/chat", json={"message": "First message"})
        cid = resp1.json()["conversation_id"]

        # Retrieve history
        history_resp = await client.get(f"/api/v1/chat/{cid}")
        assert history_resp.status_code == 200
        history = history_resp.json()
        assert len(history) >= 2  # system + user + assistant
