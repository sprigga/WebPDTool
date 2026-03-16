"""Unit tests for ModbusListenerService."""
import pytest
from app.services.modbus.modbus_listener import ModbusListenerService
from app.schemas.modbus import ModbusConfigCreate


def _make_config(**kwargs):
    defaults = dict(
        station_id=1,
        server_host="127.0.0.1",
        server_port=5020,
        device_id=1,
        enabled=False,
        simulation_mode=True
    )
    defaults.update(kwargs)
    return ModbusConfigCreate(**defaults)


def test_modbus_listener_initialization():
    """Test ModbusListenerService initialization"""
    config = _make_config()
    service = ModbusListenerService(config)

    assert service.station_id == 1
    assert service.running is False
    assert service.connected is False


def test_modbus_listener_hex_string_conversion():
    """Test hex string to int conversion"""
    service = ModbusListenerService(_make_config())

    assert service._str2hex("0x0013") == 19
    assert service._str2hex("0x0064") == 100
    assert service._str2hex("0xFFFF") == 65535


def test_modbus_listener_byte_offset():
    """Test byte offset function for SN decoding"""
    service = ModbusListenerService(_make_config())

    # 0x4D31 = "M1" in ASCII
    high, low = service._byte_offset(0x4D31)
    assert high == 0x4D  # 'M'
    assert low == 0x31   # '1'


def test_modbus_listener_decode_sn():
    """Test SN decoding from register values"""
    service = ModbusListenerService(_make_config())

    # "TEST1234" encoded in registers
    # T=0x54, E=0x45, S=0x53, T=0x54, 1=0x31, 2=0x32, 3=0x33, 4=0x34
    # In registers: 0x5445, 0x5354, 0x3132, 0x3334
    registers = [0x5445, 0x5354, 0x3132, 0x3334]
    decoded = service._decode_sn(registers)
    assert decoded == "TEST1234"


def test_modbus_listener_decode_sn_strips_nulls():
    """Test that null characters are stripped from decoded SN"""
    service = ModbusListenerService(_make_config())

    # "AB" padded with null chars
    registers = [0x4142, 0x0000]  # "AB\0\0"
    decoded = service._decode_sn(registers)
    assert '\0' not in decoded
    assert "AB" in decoded


def test_modbus_listener_get_status():
    """Test get_status returns expected structure"""
    service = ModbusListenerService(_make_config())
    status = service.get_status()

    assert status["station_id"] == 1
    assert status["running"] is False
    assert status["connected"] is False
    assert status["last_sn"] is None
    assert status["cycle_count"] == 0
