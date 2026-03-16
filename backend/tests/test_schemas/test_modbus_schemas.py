"""Unit tests for Modbus Pydantic schemas."""
import pytest
from pydantic import ValidationError
from app.schemas.modbus import ModbusConfigCreate, ModbusConfigResponse, ModbusConfigUpdate


def test_modbus_config_create_valid():
    """Test valid ModbusConfigCreate"""
    data = {
        "station_id": 1,
        "server_host": "192.168.1.100",
        "server_port": 502,
        "device_id": 1,
        "enabled": True,
        "delay_seconds": 1.0,
        "ready_status_address": "0x0013",
        "test_pass_value": "0x01"
    }
    config = ModbusConfigCreate(**data)
    assert config.server_host == "192.168.1.100"
    assert config.enabled is True


def test_modbus_config_create_invalid_port():
    """Test invalid port number"""
    with pytest.raises(ValidationError):
        ModbusConfigCreate(
            station_id=1,
            server_host="192.168.1.100",
            server_port=70000,  # Invalid: > 65535
            device_id=1
        )


def test_modbus_config_create_invalid_hex():
    """Test invalid hex string"""
    with pytest.raises(ValidationError):
        ModbusConfigCreate(
            station_id=1,
            ready_status_address="1234"  # Missing 0x prefix
        )


def test_modbus_config_response():
    """Test ModbusConfigResponse"""
    data = {
        "id": 1,
        "station_id": 1,
        "server_host": "127.0.0.1",
        "server_port": 502,
        "device_id": 1,
        "enabled": False,
        "delay_seconds": 1.0,
        "ready_status_address": "0x0013",
        "ready_status_length": 1,
        "read_sn_address": "0x0064",
        "read_sn_length": 11,
        "test_status_address": "0x0014",
        "test_status_length": 1,
        "in_testing_value": "0x00",
        "test_finished_value": "0x01",
        "test_result_address": "0x0015",
        "test_result_length": 1,
        "test_no_result": "0x00",
        "test_pass_value": "0x01",
        "test_fail_value": "0x02",
        "simulation_mode": False
    }
    response = ModbusConfigResponse(**data)
    assert response.id == 1
    assert response.station_id == 1


def test_modbus_config_update_partial():
    """Test partial update (all fields optional)"""
    update = ModbusConfigUpdate(enabled=True, server_port=503)
    assert update.enabled is True
    assert update.server_port == 503
    assert update.server_host is None  # Not provided
