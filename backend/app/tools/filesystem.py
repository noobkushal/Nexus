"""Sandboxed Filesystem Tool with Strict Directory Boundary Enforcement."""
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
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
            storage_path = Path(settings.STORAGE_DIR).resolve()
            self.allowed_roots = [storage_path]
        else:
            self.allowed_roots = [p.resolve() for p in allowed_roots]
        self._ensure_storage_structure()

    def _ensure_storage_structure(self):
        """Ensures all standard storage compartments exist."""
        base = self.allowed_roots[0]
        compartments = ["profile", "documents", "media", "projects", "generated", "attachments"]
        for comp in compartments:
            (base / comp).mkdir(parents=True, exist_ok=True)

        # Seed sample documents if empty
        overview_doc = base / "documents" / "nexus_quickstart.md"
        if not overview_doc.exists():
            overview_doc.write_text(
                "# NEXUS Quickstart Guide\n\n"
                "Welcome to NEXUS AI. This document is safely stored inside your local sandboxed filesystem.\n\n"
                "- Compartment: `storage/documents/`\n"
                "- Security: Quarantined & audited\n"
                "- Access: Least privilege\n",
                encoding="utf-8",
            )

        profile_doc = base / "profile" / "system_user.md"
        if not profile_doc.exists():
            profile_doc.write_text(
                "# System User Profile\n\n"
                "Primary Operator: Software Architect & Developer\n"
                "Preferred Environment: Windows 11, PowerShell, FastAPI, Next.js\n",
                encoding="utf-8",
            )

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

    def list_compartments(self) -> List[str]:
        base = self.allowed_roots[0]
        return [p.name for p in base.iterdir() if p.is_dir()]

    def list_files(self, relative_subpath: str = "") -> List[Dict[str, Any]]:
        base = self.allowed_roots[0]
        target = self._validate_path(base / relative_subpath)
        if not target.exists():
            return []

        results = []
        for p in target.glob("**/*"):
            if p.is_file():
                rel = str(p.relative_to(base)).replace("\\", "/")
                stat = p.stat()
                results.append({
                    "path": rel,
                    "name": p.name,
                    "size_bytes": stat.st_size,
                    "extension": p.suffix.lower(),
                    "modified_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                })
        return sorted(results, key=lambda f: f["path"])

    def read_text_file(self, relative_path: str) -> str:
        base = self.allowed_roots[0]
        target = self._validate_path(base / relative_path)
        if not target.exists() or not target.is_file():
            raise FileNotFoundError(f"File not found: {relative_path}")
        return target.read_text(encoding="utf-8")

    def write_text_file(self, relative_path: str, content: str, requires_approval: bool = True) -> str:
        base = self.allowed_roots[0]
        target = self._validate_path(base / relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        audit_logger.info(f"Filesystem write completed: {target}")
        return f"File written successfully: {relative_path}"

    def delete_file(self, relative_path: str) -> bool:
        base = self.allowed_roots[0]
        target = self._validate_path(base / relative_path)
        if target.exists() and target.is_file():
            target.unlink()
            audit_logger.warning(f"Filesystem delete completed: {target}")
            return True
        return False


sandboxed_fs = SandboxedFilesystem()
