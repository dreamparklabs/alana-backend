from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import Optional


class ProjectCreate(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    prefix: str
    workspace_id: UUID
    lead_id: Optional[UUID] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    lead_id: Optional[UUID] = None


class ProjectResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    prefix: str
    task_count: int
    workspace_id: UUID
    lead_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
