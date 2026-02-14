from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from app.database import get_db
from app.auth import get_current_user
from app.models import User, Workspace, Project, WorkspaceMember, ProjectMember, MemberRole
from app.schemas.member import (
    WorkspaceMemberCreate, WorkspaceMemberUpdate, WorkspaceMemberResponse,
    ProjectMemberCreate, ProjectMemberUpdate, ProjectMemberResponse,
    MemberListResponse, ProjectMemberListResponse, InviteMemberRequest
)

router = APIRouter(prefix="/members", tags=["members"])


# ============ Workspace Members ============

@router.get("/workspace/{workspace_id}", response_model=MemberListResponse)
def get_workspace_members(
    workspace_id: UUID,
    role: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all members of a workspace"""
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    query = db.query(WorkspaceMember).filter(WorkspaceMember.workspace_id == workspace_id)
    
    if role:
        query = query.filter(WorkspaceMember.role == role)
    
    members = query.all()
    return MemberListResponse(members=members, total=len(members))


@router.post("/workspace/{workspace_id}", response_model=WorkspaceMemberResponse)
def add_workspace_member(
    workspace_id: UUID,
    member_data: WorkspaceMemberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a member to a workspace"""
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # Check if current user has permission (owner or admin)
    current_membership = db.query(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == current_user.id
    ).first()
    
    if not current_membership or current_membership.role not in [MemberRole.OWNER.value, MemberRole.ADMIN.value]:
        if workspace.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="You don't have permission to add members")
    
    # Find user by ID or email
    user = None
    if member_data.user_id:
        user = db.query(User).filter(User.id == member_data.user_id).first()
    elif member_data.email:
        user = db.query(User).filter(User.email == member_data.email).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if already a member
    existing = db.query(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == user.id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="User is already a member of this workspace")
    
    member = WorkspaceMember(
        workspace_id=workspace_id,
        user_id=user.id,
        role=member_data.role.value,
        invited_by_id=current_user.id
    )
    
    db.add(member)
    db.commit()
    db.refresh(member)
    
    return member


@router.patch("/workspace/{workspace_id}/{member_id}", response_model=WorkspaceMemberResponse)
def update_workspace_member(
    workspace_id: UUID,
    member_id: UUID,
    member_data: WorkspaceMemberUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a workspace member's role"""
    member = db.query(WorkspaceMember).filter(
        WorkspaceMember.id == member_id,
        WorkspaceMember.workspace_id == workspace_id
    ).first()
    
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Check permissions
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if workspace.owner_id != current_user.id:
        current_membership = db.query(WorkspaceMember).filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == current_user.id
        ).first()
        if not current_membership or current_membership.role != MemberRole.ADMIN.value:
            raise HTTPException(status_code=403, detail="You don't have permission to update members")
    
    # Cannot change owner role
    if member.role == MemberRole.OWNER.value:
        raise HTTPException(status_code=400, detail="Cannot change the owner's role")
    
    if member_data.role:
        member.role = member_data.role.value
    
    db.commit()
    db.refresh(member)
    
    return member


@router.delete("/workspace/{workspace_id}/{member_id}")
def remove_workspace_member(
    workspace_id: UUID,
    member_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove a member from a workspace"""
    member = db.query(WorkspaceMember).filter(
        WorkspaceMember.id == member_id,
        WorkspaceMember.workspace_id == workspace_id
    ).first()
    
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Cannot remove owner
    if member.role == MemberRole.OWNER.value:
        raise HTTPException(status_code=400, detail="Cannot remove the workspace owner")
    
    # Check permissions (owner, admin, or self)
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if member.user_id != current_user.id and workspace.owner_id != current_user.id:
        current_membership = db.query(WorkspaceMember).filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == current_user.id
        ).first()
        if not current_membership or current_membership.role not in [MemberRole.OWNER.value, MemberRole.ADMIN.value]:
            raise HTTPException(status_code=403, detail="You don't have permission to remove members")
    
    db.delete(member)
    db.commit()
    
    return {"message": "Member removed successfully"}


# ============ Project Members ============

@router.get("/project/{project_id}", response_model=ProjectMemberListResponse)
def get_project_members(
    project_id: UUID,
    role: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all members of a project"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    query = db.query(ProjectMember).filter(ProjectMember.project_id == project_id)
    
    if role:
        query = query.filter(ProjectMember.role == role)
    
    members = query.all()
    return ProjectMemberListResponse(members=members, total=len(members))


@router.post("/project/{project_id}", response_model=ProjectMemberResponse)
def add_project_member(
    project_id: UUID,
    member_data: ProjectMemberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a member to a project"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check if user exists
    user = db.query(User).filter(User.id == member_data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if already a member
    existing = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user.id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="User is already a member of this project")
    
    member = ProjectMember(
        project_id=project_id,
        user_id=user.id,
        role=member_data.role.value
    )
    
    db.add(member)
    db.commit()
    db.refresh(member)
    
    return member


@router.delete("/project/{project_id}/{member_id}")
def remove_project_member(
    project_id: UUID,
    member_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove a member from a project"""
    member = db.query(ProjectMember).filter(
        ProjectMember.id == member_id,
        ProjectMember.project_id == project_id
    ).first()
    
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    db.delete(member)
    db.commit()
    
    return {"message": "Member removed successfully"}
