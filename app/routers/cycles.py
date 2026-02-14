from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from uuid import UUID

from app.database import get_db
from app.models import Cycle, Project, Task, State
from app.schemas.cycle import (
    CycleCreate, CycleUpdate, CycleResponse, CycleListResponse,
    CycleWithStatsResponse, CycleTasksUpdate
)
from app.auth import get_current_user
from app.models import User

router = APIRouter(prefix="/cycles", tags=["cycles"])


@router.get("/project/{project_id}", response_model=CycleListResponse)
async def get_project_cycles(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all cycles for a project"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    cycles = db.query(Cycle).filter(
        Cycle.project_id == project_id
    ).order_by(Cycle.start_date.desc()).all()
    
    return CycleListResponse(cycles=cycles, total=len(cycles))


@router.post("/", response_model=CycleResponse, status_code=status.HTTP_201_CREATED)
async def create_cycle(
    cycle_data: CycleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new cycle for a project"""
    project = db.query(Project).filter(Project.id == cycle_data.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get next cycle number
    max_number = db.query(func.max(Cycle.number)).filter(
        Cycle.project_id == cycle_data.project_id
    ).scalar() or 0
    
    cycle = Cycle(
        name=cycle_data.name,
        number=max_number + 1,
        description=cycle_data.description,
        start_date=cycle_data.start_date,
        end_date=cycle_data.end_date,
        project_id=cycle_data.project_id,
        is_active=False
    )
    
    db.add(cycle)
    db.commit()
    db.refresh(cycle)
    
    return cycle


@router.get("/{cycle_id}", response_model=CycleWithStatsResponse)
async def get_cycle(
    cycle_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific cycle with stats"""
    cycle = db.query(Cycle).filter(Cycle.id == cycle_id).first()
    if not cycle:
        raise HTTPException(status_code=404, detail="Cycle not found")
    
    # Calculate stats
    total_tasks = len(cycle.tasks)
    
    # Get completed tasks (tasks in completed state group)
    completed_states = db.query(State.id).filter(
        State.project_id == cycle.project_id,
        State.group == "completed"
    ).all()
    completed_state_ids = [s.id for s in completed_states]
    
    completed_tasks = sum(1 for task in cycle.tasks if task.state_id in completed_state_ids)
    
    progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    return CycleWithStatsResponse(
        id=cycle.id,
        name=cycle.name,
        number=cycle.number,
        description=cycle.description,
        start_date=cycle.start_date,
        end_date=cycle.end_date,
        project_id=cycle.project_id,
        is_active=cycle.is_active,
        sort_order=cycle.sort_order,
        created_at=cycle.created_at,
        updated_at=cycle.updated_at,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        progress_percentage=round(progress, 1)
    )


@router.patch("/{cycle_id}", response_model=CycleResponse)
async def update_cycle(
    cycle_id: UUID,
    cycle_data: CycleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a cycle"""
    cycle = db.query(Cycle).filter(Cycle.id == cycle_id).first()
    if not cycle:
        raise HTTPException(status_code=404, detail="Cycle not found")
    
    # Update fields
    update_data = cycle_data.model_dump(exclude_unset=True)
    
    # Validate dates if both are being updated
    if 'start_date' in update_data and 'end_date' in update_data:
        if update_data['end_date'] <= update_data['start_date']:
            raise HTTPException(status_code=400, detail="end_date must be after start_date")
    elif 'end_date' in update_data and update_data['end_date'] <= cycle.start_date:
        raise HTTPException(status_code=400, detail="end_date must be after start_date")
    elif 'start_date' in update_data and cycle.end_date <= update_data['start_date']:
        raise HTTPException(status_code=400, detail="start_date must be before end_date")
    
    # If setting as active, deactivate other cycles
    if update_data.get('is_active'):
        db.query(Cycle).filter(
            Cycle.project_id == cycle.project_id,
            Cycle.is_active == True,
            Cycle.id != cycle_id
        ).update({"is_active": False})
    
    for field, value in update_data.items():
        setattr(cycle, field, value)
    
    db.commit()
    db.refresh(cycle)
    
    return cycle


@router.delete("/{cycle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cycle(
    cycle_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a cycle"""
    cycle = db.query(Cycle).filter(Cycle.id == cycle_id).first()
    if not cycle:
        raise HTTPException(status_code=404, detail="Cycle not found")
    
    db.delete(cycle)
    db.commit()
    
    return None


@router.post("/{cycle_id}/tasks", response_model=CycleResponse)
async def add_tasks_to_cycle(
    cycle_id: UUID,
    task_data: CycleTasksUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add tasks to a cycle"""
    cycle = db.query(Cycle).filter(Cycle.id == cycle_id).first()
    if not cycle:
        raise HTTPException(status_code=404, detail="Cycle not found")
    
    # Get tasks that belong to the same project
    tasks = db.query(Task).filter(
        Task.id.in_(task_data.task_ids),
        Task.project_id == cycle.project_id
    ).all()
    
    # Add tasks to cycle
    for task in tasks:
        if task not in cycle.tasks:
            cycle.tasks.append(task)
    
    db.commit()
    db.refresh(cycle)
    
    return cycle


@router.delete("/{cycle_id}/tasks", response_model=CycleResponse)
async def remove_tasks_from_cycle(
    cycle_id: UUID,
    task_data: CycleTasksUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove tasks from a cycle"""
    cycle = db.query(Cycle).filter(Cycle.id == cycle_id).first()
    if not cycle:
        raise HTTPException(status_code=404, detail="Cycle not found")
    
    # Get tasks to remove
    tasks = db.query(Task).filter(Task.id.in_(task_data.task_ids)).all()
    
    # Remove tasks from cycle
    for task in tasks:
        if task in cycle.tasks:
            cycle.tasks.remove(task)
    
    db.commit()
    db.refresh(cycle)
    
    return cycle


@router.post("/{cycle_id}/activate", response_model=CycleResponse)
async def activate_cycle(
    cycle_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Set a cycle as the active cycle for its project"""
    cycle = db.query(Cycle).filter(Cycle.id == cycle_id).first()
    if not cycle:
        raise HTTPException(status_code=404, detail="Cycle not found")
    
    # Deactivate other cycles in the project
    db.query(Cycle).filter(
        Cycle.project_id == cycle.project_id,
        Cycle.is_active == True
    ).update({"is_active": False})
    
    # Activate this cycle
    cycle.is_active = True
    
    db.commit()
    db.refresh(cycle)
    
    return cycle
