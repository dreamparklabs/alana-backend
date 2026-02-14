from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class CycleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    start_date: datetime
    end_date: datetime
    
    @field_validator('end_date')
    @classmethod
    def end_date_after_start(cls, v, info):
        if 'start_date' in info.data and v <= info.data['start_date']:
            raise ValueError('end_date must be after start_date')
        return v


class CycleCreate(CycleBase):
    project_id: UUID


class CycleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: Optional[bool] = None


class CycleResponse(CycleBase):
    id: UUID
    number: int
    project_id: UUID
    is_active: bool
    sort_order: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CycleWithStatsResponse(CycleResponse):
    total_tasks: int = 0
    completed_tasks: int = 0
    progress_percentage: float = 0.0


class CycleListResponse(BaseModel):
    cycles: List[CycleResponse]
    total: int


class CycleTasksUpdate(BaseModel):
    task_ids: List[UUID]
