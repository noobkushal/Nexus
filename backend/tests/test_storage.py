"""Test Sandboxed Storage and Git Safety Endpoints."""
import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_list_compartments():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/storage/compartments")
        assert res.status_code == 200
        compartments = res.json()
        assert "documents" in compartments
        assert "profile" in compartments


@pytest.mark.asyncio
async def test_list_files_and_read():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # List files in documents
        res = await client.get("/api/v1/storage/files?compartment=documents")
        assert res.status_code == 200
        files = res.json()
        assert len(files) >= 1
        path = files[0]["path"]

        # Read file
        res_read = await client.get(f"/api/v1/storage/read?path={path}")
        assert res_read.status_code == 200
        data = res_read.json()
        assert "content" in data
        assert len(data["content"]) > 0


@pytest.mark.asyncio
async def test_write_and_delete_file():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Write test file
        test_path = "generated/pytest_demo.txt"
        res_write = await client.post(
            "/api/v1/storage/write",
            json={"path": test_path, "content": "Sandbox test payload 12345"},
        )
        assert res_write.status_code == 200

        # Read back
        res_read = await client.get(f"/api/v1/storage/read?path={test_path}")
        assert res_read.status_code == 200
        assert res_read.json()["content"] == "Sandbox test payload 12345"

        # Delete
        res_del = await client.delete(f"/api/v1/storage/delete?path={test_path}")
        assert res_del.status_code == 200

        # Verify 404
        res_after = await client.get(f"/api/v1/storage/read?path={test_path}")
        assert res_after.status_code == 404


@pytest.mark.asyncio
async def test_storage_path_escape_blocked():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Attempt to read file outside sandboxed storage
        res = await client.get("/api/v1/storage/read?path=../../windows/win.ini")
        assert res.status_code == 403
        assert "Access denied" in res.json()["detail"]


@pytest.mark.asyncio
async def test_git_status_and_checkpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res_status = await client.get("/api/v1/storage/git/status")
        assert res_status.status_code == 200
        data = res_status.json()
        assert data["is_git_repo"] is True
        assert "current_branch" in data
        assert "latest_commit" in data

        res_checkpoints = await client.get("/api/v1/storage/git/checkpoints?limit=3")
        assert res_checkpoints.status_code == 200
        commits = res_checkpoints.json()
        assert len(commits) >= 1
