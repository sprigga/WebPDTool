"""API tests for /api/instruments endpoints."""
import os
import tempfile
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.main import app
from app.core.database import get_async_db, Base


@pytest_asyncio.fixture(scope="function")
async def async_db_session():
    """Async SQLite session for instruments API tests."""
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)

    engine = create_async_engine(
        f"sqlite+aiosqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    TestingSession = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with TestingSession() as session:
        yield session

    await engine.dispose()
    try:
        os.unlink(db_path)
    except FileNotFoundError:
        pass


@pytest_asyncio.fixture
async def client(async_db_session):
    """Async test client with DB override."""
    async def override_get_async_db():
        yield async_db_session

    app.dependency_overrides[get_async_db] = override_get_async_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


# --- Shared payload ---
_INSTRUMENT_PAYLOAD = {
    "instrument_id": "DAQ973A_1",
    "instrument_type": "DAQ973A",
    "name": "Test DAQ",
    "conn_type": "VISA",
    "conn_params": {"resource": "GPIB0::1::INSTR"},
    "enabled": True,
    "description": "Test instrument",
}


@pytest.mark.asyncio
async def test_list_instruments_empty(client):
    """GET /api/instruments returns empty list when no data."""
    response = await client.get("/api/instruments")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_create_instrument(client):
    """POST /api/instruments creates a record and returns 201."""
    response = await client.post("/api/instruments", json=_INSTRUMENT_PAYLOAD)
    assert response.status_code == 201
    data = response.json()
    assert data["instrument_id"] == "DAQ973A_1"
    assert "id" in data
    assert data["id"] > 0


@pytest.mark.asyncio
async def test_create_instrument_duplicate(client):
    """POST with same instrument_id returns 409."""
    await client.post("/api/instruments", json=_INSTRUMENT_PAYLOAD)
    response = await client.post("/api/instruments", json=_INSTRUMENT_PAYLOAD)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_get_instrument(client):
    """GET /api/instruments/{instrument_id} returns 200."""
    await client.post("/api/instruments", json=_INSTRUMENT_PAYLOAD)
    response = await client.get("/api/instruments/DAQ973A_1")
    assert response.status_code == 200
    assert response.json()["instrument_id"] == "DAQ973A_1"


@pytest.mark.asyncio
async def test_get_instrument_not_found(client):
    """GET /api/instruments/NONEXISTENT returns 404."""
    response = await client.get("/api/instruments/NONEXISTENT")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_instrument(client):
    """PATCH /api/instruments/{instrument_id} returns 200 with updated data."""
    await client.post("/api/instruments", json=_INSTRUMENT_PAYLOAD)
    response = await client.patch(
        "/api/instruments/DAQ973A_1",
        json={"name": "Updated DAQ", "enabled": False},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated DAQ"
    assert data["enabled"] is False


@pytest.mark.asyncio
async def test_delete_instrument(client):
    """DELETE /api/instruments/{instrument_id} returns 204."""
    await client.post("/api/instruments", json=_INSTRUMENT_PAYLOAD)
    response = await client.delete("/api/instruments/DAQ973A_1")
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_instrument_not_found(client):
    """DELETE after deletion returns 404."""
    await client.post("/api/instruments", json=_INSTRUMENT_PAYLOAD)
    await client.delete("/api/instruments/DAQ973A_1")
    response = await client.delete("/api/instruments/DAQ973A_1")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_enabled_instruments(client):
    """GET /api/instruments?enabled_only=true returns only enabled."""
    await client.post("/api/instruments", json=_INSTRUMENT_PAYLOAD)
    disabled_payload = {**_INSTRUMENT_PAYLOAD, "instrument_id": "DAQ973A_2", "enabled": False}
    await client.post("/api/instruments", json=disabled_payload)

    response = await client.get("/api/instruments?enabled_only=true")
    assert response.status_code == 200
    ids = [i["instrument_id"] for i in response.json()]
    assert "DAQ973A_1" in ids
    assert "DAQ973A_2" not in ids
