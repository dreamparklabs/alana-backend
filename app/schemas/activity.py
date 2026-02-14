from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime
from uuid import UUID


class ActivityBase(BaseModel):
    entity_type: str
    entity_id: UUID
    action: str
    field: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    metadata_: Optional[dict] = None


class ActivityCreate(ActivityBase):
    workspace_id: UUID
    project_id: Optional[UUID] = None


class ActorInfo(BaseModel):
    id: UUID
    full_name: str
    avatar_url: Optional[str] = None

    class Config:
        from_attributes = True


class ActivityResponse(BaseModel):
    id: UUID
    entity_type: str
    entity_id: UUID
    action: str
    actor_id: UUID
    field: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    metadata_: Optional[dict] = None
    project_id: Optional[UUID] = None
    workspace_id: UUID
    created_at: datetime
    actor: Optional[ActorInfo] = None

    class Config:
        from_attributes = True


class ActivityListResponse(BaseModel):
    activities: list[ActivityResponse]
    total: int
