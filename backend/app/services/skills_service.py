"""Skills and Integrations Registry with Strict Permission Enforcement.

Provides dynamic tool discovery, strict least-privilege permission validation,
and enforcement ensuring agents cannot elevate their own privileges or bypass safety boundaries.
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.agents.orchestrator import orchestrator
from app.core.logging import get_audit_logger, logger

audit_logger = get_audit_logger()


class SkillSecurityViolationError(Exception):
    """Raised when an agent attempts to execute a skill without requisite permissions."""
    pass


class SkillDefinition(BaseModel):
    id: str
    name: str
    description: str
    required_permission: str
    is_consequential: bool = False
    authorized_agents: List[str] = Field(default_factory=list)


class SkillInvocationRequest(BaseModel):
    skill_id: str
    agent_id: str
    parameters: Dict[str, Any] = Field(default_factory=dict)


class SkillInvocationResponse(BaseModel):
    skill_id: str
    agent_id: str
    allowed: bool
    status: str
    result: Optional[Any] = None
    error: Optional[str] = None


class SkillsRegistry:
    """Manages skill definitions and verifies agent privilege boundaries."""

    def __init__(self):
        self._skills: Dict[str, SkillDefinition] = {}
        self._register_default_skills()

    def _register_default_skills(self):
        default_skills = [
            SkillDefinition(
                id="filesystem_read",
                name="Sandboxed Filesystem Reader",
                description="Read contents of quarantined files within approved storage roots.",
                required_permission="read:storage/documents",
                is_consequential=False,
                authorized_agents=["personal_agent", "research_agent", "coding_agent"],
            ),
            SkillDefinition(
                id="filesystem_write",
                name="Sandboxed Filesystem Writer",
                description="Write or edit files inside approved storage directories.",
                required_permission="write:approved_projects",
                is_consequential=True,
                authorized_agents=["coding_agent"],
            ),
            SkillDefinition(
                id="web_research",
                name="Sanitized Web Reader",
                description="Safely fetch and sanitize untrusted external web content with anti-SSRF.",
                required_permission="network:outbound_readonly",
                is_consequential=False,
                authorized_agents=["research_agent"],
            ),
            SkillDefinition(
                id="git_checkpoint",
                name="Git Safety Checkpointing",
                description="Create automated git commit snapshots prior to modifying codebases.",
                required_permission="read:approved_projects",
                is_consequential=False,
                authorized_agents=["coding_agent"],
            ),
            SkillDefinition(
                id="resume_tailoring",
                name="Resume Tailoring Engine",
                description="Synthesize target job requirements and customize CV variants.",
                required_permission="write:storage/generated",
                is_consequential=False,
                authorized_agents=["career_agent"],
            ),
            SkillDefinition(
                id="workflow_dispatcher",
                name="n8n Pipeline Dispatcher",
                description="Trigger automated external workflow pipelines via webhook.",
                required_permission="invoke:n8n_webhooks",
                is_consequential=True,
                authorized_agents=["workflow_agent"],
            ),
        ]
        for skill in default_skills:
            self._skills[skill.id] = skill

    def list_skills(self) -> List[SkillDefinition]:
        return list(self._skills.values())

    def get_skill(self, skill_id: str) -> Optional[SkillDefinition]:
        return self._skills.get(skill_id)

    def verify_permission(self, agent_id: str, skill_id: str) -> bool:
        """Verifies whether the agent possesses the exact permission required for the skill."""
        skill = self._skills.get(skill_id)
        if not skill:
            audit_logger.warning(f"SKILL ACCESS DENIED: Unknown skill '{skill_id}' requested by '{agent_id}'")
            return False

        agent = orchestrator.get_agent(agent_id)
        if not agent:
            audit_logger.warning(f"SKILL ACCESS DENIED: Unregistered agent '{agent_id}'")
            return False

        # Verify agent has declared permission
        has_perm = skill.required_permission in agent.permissions
        is_authorized = agent_id in skill.authorized_agents

        if not (has_perm and is_authorized):
            audit_logger.warning(
                f"SECURITY VIOLATION: Agent '{agent_id}' attempted to access skill '{skill_id}' "
                f"requiring permission '{skill.required_permission}'. Access denied."
            )
            return False

        return True

    def invoke_skill(self, req: SkillInvocationRequest) -> SkillInvocationResponse:
        """Executes skill permission checks and handles invocation."""
        skill = self._skills.get(req.skill_id)
        if not skill:
            return SkillInvocationResponse(
                skill_id=req.skill_id,
                agent_id=req.agent_id,
                allowed=False,
                status="not_found",
                error=f"Skill '{req.skill_id}' is not registered.",
            )

        if not self.verify_permission(req.agent_id, req.skill_id):
            return SkillInvocationResponse(
                skill_id=req.skill_id,
                agent_id=req.agent_id,
                allowed=False,
                status="permission_denied",
                error=(
                    f"Agent '{req.agent_id}' lacks required permission '{skill.required_permission}' "
                    f"to execute skill '{req.skill_id}'."
                ),
            )

        # Audit authorized execution
        audit_logger.info(f"Skill executed: '{req.skill_id}' by Agent '{req.agent_id}'")
        orchestrator.log_activity(
            agent_id=req.agent_id,
            action=f"Skill Executed: {skill.name}",
            details=f"Invoked with {len(req.parameters)} parameters",
            status="completed",
        )

        return SkillInvocationResponse(
            skill_id=req.skill_id,
            agent_id=req.agent_id,
            allowed=True,
            status="executed",
            result={"message": f"Skill '{skill.name}' invoked successfully by '{req.agent_id}'."},
        )


skills_registry = SkillsRegistry()
