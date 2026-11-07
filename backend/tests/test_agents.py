"""Test Agent Registry and Activity Logging."""
import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_list_agents():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/agents")
        assert response.status_code == 200
        agents = response.json()
        assert len(agents) >= 5
        agent_ids = [a["id"] for a in agents]
        assert "personal_agent" in agent_ids
        assert "coding_agent" in agent_ids


@pytest.mark.asyncio
async def test_get_agent_details():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/agents/personal_agent")
        assert response.status_code == 200
        agent = response.json()
        assert agent["name"] == "Aura"
        assert len(agent["capabilities"]) > 0
        assert len(agent["permissions"]) > 0


@pytest.mark.asyncio
async def test_agent_activities():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/agents/activities")
        assert response.status_code == 200
        activities = response.json()
        assert isinstance(activities, list)
        assert len(activities) > 0
