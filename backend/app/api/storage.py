"""Sandboxed Filesystem and Git Checkpoint API Endpoints."""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field
from app.services.git_service import git_service
from app.tools.filesystem import SecurityViolationError, sandboxed_fs

router = APIRouter(prefix="/api/v1/storage", tags=["Storage & Git"])


class FileWriteRequest(BaseModel):
    path: str = Field(..., description="Relative path within storage (e.g. 'documents/notes.md')")
    content: str = Field(..., description="Text content to write")


class GitCheckpointRequest(BaseModel):
    description: str = Field(..., max_length=200, description="Checkpoint commit message")
    author_agent: Optional[str] = Field("coding_agent", description="Requesting agent name")


@router.get("/compartments")
async def list_compartments() -> List[str]:
    """Lists authorized storage compartment folders."""
    return sandboxed_fs.list_compartments()


@router.get("/files")
async def list_files(
    compartment: Optional[str] = Query(None, description="Optional compartment filter (e.g. 'documents')"),
) -> List[Dict[str, Any]]:
    """Lists files inside sandboxed storage with metadata."""
    subpath = compartment or ""
    try:
        return sandboxed_fs.list_files(subpath)
    except SecurityViolationError as sve:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(sve))


@router.get("/read")
async def read_file(path: str = Query(..., description="Relative path to file")) -> Dict[str, Any]:
    """Reads content of a sandboxed file."""
    try:
        content = sandboxed_fs.read_text_file(path)
        return {"path": path, "content": content}
    except FileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"File not found: {path}")
    except SecurityViolationError as sve:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(sve))


@router.post("/write")
async def write_file(req: FileWriteRequest) -> Dict[str, Any]:
    """Writes content to a sandboxed file within approved directory boundaries."""
    try:
        msg = sandboxed_fs.write_text_file(req.path, req.content)
        return {"success": True, "message": msg, "path": req.path}
    except SecurityViolationError as sve:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(sve))


@router.delete("/delete")
async def delete_file(path: str = Query(..., description="Relative path to file")) -> Dict[str, Any]:
    """Deletes a file from approved storage."""
    try:
        deleted = sandboxed_fs.delete_file(path)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"File not found: {path}")
        return {"success": True, "message": f"Deleted {path}"}
    except SecurityViolationError as sve:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(sve))


# Git Checkpoint Endpoints
@router.get("/git/status")
async def get_git_status() -> Dict[str, Any]:
    """Inspects Git repository state, active branch, and modified file count."""
    return git_service.get_repo_status()


@router.get("/git/checkpoints")
async def list_git_checkpoints(
    limit: int = Query(5, ge=1, le=20, description="Max commits to return"),
) -> List[Dict[str, str]]:
    """Lists recent Git safety checkpoints."""
    return git_service.list_recent_checkpoints(limit=limit)


@router.post("/git/checkpoint")
async def create_git_checkpoint(req: GitCheckpointRequest) -> Dict[str, Any]:
    """Creates a safety Git commit snapshot before consequential edits."""
    res = git_service.create_checkpoint(description=req.description, author_agent=req.author_agent)
    if not res.get("success"):
        raise HTTPException(status_code=500, detail=res.get("error", "Git checkpoint failed"))
    return res
