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
                status="sample",
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
                status="sample",
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
                status="sample",
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
                "# Candidate Profile\n\n"
                "No candidate profile is configured. Add verified roles, education, projects, and skills before using this draft."
            )

        # Only treat skills explicitly present in the user's source profile as candidate skills.
        # Job requirements and UI-provided focus skills are not evidence of candidate proficiency.
        candidate_skill_catalog = [
            "Python", "FastAPI", "Pydantic", "Asyncio", "Next.js", "TypeScript",
            "Tailwind CSS", "LangGraph", "Docker", "Git", "State Machines",
            "Sandboxed Filesystem Security", "Human-in-the-Loop Barriers", "PostgreSQL",
            "PowerShell", "Windows",
        ]
        profile_lower = profile_text.lower()
        description_lower = req.job_description.lower()
        profile_skills = [skill for skill in candidate_skill_catalog if skill.lower() in profile_lower]
        matched_skills = [
            skill for skill in profile_skills
            if skill.lower() in description_lower
        ]
        match_score = round(len(matched_skills) / max(len(profile_skills), 1), 2)

        tailored_summary = (
            f"Draft prepared for {req.target_role} at {req.target_company}. "
            "This document uses only the configured source profile and explicitly matched keywords. "
            "It does not invent employment history, education, certifications, or achievements. "
            "Review and verify every statement before submitting an application."
        )

        matched_skills_bullet = (
            "\n".join(f"- **{skill}**" for skill in matched_skills)
            if matched_skills
            else "- No verified profile skills matched automatically. Add or confirm relevant skills manually."
        )

        resume_md = (
            f"# Curriculum Vitae — Candidate Draft\n\n"
            f"> **Tailored For**: {req.target_role} @ {req.target_company}  \n"
            f"> **Generated By**: NEXUS Career Agent (Apex)  \n"
            f"> **Keyword Overlap (heuristic)**: {int(match_score * 100)}%  \n"
            f"> **Timestamp**: {now.isoformat()}\n\n"
            f"## Draft Summary\n"
            f"{tailored_summary}\n\n"
            f"## Profile Skills Matching the Job Description\n"
            f"{matched_skills_bullet}\n\n"
            f"## Verified Experience\n"
            f"[Add your actual roles, organizations, dates, responsibilities, and measurable achievements.]\n\n"
            f"## Education & Certifications\n"
            f"[Add only completed qualifications with accurate dates and credential names.]\n\n"
            f"## Projects\n"
            f"[Add projects you personally built, with your contribution, technology, and verifiable outcomes.]\n\n"
            f"## Source Profile (used for this draft)\n\n"
            f"{profile_text.strip()}\n\n"
            f"---\n"
            f"*Draft only. Verify all claims and complete the placeholders before using this document.*"
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
