from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base


class MemberRole(str, enum.Enum):
    OWNER = "owner"      # Full access, can delete workspace
    ADMIN = "admin"      # Can manage members and settings
    MEMBER = "member"    # Can create and edit tasks
    VIEWER = "viewer"    # Read-only access


class WorkspaceMember(Base):
    __tablename__ = "workspace_members"
    __table_args__ = (
        UniqueConstraint('workspace_id', 'user_id', name='uq_workspace_member'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    role = Column(String(50), nullable=False, default=MemberRole.MEMBER.value)
    
    # Invitation tracking
    invited_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    joined_at = Column(DateTime, default=datetime.utcnow)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    workspace = relationship("Workspace", back_populates="members")
    user = relationship("User", foreign_keys=[user_id], back_populates="workspace_memberships")
    invited_by = relationship("User", foreign_keys=[invited_by_id])


class ProjectMember(Base):
    """Optional: Project-level membership for more granular access"""
    __tablename__ = "project_members"
    __table_args__ = (
        UniqueConstraint('project_id', 'user_id', name='uq_project_member'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    role = Column(String(50), nullable=False, default=MemberRole.MEMBER.value)
    
    joined_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="members")
    user = relationship("User", foreign_keys=[user_id], back_populates="project_memberships")
