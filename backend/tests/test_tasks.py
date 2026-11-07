"""Test Task Management API."""
import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_list_tasks():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/tasks")
        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data
        assert data["total"] > 0


@pytest.mark.asyncio
async def test_create_and_update_task():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create
        new_task = {
            "title": "Automated Test Task",
            "description": "Testing lifecycle from pytest",
            "priority": "high",
            "assigned_agent": "coding_agent",
        }
        res_create = await client.post("/api/v1/tasks", json=new_task)
        assert res_create.status_code == 201
        created = res_create.json()
        tid = created["id"]
        assert created["title"] == new_task["title"]
        assert created["status"] == "pending"

        # Update
        res_update = await client.patch(f"/api/v1/tasks/{tid}", json={"status": "in_progress"})
        assert res_update.status_code == 200
        updated = res_update.json()
        assert updated["status"] == "in_progress"

        # Delete
        res_del = await client.delete(f"/api/v1/tasks/{tid}")
        assert res_del.status_code == 204

        # Verify not found
        res_get = await client.get(f"/api/v1/tasks/{tid}")
        assert res_get.status_code == 404
