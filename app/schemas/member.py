from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from uuid import UUID
from enum import Enum


class MemberRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class MemberBase(BaseModel):
    role: MemberRole = MemberRole.MEMBER


class WorkspaceMemberCreate(MemberBase):
    user_id: Optional[UUID] = None
    email: Optional[EmailStr] = None  # For inviting by email


class WorkspaceMemberUpdate(BaseModel):
    role: Optional[MemberRole] = None


class ProjectMemberCreate(MemberBase):
    user_id: UUID


class ProjectMemberUpdate(BaseModel):
    role: Optional[MemberRole] = None


class UserInfo(BaseModel):
    id: UUID
    email: str
    full_name: str
    avatar_url: Optional[str] = None

    class Config:
        from_attributes = True


class WorkspaceMemberResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    user_id: UUID
    role: str
    joined_at: datetime
    created_at: datetime
    user: Optional[UserInfo] = None
    invited_by: Optional[UserInfo] = None

    class Config:
        from_attributes = True


class ProjectMemberResponse(BaseModel):
    id: UUID
    project_id: UUID
    user_id: UUID
    role: str
    joined_at: datetime
    created_at: datetime
    user: Optional[UserInfo] = None

    class Config:
        from_attributes = True


class MemberListResponse(BaseModel):
    members: list[WorkspaceMemberResponse]
    total: int


class ProjectMemberListResponse(BaseModel):
    members: list[ProjectMemberResponse]
    total: int


class InviteMemberRequest(BaseModel):
    email: EmailStr
    role: MemberRole = MemberRole.MEMBER
