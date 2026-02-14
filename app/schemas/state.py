from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


class StateBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    color: str = Field(default="#6B7280", pattern=r"^#[0-9A-Fa-f]{6}$")
    group: str = Field(default="backlog")
    sequence: float = Field(default=65535)
    is_default: bool = Field(default=False)


class StateCreate(StateBase):
    project_id: UUID


class StateUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    group: Optional[str] = None
    sequence: Optional[float] = None
    is_default: Optional[bool] = None


class StateResponse(StateBase):
    id: UUID
    project_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StateListResponse(BaseModel):
    states: list[StateResponse]
    total: int
