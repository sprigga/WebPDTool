"""Stations API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.core.database import get_async_db
from app.core.api_helpers import get_entity_or_404, PermissionChecker
from app.core.constants import ErrorMessages
from app.schemas.project import Station, StationCreate, StationUpdate
from app.models.station import Station as StationModel
from app.models.project import Project as ProjectModel
from app.dependencies import get_current_active_user

router = APIRouter()


@router.get("/projects/{project_id}/stations", response_model=List[Station])
async def get_project_stations(
    project_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Get all stations for a specific project

    Args:
        project_id: Project ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        List of stations
    """
    await get_entity_or_404(db, ProjectModel, project_id, ErrorMessages.PROJECT_NOT_FOUND)

    result = await db.execute(select(StationModel).where(StationModel.project_id == project_id))
    stations = result.scalars().all()
    return stations


@router.get("/stations/{station_id}", response_model=Station)
async def get_station(
    station_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Get station details by ID

    Args:
        station_id: Station ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Station details
    """
    return await get_entity_or_404(db, StationModel, station_id, ErrorMessages.STATION_NOT_FOUND)


@router.post("/stations", response_model=Station, status_code=status.HTTP_201_CREATED)
async def create_station(
    station: StationCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Create new station (Admin/Engineer only)

    Args:
        station: Station data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Created station
    """
    PermissionChecker.check_admin_or_engineer(current_user, "create stations")

    # Verify project exists
    await get_entity_or_404(db, ProjectModel, station.project_id, ErrorMessages.PROJECT_NOT_FOUND)

    # Check if station code already exists in this project
    result = await db.execute(
        select(StationModel)
        .where(StationModel.project_id == station.project_id)
        .where(StationModel.station_code == station.station_code)
    )
    existing_station = result.scalar_one_or_none()
    if existing_station:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Station code already exists in this project"
        )

    # Create new station
    db_station = StationModel(**station.model_dump())
    db.add(db_station)
    await db.commit()
    await db.refresh(db_station)

    return db_station


@router.put("/stations/{station_id}", response_model=Station)
async def update_station(
    station_id: int,
    station: StationUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Update station (Admin/Engineer only)

    Args:
        station_id: Station ID
        station: Updated station data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Updated station
    """
    PermissionChecker.check_admin_or_engineer(current_user, "update stations")

    # Get existing station
    db_station = await get_entity_or_404(db, StationModel, station_id, ErrorMessages.STATION_NOT_FOUND)

    # Update station fields
    update_data = station.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_station, key, value)

    await db.commit()
    await db.refresh(db_station)

    return db_station


@router.delete("/stations/{station_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_station(
    station_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Delete station (Admin only)

    Args:
        station_id: Station ID
        db: Database session
        current_user: Current authenticated user
    """
    PermissionChecker.check_admin(current_user, "delete stations")

    # Get existing station
    db_station = await get_entity_or_404(db, StationModel, station_id, ErrorMessages.STATION_NOT_FOUND)

    # Delete station
    await db.delete(db_station)
    await db.commit()

    return None
