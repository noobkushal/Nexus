"""API Endpoints for Email, Messaging, and Calendar Communications."""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status, Depends
from sqlalchemy.orm import Session
from app.core.auth import get_current_user
from app.db.models import UserModel
from app.db.session import get_db

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
)
from app.services.communication_service import (
    CommunicationSecurityError,
    communication_service,
)

router = APIRouter(prefix="/api/v1/communications", tags=["Communications"])


# --- Emails ---
@router.get("/emails", response_model=List[EmailDraft])
def get_emails(
    status_filter: Optional[CommunicationStatus] = Query(None, alias="status")
):
    """Retrieve all drafted and queued emails."""
    return communication_service.list_emails(status=status_filter)


@router.post("/emails", response_model=EmailDraft, status_code=status.HTTP_201_CREATED)
def create_email(draft_in: EmailDraftCreate):
    """Create a new email draft."""
    return communication_service.create_email_draft(draft_in)


@router.post("/emails/{email_id}/request-dispatch", response_model=EmailDraft)
def request_email_dispatch(email_id: str, user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    """Submit email draft to the human approval gate."""
    try:
        return communication_service.request_email_dispatch(email_id, user.id, db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/emails/{email_id}/dispatch", response_model=DispatchResult)
def dispatch_email(email_id: str, user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    """Transmit email after human operator approval."""
    try:
        return communication_service.dispatch_email(email_id, user.id, db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except CommunicationSecurityError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


# --- Messages ---
@router.get("/messages", response_model=List[MessageDraft])
def get_messages(
    channel_filter: Optional[CommunicationChannel] = Query(None, alias="channel")
):
    """Retrieve multi-channel messages (Slack, LinkedIn)."""
    return communication_service.list_messages(channel=channel_filter)


@router.post("/messages", response_model=MessageDraft, status_code=status.HTTP_201_CREATED)
def create_message(draft_in: MessageDraftCreate):
    """Create a new outbound message draft."""
    return communication_service.create_message_draft(draft_in)


@router.post("/messages/{message_id}/request-dispatch", response_model=MessageDraft)
def request_message_dispatch(message_id: str, user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    """Submit message draft to human approval gate."""
    try:
        return communication_service.request_message_dispatch(message_id, user.id, db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/messages/{message_id}/dispatch", response_model=DispatchResult)
def dispatch_message(message_id: str, user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    """Transmit message after human operator approval."""
    try:
        return communication_service.dispatch_message(message_id, user.id, db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except CommunicationSecurityError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


# --- Calendar ---
@router.get("/calendar", response_model=List[CalendarEvent])
def get_calendar():
    """Retrieve scheduled calendar agenda and events."""
    return communication_service.list_calendar_events()


@router.post("/calendar", response_model=CalendarEvent, status_code=status.HTTP_201_CREATED)
def create_calendar_event(event_in: CalendarEventCreate):
    """Draft a new calendar event."""
    return communication_service.create_calendar_event(event_in)
