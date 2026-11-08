"""Durable approval service with expiry and atomic, payload-bound decisions."""
import hashlib
import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from app.db.models import ApprovalModel, AuditEventModel
from app.schemas.approval import (
    ApprovalDecision,
    ApprovalRequestCreate,
    ApprovalResponse,
    ApprovalStatus,
)

APPROVAL_TTL_MINUTES = 15


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def canonical_payload(payload: dict) -> tuple[str, str]:
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    return serialized, hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _audit(db: Session, actor_user_id: Optional[str], event_type: str, resource_id: str, payload_hash: Optional[str], details: dict):
    db.add(AuditEventModel(
        id=str(uuid.uuid4()),
        actor_user_id=actor_user_id,
        event_type=event_type,
        resource_id=resource_id,
        payload_hash=payload_hash,
        details_json=json.dumps(details, sort_keys=True, separators=(",", ":")),
        created_at=utc_now(),
    ))


def _response(row: ApprovalModel) -> ApprovalResponse:
    return ApprovalResponse(
        id=row.id,
        agent_id=row.agent_id,
        action_type=row.action_type,
        title=row.title,
        description=row.description,
        payload=json.loads(row.payload_json),
        payload_hash=row.payload_hash,
        status=row.status,
        requested_at=row.requested_at,
        expires_at=row.expires_at,
        decided_at=row.decided_at,
        reviewer_id=row.reviewer_id,
        reviewer_notes=row.reviewer_notes,
        consumed_at=row.consumed_at,
    )


class ApprovalService:
    """Persists approval proposals and enforces one-time human decisions."""

    def list_approvals(self, db: Session, requester_user_id: str, status: Optional[ApprovalStatus] = None) -> List[ApprovalResponse]:
        now = utc_now()
        db.query(ApprovalModel).filter(
            ApprovalModel.requester_user_id == requester_user_id,
            ApprovalModel.status == ApprovalStatus.PENDING.value,
            ApprovalModel.expires_at <= now,
        ).update({"status": ApprovalStatus.EXPIRED.value}, synchronize_session=False)
        db.commit()
        query = db.query(ApprovalModel).filter(ApprovalModel.requester_user_id == requester_user_id)
        if status:
            query = query.filter(ApprovalModel.status == status.value)
        return [_response(row) for row in query.order_by(ApprovalModel.requested_at.desc()).all()]

    def get_approval(self, approval_id: str, requester_user_id: str, db: Session) -> Optional[ApprovalResponse]:
        row = db.query(ApprovalModel).filter(ApprovalModel.id == approval_id, ApprovalModel.requester_user_id == requester_user_id).first()
        if not row:
            return None
        if row.status == ApprovalStatus.PENDING.value:
            db.query(ApprovalModel).filter(ApprovalModel.id == approval_id, ApprovalModel.requester_user_id == requester_user_id, ApprovalModel.status == ApprovalStatus.PENDING.value, ApprovalModel.expires_at <= utc_now()).update({"status": ApprovalStatus.EXPIRED.value}, synchronize_session=False)
            db.commit()
            db.refresh(row)
        return _response(row)

    def request_approval(self, req: ApprovalRequestCreate, requester_user_id: str, db: Session) -> ApprovalResponse:
        payload_json, payload_hash = canonical_payload(req.payload)
        now = utc_now()
        row = ApprovalModel(
            id=str(uuid.uuid4()),
            requester_user_id=requester_user_id,
            agent_id=req.agent_id,
            action_type=req.action_type.value,
            title=req.title,
            description=req.description,
            payload_json=payload_json,
            payload_hash=payload_hash,
            status=ApprovalStatus.PENDING.value,
            requested_at=now,
            expires_at=now + timedelta(minutes=APPROVAL_TTL_MINUTES),
        )
        db.add(row)
        _audit(db, requester_user_id, "approval.requested", row.id, payload_hash, {"agent_id": req.agent_id, "action_type": req.action_type.value})
        db.commit()
        db.refresh(row)
        return _response(row)

    def decide_approval(self, approval_id: str, decision: ApprovalDecision, reviewer_user_id: str, db: Session) -> Optional[ApprovalResponse]:
        if decision.decision not in (ApprovalStatus.APPROVED, ApprovalStatus.REJECTED):
            raise ValueError("A decision must be approved or rejected.")
        now = utc_now()

        # Expire first, then perform a conditional update. The WHERE clause makes
        # simultaneous approvals/replays race-safe across workers and DB connections.
        db.query(ApprovalModel).filter(
            ApprovalModel.id == approval_id,
            ApprovalModel.requester_user_id == reviewer_user_id,
            ApprovalModel.status == ApprovalStatus.PENDING.value,
            ApprovalModel.expires_at <= now,
        ).update({"status": ApprovalStatus.EXPIRED.value}, synchronize_session=False)
        changed = db.query(ApprovalModel).filter(
            ApprovalModel.id == approval_id,
            ApprovalModel.requester_user_id == reviewer_user_id,
            ApprovalModel.status == ApprovalStatus.PENDING.value,
            ApprovalModel.expires_at > now,
            ApprovalModel.payload_hash == decision.payload_hash,
        ).update({
            "status": decision.decision.value,
            "reviewer_id": reviewer_user_id,
            "decided_at": now,
            "reviewer_notes": decision.reviewer_notes,
        }, synchronize_session=False)

        row = db.query(ApprovalModel).filter(ApprovalModel.id == approval_id, ApprovalModel.requester_user_id == reviewer_user_id).first()
        if not row:
            db.rollback()
            return None
        if changed != 1:
            db.commit()
            if row.payload_hash != decision.payload_hash:
                raise ValueError("Approval payload has changed; review the current request.")
            if row.status == ApprovalStatus.EXPIRED.value:
                raise TimeoutError("Approval request has expired.")
            raise ValueError("Approval is no longer pending and cannot be decided again.")

        _audit(db, reviewer_user_id, "approval.decided", row.id, row.payload_hash, {"decision": decision.decision.value})
        db.commit()
        db.refresh(row)
        return _response(row)


approval_service = ApprovalService()
