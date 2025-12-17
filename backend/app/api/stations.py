"""Stations API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas.project import Station, StationCreate, StationUpdate
from app.models.station import Station as StationModel
from app.models.project import Project as ProjectModel
from app.dependencies import get_current_active_user

router = APIRouter()


@router.get("/projects/{project_id}/stations", response_model=List[Station])
async def get_project_stations(
    project_id: int,
    db: Session = Depends(get_db),
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
    # Verify project exists
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    stations = db.query(StationModel).filter(StationModel.project_id == project_id).all()
    return stations


@router.get("/stations/{station_id}", response_model=Station)
async def get_station(
    station_id: int,
    db: Session = Depends(get_db),
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
    station = db.query(StationModel).filter(StationModel.id == station_id).first()
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")

    return station


@router.post("/stations", response_model=Station, status_code=status.HTTP_201_CREATED)
async def create_station(
    station: StationCreate,
    db: Session = Depends(get_db),
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
    # Check if user is admin or engineer
    user_role = current_user.get("role")
    if user_role not in ["admin", "engineer"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators and engineers can create stations"
        )

    # Verify project exists
    project = db.query(ProjectModel).filter(ProjectModel.id == station.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check if station code already exists in this project
    existing_station = db.query(StationModel).filter(
        StationModel.project_id == station.project_id,
        StationModel.station_code == station.station_code
    ).first()
    if existing_station:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Station code already exists in this project"
        )

    # Create new station
    db_station = StationModel(**station.dict())
    db.add(db_station)
    db.commit()
    db.refresh(db_station)

    return db_station


@router.put("/stations/{station_id}", response_model=Station)
async def update_station(
    station_id: int,
    station: StationUpdate,
    db: Session = Depends(get_db),
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
    # Check if user is admin or engineer
    user_role = current_user.get("role")
    if user_role not in ["admin", "engineer"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators and engineers can update stations"
        )

    # Get existing station
    db_station = db.query(StationModel).filter(StationModel.id == station_id).first()
    if not db_station:
        raise HTTPException(status_code=404, detail="Station not found")

    # Update station fields
    update_data = station.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_station, key, value)

    db.commit()
    db.refresh(db_station)

    return db_station


@router.delete("/stations/{station_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_station(
    station_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Delete station (Admin only)

    Args:
        station_id: Station ID
        db: Database session
        current_user: Current authenticated user
    """
    # Check if user is admin
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete stations"
        )

    # Get existing station
    db_station = db.query(StationModel).filter(StationModel.id == station_id).first()
    if not db_station:
        raise HTTPException(status_code=404, detail="Station not found")

    # Delete station
    db.delete(db_station)
    db.commit()

    return None
