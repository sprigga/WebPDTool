"""Unit tests for Modbus WebSocket connection manager."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.api.modbus_ws import ModbusConnectionManager


@pytest.mark.asyncio
async def test_ws_manager_connect():
    """Test WebSocket connection registration"""
    manager = ModbusConnectionManager()
    ws = AsyncMock()

    await manager.connect(ws, station_id=1)

    assert 1 in manager.active_connections
    assert ws in manager.active_connections[1]
    ws.accept.assert_called_once()


@pytest.mark.asyncio
async def test_ws_manager_disconnect():
    """Test WebSocket disconnection"""
    manager = ModbusConnectionManager()
    ws = AsyncMock()

    await manager.connect(ws, station_id=1)
    manager.disconnect(ws, station_id=1)

    assert 1 not in manager.active_connections


@pytest.mark.asyncio
async def test_ws_manager_send_to_station():
    """Test sending message to all station connections"""
    manager = ModbusConnectionManager()
    ws1, ws2 = AsyncMock(), AsyncMock()

    await manager.connect(ws1, station_id=5)
    await manager.connect(ws2, station_id=5)

    await manager.send_to_station(5, {"type": "status", "msg": "hello"})

    ws1.send_json.assert_called_once_with({"type": "status", "msg": "hello"})
    ws2.send_json.assert_called_once_with({"type": "status", "msg": "hello"})


@pytest.mark.asyncio
async def test_ws_manager_send_to_nonexistent_station():
    """Test sending to a station with no connections (no-op)"""
    manager = ModbusConnectionManager()
    # Should not raise
    await manager.send_to_station(999, {"type": "test"})


@pytest.mark.asyncio
async def test_ws_manager_cleanup_on_send_error():
    """Test that failed sends remove the connection"""
    manager = ModbusConnectionManager()
    ws = AsyncMock()
    ws.send_json.side_effect = Exception("connection closed")

    await manager.connect(ws, station_id=7)
    await manager.send_to_station(7, {"type": "status"})

    # Connection should be removed after error
    assert 7 not in manager.active_connections
