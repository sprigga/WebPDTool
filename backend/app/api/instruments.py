"""
REST API for instrument configuration management.
Provides CRUD endpoints for the instruments table.
No authentication required — instrument config is internal infrastructure.
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.repositories.instrument_repository import InstrumentRepository
from app.schemas.instrument import InstrumentCreate, InstrumentResponse, InstrumentUpdate

router = APIRouter()


async def _get_repo(db: AsyncSession = Depends(get_async_db)) -> InstrumentRepository:
    return InstrumentRepository(db)


@router.get("", response_model=List[InstrumentResponse])
async def list_instruments(
    enabled_only: bool = Query(False, description="Return only enabled instruments"),
    repo: InstrumentRepository = Depends(_get_repo),
):
    """List all instruments (or only enabled ones)."""
    rows = await repo.list_enabled() if enabled_only else await repo.list_all()
    return rows


@router.post("", response_model=InstrumentResponse, status_code=status.HTTP_201_CREATED)
async def create_instrument(
    data: InstrumentCreate,
    repo: InstrumentRepository = Depends(_get_repo),
):
    """Create a new instrument configuration."""
    existing = await repo.get_by_instrument_id(data.instrument_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Instrument '{data.instrument_id}' already exists.",
        )
    try:
        return await repo.create(data)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Instrument ID conflict.",
        )


@router.get("/{instrument_id}", response_model=InstrumentResponse)
async def get_instrument(
    instrument_id: str,
    repo: InstrumentRepository = Depends(_get_repo),
):
    """Get instrument by logical ID (e.g. 'DAQ973A_1')."""
    inst = await repo.get_by_instrument_id(instrument_id)
    if not inst:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Instrument '{instrument_id}' not found.",
        )
    return inst


@router.patch("/{instrument_id}", response_model=InstrumentResponse)
async def update_instrument(
    instrument_id: str,
    data: InstrumentUpdate,
    repo: InstrumentRepository = Depends(_get_repo),
):
    """Partially update an instrument configuration."""
    inst = await repo.get_by_instrument_id(instrument_id)
    if not inst:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Instrument '{instrument_id}' not found.",
        )
    updated = await repo.update(inst.id, data)
    return updated


@router.delete("/{instrument_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_instrument(
    instrument_id: str,
    repo: InstrumentRepository = Depends(_get_repo),
):
    """Delete an instrument configuration."""
    inst = await repo.get_by_instrument_id(instrument_id)
    if not inst:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Instrument '{instrument_id}' not found.",
        )
    await repo.delete(inst.id)
