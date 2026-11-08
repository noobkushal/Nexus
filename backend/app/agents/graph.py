"""Deterministic State Graph Orchestrator (LangGraph Architecture Pattern)."""
import re
from typing import Any, Callable, Dict, List, Optional
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from app.agents.orchestrator import orchestrator
from app.core.logging import get_audit_logger, logger
from app.providers.registry import provider_registry
from app.schemas.approval import ActionType, ApprovalRequestCreate
from app.services.approval_service import approval_service

audit_logger = get_audit_logger()


def contains_any_word(text: str, words: List[str]) -> bool:
    """Checks if any target word appears with whole word boundary matching."""
    return any(re.search(rf"\b{re.escape(w)}\b", text, re.IGNORECASE) for w in words)


class AgentGraphState(BaseModel):
    """Execution state propagated across the multi-agent graph nodes."""
    conversation_id: str
    user_prompt: str
    intent: str = "dialogue"
    target_agent_id: str = "personal_agent"
    steps: List[str] = Field(default_factory=list)
    action_proposals: List[Dict[str, Any]] = Field(default_factory=list)
    requires_approval: bool = False
    approval_id: Optional[str] = None
    response_content: str = ""
    claimed_actions_executed: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentStateGraph:
    """Directed state graph executing multi-agent reasoning, routing, and safety barriers."""

    async def execute(self, user_prompt: str, conversation_id: str, owner_user_id: Optional[str] = None, db: Optional[Session] = None) -> AgentGraphState:
        state = AgentGraphState(
            conversation_id=conversation_id,
            user_prompt=user_prompt,
        )

        # Node 1: Intent Classification
        state = await self._classify_intent_node(state)

        # Node 2: Agent Routing
        state = await self._route_agent_node(state)

        # Node 3: Safety Boundary & Consequential Action Evaluation
        state = await self._safety_barrier_node(state, owner_user_id, db)

        # Node 4: Provider Response Synthesis
        state = await self._synthesis_node(state)

        return state

    async def _classify_intent_node(self, state: AgentGraphState) -> AgentGraphState:
        prompt = state.user_prompt

        if contains_any_word(prompt, ["code", "git", "file", "function", "bug", "repo", "refactor"]):
            intent = "coding"
        elif contains_any_word(prompt, ["research", "search", "web", "scrape", "doc", "pdf", "papers"]):
            intent = "research"
        elif contains_any_word(prompt, ["workflow", "automate", "n8n", "webhook", "pipeline", "cron"]):
            intent = "workflow"
        elif contains_any_word(prompt, ["career", "resume", "job", "linkedin", "outreach", "cv"]):
            intent = "career"
        elif contains_any_word(prompt, ["briefing", "digest"]):
            intent = "briefing"
        elif contains_any_word(prompt, ["task", "todo", "schedule", "reminder"]):
            intent = "task_management"
        else:
            intent = "general_dialogue"

        state.intent = intent
        state.steps.append(f"Intent Classification -> '{intent}'")
        return state

    async def _route_agent_node(self, state: AgentGraphState) -> AgentGraphState:
        routing_map = {
            "coding": "coding_agent",
            "research": "research_agent",
            "workflow": "workflow_agent",
            "career": "career_agent",
            "briefing": "personal_agent",
            "task_management": "personal_agent",
            "general_dialogue": "personal_agent",
        }
        agent_id = routing_map.get(state.intent, "personal_agent")
        state.target_agent_id = agent_id

        agent_info = orchestrator.get_agent(agent_id)
        agent_name = agent_info.name if agent_info else "Aura"
        state.steps.append(f"Graph Router -> Assigned to Agent '{agent_name}' ({agent_id})")

        orchestrator.log_activity(
            agent_id=agent_id,
            action="Graph Routing",
            details=f"Prompt matched intent '{state.intent}'",
            status="completed",
        )
        return state

    async def _safety_barrier_node(self, state: AgentGraphState, owner_user_id: Optional[str], db: Optional[Session]) -> AgentGraphState:
        prompt = state.user_prompt
        consequential = False
        action_type = None
        action_title = None

        if contains_any_word(prompt, ["delete", "remove", "wipe"]) and contains_any_word(prompt, ["file", "files", "folder", "directory"]):
            consequential = True
            action_type = ActionType.FILESYSTEM_DELETE
            action_title = "Filesystem Deletion Proposal"
        elif contains_any_word(prompt, ["send", "transmit", "publish"]) and contains_any_word(prompt, ["message", "messages", "email", "linkedin"]):
            consequential = True
            action_type = ActionType.EXTERNAL_MESSAGE
            action_title = "Outreach Transmission Proposal"
        elif contains_any_word(prompt, ["trigger", "execute"]) and contains_any_word(prompt, ["workflow", "pipeline", "webhook"]):
            consequential = True
            action_type = ActionType.WORKFLOW_TRIGGER
            action_title = "External Pipeline Execution"

        if consequential and action_type and action_title:
            if not owner_user_id or db is None:
                raise RuntimeError("Consequential actions require an authenticated owner and persistent database session.")
            state.requires_approval = True
            appr = approval_service.request_approval(
                ApprovalRequestCreate(
                    agent_id=state.target_agent_id,
                    action_type=action_type,
                    title=action_title,
                    description=f"Agent proposed consequential action from prompt: '{state.user_prompt[:100]}'",
                    payload={"prompt": state.user_prompt},
                ),
                requester_user_id=owner_user_id,
                db=db,
            )
            state.approval_id = appr.id
            state.steps.append(f"Safety Guard -> Consequential Action Detected! Subscribed to Approval Queue (#{appr.id})")
        else:
            state.steps.append("Safety Guard -> Read-only / Non-consequential query (Autonomous execution permitted)")

        return state

    async def _synthesis_node(self, state: AgentGraphState) -> AgentGraphState:
        provider = provider_registry.active_provider

        # Check if gated by approval
        if state.requires_approval:
            state.response_content = (
                f"[SAFETY BARRIER INTERCEPT — NEXUS Orchestrator]\n"
                f"Your request involves a consequential operation ({state.intent}).\n"
                f"Action Approval Request #{state.approval_id} has been queued.\n"
                f"Please review and approve this action in Mission Control or the Approval Gate before execution."
            )
            state.claimed_actions_executed = False
            state.steps.append("Synthesis -> Gated by Human Approval Barrier")
            return state

        # Query provider
        from app.providers.base import ChatMessage, MessageRole
        messages = [
            ChatMessage(role=MessageRole.USER, content=state.user_prompt)
        ]
        llm_resp = await provider.generate_chat_response(messages=messages)
        state.response_content = llm_resp.content
        state.claimed_actions_executed = False
        state.metadata["provider"] = llm_resp.provider_name
        state.metadata["model"] = llm_resp.model_name
        state.steps.append(f"Synthesis -> Completed via Provider '{llm_resp.provider_name}'")

        # Specific Agent Autonomous Artifact Generation (Non-consequential, safe storage)
        if state.target_agent_id == "research_agent":
            from app.tools.browser import sandboxed_web_reader
            slug = re.sub(r"[^a-zA-Z0-9 ]+", "", state.user_prompt)[:30].strip() or "general_research"
            dossier_rel = sandboxed_web_reader.save_research_dossier(
                topic=slug,
                query=state.user_prompt,
                content=llm_resp.content,
                sources=["https://arxiv.org/abs/2401.00001", "https://docs.nexus.local/reference"],
            )
            state.metadata["dossier_path"] = dossier_rel
            state.steps.append(f"Scout Archive -> Sanitized research dossier stored at '{dossier_rel}'")

        elif state.intent == "briefing":
            from app.services.briefing_service import briefing_service
            briefing_info = briefing_service.generate_daily_briefing()
            state.response_content = briefing_info["content"]
            state.metadata["briefing_path"] = briefing_info["path"]
            state.steps.append(f"Aura Engine -> Compiled executive briefing '{briefing_info['filename']}'")

        elif state.target_agent_id == "coding_agent" and contains_any_word(state.user_prompt, ["scaffold", "generate", "create", "build", "template"]):
            from app.tools.scaffolder import app_scaffolder
            template = "fastapi_microservice"
            p_lower = state.user_prompt.lower()
            if "next" in p_lower or "website" in p_lower or "landing" in p_lower:
                template = "nextjs_landing"
            elif "cli" in p_lower:
                template = "python_cli"

            proj_slug = re.sub(r"[^a-zA-Z0-9]+", "_", state.user_prompt)[:20].strip("_") or "nexus_app"
            scaffold_res = app_scaffolder.scaffold_project(
                project_name=proj_slug,
                template=template,
                description=f"Generated via Forge agent for prompt: {state.user_prompt[:60]}",
            )
            state.metadata["scaffolded_project"] = scaffold_res
            state.steps.append(f"Forge Scaffolder -> Generated {template} at storage/{scaffold_res['directory']} ({len(scaffold_res['created_files'])} files)")

        elif state.target_agent_id == "career_agent" and contains_any_word(state.user_prompt, ["tailor", "resume", "cv"]):
            from app.services.career_service import career_service
            from app.schemas.career import ResumeTailorRequest
            role_slug = re.sub(r"[^a-zA-Z0-9 ]+", "", state.user_prompt)[:30].strip() or "Senior Architect"
            tailor_res = career_service.tailor_resume(
                ResumeTailorRequest(
                    target_role=role_slug,
                    target_company="Target Enterprise",
                    job_description=state.user_prompt,
                )
            )
            state.metadata["tailored_resume_path"] = tailor_res.relative_path
            state.steps.append(f"Apex Career -> Tailored CV generated at storage/{tailor_res.relative_path} ({tailor_res.match_score:.0%})")

        return state


agent_graph = AgentStateGraph()
