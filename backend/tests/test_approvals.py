"""Persistence, owner isolation, expiry, and replay tests for approvals."""
from datetime import datetime, timedelta, timezone
import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base
from app.db import models  # noqa: F401
from app.db.models import UserModel, ApprovalModel, AuditEventModel
from app.schemas.approval import ActionType, ApprovalDecision, ApprovalRequestCreate, ApprovalStatus
from app.services.approval_service import ApprovalService


@pytest.fixture
def approval_db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    factory = sessionmaker(bind=engine)
    db = factory()
    owner_id = str(uuid.uuid4())
    db.add(UserModel(id=owner_id, username="approval-owner", role="owner", password_hash=None, is_active=True, token_version=0))
    db.commit()
    yield db, factory, owner_id
    db.close()
    engine.dispose()


def make_request():
    return ApprovalRequestCreate(
        agent_id="career_agent",
        action_type=ActionType.EXTERNAL_MESSAGE,
        title="Send recruiter outreach",
        description="Send the reviewed recruiter message.",
        payload={"recipient": "recruiter@example.com", "body": "Hello"},
    )


def test_approval_persists_with_canonical_payload_digest(approval_db):
    db, factory, owner_id = approval_db
    created = ApprovalService().request_approval(make_request(), owner_id, db)
    db.close()
    reopened = factory()
    loaded = ApprovalService().get_approval(created.id, owner_id, reopened)
    assert loaded is not None
    assert loaded.status == ApprovalStatus.PENDING
    assert loaded.payload == {"body": "Hello", "recipient": "recruiter@example.com"}
    assert len(loaded.payload_hash) == 64
    assert reopened.query(AuditEventModel).filter_by(event_type="approval.requested").count() == 1
    reopened.close()


def test_approval_decision_is_bound_to_payload_and_single_use(approval_db):
    db, _, owner_id = approval_db
    service = ApprovalService()
    created = service.request_approval(make_request(), owner_id, db)
    wrong = ApprovalDecision(decision=ApprovalStatus.APPROVED, payload_hash="0" * 64)
    with pytest.raises(ValueError, match="payload"):
        service.decide_approval(created.id, wrong, owner_id, db)
    valid = ApprovalDecision(decision=ApprovalStatus.APPROVED, payload_hash=created.payload_hash)
    decided = service.decide_approval(created.id, valid, owner_id, db)
    assert decided.status == ApprovalStatus.APPROVED
    with pytest.raises(ValueError, match="no longer pending"):
        service.decide_approval(created.id, valid, owner_id, db)


def test_approval_is_owner_scoped(approval_db):
    db, _, owner_id = approval_db
    service = ApprovalService()
    created = service.request_approval(make_request(), owner_id, db)
    assert service.get_approval(created.id, str(uuid.uuid4()), db) is None
    assert service.list_approvals(db, requester_user_id=str(uuid.uuid4())) == []


def test_expired_approval_cannot_be_approved(approval_db):
    db, _, owner_id = approval_db
    service = ApprovalService()
    created = service.request_approval(make_request(), owner_id, db)
    row = db.query(ApprovalModel).filter_by(id=created.id).one()
    row.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    db.commit()
    decision = ApprovalDecision(decision=ApprovalStatus.APPROVED, payload_hash=created.payload_hash)
    with pytest.raises(TimeoutError, match="expired"):
        service.decide_approval(created.id, decision, owner_id, db)
    current = service.get_approval(created.id, owner_id, db)
    assert current.status == ApprovalStatus.EXPIRED


def test_approved_request_can_be_consumed_only_once(approval_db):
    db, _, owner_id = approval_db
    service = ApprovalService()
    created = service.request_approval(make_request(), owner_id, db)
    approved = service.decide_approval(
        created.id,
        ApprovalDecision(decision=ApprovalStatus.APPROVED, payload_hash=created.payload_hash),
        owner_id,
        db,
    )
    assert approved.status == ApprovalStatus.APPROVED
    consumed = service.consume_approval(created.id, created.payload_hash, owner_id, db)
    assert consumed.status == ApprovalStatus.CONSUMED
    assert consumed.consumed_at is not None
    assert service.consume_approval(created.id, created.payload_hash, owner_id, db) is None


def test_owner_can_decide_operator_created_approval(approval_db):
    db, _, owner_id = approval_db
    operator_id = str(uuid.uuid4())
    db.add(UserModel(id=operator_id, username="approval-operator", role="operator", is_active=True, token_version=0))
    db.commit()

    service = ApprovalService()
    created = service.request_approval(make_request(), operator_id, db)
    decision = ApprovalDecision(decision=ApprovalStatus.APPROVED, payload_hash=created.payload_hash)
    decided = service.decide_approval(created.id, decision, owner_id, db)

    assert decided.status == ApprovalStatus.APPROVED
    assert decided.reviewer_id == owner_id
    assert decided.id == created.id
