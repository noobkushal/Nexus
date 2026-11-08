"""Persistent, owner-scoped task service."""
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from app.db.models import TaskModel
from app.schemas.task import TaskCreate, TaskPriority, TaskResponse, TaskStatus, TaskUpdate


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _to_response(row: TaskModel) -> TaskResponse:
    return TaskResponse(
        id=row.id, title=row.title, description=row.description,
        status=TaskStatus(row.status), priority=TaskPriority(row.priority),
        assigned_agent=row.assigned_agent, created_at=row.created_at, updated_at=row.updated_at,
    )


class TaskService:
    """All task operations are persisted and scoped to the authenticated owner."""

    def list_tasks(self, owner_id: str, db: Session, status: Optional[TaskStatus] = None,
                   priority: Optional[TaskPriority] = None) -> List[TaskResponse]:
        query = db.query(TaskModel).filter(TaskModel.owner_id == owner_id)
        if status:
            query = query.filter(TaskModel.status == status.value)
        if priority:
            query = query.filter(TaskModel.priority == priority.value)
        return [_to_response(row) for row in query.order_by(TaskModel.created_at.desc()).all()]

    def get_task(self, task_id: str, owner_id: str, db: Session) -> Optional[TaskResponse]:
        row = db.query(TaskModel).filter(TaskModel.id == task_id, TaskModel.owner_id == owner_id).first()
        return _to_response(row) if row else None

    def create_task(self, payload: TaskCreate, owner_id: str, db: Session) -> TaskResponse:
        now = utc_now()
        row = TaskModel(
            id=str(uuid.uuid4()), owner_id=owner_id, title=payload.title.strip(),
            description=payload.description, status=TaskStatus.PENDING.value,
            priority=payload.priority.value, assigned_agent=payload.assigned_agent,
            created_at=now, updated_at=now,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return _to_response(row)

    def update_task(self, task_id: str, payload: TaskUpdate, owner_id: str, db: Session) -> Optional[TaskResponse]:
        row = db.query(TaskModel).filter(TaskModel.id == task_id, TaskModel.owner_id == owner_id).first()
        if not row:
            return None
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(row, key, value.value if hasattr(value, "value") else value)
        row.updated_at = utc_now()
        db.commit()
        db.refresh(row)
        return _to_response(row)

    def delete_task(self, task_id: str, owner_id: str, db: Session) -> bool:
        row = db.query(TaskModel).filter(TaskModel.id == task_id, TaskModel.owner_id == owner_id).first()
        if not row:
            return False
        db.delete(row)
        db.commit()
        return True


task_service = TaskService()
