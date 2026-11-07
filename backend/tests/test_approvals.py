"""Test Human Approval Gate."""
import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_list_approvals():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/approvals")
        assert res.status_code == 200
        data = res.json()
        assert len(data) >= 2


@pytest.mark.asyncio
async def test_create_and_decide_approval():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create approval request
        req_body = {
            "agent_id": "coding_agent",
            "action_type": "code_modification",
            "title": "Apply Refactored Auth Middleware",
            "description": "Requires human review before modifying auth guards.",
            "payload": {"diff": "+ new_check()"},
        }
        res_create = await client.post("/api/v1/approvals", json=req_body)
        assert res_create.status_code == 201
        created = res_create.json()
        aid = created["id"]
        assert created["status"] == "pending"

        # Decide: approve
        decision_body = {
            "decision": "approved",
            "reviewer_notes": "Reviewed and validated by architect.",
        }
        res_decide = await client.post(f"/api/v1/approvals/{aid}/decision", json=decision_body)
        assert res_decide.status_code == 200
        decided = res_decide.json()
        assert decided["status"] == "approved"
        assert decided["reviewer_notes"] == decision_body["reviewer_notes"]
