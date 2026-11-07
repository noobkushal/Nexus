"""Communication and Messaging Service with Mandatory Approval Barrier.

Coordinates email drafting, multi-channel messaging (Slack, LinkedIn), and calendar
scheduling. Enforces human approval prior to any external transmission.
"""
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.agents.orchestrator import orchestrator
from app.core.logging import get_audit_logger, logger
from app.schemas.approval import ActionType, ApprovalRequestCreate, ApprovalStatus
from app.schemas.communication import (
    CalendarEvent,
    CalendarEventCreate,
    CommunicationChannel,
    CommunicationStatus,
    DispatchResult,
    EmailDraft,
    EmailDraftCreate,
    MessageDraft,
    MessageDraftCreate,
    PriorityLevel,
    utc_now,
)
from app.services.approval_service import approval_service

audit_logger = get_audit_logger()


class CommunicationSecurityError(Exception):
    """Raised when an unapproved message dispatch is attempted."""
    pass


class CommunicationService:
    """Manages drafts and enforces approval before outbound dispatch."""

    def __init__(self):
        self._emails: Dict[str, EmailDraft] = {}
        self._messages: Dict[str, MessageDraft] = {}
        self._calendar_events: Dict[str, CalendarEvent] = {}
        self._seed_default_data()

    def _seed_default_data(self):
        """Seeds initial communication drafts for system bootstrap and verification."""
        email1_id = "email-001"
        self._emails[email1_id] = EmailDraft(
            id=email1_id,
            sender="architect@nexus.local",
            recipient="recruiter@techinnovations.io",
            subject="Senior AI Systems Architect — Application & Technical Portfolio",
            body=(
                "Dear Hiring Team,\n\n"
                "I am writing to express my strong interest in the Senior AI Systems Architect role. "
                "Attached is my technical portfolio detailing local-first agentic systems, deterministic "
                "state machine graph routing, and sandboxed AI orchestration.\n\n"
                "Best regards,\nNEXUS Operator"
            ),
            status=CommunicationStatus.DRAFT,
            priority=PriorityLevel.HIGH,
            created_at=utc_now(),
        )

        msg1_id = "msg-001"
        self._messages[msg1_id] = MessageDraft(
            id=msg1_id,
            channel=CommunicationChannel.LINKEDIN,
            recipient="Dr. Elena Vance (Lead AI Research)",
            content=(
                "Hi Dr. Vance, I reviewed your recent publication on local-first LLM orchestration. "
                "We recently developed a modular state graph runtime with zero external dependencies. "
                "Would love to connect!"
            ),
            status=CommunicationStatus.DRAFT,
            created_at=utc_now(),
        )

        cal1_id = "cal-001"
        self._calendar_events[cal1_id] = CalendarEvent(
            id=cal1_id,
            title="NEXUS AI Architecture Review & Milestone Evaluation",
            description="Bi-weekly review of local-first agent graph, sandboxed filesystem, and safety barriers.",
            start_time="2026-11-10T10:00:00Z",
            end_time="2026-11-10T11:00:00Z",
            attendees=["operator@nexus.local", "architect@nexus.local"],
            status=CommunicationStatus.DRAFT,
            created_at=utc_now(),
        )

    # --- Email Operations ---
    def list_emails(self, status: Optional[CommunicationStatus] = None) -> List[EmailDraft]:
        items = list(self._emails.values())
        if status:
            items = [e for e in items if e.status == status]
        return sorted(items, key=lambda x: x.created_at, reverse=True)

    def get_email(self, email_id: str) -> Optional[EmailDraft]:
        return self._emails.get(email_id)

    def create_email_draft(self, draft_in: EmailDraftCreate, sender: str = "operator@nexus.local") -> EmailDraft:
        email_id = f"email-{uuid.uuid4().hex[:8]}"
        email = EmailDraft(
            id=email_id,
            sender=sender,
            recipient=draft_in.recipient,
            subject=draft_in.subject,
            body=draft_in.body,
            status=CommunicationStatus.DRAFT,
            priority=draft_in.priority,
            created_at=utc_now(),
        )
        self._emails[email_id] = email
        audit_logger.info(f"Email draft created: {email_id} to {email.recipient}")
        return email

    def request_email_dispatch(self, email_id: str) -> EmailDraft:
        """Submits an email draft to the human approval gate."""
        email = self._emails.get(email_id)
        if not email:
            raise ValueError(f"Email draft '{email_id}' not found.")

        # Create approval request
        appr = approval_service.request_approval(
            ApprovalRequestCreate(
                agent_id="personal_agent",
                action_type=ActionType.EXTERNAL_MESSAGE,
                title=f"Dispatch Email: '{email.subject[:50]}'",
                description=f"Send email to '{email.recipient}' with priority '{email.priority.value}'.",
                payload={"email_id": email.id, "recipient": email.recipient, "subject": email.subject},
            )
        )
        email.status = CommunicationStatus.PENDING_APPROVAL
        email.approval_id = appr.id
        audit_logger.info(f"Email {email_id} queued for approval #{appr.id}")
        return email

    def dispatch_email(self, email_id: str) -> DispatchResult:
        """Executes dispatch ONLY if explicitly approved by the human operator."""
        email = self._emails.get(email_id)
        if not email:
            raise ValueError(f"Email draft '{email_id}' not found.")

        if not email.approval_id:
            raise CommunicationSecurityError(
                f"Dispatch blocked: Email '{email_id}' has not been submitted for approval."
            )

        appr = approval_service.get_approval(email.approval_id)
        if not appr or appr.status != ApprovalStatus.APPROVED:
            raise CommunicationSecurityError(
                f"Dispatch blocked: Approval #{email.approval_id} is '{appr.status if appr else 'missing'}'. "
                f"Human approval is mandatory before transmission."
            )

        email.status = CommunicationStatus.DISPATCHED
        email.dispatched_at = utc_now()

        audit_logger.warning(
            f"SECURITY DISPATCH: Outbound email transmitted to {email.recipient} under approval #{appr.id}"
        )
        orchestrator.log_activity(
            agent_id="personal_agent",
            action="Email Dispatched",
            details=f"Sent to {email.recipient}: '{email.subject}'",
            status="completed",
        )

        return DispatchResult(
            id=email.id,
            channel="email",
            status=CommunicationStatus.DISPATCHED,
            dispatched=True,
            message=f"Email successfully dispatched to {email.recipient}.",
            audit_logged=True,
        )

    # --- Message Operations ---
    def list_messages(self, channel: Optional[CommunicationChannel] = None) -> List[MessageDraft]:
        items = list(self._messages.values())
        if channel:
            items = [m for m in items if m.channel == channel]
        return sorted(items, key=lambda x: x.created_at, reverse=True)

    def create_message_draft(self, draft_in: MessageDraftCreate) -> MessageDraft:
        msg_id = f"msg-{uuid.uuid4().hex[:8]}"
        msg = MessageDraft(
            id=msg_id,
            channel=draft_in.channel,
            recipient=draft_in.recipient,
            content=draft_in.content,
            status=CommunicationStatus.DRAFT,
            created_at=utc_now(),
        )
        self._messages[msg_id] = msg
        audit_logger.info(f"Message draft created: {msg_id} ({draft_in.channel.value})")
        return msg

    def request_message_dispatch(self, message_id: str) -> MessageDraft:
        msg = self._messages.get(message_id)
        if not msg:
            raise ValueError(f"Message draft '{message_id}' not found.")

        appr = approval_service.request_approval(
            ApprovalRequestCreate(
                agent_id="career_agent" if msg.channel == CommunicationChannel.LINKEDIN else "personal_agent",
                action_type=ActionType.EXTERNAL_MESSAGE,
                title=f"Send {msg.channel.value.title()} Message to '{msg.recipient[:40]}'",
                description=f"Outbound communication via {msg.channel.value}: '{msg.content[:80]}...'",
                payload={"message_id": msg.id, "channel": msg.channel.value, "recipient": msg.recipient},
            )
        )
        msg.status = CommunicationStatus.PENDING_APPROVAL
        msg.approval_id = appr.id
        return msg

    def dispatch_message(self, message_id: str) -> DispatchResult:
        msg = self._messages.get(message_id)
        if not msg:
            raise ValueError(f"Message draft '{message_id}' not found.")

        if not msg.approval_id:
            raise CommunicationSecurityError("Dispatch blocked: Message has not been submitted for approval.")

        appr = approval_service.get_approval(msg.approval_id)
        if not appr or appr.status != ApprovalStatus.APPROVED:
            raise CommunicationSecurityError(
                f"Dispatch blocked: Approval status is '{appr.status if appr else 'missing'}'. "
                f"Human approval required."
            )

        msg.status = CommunicationStatus.DISPATCHED
        msg.dispatched_at = utc_now()

        audit_logger.warning(
            f"SECURITY DISPATCH: Outbound {msg.channel.value} message sent to {msg.recipient} under approval #{appr.id}"
        )

        return DispatchResult(
            id=msg.id,
            channel=msg.channel.value,
            status=CommunicationStatus.DISPATCHED,
            dispatched=True,
            message=f"{msg.channel.value.title()} message sent to {msg.recipient}.",
            audit_logged=True,
        )

    # --- Calendar Operations ---
    def list_calendar_events(self) -> List[CalendarEvent]:
        return sorted(list(self._calendar_events.values()), key=lambda x: x.start_time)

    def create_calendar_event(self, event_in: CalendarEventCreate) -> CalendarEvent:
        cal_id = f"cal-{uuid.uuid4().hex[:8]}"
        event = CalendarEvent(
            id=cal_id,
            title=event_in.title,
            description=event_in.description,
            start_time=event_in.start_time,
            end_time=event_in.end_time,
            attendees=event_in.attendees,
            status=CommunicationStatus.DRAFT,
            created_at=utc_now(),
        )
        self._calendar_events[cal_id] = event
        audit_logger.info(f"Calendar event drafted: {event.title} ({cal_id})")
        return event


communication_service = CommunicationService()
