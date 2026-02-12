from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.database import get_db
from app.models.user import User
from app.models.task import Task, TaskStatus
from app.models.project import Project
from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate
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
    
    # Get max sort order for the status
    max_order = db.query(Task).filter(
        Task.project_id == task_data.project_id,
        Task.status == task_data.status
    ).count()
    
    task = Task(
        **task_data.model_dump(),
        number=task_number,
        creator_id=current_user.id,
        sort_order=max_order
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("/", response_model=List[TaskResponse])
async def list_tasks(
    project_id: UUID,
    status: Optional[TaskStatus] = None,
    assignee_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    query = db.query(Task).filter(Task.project_id == project_id)
    
    if status:
        query = query.filter(Task.status == status)
    if assignee_id:
        query = query.filter(Task.assignee_id == assignee_id)
    
    tasks = query.order_by(Task.sort_order).all()
    return tasks


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    task = db.query(Task).filter(Task.id == task_id).first()
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
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    update_data = task_update.model_dump(exclude_unset=True)
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
    new_status: TaskStatus,
    new_order: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Move a task to a new status and/or position (for drag-and-drop)"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    old_status = task.status
    old_order = task.sort_order
    
    # If moving within same status
    if old_status == new_status:
        if new_order > old_order:
            # Moving down
            db.query(Task).filter(
                Task.project_id == task.project_id,
                Task.status == new_status,
                Task.sort_order > old_order,
                Task.sort_order <= new_order
            ).update({Task.sort_order: Task.sort_order - 1})
        else:
            # Moving up
            db.query(Task).filter(
                Task.project_id == task.project_id,
                Task.status == new_status,
                Task.sort_order >= new_order,
                Task.sort_order < old_order
            ).update({Task.sort_order: Task.sort_order + 1})
    else:
        # Moving to different status
        # Decrease order of tasks below in old status
        db.query(Task).filter(
            Task.project_id == task.project_id,
            Task.status == old_status,
            Task.sort_order > old_order
        ).update({Task.sort_order: Task.sort_order - 1})
        
        # Increase order of tasks at and below new position
        db.query(Task).filter(
            Task.project_id == task.project_id,
            Task.status == new_status,
            Task.sort_order >= new_order
        ).update({Task.sort_order: Task.sort_order + 1})
    
    task.status = new_status
    task.sort_order = new_order
    db.commit()
    db.refresh(task)
    return task
