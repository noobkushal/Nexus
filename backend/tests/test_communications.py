"""Tests for Communication Workflows and Mandatory Approval Barrier."""
import pytest
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
from app.services.communication_service import (
    CommunicationSecurityError,
    CommunicationService,
)


@pytest.fixture
def comm_service():
    """Provides a fresh communication service instance for tests."""
    return CommunicationService()


def test_list_initial_communications(comm_service):
    """Verify default seeded drafts exist."""
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
    """Verify email draft creation without external transmission."""
    draft_in = EmailDraftCreate(
        recipient="partner@company.com",
        subject="Collaboration on Local AI Edge Stack",
        body="Let us discuss the integration roadmap.",
        priority=PriorityLevel.HIGH,
    )
    email = comm_service.create_email_draft(draft_in)
    assert email.id.startswith("email-")
    assert email.status == CommunicationStatus.DRAFT
    assert email.recipient == "partner@company.com"


def test_unapproved_email_dispatch_fails(comm_service):
    """Verify dispatching an unapproved email raises CommunicationSecurityError."""
    draft_in = EmailDraftCreate(
        recipient="unauthorized@target.com",
        subject="Important Notice",
        body="Testing guardrails.",
    )
    email = comm_service.create_email_draft(draft_in)

    # Directly dispatching without approval must fail
    with pytest.raises(CommunicationSecurityError, match="Dispatch blocked"):
        comm_service.dispatch_email(email.id)


def test_email_approval_and_dispatch_lifecycle(comm_service):
    """Verify end-to-end lifecycle: draft -> request approval -> approve -> dispatch."""
    draft_in = EmailDraftCreate(
        recipient="investor@fund.vc",
        subject="NEXUS AI Milestone 1 Demo",
        body="NEXUS AI foundation is live and fully verified.",
    )
    email = comm_service.create_email_draft(draft_in)

    # 1. Request dispatch
    email = comm_service.request_email_dispatch(email.id)
    assert email.status == CommunicationStatus.PENDING_APPROVAL
    assert email.approval_id is not None

    # 2. Attempt dispatch before human decision
    with pytest.raises(CommunicationSecurityError, match="Human approval is mandatory"):
        comm_service.dispatch_email(email.id)

    # 3. Human operator approves request
    decision = approval_service.decide_approval(
        email.approval_id,
        ApprovalDecision(decision=ApprovalStatus.APPROVED, reviewer_notes="Approved by Operator"),
    )
    assert decision.status == ApprovalStatus.APPROVED

    # 4. Dispatch succeeds now
    result = comm_service.dispatch_email(email.id)
    assert result.dispatched is True
    assert result.status == CommunicationStatus.DISPATCHED
    assert "successfully dispatched" in result.message

    # 5. Verify email updated in store
    updated = comm_service.get_email(email.id)
    assert updated.status == CommunicationStatus.DISPATCHED
    assert updated.dispatched_at is not None


def test_message_approval_and_dispatch(comm_service):
    """Verify LinkedIn/Slack message draft and approval cycle."""
    msg_in = MessageDraftCreate(
        channel=CommunicationChannel.LINKEDIN,
        recipient="CTO Jane Doe",
        content="Excited about your work on edge computing!",
    )
    msg = comm_service.create_message_draft(msg_in)
    assert msg.status == CommunicationStatus.DRAFT

    # Request dispatch
    msg = comm_service.request_message_dispatch(msg.id)
    assert msg.status == CommunicationStatus.PENDING_APPROVAL

    # Approve
    approval_service.decide_approval(
        msg.approval_id,
        ApprovalDecision(decision=ApprovalStatus.APPROVED, reviewer_notes="Message verified"),
    )

    result = comm_service.dispatch_message(msg.id)
    assert result.dispatched is True
    assert result.channel == "linkedin"


def test_create_calendar_event(comm_service):
    """Verify drafting calendar events."""
    event_in = CalendarEventCreate(
        title="Sprint Retrospective",
        description="Review of Core Module 5 implementation",
        start_time="2026-11-12T15:00:00Z",
        end_time="2026-11-12T16:00:00Z",
        attendees=["dev@nexus.local"],
    )
    event = comm_service.create_calendar_event(event_in)
    assert event.id.startswith("cal-")
    assert event.title == "Sprint Retrospective"
