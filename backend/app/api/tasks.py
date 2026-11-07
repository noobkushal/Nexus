"""Task Management Endpoints."""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from app.schemas.task import (
    TaskCreate,
    TaskListResponse,
    TaskPriority,
    TaskResponse,
    TaskStatus,
    TaskUpdate,
)
from app.services.task_service import task_service

router = APIRouter(prefix="/api/v1/tasks", tags=["Tasks"])


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    status: Optional[TaskStatus] = Query(None, description="Filter by status"),
    priority: Optional[TaskPriority] = Query(None, description="Filter by priority"),
) -> TaskListResponse:
    """Lists all tasks with optional status and priority filters."""
    tasks = task_service.list_tasks(status=status, priority=priority)
    return TaskListResponse(tasks=tasks, total=len(tasks))


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(payload: TaskCreate) -> TaskResponse:
    """Creates a new task."""
    return task_service.create_task(payload)


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str) -> TaskResponse:
    """Retrieves a single task by ID."""
    task = task_service.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task '{task_id}' not found.",
        )
    return task


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(task_id: str, payload: TaskUpdate) -> TaskResponse:
    """Updates an existing task."""
    updated = task_service.update_task(task_id, payload)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task '{task_id}' not found.",
        )
    return updated


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: str):
    """Deletes a task by ID."""
    deleted = task_service.delete_task(task_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task '{task_id}' not found.",
        )
    return None
