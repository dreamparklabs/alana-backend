from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class CommentBase(BaseModel):
    content: str
    content_html: Optional[str] = None


class CommentCreate(CommentBase):
    entity_type: str
    entity_id: UUID
    parent_id: Optional[UUID] = None


class CommentUpdate(BaseModel):
    content: Optional[str] = None
    content_html: Optional[str] = None


class AuthorInfo(BaseModel):
    id: UUID
    full_name: str
    avatar_url: Optional[str] = None

    class Config:
        from_attributes = True


class CommentResponse(BaseModel):
    id: UUID
    entity_type: str
    entity_id: UUID
    content: str
    content_html: Optional[str] = None
    author_id: UUID
    parent_id: Optional[UUID] = None
    workspace_id: UUID
    project_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    author: Optional[AuthorInfo] = None
    replies: Optional[List["CommentResponse"]] = None

    class Config:
        from_attributes = True


class CommentListResponse(BaseModel):
    comments: list[CommentResponse]
    total: int
