from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class LabelBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    color: str = Field(default="#6B7280", pattern=r"^#[0-9A-Fa-f]{6}$")
    description: Optional[str] = Field(None, max_length=500)


class LabelCreate(LabelBase):
    workspace_id: UUID
    project_id: Optional[UUID] = None


class LabelUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    description: Optional[str] = Field(None, max_length=500)
    sort_order: Optional[float] = None


class LabelResponse(LabelBase):
    id: UUID
    workspace_id: UUID
    project_id: Optional[UUID]
    sort_order: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LabelListResponse(BaseModel):
    labels: List[LabelResponse]
    total: int
