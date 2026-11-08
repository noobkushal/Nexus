"""Tests for communication workflows using durable approval records."""
from datetime import datetime, timezone
import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base
from app.db import models  # noqa: F401
from app.db.models import UserModel
from app.schemas.approval import ApprovalDecision, ApprovalStatus
from app.schemas.communication import (
    CalendarEventCreate,
    CommunicationChannel,
    CommunicationStatus,
    EmailDraftCreate,
    MessageDraftCreate,
    PriorityLevel,
)
from app.services.approval_service import approval_service
from app.services.communication_service import CommunicationSecurityError, CommunicationService


@pytest.fixture
def comm_service():
    return CommunicationService()


@pytest.fixture
def approval_context():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    db = sessionmaker(bind=engine)()
    owner_id = str(uuid.uuid4())
    db.add(UserModel(id=owner_id, username="comm-owner", role="owner", is_active=True, token_version=0))
    db.commit()
    yield db, owner_id
    db.close()
    engine.dispose()


def test_list_initial_communications(comm_service):
    emails = comm_service.list_emails()
    assert len(emails) >= 1
    assert emails[0].subject.startswith("Senior AI Systems Architect")
    messages = comm_service.list_messages()
    assert len(messages) >= 1
    assert messages[0].channel == CommunicationChannel.LINKEDIN
    calendar = comm_service.list_calendar_events()
    assert len(calendar) >= 1
    assert "Architecture Review" in calendar[0].title


def test_create_email_draft(comm_service):
    draft = EmailDraftCreate(recipient="partner@company.com", subject="Collaboration on Local AI Edge Stack", body="Let us discuss the integration roadmap.", priority=PriorityLevel.HIGH)
    email = comm_service.create_email_draft(draft)
    assert email.id.startswith("email-")
    assert email.status == CommunicationStatus.DRAFT
    assert email.recipient == "partner@company.com"


def test_unapproved_email_dispatch_fails(comm_service, approval_context):
    db, owner_id = approval_context
    email = comm_service.create_email_draft(EmailDraftCreate(recipient="unauthorized@target.com", subject="Important Notice", body="Testing guardrails."))
    with pytest.raises(CommunicationSecurityError, match="Dispatch blocked"):
        comm_service.dispatch_email(email.id, owner_id, db)


def test_email_approval_does_not_fake_unconfigured_dispatch(comm_service, approval_context):
    db, owner_id = approval_context
    email = comm_service.create_email_draft(EmailDraftCreate(recipient="investor@fund.vc", subject="NEXUS AI Milestone 1 Demo", body="NEXUS AI foundation is live and fully verified."))
    email = comm_service.request_email_dispatch(email.id, owner_id, db)
    assert email.status == CommunicationStatus.PENDING_APPROVAL
    approval = approval_service.get_approval(email.approval_id, owner_id, db)
    assert approval.status == ApprovalStatus.PENDING

    with pytest.raises(CommunicationSecurityError, match="Human approval is mandatory"):
        comm_service.dispatch_email(email.id, owner_id, db)

    decision = approval_service.decide_approval(
        email.approval_id,
        ApprovalDecision(decision=ApprovalStatus.APPROVED, payload_hash=approval.payload_hash, reviewer_notes="Reviewed by owner"),
        owner_id,
        db,
    )
    assert decision.status == ApprovalStatus.APPROVED
    result = comm_service.dispatch_email(email.id, owner_id, db)
    assert result.dispatched is False
    assert result.status == CommunicationStatus.APPROVED
    assert "Nothing was sent" in result.message
    assert comm_service.get_email(email.id).status == CommunicationStatus.APPROVED


def test_message_approval_does_not_fake_unconfigured_dispatch(comm_service, approval_context):
    db, owner_id = approval_context
    msg = comm_service.create_message_draft(MessageDraftCreate(channel=CommunicationChannel.LINKEDIN, recipient="CTO Jane Doe", content="Excited about your work on edge computing!"))
    msg = comm_service.request_message_dispatch(msg.id, owner_id, db)
    approval = approval_service.get_approval(msg.approval_id, owner_id, db)
    approval_service.decide_approval(
        msg.approval_id,
        ApprovalDecision(decision=ApprovalStatus.APPROVED, payload_hash=approval.payload_hash, reviewer_notes="Message verified"),
        owner_id,
        db,
    )
    result = comm_service.dispatch_message(msg.id, owner_id, db)
    assert result.dispatched is False
    assert result.status == CommunicationStatus.APPROVED
    assert "Nothing was sent" in result.message
    msg.content = "tampered after approval"
    with pytest.raises(CommunicationSecurityError):
        comm_service.dispatch_message(msg.id, owner_id, db)


def test_create_calendar_event(comm_service):
    event = comm_service.create_calendar_event(CalendarEventCreate(
        title="Sprint Retrospective",
        description="Review of Core Module 5 implementation",
        start_time="2026-11-12T15:00:00Z",
        end_time="2026-11-12T16:00:00Z",
        attendees=["dev@nexus.local"],
    ))
    assert event.id.startswith("cal-")
    assert event.title == "Sprint Retrospective"
