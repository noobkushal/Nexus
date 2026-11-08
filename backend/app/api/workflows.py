"""Workflow automation API backed by persistent n8n execution records."""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.db.models import UserModel
from app.db.session import get_db
from app.services.workflow_service import WorkflowDefinition, WorkflowExecution, workflow_service

router = APIRouter(prefix="/api/v1/workflows", tags=["Workflows"])


class TriggerWorkflowRequest(BaseModel):
    payload: Optional[Dict[str, Any]] = Field(default=None)


@router.get("", response_model=List[WorkflowDefinition])
async def list_workflows() -> List[WorkflowDefinition]:
    return workflow_service.list_workflows()


@router.get("/executions", response_model=List[WorkflowExecution])
async def list_executions(user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)) -> List[WorkflowExecution]:
    return workflow_service.list_executions(user.id, db)


@router.post("/{workflow_id}/trigger", response_model=WorkflowExecution)
async def trigger_workflow(
    workflow_id: str, req: TriggerWorkflowRequest,
    user: UserModel = Depends(get_current_user), db: Session = Depends(get_db),
) -> WorkflowExecution:
    try:
        return await workflow_service.trigger_workflow(workflow_id, req.payload, user.id, db)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
