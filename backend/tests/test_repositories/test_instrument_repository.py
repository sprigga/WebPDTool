"""Integration tests for InstrumentRepository."""
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.core.database import Base
from app.models.instrument import Instrument
# Original code: from app.repositories.instrument_repository import InstrumentRepository
# Modified: Import the renamed async class (Wave 6 - Task 14)
from app.repositories.instrument_repository import InstrumentRepository as AsyncInstrumentRepository
from app.schemas.instrument import InstrumentCreate


@pytest.fixture(scope="function")
async def engine():
    eng = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db(engine):
    async with AsyncSession(engine) as s:
        yield s


@pytest.mark.asyncio
async def test_list_enabled_empty(db):
    """Test list_enabled returns empty list when no instruments."""
    # Use the renamed async InstrumentRepository
    repo = AsyncInstrumentRepository(db)
    result = await repo.list_enabled()
    assert result == []


@pytest.mark.asyncio
async def test_create_and_get(db):
    """Test creating and retrieving an instrument."""
    repo = AsyncInstrumentRepository(db)

    created = await repo.create(
        InstrumentCreate(
            instrument_id="TEST_1",
            instrument_type="TEST",
            name="Test Instrument",
            conn_type="VISA",
            conn_params={"address": "test"},
        )
    )

    assert created.instrument_id == "TEST_1"
    assert created.name == "Test Instrument"

    # Verify we can retrieve it
    fetched = await repo.get_by_instrument_id("TEST_1")
    assert fetched is not None
    assert fetched.id == created.id
