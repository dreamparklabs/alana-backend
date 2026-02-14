from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class Activity(Base):
    """Tracks all changes to entities for activity feeds"""
    __tablename__ = "activities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # What was changed
    entity_type = Column(String(50), nullable=False)  # "task", "project", "cycle"
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    
    # What kind of change
    action = Column(String(50), nullable=False)  # "created", "updated", "deleted", "commented"
    
    # Who made the change
    actor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Change details
    field = Column(String(100), nullable=True)  # Which field changed (for updates)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    
    # Additional context
    metadata_ = Column("metadata", JSONB, nullable=True)  # Extra data like comment text
    
    # Context
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    actor = relationship("User", foreign_keys=[actor_id])
    project = relationship("Project", back_populates="activities")
    workspace = relationship("Workspace", back_populates="activities")
