"""Tests for Application and Website Scaffolding Tool."""
import pytest
from app.tools.filesystem import sandboxed_fs
from app.tools.scaffolder import ApplicationScaffolder, ProjectScaffoldError, app_scaffolder


def test_list_templates():
    """Verify supported project templates."""
    templates = app_scaffolder.list_templates()
    assert "fastapi_microservice" in templates
    assert "nextjs_landing" in templates
    assert "python_cli" in templates


def test_scaffold_fastapi_microservice():
    """Verify scaffolding a FastAPI project inside storage/projects/."""
    result = app_scaffolder.scaffold_project(
        project_name="metrics_api",
        template="fastapi_microservice",
        description="Telemetry microservice for NEXUS metrics",
    )

    assert result["project_name"] == "metrics_api"
    assert result["template"] == "fastapi_microservice"
    assert result["status"] == "ready"
    assert len(result["created_files"]) >= 4

    # Verify created files exist on disk
    main_code = sandboxed_fs.read_text_file("projects/metrics_api/main.py")
    assert "FastAPI" in main_code
    assert 'app = FastAPI(title="Metrics_Api"' in main_code

    test_code = sandboxed_fs.read_text_file("projects/metrics_api/tests/test_api.py")
    assert "test_health" in test_code


def test_scaffold_invalid_template():
    """Verify invalid template raises ProjectScaffoldError."""
    with pytest.raises(ProjectScaffoldError, match="Unsupported template"):
        app_scaffolder.scaffold_project(
            project_name="fail_project",
            template="unsupported_template_xyz",
        )
