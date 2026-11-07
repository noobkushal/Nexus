"""API Endpoints for Career Intelligence and Resume Tailoring."""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.career import JobOpportunity, ResumeTailorRequest, ResumeTailorResponse
from app.services.career_service import career_service

router = APIRouter(prefix="/api/v1/career", tags=["Career Intelligence & Resumes"])


@router.get("/jobs", response_model=List[JobOpportunity])
def list_jobs(status_filter: Optional[str] = Query(None, alias="status")):
    """List discovered job opportunities and candidate match scores."""
    return career_service.list_jobs(status=status_filter)


@router.get("/jobs/{job_id}", response_model=JobOpportunity)
def get_job(job_id: str):
    """Retrieve details of a specific job opportunity."""
    job = career_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job '{job_id}' not found.")
    return job


@router.post("/tailor-resume", response_model=ResumeTailorResponse, status_code=status.HTTP_201_CREATED)
def tailor_resume(req: ResumeTailorRequest):
    """Tailor a candidate CV/resume to match a target job specification."""
    return career_service.tailor_resume(req)


@router.get("/resumes", response_model=List[Dict[str, Any]])
def list_tailored_resumes():
    """List all previously generated tailored resumes in storage/generated/."""
    return career_service.list_tailored_resumes()
