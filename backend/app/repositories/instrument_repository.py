"""
Instrument Repository — data access layer for the instruments table.
Provides CRUD operations. All callers pass a SQLAlchemy Session.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.instrument import Instrument
from app.schemas.instrument import InstrumentCreate, InstrumentUpdate


class InstrumentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, instrument_pk: int) -> Optional[Instrument]:
        return self.db.get(Instrument, instrument_pk)

    def get_by_instrument_id(self, instrument_id: str) -> Optional[Instrument]:
        return (
            self.db.query(Instrument)
            .filter(Instrument.instrument_id == instrument_id)
            .first()
        )

    def list_all(self) -> List[Instrument]:
        return self.db.query(Instrument).order_by(Instrument.instrument_id).all()

    def list_enabled(self) -> List[Instrument]:
        return (
            self.db.query(Instrument)
            .filter(Instrument.enabled.is_(True))
            .order_by(Instrument.instrument_id)
            .all()
        )

    def create(self, data: InstrumentCreate) -> Instrument:
        inst = Instrument(**data.model_dump())
        self.db.add(inst)
        self.db.commit()
        self.db.refresh(inst)
        return inst

    def update(self, instrument_pk: int, data: InstrumentUpdate) -> Optional[Instrument]:
        inst = self.get_by_id(instrument_pk)
        if inst is None:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(inst, field, value)
        self.db.commit()
        self.db.refresh(inst)
        return inst

    def delete(self, instrument_pk: int) -> bool:
        inst = self.get_by_id(instrument_pk)
        if inst is None:
            return False
        self.db.delete(inst)
        self.db.commit()
        return True


from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select as sa_select


class AsyncInstrumentRepository:
    """Async variant used by API routers with AsyncSession.
    The sync InstrumentRepository is kept for InstrumentConfigProvider's cache refreshes."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, instrument_pk: int) -> Optional[Instrument]:
        return await self.db.get(Instrument, instrument_pk)

    async def get_by_instrument_id(self, instrument_id: str) -> Optional[Instrument]:
        result = await self.db.execute(
            sa_select(Instrument).where(Instrument.instrument_id == instrument_id)
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> List[Instrument]:
        result = await self.db.execute(
            sa_select(Instrument).order_by(Instrument.instrument_id)
        )
        return result.scalars().all()

    async def list_enabled(self) -> List[Instrument]:
        result = await self.db.execute(
            sa_select(Instrument)
            .where(Instrument.enabled.is_(True))
            .order_by(Instrument.instrument_id)
        )
        return result.scalars().all()

    async def create(self, data: InstrumentCreate) -> Instrument:
        inst = Instrument(**data.model_dump())
        self.db.add(inst)
        await self.db.commit()
        await self.db.refresh(inst)
        return inst

    async def update(self, instrument_pk: int, data: InstrumentUpdate) -> Optional[Instrument]:
        inst = await self.get_by_id(instrument_pk)   # await intra-class call
        if inst is None:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(inst, field, value)
        await self.db.commit()
        await self.db.refresh(inst)
        return inst

    async def delete(self, instrument_pk: int) -> bool:
        inst = await self.get_by_id(instrument_pk)   # await intra-class call
        if inst is None:
            return False
        await self.db.delete(inst)
        await self.db.commit()
        return True
