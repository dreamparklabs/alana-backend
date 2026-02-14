from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base


class StateGroup(str, enum.Enum):
    """Groups for organizing states in the workflow"""
    BACKLOG = "backlog"
    UNSTARTED = "unstarted"
    STARTED = "started"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class State(Base):
    __tablename__ = "states"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    color = Column(String(7), nullable=False, default="#6B7280")
    group = Column(String(50), nullable=False, default=StateGroup.BACKLOG.value)
    sequence = Column(Float, nullable=False, default=65535)
    is_default = Column(Boolean, default=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="states")
    tasks = relationship("Task", back_populates="state")

    def __repr__(self):
        return f"<State {self.name}>"


# Default states to create for new projects
DEFAULT_STATES = [
    {"name": "Backlog", "color": "#6B7280", "group": "backlog", "sequence": 10000, "is_default": True},
    {"name": "Todo", "color": "#3B82F6", "group": "unstarted", "sequence": 20000, "is_default": False},
    {"name": "In Progress", "color": "#F59E0B", "group": "started", "sequence": 30000, "is_default": False},
    {"name": "In Review", "color": "#8B5CF6", "group": "started", "sequence": 40000, "is_default": False},
    {"name": "Done", "color": "#10B981", "group": "completed", "sequence": 50000, "is_default": False},
    {"name": "Cancelled", "color": "#EF4444", "group": "cancelled", "sequence": 60000, "is_default": False},
]
