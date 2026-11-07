"""Multi-Agent Orchestrator and Agent Registry."""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AgentCapability(BaseModel):
    name: str
    description: str
    requires_approval: bool = False


class AgentInfo(BaseModel):
    id: str
    name: str
    role: str
    description: str
    status: str = "idle"  # idle, active, waiting_approval, paused
    capabilities: List[AgentCapability]
    permissions: List[str]
    created_at: datetime = Field(default_factory=utc_now)


class AgentActivity(BaseModel):
    timestamp: datetime = Field(default_factory=utc_now)
    agent_id: str
    action: str
    details: str
    status: str = "completed"  # pending, completed, rejected


class AgentOrchestrator:
    """Coordinates agent execution, manages registry, and logs agent activities."""

    def __init__(self):
        self._agents: Dict[str, AgentInfo] = {}
        self._activities: List[AgentActivity] = []
        self._register_default_agents()

    def _register_default_agents(self):
        default_agents = [
            AgentInfo(
                id="personal_agent",
                name="Aura",
                role="Personal Assistant & Coordinator",
                description="Core conversational assistant, daily briefings, and interaction manager.",
                status="idle",
                capabilities=[
                    AgentCapability(name="dialogue", description="Natural conversational interaction"),
                    AgentCapability(name="calendar_sync", description="Drafting calendar schedules", requires_approval=True),
                    AgentCapability(name="task_dispatch", description="Assigning items to specialized agents"),
                ],
                permissions=["read:profile", "read:tasks", "write:tasks"],
            ),
            AgentInfo(
                id="research_agent",
                name="Scout",
                role="Web & Document Researcher",
                description="Autonomous web browsing, source synthesis, and document summaries.",
                status="idle",
                capabilities=[
                    AgentCapability(name="web_search", description="Query search engines and scrape verified docs"),
                    AgentCapability(name="doc_summarize", description="Summarize PDFs and text files"),
                ],
                permissions=["read:storage/documents", "network:outbound_readonly"],
            ),
            AgentInfo(
                id="coding_agent",
                name="Forge",
                role="Software Development & Local Projects",
                description="Works on approved local workspaces, verifies code, creates Git checkpoints.",
                status="idle",
                capabilities=[
                    AgentCapability(name="code_analysis", description="Inspect codebase and run tests"),
                    AgentCapability(name="file_modification", description="Edit files inside approved directories", requires_approval=True),
                    AgentCapability(name="git_checkpoint", description="Create safety git commits before edits"),
                ],
                permissions=["read:approved_projects", "write:approved_projects"],
            ),
            AgentInfo(
                id="workflow_agent",
                name="Conduit",
                role="Workflow Automation & n8n Bridge",
                description="Manages event triggers, webhook execution, and external integrations.",
                status="idle",
                capabilities=[
                    AgentCapability(name="trigger_workflow", description="Execute registered n8n webhooks", requires_approval=True),
                    AgentCapability(name="monitor_runs", description="Poll and log pipeline executions"),
                ],
                permissions=["invoke:n8n_webhooks"],
            ),
            AgentInfo(
                id="career_agent",
                name="Apex",
                role="Career Strategist & Resume Tailoring",
                description="Job discovery, CV alignment, and human-reviewed LinkedIn outreach.",
                status="idle",
                capabilities=[
                    AgentCapability(name="resume_tailor", description="Generate targeted resume variants"),
                    AgentCapability(name="outreach_draft", description="Draft personalized connection requests", requires_approval=True),
                ],
                permissions=["read:profile", "write:storage/generated"],
            ),
        ]
        for agent in default_agents:
            self._agents[agent.id] = agent

        # Seed initial activities
        self._activities.append(
            AgentActivity(
                agent_id="personal_agent",
                action="System Initialization",
                details="Agent loaded with default permission boundaries.",
                status="completed",
            )
        )
        self._activities.append(
            AgentActivity(
                agent_id="coding_agent",
                action="Filesystem Scan",
                details="Verified local directory barriers for E:\\NEXUS.",
                status="completed",
            )
        )

    def list_agents(self) -> List[AgentInfo]:
        return list(self._agents.values())

    def get_agent(self, agent_id: str) -> Optional[AgentInfo]:
        return self._agents.get(agent_id)

    def log_activity(self, agent_id: str, action: str, details: str, status: str = "completed"):
        activity = AgentActivity(
            agent_id=agent_id,
            action=action,
            details=details,
            status=status,
        )
        self._activities.append(activity)

    def list_activities(self, limit: int = 20) -> List[AgentActivity]:
        return sorted(self._activities, key=lambda a: a.timestamp, reverse=True)[:limit]


orchestrator = AgentOrchestrator()
