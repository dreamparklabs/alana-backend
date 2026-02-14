from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True)
    color = Column(String(7), nullable=True)  # Hex color
    prefix = Column(String(10), nullable=False)  # Task prefix like "ALN" for ALN-123
    task_count = Column(Integer, default=0)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    workspace = relationship("Workspace", back_populates="projects")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    states = relationship("State", back_populates="project", cascade="all, delete-orphan")
    labels = relationship("Label", back_populates="project")
    cycles = relationship("Cycle", back_populates="project", cascade="all, delete-orphan")
    activities = relationship("Activity", back_populates="project")
    comments = relationship("Comment", back_populates="project")
    members = relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan")
