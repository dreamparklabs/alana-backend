from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


# Association table for many-to-many relationship between tasks and labels
task_labels = Table(
    'task_labels',
    Base.metadata,
    Column('task_id', UUID(as_uuid=True), ForeignKey('tasks.id', ondelete='CASCADE'), primary_key=True),
    Column('label_id', UUID(as_uuid=True), ForeignKey('labels.id', ondelete='CASCADE'), primary_key=True),
    Column('created_at', DateTime, default=datetime.utcnow)
)


class Label(Base):
    __tablename__ = "labels"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    color = Column(String(7), nullable=False, default="#6B7280")
    description = Column(String(500), nullable=True)
    sort_order = Column(Float, default=65535)
    
    # Labels can be workspace-wide or project-specific
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    workspace = relationship("Workspace", back_populates="labels")
    project = relationship("Project", back_populates="labels")
    tasks = relationship("Task", secondary=task_labels, back_populates="labels")

    def __repr__(self):
        return f"<Label {self.name}>"
