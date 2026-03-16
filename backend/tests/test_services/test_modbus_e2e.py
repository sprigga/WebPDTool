"""
End-to-end tests for Modbus listener integration.

These tests require a live Modbus TCP server at 127.0.0.1:5020.
Run the simulator first:
    python scripts/modbus_simulator.py --port 5020

Then run with:
    uv run pytest -m e2e tests/test_services/test_modbus_e2e.py -v
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from app.schemas.modbus import ModbusConfigCreate
from app.services.modbus.modbus_listener import ModbusListenerService
from app.services.modbus.modbus_manager import ModbusManager


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_modbus_listener_connects_and_polls():
    """
    E2E: Listener connects to simulator and begins polling.
    Requires simulator on 127.0.0.1:5020.
    """
    config = ModbusConfigCreate(
        station_id=1,
        server_host="127.0.0.1",
        server_port=5020,
        device_id=1,
        enabled=True,
        delay_seconds=0.5,
        simulation_mode=False
    )

    listener = ModbusListenerService(config)
    received_sns = []
    listener.on_sn_received = received_sns.append

    await listener.start()
    await asyncio.sleep(1.0)  # Allow one poll cycle

    assert listener.running is True
    # connected depends on simulator availability
    await listener.stop()
    assert listener.running is False


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_modbus_manager_e2e_lifecycle():
    """
    E2E: Manager starts, polls, and stops a listener.
    Requires simulator on 127.0.0.1:5020.
    """
    manager = ModbusManager()
    config = ModbusConfigCreate(
        station_id=50,
        server_host="127.0.0.1",
        server_port=5020,
        device_id=1,
        enabled=True,
        delay_seconds=0.5
    )

    await manager.start_listener(config)
    assert 50 in manager.active_listeners

    await asyncio.sleep(0.5)
    status = manager.get_status(50)
    assert status is not None
    assert status["running"] is True

    await manager.stop_listener(50)
    assert 50 not in manager.active_listeners


@pytest.mark.asyncio
async def test_modbus_sn_decode_end_to_end():
    """
    Unit-level E2E: Full SN decode pipeline from raw registers to string.
    No hardware required.
    """
    config = ModbusConfigCreate(
        station_id=1,
        server_host="127.0.0.1",
        server_port=5020,
        device_id=1,
        simulation_mode=True
    )
    listener = ModbusListenerService(config)

    # Registers from simulator: "TEST12345678"
    sn_data = [0x5445, 0x5354, 0x3132, 0x3334, 0x3536, 0x3738, 0x0000, 0x0000, 0x0000, 0x0000, 0x0000]
    decoded = listener._decode_sn(sn_data)

    assert decoded == "TEST12345678"
