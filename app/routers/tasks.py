from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from uuid import UUID

from app.database import get_db
from app.models.user import User
from app.models.task import Task
from app.models.project import Project
from app.models.state import State
from app.models.label import Label
from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate, TaskListResponse
from app.auth import get_current_active_user

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Verify project exists
    project = db.query(Project).filter(Project.id == task_data.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Increment task count and get task number
    project.task_count += 1
    task_number = project.task_count
    
    # If no state_id provided, use the default state for the project
    state_id = task_data.state_id
    if not state_id:
        default_state = db.query(State).filter(
            State.project_id == task_data.project_id,
            State.is_default == True
        ).first()
        if default_state:
            state_id = default_state.id
    
    # Get max sort order for the state
    max_order = db.query(Task).filter(
        Task.project_id == task_data.project_id,
        Task.state_id == state_id
    ).count()
    
    # Extract label_ids before creating task
    label_ids = task_data.label_ids or []
    task_dict = task_data.model_dump(exclude={'label_ids'})
    task_dict['state_id'] = state_id
    
    task = Task(
        **task_dict,
        number=task_number,
        creator_id=current_user.id,
        sort_order=max_order
    )
    
    # Add labels if provided
    if label_ids:
        labels = db.query(Label).filter(Label.id.in_(label_ids)).all()
        task.labels = labels
    
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("/", response_model=TaskListResponse)
async def list_tasks(
    project_id: UUID,
    state_id: Optional[UUID] = None,
    assignee_id: Optional[UUID] = None,
    label_id: Optional[UUID] = None,
    cycle_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    query = db.query(Task).options(
        joinedload(Task.state),
        joinedload(Task.labels)
    ).filter(Task.project_id == project_id)
    
    if state_id:
        query = query.filter(Task.state_id == state_id)
    if assignee_id:
        query = query.filter(Task.assignee_id == assignee_id)
    if label_id:
        query = query.join(Task.labels).filter(Label.id == label_id)
    if cycle_id:
        from app.models.cycle import Cycle
        query = query.join(Task.cycles).filter(Cycle.id == cycle_id)
    
    tasks = query.order_by(Task.sort_order).all()
    return TaskListResponse(tasks=tasks, total=len(tasks))


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    task = db.query(Task).options(
        joinedload(Task.state),
        joinedload(Task.labels)
    ).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    task_update: TaskUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    task = db.query(Task).options(
        joinedload(Task.state),
        joinedload(Task.labels)
    ).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    update_data = task_update.model_dump(exclude_unset=True)
    
    # Handle labels separately
    if 'label_ids' in update_data:
        label_ids = update_data.pop('label_ids')
        if label_ids is not None:
            labels = db.query(Label).filter(Label.id.in_(label_ids)).all()
            task.labels = labels
    
    for field, value in update_data.items():
        setattr(task, field, value)
    
    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    db.delete(task)
    db.commit()


@router.post("/{task_id}/move", response_model=TaskResponse)
async def move_task(
    task_id: UUID,
    new_state_id: UUID,
    new_order: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Move a task to a new state and/or position (for drag-and-drop)"""
    task = db.query(Task).options(
        joinedload(Task.state),
        joinedload(Task.labels)
    ).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Verify new state exists and belongs to same project
    new_state = db.query(State).filter(State.id == new_state_id).first()
    if not new_state:
        raise HTTPException(status_code=404, detail="State not found")
    if new_state.project_id != task.project_id:
        raise HTTPException(status_code=400, detail="State does not belong to task's project")
    
    old_state_id = task.state_id
    old_order = task.sort_order
    
    # If moving within same state
    if old_state_id == new_state_id:
        if new_order > old_order:
            # Moving down
            db.query(Task).filter(
                Task.project_id == task.project_id,
                Task.state_id == new_state_id,
                Task.sort_order > old_order,
                Task.sort_order <= new_order
            ).update({Task.sort_order: Task.sort_order - 1})
        else:
            # Moving up
            db.query(Task).filter(
                Task.project_id == task.project_id,
                Task.state_id == new_state_id,
                Task.sort_order >= new_order,
                Task.sort_order < old_order
            ).update({Task.sort_order: Task.sort_order + 1})
    else:
        # Moving to different state
        # Decrease order of tasks below in old state
        db.query(Task).filter(
            Task.project_id == task.project_id,
            Task.state_id == old_state_id,
            Task.sort_order > old_order
        ).update({Task.sort_order: Task.sort_order - 1})
        
        # Increase order of tasks at and below new position
        db.query(Task).filter(
            Task.project_id == task.project_id,
            Task.state_id == new_state_id,
            Task.sort_order >= new_order
        ).update({Task.sort_order: Task.sort_order + 1})
    
    task.state_id = new_state_id
    task.sort_order = new_order
    db.commit()
    db.refresh(task)
    return task


@router.post("/{task_id}/labels/{label_id}", response_model=TaskResponse)
async def add_label_to_task(
    task_id: UUID,
    label_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Add a label to a task"""
    task = db.query(Task).options(
        joinedload(Task.state),
        joinedload(Task.labels)
    ).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    label = db.query(Label).filter(Label.id == label_id).first()
    if not label:
        raise HTTPException(status_code=404, detail="Label not found")
    
    if label not in task.labels:
        task.labels.append(label)
        db.commit()
        db.refresh(task)
    
    return task


@router.delete("/{task_id}/labels/{label_id}", response_model=TaskResponse)
async def remove_label_from_task(
    task_id: UUID,
    label_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Remove a label from a task"""
    task = db.query(Task).options(
        joinedload(Task.state),
        joinedload(Task.labels)
    ).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    label = db.query(Label).filter(Label.id == label_id).first()
    if not label:
        raise HTTPException(status_code=404, detail="Label not found")
    
    if label in task.labels:
        task.labels.remove(label)
        db.commit()
        db.refresh(task)
    
    return task
