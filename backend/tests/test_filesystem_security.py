"""Test Sandboxed Filesystem Security Boundaries."""
import pytest
from pathlib import Path
from app.tools.filesystem import SandboxedFilesystem, SecurityViolationError


def test_allowed_path_within_root(tmp_path: Path):
    fs = SandboxedFilesystem(allowed_roots=[tmp_path])
    res = fs.write_text_file("notes.txt", "Nexus test note")
    assert "notes.txt" in res
    assert fs.read_text_file("notes.txt") == "Nexus test note"


def test_path_traversal_prevention(tmp_path: Path):
    fs = SandboxedFilesystem(allowed_roots=[tmp_path])
    with pytest.raises(SecurityViolationError):
        # Attempt directory traversal outside tmp_path
        fs._validate_path(tmp_path / ".." / "system32" / "test.txt")
