"""API Endpoints for Daily Briefings and Reminders Engine."""
from typing import Any, Dict, List
from fastapi import APIRouter, status, Depends
from sqlalchemy.orm import Session
from app.core.auth import get_current_user
from app.db.models import UserModel
from app.db.session import get_db

from app.services.briefing_service import briefing_service

router = APIRouter(prefix="/api/v1/briefings", tags=["Daily Briefings & Reminders"])


@router.get("/latest", response_model=Dict[str, Any])
def get_latest_briefing(user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    """Retrieve the most recent executive daily briefing."""
    return briefing_service.get_latest_briefing(owner_user_id=user.id, db=db)


@router.post("/generate", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
def generate_briefing(user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    """Generate and persist a new daily operational briefing."""
    return briefing_service.generate_daily_briefing(owner_user_id=user.id, db=db)


@router.get("/reminders", response_model=List[Dict[str, Any]])
def get_reminders(user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    """List actionable reminders across approvals, tasks, and communications."""
    return briefing_service.list_reminders(owner_user_id=user.id, db=db)
