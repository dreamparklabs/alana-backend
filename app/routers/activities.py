from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional
from uuid import UUID

from app.database import get_db
from app.auth import get_current_user
from app.models import User, Activity, Workspace, Project
from app.schemas.activity import ActivityResponse, ActivityListResponse

router = APIRouter(prefix="/activities", tags=["activities"])


@router.get("/workspace/{workspace_id}", response_model=ActivityListResponse)
def get_workspace_activities(
    workspace_id: UUID,
    entity_type: Optional[str] = None,
    entity_id: Optional[UUID] = None,
    limit: int = Query(default=50, le=100),
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get activities for a workspace"""
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    query = db.query(Activity).filter(Activity.workspace_id == workspace_id)
    
    if entity_type:
        query = query.filter(Activity.entity_type == entity_type)
    if entity_id:
        query = query.filter(Activity.entity_id == entity_id)
    
    total = query.count()
    activities = query.order_by(desc(Activity.created_at)).offset(offset).limit(limit).all()
    
    return ActivityListResponse(activities=activities, total=total)


@router.get("/project/{project_id}", response_model=ActivityListResponse)
def get_project_activities(
    project_id: UUID,
    entity_type: Optional[str] = None,
    limit: int = Query(default=50, le=100),
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get activities for a project"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    query = db.query(Activity).filter(Activity.project_id == project_id)
    
    if entity_type:
        query = query.filter(Activity.entity_type == entity_type)
    
    total = query.count()
    activities = query.order_by(desc(Activity.created_at)).offset(offset).limit(limit).all()
    
    return ActivityListResponse(activities=activities, total=total)


@router.get("/entity/{entity_type}/{entity_id}", response_model=ActivityListResponse)
def get_entity_activities(
    entity_type: str,
    entity_id: UUID,
    limit: int = Query(default=50, le=100),
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get activities for a specific entity (task, project, etc.)"""
    query = db.query(Activity).filter(
        Activity.entity_type == entity_type,
        Activity.entity_id == entity_id
    )
    
    total = query.count()
    activities = query.order_by(desc(Activity.created_at)).offset(offset).limit(limit).all()
    
    return ActivityListResponse(activities=activities, total=total)
