from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class Comment(Base):
    __tablename__ = "comments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # What is being commented on
    entity_type = Column(String(50), nullable=False)  # "task", "project"
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Comment content
    content = Column(Text, nullable=False)
    content_html = Column(Text, nullable=True)  # Rendered HTML for rich text
    
    # Author
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Threading (optional)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("comments.id"), nullable=True)
    
    # Context
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    author = relationship("User", back_populates="comments")
    parent = relationship("Comment", remote_side=[id], backref="replies")
    workspace = relationship("Workspace", back_populates="comments")
    project = relationship("Project", back_populates="comments")
