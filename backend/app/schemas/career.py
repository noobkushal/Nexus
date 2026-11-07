"""Schemas for Career Intelligence, Job Discovery, and Resume Tailoring."""
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class JobOpportunity(BaseModel):
    id: str
    title: str
    company: str
    location: str
    skills_required: List[str]
    description: str
    match_score: float = Field(..., ge=0.0, le=1.0)
    status: str = "discovered"  # discovered, tailored, applied, archived
    discovered_at: datetime = Field(default_factory=utc_now)


class ResumeTailorRequest(BaseModel):
    job_id: Optional[str] = None
    target_role: str = Field(..., max_length=200)
    target_company: str = Field(..., max_length=200)
    job_description: str = Field(..., min_length=20)
    focus_skills: List[str] = Field(default_factory=list)


class ResumeTailorResponse(BaseModel):
    id: str
    target_role: str
    target_company: str
    match_score: float
    tailored_summary: str
    matched_skills: List[str]
    relative_path: str
    content: str
    created_at: datetime = Field(default_factory=utc_now)
