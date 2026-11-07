"""Career Intelligence, Job Discovery, and Resume Tailoring Service.

Provides candidate profile alignment, semantic keyword matching, and generates
quarantined, tailored resume variants stored in storage/generated/.
"""
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.agents.orchestrator import orchestrator
from app.core.config import settings
from app.core.logging import get_audit_logger, logger
from app.schemas.career import JobOpportunity, ResumeTailorRequest, ResumeTailorResponse, utc_now
from app.tools.filesystem import sandboxed_fs

audit_logger = get_audit_logger()


class CareerService:
    """Manages job opportunities and creates tailored CV/resume documents."""

    def __init__(self):
        self._jobs: Dict[str, JobOpportunity] = {}
        self._seed_default_jobs()

    def _seed_default_jobs(self):
        seed_list = [
            JobOpportunity(
                id="job-001",
                title="Lead AI Systems & Agentic Orchestration Architect",
                company="NexusLabs Partner Systems",
                location="Remote (Global)",
                skills_required=["Python", "FastAPI", "Next.js", "State Machines", "Docker", "Sandboxing"],
                description=(
                    "Looking for a principal software engineer to architect local-first autonomous agent frameworks. "
                    "Must have expertise in deterministic state routing, human-in-the-loop safety guards, "
                    "FastAPI asynchronous services, and Next.js reactive dashboards."
                ),
                match_score=0.96,
                status="discovered",
            ),
            JobOpportunity(
                id="job-002",
                title="Staff Automation Engineer (n8n & Distributed Workflows)",
                company="VectorScale Cloud",
                location="San Francisco, CA / Remote",
                skills_required=["Python", "n8n", "Webhooks", "PostgreSQL", "CI/CD", "Security"],
                description=(
                    "Join our core automation squad building fault-tolerant workflow orchestrators. "
                    "Requires deep knowledge of event-driven architectures, webhook dispatching, and sandboxed storage."
                ),
                match_score=0.88,
                status="discovered",
            ),
            JobOpportunity(
                id="job-003",
                title="Senior Full-Stack AI Engineer",
                company="Cognitive Edge Labs",
                location="Remote (North America / EMEA)",
                skills_required=["TypeScript", "Next.js", "Tailwind CSS", "Python", "Local LLMs"],
                description=(
                    "Seeking a senior engineer to craft developer interfaces for local AI models. "
                    "Focus on low-latency interfaces, responsive UX, and dark-themed AI workstations."
                ),
                match_score=0.92,
                status="discovered",
            ),
        ]
        for job in seed_list:
            self._jobs[job.id] = job

    def list_jobs(self, status: Optional[str] = None) -> List[JobOpportunity]:
        items = list(self._jobs.values())
        if status:
            items = [j for j in items if j.status == status]
        return sorted(items, key=lambda x: x.match_score, reverse=True)

    def get_job(self, job_id: str) -> Optional[JobOpportunity]:
        return self._jobs.get(job_id)

    def tailor_resume(self, req: ResumeTailorRequest) -> ResumeTailorResponse:
        """Analyzes target requirements and generates a customized Markdown resume."""
        now = datetime.now(timezone.utc)
        rid = f"cv-{uuid.uuid4().hex[:8]}"
        company_slug = re.sub(r"[^a-zA-Z0-9]+", "_", req.target_company.lower()).strip("_") or "target"
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        rel_path = f"generated/tailored_resume_{company_slug}_{timestamp}.md"

        # Read base candidate profile if exists
        try:
            profile_text = sandboxed_fs.read_text_file("profile/system_user.md")
        except Exception:
            profile_text = (
                "# System User Profile\n\n"
                "Software Architect & Full-Stack Engineer specializing in local-first AI and autonomous systems."
            )

        # Candidate key skills pool
        candidate_skills = [
            "Python", "FastAPI", "Pydantic", "Asyncio", "Next.js", "TypeScript",
            "Tailwind CSS", "LangGraph", "Docker", "Git", "State Machines",
            "Sandboxed Filesystem Security", "Human-in-the-Loop Barriers", "PostgreSQL",
        ]

        desc_lower = req.job_description.lower()
        matched_skills = [s for s in candidate_skills if s.lower() in desc_lower]
        # Include explicitly requested focus skills
        for fs in req.focus_skills:
            if fs not in matched_skills:
                matched_skills.append(fs)

        if not matched_skills:
            matched_skills = ["FastAPI", "Python", "Next.js", "State Machines", "Security Sandboxing"]

        match_score = min(1.0, 0.70 + (len(matched_skills) * 0.05))

        tailored_summary = (
            f"Accomplished Systems Architect with demonstrated excellence in building local-first, "
            f"autonomous AI automation platforms. Proven track record deploying deterministic state-machine "
            f"architectures, asynchronous FastAPI microservices, and reactive Next.js interfaces tailored for "
            f"{req.target_company}'s {req.target_role} mission."
        )

        matched_skills_bullet = "\n".join(f"- **{skill}**" for skill in matched_skills)

        # Assemble customized resume document
        resume_md = (
            f"# Curriculum Vitae: Principal AI & Systems Architect\n\n"
            f"> **Tailored For**: {req.target_role} @ {req.target_company}  \n"
            f"> **Generated By**: NEXUS Career Agent (Apex)  \n"
            f"> **Alignment Match Score**: {int(match_score * 100)}%  \n"
            f"> **Timestamp**: {now.isoformat()}\n\n"
            f"## Executive Summary\n"
            f"{tailored_summary}\n\n"
            f"## Target Skill Alignment\n"
            f"{matched_skills_bullet}\n\n"
            f"## Core Architecture Highlights & Experience\n\n"
            f"### Lead Architect & Full-Stack Engineer — NEXUS AI Platform (2025 – Present)\n"
            f"- **Modular AI Operating System**: Engineered local-first autonomous runtime supporting offline-safe operation with zero external AI dependencies.\n"
            f"- **Deterministic Multi-Agent Graph**: Built directed state graph executing intent classification, multi-agent dispatch (Aura, Scout, Forge, Conduit, Apex), and safety barrier intercepts.\n"
            f"- **Sandboxed Security**: Restricted filesystem tools to quarantined directories with anti-SSRF protections and untrusted HTML sanitization.\n"
            f"- **Human-in-the-Loop Gate**: Enforced mandatory approval mechanisms before consequential operations (file deletion, external communications, automated deployments).\n"
            f"- **Full-Stack Delivery**: Designed high-performance Next.js 14 App Router dashboard with responsive telemetry, file previewers, and real-time trace diagnostics.\n\n"
            f"## Candidate Profile Baseline\n\n"
            f"```\n{profile_text.strip()}\n```\n\n"
            f"---\n"
            f"*Generated locally and safely quarantined inside E:\\NEXUS\\storage\\generated.*"
        )

        # Save to sandboxed storage
        sandboxed_fs.write_text_file(rel_path, resume_md, requires_approval=False)

        # Update job status if matching existing job
        if req.job_id and req.job_id in self._jobs:
            self._jobs[req.job_id].status = "tailored"

        orchestrator.log_activity(
            agent_id="career_agent",
            action="Resume Tailored",
            details=f"Customized CV for {req.target_role} at {req.target_company} ({match_score:.0%})",
            status="completed",
        )
        audit_logger.info(f"Tailored resume saved: {rel_path}")

        return ResumeTailorResponse(
            id=rid,
            target_role=req.target_role,
            target_company=req.target_company,
            match_score=round(match_score, 2),
            tailored_summary=tailored_summary,
            matched_skills=matched_skills,
            relative_path=rel_path,
            content=resume_md,
            created_at=now,
        )

    def list_tailored_resumes(self) -> List[Dict[str, Any]]:
        """Lists all tailored resumes stored in storage/generated/."""
        storage_base = Path(settings.STORAGE_DIR).resolve()
        generated_dir = storage_base / "generated"
        files = sorted(generated_dir.glob("tailored_resume_*.md"), key=lambda p: p.stat().st_mtime, reverse=True)

        results = []
        for f in files:
            stat = f.stat()
            results.append({
                "filename": f.name,
                "relative_path": f"generated/{f.name}",
                "size_bytes": stat.st_size,
                "modified_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
            })
        return results


career_service = CareerService()
