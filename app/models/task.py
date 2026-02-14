from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base


class TaskPriority(str, enum.Enum):
    NO_PRIORITY = "no_priority"
    URGENT = "urgent"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Task(Base):
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    number = Column(Integer, nullable=False)  # Task number within project
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    state_id = Column(UUID(as_uuid=True), ForeignKey("states.id"), nullable=True)
    priority = Column(Enum(TaskPriority), default=TaskPriority.NO_PRIORITY, nullable=False)
    estimate = Column(Integer, nullable=True)  # Story points or hours
    due_date = Column(DateTime, nullable=True)
    start_date = Column(DateTime, nullable=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    assignee_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    creator_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="tasks")
    state = relationship("State", back_populates="tasks")
    assignee = relationship("User", back_populates="assigned_tasks", foreign_keys=[assignee_id])
    creator = relationship("User", back_populates="created_tasks", foreign_keys=[creator_id])
    parent = relationship("Task", remote_side=[id], backref="subtasks")
    labels = relationship("Label", secondary="task_labels", back_populates="tasks")
    cycles = relationship("Cycle", secondary="cycle_tasks", back_populates="tasks")
