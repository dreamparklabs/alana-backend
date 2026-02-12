from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import Optional
from app.models.task import TaskStatus, TaskPriority


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.BACKLOG
    priority: TaskPriority = TaskPriority.NO_PRIORITY
    estimate: Optional[int] = None
    due_date: Optional[datetime] = None
    project_id: UUID
    assignee_id: Optional[UUID] = None
    parent_id: Optional[UUID] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    estimate: Optional[int] = None
    due_date: Optional[datetime] = None
    assignee_id: Optional[UUID] = None
    sort_order: Optional[int] = None


class TaskResponse(BaseModel):
    id: UUID
    number: int
    title: str
    description: Optional[str] = None
    status: TaskStatus
    priority: TaskPriority
    estimate: Optional[int] = None
    due_date: Optional[datetime] = None
    project_id: UUID
    assignee_id: Optional[UUID] = None
    creator_id: UUID
    parent_id: Optional[UUID] = None
    sort_order: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
