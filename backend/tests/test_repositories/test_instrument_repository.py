"""Integration tests for InstrumentRepository."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.core.database import Base
from app.models.instrument import Instrument
from app.repositories.instrument_repository import InstrumentRepository


@pytest.fixture(scope="function")
def engine():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)


@pytest.fixture
def db(engine):
    with Session(engine) as s:
        yield s


@pytest.fixture
def repo(db):
    return InstrumentRepository(db)


@pytest.fixture(autouse=True)
def seed(db):
    db.add(Instrument(
        instrument_id="test_inst_1",
        instrument_type="DAQ973A",
        name="Test Instrument",
        conn_type="VISA",
        conn_params={"address": "TCPIP0::192.168.1.10::inst0::INSTR", "timeout": 5000},
        enabled=True,
    ))
    db.commit()
    yield
    db.query(Instrument).delete()
    db.commit()


def test_get_by_instrument_id(repo):
    inst = repo.get_by_instrument_id("test_inst_1")
    assert inst is not None
    assert inst.instrument_type == "DAQ973A"


def test_get_by_instrument_id_not_found(repo):
    assert repo.get_by_instrument_id("nonexistent") is None


def test_list_all(repo):
    result = repo.list_all()
    assert len(result) >= 1


def test_list_enabled(repo):
    result = repo.list_enabled()
    assert all(i.enabled for i in result)


def test_create(repo):
    from app.schemas.instrument import InstrumentCreate
    data = InstrumentCreate(
        instrument_id="new_inst",
        instrument_type="MODEL2303",
        name="New Instrument",
        conn_type="SERIAL",
        conn_params={"port": "COM3", "baudrate": 115200},
    )
    inst = repo.create(data)
    assert inst.id is not None
    assert inst.instrument_id == "new_inst"


def test_update(repo):
    inst = repo.get_by_instrument_id("test_inst_1")
    from app.schemas.instrument import InstrumentUpdate
    updated = repo.update(inst.id, InstrumentUpdate(enabled=False, name="Updated"))
    assert updated.enabled is False
    assert updated.name == "Updated"


def test_delete(repo):
    inst = repo.get_by_instrument_id("test_inst_1")
    result = repo.delete(inst.id)
    assert result is True
    assert repo.get_by_instrument_id("test_inst_1") is None


def test_delete_not_found(repo):
    assert repo.delete(99999) is False
