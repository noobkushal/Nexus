"""Agent Registry and Observability Endpoints."""
from typing import List
from fastapi import APIRouter, HTTPException, Query, status
from app.agents.orchestrator import AgentActivity, AgentInfo, orchestrator

router = APIRouter(prefix="/api/v1/agents", tags=["Agents"])


@router.get("", response_model=List[AgentInfo])
async def list_agents() -> List[AgentInfo]:
    """Lists all registered agents in the NEXUS multi-agent system."""
    return orchestrator.list_agents()


@router.get("/activities", response_model=List[AgentActivity])
async def list_agent_activities(
    limit: int = Query(20, ge=1, le=100, description="Max activities to return"),
) -> List[AgentActivity]:
    """Returns recent agent action logs and audit trail."""
    return orchestrator.list_activities(limit=limit)


@router.get("/{agent_id}", response_model=AgentInfo)
async def get_agent_details(agent_id: str) -> AgentInfo:
    """Retrieves specific details, capabilities, and permissions for an agent."""
    agent = orchestrator.get_agent(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found.",
        )
    return agent
