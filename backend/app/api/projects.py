"""Projects API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas.project import (
    Project,
    ProjectCreate,
    ProjectUpdate,
    ProjectWithStations
)
from app.models.project import Project as ProjectModel
from app.dependencies import get_current_active_user

router = APIRouter()


@router.get("", response_model=List[Project])
async def get_projects(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Get list of all projects

    Args:
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        db: Database session
        current_user: Current authenticated user

    Returns:
        List of projects
    """
    projects = db.query(ProjectModel).offset(skip).limit(limit).all()
    return projects


@router.get("/{project_id}", response_model=ProjectWithStations)
async def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Get project details by ID

    Args:
        project_id: Project ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Project details with stations
    """
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return project


@router.post("", response_model=Project, status_code=status.HTTP_201_CREATED)
async def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Create new project (Admin only)

    Args:
        project: Project data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Created project
    """
    # Check if user is admin
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create projects"
        )

    # Check if project code already exists
    existing_project = db.query(ProjectModel).filter(
        ProjectModel.project_code == project.project_code
    ).first()
    if existing_project:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project code already exists"
        )

    # Create new project
    db_project = ProjectModel(**project.dict())
    db.add(db_project)
    db.commit()
    db.refresh(db_project)

    return db_project


@router.put("/{project_id}", response_model=Project)
async def update_project(
    project_id: int,
    project: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Update project (Admin only)

    Args:
        project_id: Project ID
        project: Updated project data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Updated project
    """
    # Check if user is admin
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update projects"
        )

    # Get existing project
    db_project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Update project fields
    update_data = project.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_project, key, value)

    db.commit()
    db.refresh(db_project)

    return db_project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Delete project (Admin only)

    Args:
        project_id: Project ID
        db: Database session
        current_user: Current authenticated user
    """
    # Check if user is admin
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete projects"
        )

    # Get existing project
    db_project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Delete project (cascade will delete stations)
    db.delete(db_project)
    db.commit()

    return None
