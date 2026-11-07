"""Human Approval Service enforcing strict boundaries on consequential actions."""
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional
from app.core.logging import get_audit_logger, logger
from app.schemas.approval import (
    ActionType,
    ApprovalDecision,
    ApprovalRequestCreate,
    ApprovalResponse,
    ApprovalStatus,
)

audit_logger = get_audit_logger()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ApprovalService:
    """Manages consequential action proposals requiring human review."""

    def __init__(self):
        self._approvals: Dict[str, ApprovalResponse] = {}
        self._seed_default_approvals()

    def _seed_default_approvals(self):
        seeds = [
            (
                "career_agent",
                ActionType.EXTERNAL_MESSAGE,
                "LinkedIn Outreach to Sarah Jenkins",
                "Draft connection note to Platform Architect at Apex Tech Labs.",
                {"recipient": "Sarah Jenkins", "channel": "LinkedIn", "preview": "Hi Sarah..."},
            ),
            (
                "workflow_agent",
                ActionType.WORKFLOW_TRIGGER,
                "Execute Daily Briefing n8n Pipeline",
                "Trigger automated morning calendar aggregation webhook.",
                {"webhook": "/webhook/daily-briefing", "time": "08:00 AM"},
            ),
        ]
        now = utc_now()
        for agent_id, atype, title, desc, payload in seeds:
            aid = str(uuid.uuid4())[:8]
            self._approvals[aid] = ApprovalResponse(
                id=aid,
                agent_id=agent_id,
                action_type=atype,
                title=title,
                description=desc,
                payload=payload,
                status=ApprovalStatus.PENDING,
                requested_at=now,
            )

    def list_approvals(self, status: Optional[ApprovalStatus] = None) -> List[ApprovalResponse]:
        items = list(self._approvals.values())
        if status:
            items = [a for a in items if a.status == status]
        return sorted(items, key=lambda a: a.requested_at, reverse=True)

    def get_approval(self, approval_id: str) -> Optional[ApprovalResponse]:
        return self._approvals.get(approval_id)

    def request_approval(self, req: ApprovalRequestCreate) -> ApprovalResponse:
        aid = str(uuid.uuid4())[:8]
        now = utc_now()
        approval = ApprovalResponse(
            id=aid,
            agent_id=req.agent_id,
            action_type=req.action_type,
            title=req.title,
            description=req.description,
            payload=req.payload,
            status=ApprovalStatus.PENDING,
            requested_at=now,
        )
        self._approvals[aid] = approval
        audit_logger.warning(
            f"ACTION PROPOSAL SUBMITTED: [{aid}] Agent '{req.agent_id}' requested '{req.action_type.value}' - {req.title}"
        )
        return approval

    def decide_approval(self, approval_id: str, decision: ApprovalDecision) -> Optional[ApprovalResponse]:
        approval = self._approvals.get(approval_id)
        if not approval:
            return None

        approval.status = decision.decision
        approval.decided_at = utc_now()
        approval.reviewer_notes = decision.reviewer_notes

        audit_logger.info(
            f"ACTION PROPOSAL RESOLVED: [{approval_id}] Status: {decision.decision.value} | Notes: {decision.reviewer_notes}"
        )
        return approval


approval_service = ApprovalService()
