"""Action Approval API Endpoints (Human-in-the-Loop Barrier)."""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from app.schemas.approval import (
    ApprovalDecision,
    ApprovalRequestCreate,
    ApprovalResponse,
    ApprovalStatus,
)
from app.services.approval_service import approval_service

router = APIRouter(prefix="/api/v1/approvals", tags=["Approvals"])


@router.get("", response_model=List[ApprovalResponse])
async def list_approvals(
    status: Optional[ApprovalStatus] = Query(None, description="Filter by approval status"),
) -> List[ApprovalResponse]:
    """Lists all consequential action proposals and review states."""
    return approval_service.list_approvals(status=status)


@router.post("", response_model=ApprovalResponse, status_code=status.HTTP_201_CREATED)
async def submit_approval_request(req: ApprovalRequestCreate) -> ApprovalResponse:
    """Submits a new action proposal requiring human sign-off."""
    return approval_service.request_approval(req)


@router.get("/{approval_id}", response_model=ApprovalResponse)
async def get_approval(approval_id: str) -> ApprovalResponse:
    """Retrieves specific approval request by ID."""
    appr = approval_service.get_approval(approval_id)
    if not appr:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Approval request '{approval_id}' not found.",
        )
    return appr


@router.post("/{approval_id}/decision", response_model=ApprovalResponse)
async def submit_approval_decision(approval_id: str, decision: ApprovalDecision) -> ApprovalResponse:
    """Submits human review decision (approved or rejected)."""
    updated = approval_service.decide_approval(approval_id, decision)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Approval request '{approval_id}' not found.",
        )
    return updated
