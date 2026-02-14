from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional
from uuid import UUID

from app.database import get_db
from app.auth import get_current_user
from app.models import User, Comment, Workspace, Project, Task
from app.schemas.comment import (
    CommentCreate, CommentUpdate, CommentResponse, CommentListResponse
)

router = APIRouter(prefix="/comments", tags=["comments"])


def get_workspace_id_for_entity(db: Session, entity_type: str, entity_id: UUID) -> UUID:
    """Get workspace_id for an entity"""
    if entity_type == "task":
        task = db.query(Task).filter(Task.id == entity_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        project = db.query(Project).filter(Project.id == task.project_id).first()
        return project.workspace_id
    elif entity_type == "project":
        project = db.query(Project).filter(Project.id == entity_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return project.workspace_id
    else:
        raise HTTPException(status_code=400, detail=f"Invalid entity type: {entity_type}")


@router.post("", response_model=CommentResponse)
def create_comment(
    comment_data: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new comment"""
    workspace_id = get_workspace_id_for_entity(db, comment_data.entity_type, comment_data.entity_id)
    
    # Get project_id if entity is a task
    project_id = None
    if comment_data.entity_type == "task":
        task = db.query(Task).filter(Task.id == comment_data.entity_id).first()
        project_id = task.project_id
    elif comment_data.entity_type == "project":
        project_id = comment_data.entity_id
    
    comment = Comment(
        entity_type=comment_data.entity_type,
        entity_id=comment_data.entity_id,
        content=comment_data.content,
        content_html=comment_data.content_html,
        author_id=current_user.id,
        parent_id=comment_data.parent_id,
        workspace_id=workspace_id,
        project_id=project_id
    )
    
    db.add(comment)
    db.commit()
    db.refresh(comment)
    
    return comment


@router.get("/entity/{entity_type}/{entity_id}", response_model=CommentListResponse)
def get_entity_comments(
    entity_type: str,
    entity_id: UUID,
    include_replies: bool = True,
    limit: int = Query(default=50, le=100),
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get comments for a specific entity"""
    query = db.query(Comment).filter(
        Comment.entity_type == entity_type,
        Comment.entity_id == entity_id
    )
    
    # Only get top-level comments if not including replies inline
    if not include_replies:
        query = query.filter(Comment.parent_id.is_(None))
    
    total = query.count()
    comments = query.order_by(desc(Comment.created_at)).offset(offset).limit(limit).all()
    
    return CommentListResponse(comments=comments, total=total)


@router.get("/{comment_id}", response_model=CommentResponse)
def get_comment(
    comment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific comment"""
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    return comment


@router.patch("/{comment_id}", response_model=CommentResponse)
def update_comment(
    comment_id: UUID,
    comment_data: CommentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a comment (only author can update)"""
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    if comment.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only edit your own comments")
    
    update_data = comment_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(comment, field, value)
    
    db.commit()
    db.refresh(comment)
    
    return comment


@router.delete("/{comment_id}")
def delete_comment(
    comment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a comment (only author can delete)"""
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    if comment.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only delete your own comments")
    
    db.delete(comment)
    db.commit()
    
    return {"message": "Comment deleted successfully"}
