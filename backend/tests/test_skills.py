"""Tests for Skills and Integrations Registry with Least-Privilege Enforcement."""
import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.services.skills_service import (
    SkillInvocationRequest,
    skills_registry,
)


def test_list_skills():
    """Verify default registered skills exist."""
    skills = skills_registry.list_skills()
    assert len(skills) >= 5
    skill_ids = [s.id for s in skills]
    assert "filesystem_read" in skill_ids
    assert "filesystem_write" in skill_ids
    assert "web_research" in skill_ids
    assert "git_checkpoint" in skill_ids


def test_authorized_skill_invocation():
    """Verify agent with declared permission is allowed to invoke skill."""
    req = SkillInvocationRequest(
        skill_id="web_research",
        agent_id="research_agent",  # Scout has 'network:outbound_readonly'
        parameters={"url": "https://docs.nexus.local"},
    )
    resp = skills_registry.invoke_skill(req)

    assert resp.allowed is True
    assert resp.status == "executed"
    assert resp.result is not None


def test_unauthorized_skill_invocation_blocked():
    """Verify agent lacking declared permission is strictly denied (privilege escalation blocked)."""
    # Personal agent (Aura) does not possess 'write:approved_projects'
    req = SkillInvocationRequest(
        skill_id="filesystem_write",
        agent_id="personal_agent",
        parameters={"path": "projects/exploit.py"},
    )
    resp = skills_registry.invoke_skill(req)

    assert resp.allowed is False
    assert resp.status == "permission_denied"
    assert "lacks required permission" in resp.error


@pytest.mark.asyncio
async def test_skills_api_endpoints():
    """Verify Skills API endpoints via FastAPI client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # List skills
        list_resp = await client.get("/api/v1/skills")
        assert list_resp.status_code == 200
        skills_data = list_resp.json()
        assert len(skills_data) >= 5

        # Get specific skill
        get_resp = await client.get("/api/v1/skills/git_checkpoint")
        assert get_resp.status_code == 200
        assert get_resp.json()["id"] == "git_checkpoint"

        # Invoke authorized
        invoke_resp = await client.post(
            "/api/v1/skills/invoke",
            json={
                "skill_id": "git_checkpoint",
                "agent_id": "coding_agent",
                "parameters": {"message": "Test checkpoint"},
            },
        )
        assert invoke_resp.status_code == 200
        assert invoke_resp.json()["allowed"] is True
