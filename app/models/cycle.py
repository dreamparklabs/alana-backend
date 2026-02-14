from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Boolean, Float, Table, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


# Association table for tasks in cycles
cycle_tasks = Table(
    'cycle_tasks',
    Base.metadata,
    Column('cycle_id', UUID(as_uuid=True), ForeignKey('cycles.id', ondelete='CASCADE'), primary_key=True),
    Column('task_id', UUID(as_uuid=True), ForeignKey('tasks.id', ondelete='CASCADE'), primary_key=True),
    Column('added_at', DateTime, default=datetime.utcnow)
)


class Cycle(Base):
    __tablename__ = "cycles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    number = Column(Integer, nullable=False)  # Cycle 1, Cycle 2, etc.
    description = Column(Text, nullable=True)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    
    # Settings
    is_active = Column(Boolean, default=False)
    sort_order = Column(Float, default=65535)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="cycles")
    tasks = relationship("Task", secondary=cycle_tasks, back_populates="cycles")

    def __repr__(self):
        return f"<Cycle {self.name}>"
