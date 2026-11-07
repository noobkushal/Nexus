"""Tests for Task Scheduling, Reminders, and Daily Briefings Engine."""
import pytest
from httpx import ASGITransport, AsyncClient
from app.agents.graph import agent_graph
from app.main import app
from app.services.briefing_service import briefing_service
from app.tools.filesystem import sandboxed_fs


def test_generate_daily_briefing():
    """Verify daily briefing generation, structure, and disk persistence."""
    result = briefing_service.generate_daily_briefing()

    assert "filename" in result
    assert result["filename"].startswith("daily_briefing_")
    assert result["filename"].endswith(".md")
    assert "content" in result
    assert "# NEXUS Daily Operator Briefing" in result["content"]
    assert "Safety & Human-in-the-Loop Barrier" in result["content"]
    assert "Priority Tasks" in result["content"]

    # Verify physical file existence in sandboxed storage
    content_on_disk = sandboxed_fs.read_text_file(result["path"])
    assert "# NEXUS Daily Operator Briefing" in content_on_disk


def test_get_latest_briefing():
    """Verify retrieving the latest generated briefing."""
    gen = briefing_service.generate_daily_briefing()
    latest = briefing_service.get_latest_briefing()

    assert latest["filename"] == gen["filename"]
    assert "# NEXUS Daily Operator Briefing" in latest["content"]


def test_list_reminders():
    """Verify reminders aggregation across tasks, approvals, and communications."""
    reminders = briefing_service.list_reminders()
    assert isinstance(reminders, list)
    # Check structure of reminders if any exist
    for r in reminders:
        assert "type" in r
        assert "priority" in r
        assert "title" in r


@pytest.mark.asyncio
async def test_briefing_api_endpoints():
    """Verify FastAPI briefing endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Generate on-demand
        post_resp = await client.post("/api/v1/briefings/generate")
        assert post_resp.status_code == 201
        data = post_resp.json()
        assert "filename" in data
        assert "# NEXUS Daily Operator Briefing" in data["content"]

        # Get latest
        get_resp = await client.get("/api/v1/briefings/latest")
        assert get_resp.status_code == 200
        latest_data = get_resp.json()
        assert latest_data["filename"] == data["filename"]

        # Get reminders
        reminders_resp = await client.get("/api/v1/briefings/reminders")
        assert reminders_resp.status_code == 200
        assert isinstance(reminders_resp.json(), list)


@pytest.mark.asyncio
async def test_graph_briefing_routing():
    """Verify state graph routes briefing request to personal_agent and generates briefing."""
    state = await agent_graph.execute(
        user_prompt="Please generate my morning briefing and digest",
        conversation_id="conv-briefing-test",
    )
    assert state.intent == "briefing"
    assert state.target_agent_id == "personal_agent"
    assert "# NEXUS Daily Operator Briefing" in state.response_content
    assert "briefing_path" in state.metadata
    assert any("Aura Engine -> Compiled executive briefing" in s for s in state.steps)
