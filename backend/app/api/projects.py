"""Projects API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.api_helpers import PermissionChecker
from app.core.constants import ErrorMessages
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
    # Original code: skip parameter (inconsistent with tests.py)
    # Modified: Renamed to offset for API consistency across all endpoints
    offset: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Get list of all projects

    Args:
        offset: Number of records to skip (pagination)
        limit: Maximum number of records to return
        db: Database session
        current_user: Current authenticated user

    Returns:
        List of projects
    """
    projects = db.query(ProjectModel).offset(offset).limit(limit).all()
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
        # Original code: Raw string
        # raise HTTPException(status_code=404, detail="Project not found")
        # Refactored: Use ErrorMessages constant
        raise HTTPException(status_code=404, detail=ErrorMessages.PROJECT_NOT_FOUND)

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
    # Original code: Direct string comparison
    # if current_user.get("role") != "admin":
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Only administrators can create projects"
    #     )
    # Refactored: Use PermissionChecker helper
    PermissionChecker.check_admin(current_user, "create projects")

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
    # Original code: Pydantic v1 syntax
    # db_project = ProjectModel(**project.dict())
    # Refactored: Pydantic v2 syntax
    db_project = ProjectModel(**project.model_dump())
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
    # Original code: Direct string comparison
    # if current_user.get("role") != "admin":
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Only administrators can update projects"
    #     )
    # Refactored: Use PermissionChecker helper
    PermissionChecker.check_admin(current_user, "update projects")

    # Get existing project
    db_project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not db_project:
        # Original code: Raw string
        # raise HTTPException(status_code=404, detail="Project not found")
        # Refactored: Use ErrorMessages constant
        raise HTTPException(status_code=404, detail=ErrorMessages.PROJECT_NOT_FOUND)

    # Update project fields
    # Original code: Pydantic v1 syntax
    # update_data = project.dict(exclude_unset=True)
    # Refactored: Pydantic v2 syntax
    update_data = project.model_dump(exclude_unset=True)
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
    # Original code: Direct string comparison
    # if current_user.get("role") != "admin":
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Only administrators can delete projects"
    #     )
    # Refactored: Use PermissionChecker helper
    PermissionChecker.check_admin(current_user, "delete projects")

    # Get existing project
    db_project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not db_project:
        # Original code: Raw string
        # raise HTTPException(status_code=404, detail="Project not found")
        # Refactored: Use ErrorMessages constant
        raise HTTPException(status_code=404, detail=ErrorMessages.PROJECT_NOT_FOUND)

    # Delete project (cascade will delete stations)
    db.delete(db_project)
    db.commit()

    return None
