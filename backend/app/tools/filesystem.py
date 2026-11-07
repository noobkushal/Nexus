"""Sandboxed Filesystem Tool with Strict Directory Boundary Enforcement."""
from pathlib import Path
from typing import List, Optional
from app.core.config import settings
from app.core.logging import get_audit_logger, logger

audit_logger = get_audit_logger()


class SecurityViolationError(Exception):
    """Raised when an operation attempts to breach allowed path boundaries."""
    pass


class SandboxedFilesystem:
    """Manages secure filesystem operations restricted to approved directories."""

    def __init__(self, allowed_roots: Optional[List[Path]] = None):
        if allowed_roots is None:
            # By default only allow storage and explicitly configured subdirectories
            storage_path = Path(settings.STORAGE_DIR).resolve()
            self.allowed_roots = [storage_path]
        else:
            self.allowed_roots = [p.resolve() for p in allowed_roots]

    def _validate_path(self, target_path: Path) -> Path:
        resolved = target_path.resolve()
        is_safe = any(
            resolved == root or root in resolved.parents
            for root in self.allowed_roots
        )
        if not is_safe:
            audit_logger.warning(f"SECURITY ALERT: Attempted path escape to {resolved}")
            raise SecurityViolationError(
                f"Access denied: Path '{resolved}' is outside approved directories."
            )
        return resolved

    def list_files(self, relative_subpath: str = "") -> List[str]:
        base = self.allowed_roots[0]
        target = self._validate_path(base / relative_subpath)
        if not target.exists():
            return []
        return [str(p.relative_to(base)) for p in target.glob("**/*") if p.is_file()]

    def read_text_file(self, relative_path: str) -> str:
        base = self.allowed_roots[0]
        target = self._validate_path(base / relative_path)
        if not target.exists() or not target.is_file():
            raise FileNotFoundError(f"File not found: {relative_path}")
        return target.read_text(encoding="utf-8")

    def write_text_file(self, relative_path: str, content: str, requires_approval: bool = True) -> str:
        """Writes file with security boundary check. In Milestone 1, consequential writes log audit."""
        base = self.allowed_roots[0]
        target = self._validate_path(base / relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        audit_logger.info(f"Filesystem write completed: {target}")
        return f"File written successfully: {relative_path}"


sandboxed_fs = SandboxedFilesystem()
