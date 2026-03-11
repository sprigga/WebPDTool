"""API tests for /api/instruments endpoints."""
import os
import tempfile
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import get_db, Base


@pytest.fixture(scope="function")
def db_session():
    """Get database session backed by a temp SQLite file."""
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)

    test_engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=test_engine)
    TestingSessionLocal = sessionmaker(bind=test_engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        test_engine.dispose()
        try:
            os.unlink(db_path)
        except FileNotFoundError:
            pass


@pytest.fixture
def client(db_session):
    """Test client with DB override (no auth required for instruments API)."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
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


def test_list_instruments_empty(client):
    """GET /api/instruments returns empty list when no data."""
    response = client.get("/api/instruments")
    assert response.status_code == 200
    assert response.json() == []


def test_create_instrument(client):
    """POST /api/instruments creates a record and returns 201."""
    response = client.post("/api/instruments", json=_INSTRUMENT_PAYLOAD)
    assert response.status_code == 201
    data = response.json()
    assert data["instrument_id"] == "DAQ973A_1"
    assert "id" in data
    assert data["id"] > 0


def test_create_instrument_duplicate(client):
    """POST with same instrument_id returns 409."""
    client.post("/api/instruments", json=_INSTRUMENT_PAYLOAD)
    response = client.post("/api/instruments", json=_INSTRUMENT_PAYLOAD)
    assert response.status_code == 409


def test_get_instrument(client):
    """GET /api/instruments/{instrument_id} returns 200."""
    client.post("/api/instruments", json=_INSTRUMENT_PAYLOAD)
    response = client.get("/api/instruments/DAQ973A_1")
    assert response.status_code == 200
    assert response.json()["instrument_id"] == "DAQ973A_1"


def test_get_instrument_not_found(client):
    """GET /api/instruments/NONEXISTENT returns 404."""
    response = client.get("/api/instruments/NONEXISTENT")
    assert response.status_code == 404


def test_update_instrument(client):
    """PATCH /api/instruments/{instrument_id} returns 200 with updated data."""
    client.post("/api/instruments", json=_INSTRUMENT_PAYLOAD)
    response = client.patch(
        "/api/instruments/DAQ973A_1",
        json={"name": "Updated DAQ", "enabled": False},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated DAQ"
    assert data["enabled"] is False


def test_delete_instrument(client):
    """DELETE /api/instruments/{instrument_id} returns 204."""
    client.post("/api/instruments", json=_INSTRUMENT_PAYLOAD)
    response = client.delete("/api/instruments/DAQ973A_1")
    assert response.status_code == 204


def test_delete_instrument_not_found(client):
    """DELETE after deletion returns 404."""
    client.post("/api/instruments", json=_INSTRUMENT_PAYLOAD)
    client.delete("/api/instruments/DAQ973A_1")
    response = client.delete("/api/instruments/DAQ973A_1")
    assert response.status_code == 404


def test_list_enabled_instruments(client):
    """GET /api/instruments?enabled_only=true returns only enabled."""
    client.post("/api/instruments", json=_INSTRUMENT_PAYLOAD)
    disabled_payload = {**_INSTRUMENT_PAYLOAD, "instrument_id": "DAQ973A_2", "enabled": False}
    client.post("/api/instruments", json=disabled_payload)

    response = client.get("/api/instruments?enabled_only=true")
    assert response.status_code == 200
    ids = [i["instrument_id"] for i in response.json()]
    assert "DAQ973A_1" in ids
    assert "DAQ973A_2" not in ids
