"""API Endpoints for Skills and Integrations Registry."""
from typing import List
from fastapi import APIRouter, HTTPException, status

from app.services.skills_service import (
    SkillDefinition,
    SkillInvocationRequest,
    SkillInvocationResponse,
    skills_registry,
)

router = APIRouter(prefix="/api/v1/skills", tags=["Skills & Integrations Registry"])


@router.get("", response_model=List[SkillDefinition])
def list_skills():
    """List all registered skills, required permissions, and authorized agents."""
    return skills_registry.list_skills()


@router.get("/{skill_id}", response_model=SkillDefinition)
def get_skill(skill_id: str):
    """Retrieve skill specifications and security requirements."""
    skill = skills_registry.get_skill(skill_id)
    if not skill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Skill '{skill_id}' not found.")
    return skill


@router.post("/invoke", response_model=SkillInvocationResponse)
def invoke_skill(req: SkillInvocationRequest):
    """Invoke a registered skill with strict permission boundary checking."""
    return skills_registry.invoke_skill(req)
