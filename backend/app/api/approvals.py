"""Durable approval API endpoints with owner-scoped access."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, require_roles
from app.db.models import UserModel
from app.db.session import get_db
from app.schemas.approval import ApprovalDecision, ApprovalRequestCreate, ApprovalResponse, ApprovalStatus
from app.services.approval_service import approval_service

router = APIRouter(prefix="/api/v1/approvals", tags=["Approvals"])


@router.get("", response_model=List[ApprovalResponse])
async def list_approvals(
    status_filter: Optional[ApprovalStatus] = Query(None, alias="status"),
    user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[ApprovalResponse]:
    return approval_service.list_approvals(db=db, requester_user_id=user.id, status=status_filter)


@router.post("", response_model=ApprovalResponse, status_code=status.HTTP_201_CREATED)
async def submit_approval_request(
    req: ApprovalRequestCreate,
    user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApprovalResponse:
    return approval_service.request_approval(req, requester_user_id=user.id, db=db)


@router.get("/{approval_id}", response_model=ApprovalResponse)
async def get_approval(
    approval_id: str,
    user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApprovalResponse:
    approval = approval_service.get_approval(approval_id, requester_user_id=user.id, db=db)
    if not approval:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval request not found.")
    return approval


@router.post("/{approval_id}/decision", response_model=ApprovalResponse)
async def submit_approval_decision(
    approval_id: str,
    decision: ApprovalDecision,
    reviewer: UserModel = Depends(require_roles("owner")),
    db: Session = Depends(get_db),
) -> ApprovalResponse:
    try:
        updated = approval_service.decide_approval(
            approval_id,
            decision,
            reviewer_user_id=reviewer.id,
            db=db,
        )
    except TimeoutError as exc:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval request not found.")
    return updated
