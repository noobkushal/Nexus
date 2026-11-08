"""Owner-scoped persistent task management endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.auth import get_current_user
from app.db.models import UserModel
from app.db.session import get_db
from app.schemas.task import TaskCreate, TaskListResponse, TaskPriority, TaskResponse, TaskStatus, TaskUpdate
from app.services.task_service import task_service

router = APIRouter(prefix="/api/v1/tasks", tags=["Tasks"])


@router.get("", response_model=TaskListResponse)
async def list_tasks(status_filter: Optional[TaskStatus] = Query(None, alias="status"),
                     priority: Optional[TaskPriority] = Query(None),
                     current_user: UserModel = Depends(get_current_user),
                     db: Session = Depends(get_db)) -> TaskListResponse:
    tasks = task_service.list_tasks(current_user.id, db, status_filter, priority)
    return TaskListResponse(tasks=tasks, total=len(tasks))


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(payload: TaskCreate, current_user: UserModel = Depends(get_current_user),
                      db: Session = Depends(get_db)) -> TaskResponse:
    return task_service.create_task(payload, current_user.id, db)


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str, current_user: UserModel = Depends(get_current_user),
                   db: Session = Depends(get_db)) -> TaskResponse:
    task = task_service.get_task(task_id, current_user.id, db)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")
    return task


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(task_id: str, payload: TaskUpdate, current_user: UserModel = Depends(get_current_user),
                      db: Session = Depends(get_db)) -> TaskResponse:
    updated = task_service.update_task(task_id, payload, current_user.id, db)
    if not updated:
        raise HTTPException(status_code=404, detail="Task not found.")
    return updated


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: str, current_user: UserModel = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    if not task_service.delete_task(task_id, current_user.id, db):
        raise HTTPException(status_code=404, detail="Task not found.")
    return None
