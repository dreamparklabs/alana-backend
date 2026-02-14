from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from uuid import UUID

from app.database import get_db
from app.models import State, Project, DEFAULT_STATES
from app.schemas.state import StateCreate, StateUpdate, StateResponse, StateListResponse
from app.auth import get_current_user
from app.models import User

router = APIRouter(prefix="/states", tags=["states"])


@router.get("/project/{project_id}", response_model=StateListResponse)
async def get_project_states(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all states for a project"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    states = db.query(State).filter(
        State.project_id == project_id
    ).order_by(State.sequence).all()
    
    return StateListResponse(states=states, total=len(states))


@router.post("/", response_model=StateResponse, status_code=status.HTTP_201_CREATED)
async def create_state(
    state_data: StateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new state for a project"""
    project = db.query(Project).filter(Project.id == state_data.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check for duplicate name in project
    existing = db.query(State).filter(
        State.project_id == state_data.project_id,
        func.lower(State.name) == state_data.name.lower()
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="State with this name already exists in project")
    
    # Get max sequence for ordering
    max_seq = db.query(func.max(State.sequence)).filter(
        State.project_id == state_data.project_id
    ).scalar() or 0
    
    state = State(
        name=state_data.name,
        description=state_data.description,
        color=state_data.color,
        group=state_data.group,
        sequence=max_seq + 10000,
        is_default=state_data.is_default,
        project_id=state_data.project_id
    )
    
    # If this is set as default, unset other defaults
    if state.is_default:
        db.query(State).filter(
            State.project_id == state_data.project_id,
            State.is_default == True
        ).update({"is_default": False})
    
    db.add(state)
    db.commit()
    db.refresh(state)
    
    return state


@router.get("/{state_id}", response_model=StateResponse)
async def get_state(
    state_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific state"""
    state = db.query(State).filter(State.id == state_id).first()
    if not state:
        raise HTTPException(status_code=404, detail="State not found")
    
    return state


@router.patch("/{state_id}", response_model=StateResponse)
async def update_state(
    state_id: UUID,
    state_data: StateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a state"""
    state = db.query(State).filter(State.id == state_id).first()
    if not state:
        raise HTTPException(status_code=404, detail="State not found")
    
    # Check for duplicate name if name is being updated
    if state_data.name and state_data.name.lower() != state.name.lower():
        existing = db.query(State).filter(
            State.project_id == state.project_id,
            func.lower(State.name) == state_data.name.lower(),
            State.id != state_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="State with this name already exists in project")
    
    # Update fields
    update_data = state_data.model_dump(exclude_unset=True)
    
    # If setting as default, unset other defaults
    if update_data.get("is_default"):
        db.query(State).filter(
            State.project_id == state.project_id,
            State.is_default == True,
            State.id != state_id
        ).update({"is_default": False})
    
    for field, value in update_data.items():
        setattr(state, field, value)
    
    db.commit()
    db.refresh(state)
    
    return state


@router.delete("/{state_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_state(
    state_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a state"""
    state = db.query(State).filter(State.id == state_id).first()
    if not state:
        raise HTTPException(status_code=404, detail="State not found")
    
    # Check if any tasks are using this state
    from app.models import Task
    task_count = db.query(Task).filter(Task.state_id == state_id).count()
    if task_count > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot delete state: {task_count} tasks are using this state"
        )
    
    db.delete(state)
    db.commit()
    
    return None


@router.post("/project/{project_id}/initialize", response_model=StateListResponse)
async def initialize_project_states(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Initialize default states for a project"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check if project already has states
    existing_count = db.query(State).filter(State.project_id == project_id).count()
    if existing_count > 0:
        raise HTTPException(status_code=400, detail="Project already has states")
    
    # Create default states
    states = []
    for state_data in DEFAULT_STATES:
        state = State(
            name=state_data["name"],
            color=state_data["color"],
            group=state_data["group"],
            sequence=state_data["sequence"],
            is_default=state_data.get("is_default", False),
            project_id=project_id
        )
        db.add(state)
        states.append(state)
    
    db.commit()
    
    # Refresh all states
    for state in states:
        db.refresh(state)
    
    return StateListResponse(states=states, total=len(states))


@router.post("/project/{project_id}/reorder", response_model=StateListResponse)
async def reorder_states(
    project_id: UUID,
    state_ids: List[UUID],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reorder states by providing list of state IDs in desired order"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Update sequence for each state
    for index, state_id in enumerate(state_ids):
        db.query(State).filter(
            State.id == state_id,
            State.project_id == project_id
        ).update({"sequence": (index + 1) * 10000})
    
    db.commit()
    
    # Return updated states
    states = db.query(State).filter(
        State.project_id == project_id
    ).order_by(State.sequence).all()
    
    return StateListResponse(states=states, total=len(states))
