"""Unit tests for ModbusConfig ORM model."""
import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session
from app.core.database import Base
from app.models.modbus_config import ModbusConfig
from app.models.station import Station
from app.models.project import Project


@pytest.fixture(scope="function")
def engine():
    # Import all models so Base.metadata includes all tables
    import app.models.modbus_config  # noqa
    import app.models.station  # noqa
    import app.models.project  # noqa
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)


@pytest.fixture
def db(engine):
    with Session(engine) as s:
        yield s


def test_modbus_config_table_exists(engine):
    assert inspect(engine).has_table("modbus_configs")


def test_create_modbus_config(db):
    """Test creating a ModbusConfig record with default values"""
    # Need a station first (FK constraint)
    project = Project(project_name="TestProject", project_code="TP01", description="Test")
    db.add(project)
    db.flush()

    station = Station(
        project_id=project.id,
        station_name="TestStation",
        station_code="ST01"
    )
    db.add(station)
    db.flush()

    config = ModbusConfig(
        station_id=station.id,
        server_host="127.0.0.1",
        server_port=502,
        device_id=1,
        enabled=True,
        delay_seconds=1,
        ready_status_address="0x0013",
        ready_status_length=1,
        read_sn_address="0x0064",
        read_sn_length=11,
        test_status_address="0x0014",
        test_status_length=1,
        in_testing_value="0x00",
        test_finished_value="0x01",
        test_result_address="0x0015",
        test_result_length=1,
        test_no_result="0x00",
        test_pass_value="0x01",
        test_fail_value="0x02",
        simulation_mode=False
    )
    db.add(config)
    db.commit()
    db.refresh(config)

    assert config.id is not None
    assert config.server_host == "127.0.0.1"
    assert config.enabled is True
    assert config.delay_seconds == 1


def test_modbus_config_station_relationship(db):
    """Test that ModbusConfig relates to Station"""
    project = Project(project_name="RelProject", project_code="RL01", description="Rel")
    db.add(project)
    db.flush()

    station = Station(
        project_id=project.id,
        station_name="RelStation",
        station_code="RS01"
    )
    db.add(station)
    db.flush()

    config = ModbusConfig(
        station_id=station.id,
        server_host="192.168.1.100",
        server_port=502,
        device_id=1
    )
    db.add(config)
    db.commit()
    db.refresh(config)

    assert config.station_id == station.id
    assert config.station.station_code == "RS01"


def test_modbus_config_unique_per_station(db):
    """Test that only one ModbusConfig can exist per station"""
    from sqlalchemy.exc import IntegrityError

    project = Project(project_name="UniProject", project_code="UN01", description="Uni")
    db.add(project)
    db.flush()

    station = Station(
        project_id=project.id,
        station_name="UniStation",
        station_code="US01"
    )
    db.add(station)
    db.flush()

    config1 = ModbusConfig(station_id=station.id, server_host="127.0.0.1", server_port=502, device_id=1)
    config2 = ModbusConfig(station_id=station.id, server_host="192.168.1.1", server_port=502, device_id=2)
    db.add(config1)
    db.flush()
    db.add(config2)

    with pytest.raises(IntegrityError):
        db.commit()
