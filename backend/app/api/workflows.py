"""Workflows and Automation API Endpoints."""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.workflow_service import (
    WorkflowDefinition,
    WorkflowExecution,
    workflow_service,
)

router = APIRouter(prefix="/api/v1/workflows", tags=["Workflows"])


class TriggerWorkflowRequest(BaseModel):
    payload: Optional[Dict[str, Any]] = None


@router.get("", response_model=List[WorkflowDefinition])
async def list_workflows() -> List[WorkflowDefinition]:
    """Lists registered automation workflows."""
    return workflow_service.list_workflows()


@router.get("/executions", response_model=List[WorkflowExecution])
async def list_executions() -> List[WorkflowExecution]:
    """Lists recent workflow executions and status logs."""
    return workflow_service.list_executions()


@router.post("/{workflow_id}/trigger", response_model=WorkflowExecution)
async def trigger_workflow(workflow_id: str, req: TriggerWorkflowRequest) -> WorkflowExecution:
    """Triggers an automation workflow (simulated in offline standalone mode)."""
    try:
        return await workflow_service.trigger_workflow(workflow_id, req.payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
