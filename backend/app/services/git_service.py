"""Git Checkpoint and Local Repository Safety Service."""
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional
from app.core.config import ROOT_DIR
from app.core.logging import get_audit_logger, logger

audit_logger = get_audit_logger()


class GitService:
    """Manages Git checkpoints and branch state for local project workspaces."""

    def __init__(self, repo_root: Optional[Path] = None):
        self.repo_root = (repo_root or ROOT_DIR).resolve()

    def _run_git_command(self, args: List[str]) -> subprocess.CompletedProcess:
        """Executes a bounded git command inside the designated repo root."""
        return subprocess.run(
            ["git"] + args,
            cwd=str(self.repo_root),
            capture_output=True,
            text=True,
            timeout=10,
        )

    def get_repo_status(self) -> Dict[str, Any]:
        """Inspects current branch, commit hash, and dirty status."""
        try:
            # Check branch
            branch_proc = self._run_git_command(["rev-parse", "--abbrev-ref", "HEAD"])
            branch = branch_proc.stdout.strip() if branch_proc.returncode == 0 else "unknown"

            # Check commit
            commit_proc = self._run_git_command(["rev-parse", "--short", "HEAD"])
            commit = commit_proc.stdout.strip() if commit_proc.returncode == 0 else "none"

            # Check status
            status_proc = self._run_git_command(["status", "--porcelain"])
            modified_files = [line.strip() for line in status_proc.stdout.splitlines() if line.strip()]

            # Last commit message
            log_proc = self._run_git_command(["log", "-1", "--pretty=%B"])
            last_msg = log_proc.stdout.strip() if log_proc.returncode == 0 else "No commits"

            return {
                "is_git_repo": True,
                "repo_path": str(self.repo_root),
                "current_branch": branch,
                "latest_commit": commit,
                "last_commit_message": last_msg,
                "clean_working_tree": len(modified_files) == 0,
                "uncommitted_changes_count": len(modified_files),
                "uncommitted_files": modified_files[:10],
            }
        except Exception as exc:
            logger.warning(f"Git inspection failed: {exc}")
            return {
                "is_git_repo": False,
                "repo_path": str(self.repo_root),
                "error": str(exc),
            }

    def list_recent_checkpoints(self, limit: int = 5) -> List[Dict[str, str]]:
        """Lists recent commits / checkpoints."""
        try:
            proc = self._run_git_command(["log", f"-{limit}", "--pretty=format:%h|%an|%ad|%s", "--date=short"])
            if proc.returncode != 0:
                return []
            checkpoints = []
            for line in proc.stdout.splitlines():
                if "|" in line:
                    parts = line.split("|", 3)
                    checkpoints.append({
                        "hash": parts[0],
                        "author": parts[1],
                        "date": parts[2],
                        "message": parts[3],
                    })
            return checkpoints
        except Exception as exc:
            logger.warning(f"Failed to list git checkpoints: {exc}")
            return []

    def create_checkpoint(self, description: str, author_agent: str = "coding_agent") -> Dict[str, Any]:
        """Creates an automated safety commit checkpoint before consequential modifications."""
        try:
            # Stage changes
            self._run_git_command(["add", "."])

            # Commit
            commit_msg = f"checkpoint({author_agent}): {description}"
            proc = self._run_git_command(["commit", "-m", commit_msg])

            audit_logger.info(f"Git safety checkpoint created: {commit_msg}")
            status = self.get_repo_status()
            return {
                "success": proc.returncode == 0 or "nothing to commit" in proc.stdout,
                "message": commit_msg,
                "commit": status.get("latest_commit"),
                "clean": status.get("clean_working_tree"),
            }
        except Exception as exc:
            logger.error(f"Checkpoint creation failed: {exc}")
            return {
                "success": False,
                "error": str(exc),
            }


git_service = GitService()
