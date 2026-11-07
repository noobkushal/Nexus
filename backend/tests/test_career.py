"""Tests for Career Intelligence and Resume Tailoring Engine."""
import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.schemas.career import ResumeTailorRequest
from app.services.career_service import career_service
from app.tools.filesystem import sandboxed_fs


def test_list_and_get_jobs():
    """Verify default discovered job opportunities exist."""
    jobs = career_service.list_jobs()
    assert len(jobs) >= 2
    assert jobs[0].match_score >= 0.80

    first_job = jobs[0]
    fetched = career_service.get_job(first_job.id)
    assert fetched is not None
    assert fetched.title == first_job.title


def test_tailor_resume_service():
    """Verify tailoring a resume generates a custom CV and persists to storage/generated/."""
    req = ResumeTailorRequest(
        target_role="Lead AI Systems Architect",
        target_company="Anthropic Systems",
        job_description=(
            "Looking for an architect with Python, FastAPI, Next.js, state machine graphs, "
            "and sandboxed filesystem security expertise to build local-first AI tools."
        ),
        focus_skills=["FastAPI", "Next.js", "Sandboxed Security"],
    )
    result = career_service.tailor_resume(req)

    assert result.target_company == "Anthropic Systems"
    assert result.match_score >= 0.80
    assert result.relative_path.startswith("generated/tailored_resume_anthropic_systems_")
    assert "FastAPI" in result.matched_skills

    # Verify physical file existence in storage
    saved_text = sandboxed_fs.read_text_file(result.relative_path)
    assert "# Curriculum Vitae: Principal AI & Systems Architect" in saved_text
    assert "Lead AI Systems Architect @ Anthropic Systems" in saved_text
    assert "NEXUS AI Platform" in saved_text


@pytest.mark.asyncio
async def test_career_api_endpoints():
    """Verify career endpoints via FastAPI client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Get jobs
        jobs_resp = await client.get("/api/v1/career/jobs")
        assert jobs_resp.status_code == 200
        jobs_data = jobs_resp.json()
        assert len(jobs_data) >= 1

        # Tailor CV
        tailor_payload = {
            "target_role": "Senior Automation Engineer",
            "target_company": "CloudForge Labs",
            "job_description": "We need engineers fluent in Python, Docker, n8n webhooks, and sandboxed storage systems.",
            "focus_skills": ["Python", "n8n", "Sandboxed Storage"],
        }
        post_resp = await client.post("/api/v1/career/tailor-resume", json=tailor_payload)
        assert post_resp.status_code == 201
        data = post_resp.json()
        assert data["target_company"] == "CloudForge Labs"
        assert "CloudForge Labs" in data["content"]

        # List resumes
        resumes_resp = await client.get("/api/v1/career/resumes")
        assert resumes_resp.status_code == 200
        resumes_data = resumes_resp.json()
        assert any("cloudforge_labs" in r["filename"] for r in resumes_data)
