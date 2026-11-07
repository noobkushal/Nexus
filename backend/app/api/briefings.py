"""API Endpoints for Daily Briefings and Reminders Engine."""
from typing import Any, Dict, List
from fastapi import APIRouter, status

from app.services.briefing_service import briefing_service

router = APIRouter(prefix="/api/v1/briefings", tags=["Daily Briefings & Reminders"])


@router.get("/latest", response_model=Dict[str, Any])
def get_latest_briefing():
    """Retrieve the most recent executive daily briefing."""
    return briefing_service.get_latest_briefing()


@router.post("/generate", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
def generate_briefing():
    """Generate and persist a new daily operational briefing."""
    return briefing_service.generate_daily_briefing()


@router.get("/reminders", response_model=List[Dict[str, Any]])
def get_reminders():
    """List actionable reminders across approvals, tasks, and communications."""
    return briefing_service.list_reminders()
