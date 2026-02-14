from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import Optional, List
from app.models.task import TaskPriority


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    state_id: Optional[UUID] = None
    priority: TaskPriority = TaskPriority.NO_PRIORITY
    estimate: Optional[int] = None
    due_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    project_id: UUID
    assignee_id: Optional[UUID] = None
    parent_id: Optional[UUID] = None
    label_ids: Optional[List[UUID]] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    state_id: Optional[UUID] = None
    priority: Optional[TaskPriority] = None
    estimate: Optional[int] = None
    due_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    assignee_id: Optional[UUID] = None
    sort_order: Optional[int] = None
    label_ids: Optional[List[UUID]] = None


class LabelBrief(BaseModel):
    id: UUID
    name: str
    color: str

    class Config:
        from_attributes = True


class StateBrief(BaseModel):
    id: UUID
    name: str
    color: str
    group: str

    class Config:
        from_attributes = True


class TaskResponse(BaseModel):
    id: UUID
    number: int
    title: str
    description: Optional[str] = None
    state_id: Optional[UUID] = None
    state: Optional[StateBrief] = None
    priority: TaskPriority
    estimate: Optional[int] = None
    due_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    project_id: UUID
    assignee_id: Optional[UUID] = None
    creator_id: UUID
    parent_id: Optional[UUID] = None
    sort_order: int
    labels: List[LabelBrief] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    tasks: List[TaskResponse]
    total: int
