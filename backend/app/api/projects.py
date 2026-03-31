"""Projects API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.core.database import get_async_db
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
    offset: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_db),
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
    result = await db.execute(select(ProjectModel).offset(offset).limit(limit))
    projects = result.scalars().all()
    return projects


@router.get("/{project_id}", response_model=ProjectWithStations)
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_async_db),
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
    result = await db.execute(select(ProjectModel).where(ProjectModel.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail=ErrorMessages.PROJECT_NOT_FOUND)

    return project


@router.post("", response_model=Project, status_code=status.HTTP_201_CREATED)
async def create_project(
    project: ProjectCreate,
    db: AsyncSession = Depends(get_async_db),
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
    PermissionChecker.check_admin(current_user, "create projects")

    # Check if project code already exists
    result = await db.execute(
        select(ProjectModel).where(ProjectModel.project_code == project.project_code)
    )
    existing_project = result.scalar_one_or_none()
    if existing_project:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project code already exists"
        )

    # Create new project
    db_project = ProjectModel(**project.model_dump())
    db.add(db_project)
    await db.commit()
    await db.refresh(db_project)

    return db_project


@router.put("/{project_id}", response_model=Project)
async def update_project(
    project_id: int,
    project: ProjectUpdate,
    db: AsyncSession = Depends(get_async_db),
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
    PermissionChecker.check_admin(current_user, "update projects")

    # Get existing project
    result = await db.execute(select(ProjectModel).where(ProjectModel.id == project_id))
    db_project = result.scalar_one_or_none()
    if not db_project:
        raise HTTPException(status_code=404, detail=ErrorMessages.PROJECT_NOT_FOUND)

    # Update project fields
    update_data = project.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_project, key, value)

    await db.commit()
    await db.refresh(db_project)

    return db_project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Delete project (Admin only)

    Args:
        project_id: Project ID
        db: Database session
        current_user: Current authenticated user
    """
    PermissionChecker.check_admin(current_user, "delete projects")

    # Get existing project
    result = await db.execute(select(ProjectModel).where(ProjectModel.id == project_id))
    db_project = result.scalar_one_or_none()
    if not db_project:
        raise HTTPException(status_code=404, detail=ErrorMessages.PROJECT_NOT_FOUND)

    # Delete project (cascade will delete stations)
    await db.delete(db_project)
    await db.commit()

    return None
