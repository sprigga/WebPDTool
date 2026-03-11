"""Unit tests for Instrument ORM model."""
import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session
from app.core.database import Base
from app.models.instrument import Instrument


@pytest.fixture(scope="module")
def engine():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    return eng


@pytest.fixture
def db(engine):
    with Session(engine) as s:
        yield s


def test_instrument_table_exists(engine):
    assert inspect(engine).has_table("instruments")


def test_instrument_required_columns(engine):
    cols = {c["name"] for c in inspect(engine).get_columns("instruments")}
    assert {"instrument_id", "instrument_type", "name", "conn_type", "conn_params",
            "enabled", "description", "created_at", "updated_at"}.issubset(cols)


def test_instrument_create_and_read(db):
    inst = Instrument(
        instrument_id="DAQ973A_1",
        instrument_type="DAQ973A",
        name="Keysight DAQ973A #1",
        conn_type="VISA",
        conn_params={"address": "TCPIP0::192.168.1.10::inst0::INSTR", "timeout": 5000},
        enabled=True,
    )
    db.add(inst)
    db.commit()
    db.refresh(inst)
    assert inst.id is not None
    assert inst.instrument_id == "DAQ973A_1"


def test_instrument_unique_constraint(db):
    from sqlalchemy.exc import IntegrityError
    db.add(Instrument(
        instrument_id="DAQ973A_1",
        instrument_type="DAQ973A",
        name="Duplicate",
        conn_type="VISA",
        conn_params={},
    ))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()
