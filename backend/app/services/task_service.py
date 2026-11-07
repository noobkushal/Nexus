"""Task Service for tracking platform tasks and agent work items."""
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional
from app.core.logging import logger
from app.schemas.task import TaskCreate, TaskPriority, TaskResponse, TaskStatus, TaskUpdate


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TaskService:
    """In-memory task store with support for persistence hooks."""

    def __init__(self):
        self._tasks: Dict[str, TaskResponse] = {}
        self._seed_initial_tasks()

    def _seed_initial_tasks(self):
        """Seed foundational system tasks."""
        seeds = [
            (
                "Initialize NEXUS Foundation",
                "Scaffold modular FastAPI backend and establish deterministic mock AI provider.",
                TaskStatus.COMPLETED,
                TaskPriority.HIGH,
                "orchestrator",
            ),
            (
                "Deploy Dashboard Interface",
                "Construct Next.js dark-themed dashboard with responsive navigation and status cards.",
                TaskStatus.IN_PROGRESS,
                TaskPriority.HIGH,
                "personal_agent",
            ),
            (
                "Establish n8n Integration Pipeline",
                "Configure webhook listeners and execution contracts for external automations.",
                TaskStatus.PENDING,
                TaskPriority.MEDIUM,
                "orchestrator",
            ),
            (
                "Configure Long-Term Memory Vector Store",
                "Prepare PostgreSQL + pgvector schema and abstraction interfaces.",
                TaskStatus.PENDING,
                TaskPriority.LOW,
                "personal_agent",
            ),
        ]
        now = utc_now()
        for title, desc, status, priority, agent in seeds:
            tid = str(uuid.uuid4())[:8]
            self._tasks[tid] = TaskResponse(
                id=tid,
                title=title,
                description=desc,
                status=status,
                priority=priority,
                assigned_agent=agent,
                created_at=now,
                updated_at=now,
            )

    def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
    ) -> List[TaskResponse]:
        tasks = list(self._tasks.values())
        if status:
            tasks = [t for t in tasks if t.status == status]
        if priority:
            tasks = [t for t in tasks if t.priority == priority]
        # Return newest first
        return sorted(tasks, key=lambda t: t.created_at, reverse=True)

    def get_task(self, task_id: str) -> Optional[TaskResponse]:
        return self._tasks.get(task_id)

    def create_task(self, payload: TaskCreate) -> TaskResponse:
        now = utc_now()
        tid = str(uuid.uuid4())[:8]
        task = TaskResponse(
            id=tid,
            title=payload.title,
            description=payload.description,
            status=TaskStatus.PENDING,
            priority=payload.priority,
            assigned_agent=payload.assigned_agent,
            created_at=now,
            updated_at=now,
        )
        self._tasks[tid] = task
        logger.info(f"Task created: {tid} - {task.title}")
        return task

    def update_task(self, task_id: str, payload: TaskUpdate) -> Optional[TaskResponse]:
        task = self._tasks.get(task_id)
        if not task:
            return None

        update_data = payload.model_dump(exclude_unset=True)
        task_dict = task.model_dump()
        task_dict.update(update_data)
        task_dict["updated_at"] = utc_now()

        updated_task = TaskResponse(**task_dict)
        self._tasks[task_id] = updated_task
        logger.info(f"Task updated: {task_id} - status={updated_task.status}")
        return updated_task

    def delete_task(self, task_id: str) -> bool:
        if task_id in self._tasks:
            del self._tasks[task_id]
            logger.info(f"Task deleted: {task_id}")
            return True
        return False


task_service = TaskService()
