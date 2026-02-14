from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List, Optional
from uuid import UUID

from app.database import get_db
from app.models import Label, Workspace, Project
from app.schemas.label import LabelCreate, LabelUpdate, LabelResponse, LabelListResponse
from app.auth import get_current_user
from app.models import User

router = APIRouter(prefix="/labels", tags=["labels"])


@router.get("/workspace/{workspace_id}", response_model=LabelListResponse)
async def get_workspace_labels(
    workspace_id: UUID,
    project_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all labels for a workspace, optionally filtered by project"""
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    query = db.query(Label).filter(Label.workspace_id == workspace_id)
    
    if project_id:
        # Get workspace-wide labels (project_id is null) OR project-specific labels
        query = query.filter(
            or_(Label.project_id == None, Label.project_id == project_id)
        )
    
    labels = query.order_by(Label.sort_order).all()
    
    return LabelListResponse(labels=labels, total=len(labels))


@router.post("/", response_model=LabelResponse, status_code=status.HTTP_201_CREATED)
async def create_label(
    label_data: LabelCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new label"""
    workspace = db.query(Workspace).filter(Workspace.id == label_data.workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    if label_data.project_id:
        project = db.query(Project).filter(Project.id == label_data.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        if project.workspace_id != label_data.workspace_id:
            raise HTTPException(status_code=400, detail="Project does not belong to workspace")
    
    # Check for duplicate name in same scope
    existing_query = db.query(Label).filter(
        Label.workspace_id == label_data.workspace_id,
        func.lower(Label.name) == label_data.name.lower()
    )
    if label_data.project_id:
        existing_query = existing_query.filter(Label.project_id == label_data.project_id)
    else:
        existing_query = existing_query.filter(Label.project_id == None)
    
    if existing_query.first():
        raise HTTPException(status_code=400, detail="Label with this name already exists")
    
    # Get max sort_order
    max_order = db.query(func.max(Label.sort_order)).filter(
        Label.workspace_id == label_data.workspace_id
    ).scalar() or 0
    
    label = Label(
        name=label_data.name,
        color=label_data.color,
        description=label_data.description,
        workspace_id=label_data.workspace_id,
        project_id=label_data.project_id,
        sort_order=max_order + 10000
    )
    
    db.add(label)
    db.commit()
    db.refresh(label)
    
    return label


@router.get("/{label_id}", response_model=LabelResponse)
async def get_label(
    label_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific label"""
    label = db.query(Label).filter(Label.id == label_id).first()
    if not label:
        raise HTTPException(status_code=404, detail="Label not found")
    
    return label


@router.patch("/{label_id}", response_model=LabelResponse)
async def update_label(
    label_id: UUID,
    label_data: LabelUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a label"""
    label = db.query(Label).filter(Label.id == label_id).first()
    if not label:
        raise HTTPException(status_code=404, detail="Label not found")
    
    # Check for duplicate name if name is being updated
    if label_data.name and label_data.name.lower() != label.name.lower():
        existing_query = db.query(Label).filter(
            Label.workspace_id == label.workspace_id,
            func.lower(Label.name) == label_data.name.lower(),
            Label.id != label_id
        )
        if label.project_id:
            existing_query = existing_query.filter(Label.project_id == label.project_id)
        else:
            existing_query = existing_query.filter(Label.project_id == None)
        
        if existing_query.first():
            raise HTTPException(status_code=400, detail="Label with this name already exists")
    
    # Update fields
    update_data = label_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(label, field, value)
    
    db.commit()
    db.refresh(label)
    
    return label


@router.delete("/{label_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_label(
    label_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a label"""
    label = db.query(Label).filter(Label.id == label_id).first()
    if not label:
        raise HTTPException(status_code=404, detail="Label not found")
    
    db.delete(label)
    db.commit()
    
    return None
