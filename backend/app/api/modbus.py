"""
Modbus Configuration REST API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.core.database import get_async_db as get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.modbus_config import ModbusConfig as ModbusConfigModel
from app.models.station import Station
from app.schemas.modbus import (
    ModbusConfigCreate,
    ModbusConfigResponse,
    ModbusConfigUpdate,
    ModbusStatusResponse
)
from app.services.modbus.modbus_manager import modbus_manager


router = APIRouter()


@router.get("/configs", response_model=List[ModbusConfigResponse])
async def get_modbus_configs(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all Modbus configurations"""
    result = await db.execute(
        select(ModbusConfigModel).offset(skip).limit(limit)
    )
    configs = result.scalars().all()
    return configs


@router.get("/configs/{config_id}", response_model=ModbusConfigResponse)
async def get_modbus_config(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get specific Modbus configuration by ID"""
    result = await db.execute(
        select(ModbusConfigModel).where(ModbusConfigModel.id == config_id)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Modbus configuration not found"
        )

    return config


@router.get("/stations/{station_id}/config", response_model=ModbusConfigResponse)
async def get_station_modbus_config(
    station_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get Modbus configuration for a specific station"""
    result = await db.execute(
        select(ModbusConfigModel).where(ModbusConfigModel.station_id == station_id)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Modbus configuration not found for this station"
        )

    return config


@router.post("/configs", response_model=ModbusConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_modbus_config(
    config: ModbusConfigCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create new Modbus configuration. Validates that station exists."""
    # Check if station exists
    result = await db.execute(
        select(Station).where(Station.id == config.station_id)
    )
    station = result.scalar_one_or_none()

    if not station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Station not found"
        )

    # Check if config already exists for this station
    existing = await db.execute(
        select(ModbusConfigModel).where(ModbusConfigModel.station_id == config.station_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Modbus configuration already exists for this station"
        )

    db_config = ModbusConfigModel(**config.model_dump())
    db.add(db_config)
    await db.commit()
    await db.refresh(db_config)

    return db_config


@router.put("/configs/{config_id}", response_model=ModbusConfigResponse)
async def update_modbus_config(
    config_id: int,
    config_update: ModbusConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update Modbus configuration"""
    result = await db.execute(
        select(ModbusConfigModel).where(ModbusConfigModel.id == config_id)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Modbus configuration not found"
        )

    update_data = config_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(config, field, value)

    await db.commit()
    await db.refresh(config)

    return config


@router.delete("/configs/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_modbus_config(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete Modbus configuration"""
    result = await db.execute(
        select(ModbusConfigModel).where(ModbusConfigModel.id == config_id)
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Modbus configuration not found"
        )

    await db.delete(config)
    await db.commit()

    return None


@router.get("/status", response_model=dict)
async def get_all_modbus_status(
    current_user: User = Depends(get_current_user)
):
    """Get status of all active Modbus listeners"""
    return modbus_manager.get_all_statuses()


@router.get("/status/{station_id}", response_model=ModbusStatusResponse)
async def get_modbus_status(
    station_id: int,
    current_user: User = Depends(get_current_user)
):
    """Get status of Modbus listener for a station"""
    status_data = modbus_manager.get_status(station_id)
    if not status_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active Modbus listener for station {station_id}"
        )
    return status_data
