"""Unit tests for ModbusManager singleton."""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from app.services.modbus.modbus_manager import modbus_manager, ModbusManager
from app.schemas.modbus import ModbusConfigCreate


def _make_config(station_id=99):
    return ModbusConfigCreate(
        station_id=station_id,
        server_host="127.0.0.1",
        server_port=5020,
        device_id=1,
        enabled=True,
        simulation_mode=True
    )


def test_modbus_manager_is_singleton():
    """Test that modbus_manager is a module-level singleton"""
    from app.services.modbus.modbus_manager import modbus_manager as mm2
    assert modbus_manager is mm2


@pytest.mark.asyncio
async def test_modbus_manager_start_listener():
    """Test starting a listener (with mocked _run_async to avoid real connection)"""
    manager = ModbusManager()
    config = _make_config(station_id=100)

    # Mock _run_async to avoid real Modbus connection; start() still sets running=True
    with patch('app.services.modbus.modbus_listener.ModbusListenerService._run_async', new_callable=AsyncMock):
        await manager.start_listener(config)
        assert 100 in manager.active_listeners

        status = manager.get_status(100)
        assert status["station_id"] == 100
        assert status["running"] is True

        # Stop listener
        await manager.stop_listener(100)
        assert 100 not in manager.active_listeners


@pytest.mark.asyncio
async def test_modbus_manager_no_duplicate_listeners():
    """Test that starting a listener twice returns the existing one"""
    manager = ModbusManager()
    config = _make_config(station_id=101)

    with patch('app.services.modbus.modbus_listener.ModbusListenerService._run_async', new_callable=AsyncMock):
        listener1 = await manager.start_listener(config)
        listener2 = await manager.start_listener(config)
        assert listener1 is listener2
        assert len(manager.active_listeners) == 1

        await manager.stop_listener(101)


@pytest.mark.asyncio
async def test_modbus_manager_get_status_none_for_inactive():
    """Test get_status returns None for inactive station"""
    manager = ModbusManager()
    status = manager.get_status(9999)
    assert status is None


@pytest.mark.asyncio
async def test_modbus_manager_get_all_statuses():
    """Test get_all_statuses returns dict of all active listeners"""
    manager = ModbusManager()

    with patch('app.services.modbus.modbus_listener.ModbusListenerService._run_async', new_callable=AsyncMock):
        await manager.start_listener(_make_config(station_id=201))
        await manager.start_listener(_make_config(station_id=202))

        all_statuses = manager.get_all_statuses()
        assert 201 in all_statuses
        assert 202 in all_statuses

        await manager.stop_all()
        assert len(manager.active_listeners) == 0
