"""Persistent task API regression tests."""
import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import Session
from app.main import app
from app.core.auth import get_current_user
from app.db.models import UserModel


@pytest.mark.asyncio
async def test_task_lifecycle_persists_in_database(test_database):
    factory, owner = test_database
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/tasks")
        assert response.status_code == 200
        assert response.json()["total"] == 0

        payload = {"title":"Persistent Task","description":"survives service reload","priority":"high","assigned_agent":"coding_agent"}
        created_response = await client.post("/api/v1/tasks", json=payload)
        assert created_response.status_code == 201
        created = created_response.json()
        task_id = created["id"]
        with factory() as verify_db:
            from app.db.models import TaskModel
            assert verify_db.query(TaskModel).filter_by(id=task_id, owner_id=owner.id).count() == 1

        updated = await client.patch(f"/api/v1/tasks/{task_id}", json={"status":"in_progress"})
        assert updated.status_code == 200
        assert updated.json()["status"] == "in_progress"
        assert (await client.get(f"/api/v1/tasks/{task_id}")).status_code == 200
        assert (await client.delete(f"/api/v1/tasks/{task_id}")).status_code == 204
        assert (await client.get(f"/api/v1/tasks/{task_id}")).status_code == 404


@pytest.mark.asyncio
async def test_task_ids_are_owner_scoped(test_database):
    factory, owner = test_database
    with factory() as db:
        other = UserModel(id=str(uuid.uuid4()), username="other-owner", role="owner", is_active=True, token_version=0)
        db.add(other)
        db.commit()
        from app.db.models import TaskModel
        row = TaskModel(id="other-task", owner_id=other.id, title="Private", status="pending", priority="medium")
        db.add(row)
        db.commit()

    original = app.dependency_overrides.get(get_current_user)
    app.dependency_overrides[get_current_user] = lambda: owner
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/tasks/other-task")
            assert response.status_code == 404
    finally:
        if original is None:
            app.dependency_overrides.pop(get_current_user, None)
        else:
            app.dependency_overrides[get_current_user] = original


@pytest.mark.asyncio
async def test_workflow_requires_real_n8n_configuration(monkeypatch):
    from app.core.config import settings
    from app.services.workflow_service import WorkflowService
    monkeypatch.setattr(settings, "N8N_WEBHOOK_URL", None)
    with pytest.raises(RuntimeError, match="n8n is not configured"):
        await WorkflowService().trigger_workflow("daily_briefing")


@pytest.mark.asyncio
async def test_workflow_never_claims_success_when_webhook_fails(monkeypatch, test_database):
    import httpx
    from app.core.config import settings
    from app.services.workflow_service import WorkflowService, ExecutionStatus
    monkeypatch.setattr(settings, "N8N_WEBHOOK_URL", "http://127.0.0.1:5678")

    class FailedClient:
        def __init__(self, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): return None
        async def post(self, url, json):
            request = httpx.Request("POST", url)
            httpx.Response(500, request=request).raise_for_status()

    monkeypatch.setattr(httpx, "AsyncClient", FailedClient)
    factory, owner = test_database
    with factory() as db:
        execution = await WorkflowService().trigger_workflow("daily_briefing", owner_id=owner.id, db=db)
        from app.db.models import WorkflowExecutionModel
        persisted = db.query(WorkflowExecutionModel).filter_by(id=execution.execution_id, owner_id=owner.id).one()
        assert persisted.status == "failed"
    assert execution.status == ExecutionStatus.FAILED
    assert execution.result["message"].startswith("n8n webhook dispatch failed")



@pytest.mark.asyncio
async def test_workflow_success_is_persisted_and_owner_scoped(monkeypatch, test_database):
    import httpx
    from app.core.config import settings
    from app.services.workflow_service import WorkflowService, ExecutionStatus
    from app.db.models import WorkflowExecutionModel

    monkeypatch.setattr(settings, "N8N_WEBHOOK_URL", "http://127.0.0.1:5678")
    class SuccessfulClient:
        def __init__(self, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): return None
        async def post(self, url, json):
            return httpx.Response(200, request=httpx.Request("POST", url))

    monkeypatch.setattr(httpx, "AsyncClient", SuccessfulClient)
    factory, owner = test_database
    with factory() as db:
        service = WorkflowService()
        execution = await service.trigger_workflow("daily_briefing", {"source": "test"}, owner.id, db)
        assert execution.status == ExecutionStatus.SUCCESS
        assert service.list_executions(owner.id, db)[0].execution_id == execution.execution_id
        assert db.query(WorkflowExecutionModel).filter_by(owner_id=owner.id).count() == 1
        other = UserModel(id=str(uuid.uuid4()), username="workflow-other", role="owner", is_active=True, token_version=0)
        db.add(other)
        db.commit()
        assert service.list_executions(other.id, db) == []
