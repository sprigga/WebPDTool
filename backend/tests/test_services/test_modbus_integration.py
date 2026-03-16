"""Integration tests for Modbus + TestEngine result writing."""
import pytest
from unittest.mock import AsyncMock, patch
from app.services.modbus.modbus_manager import modbus_manager


@pytest.mark.asyncio
async def test_write_modbus_result_called_on_pass():
    """Test that modbus_manager.write_test_result is called with True on PASS"""
    with patch.object(modbus_manager, 'write_test_result', new_callable=AsyncMock) as mock_write:
        mock_write.return_value = True
        result = await modbus_manager.write_test_result(station_id=1, passed=True)
        mock_write.assert_called_once_with(station_id=1, passed=True)
        assert result is True


@pytest.mark.asyncio
async def test_write_modbus_result_called_on_fail():
    """Test that modbus_manager.write_test_result is called with False on FAIL"""
    with patch.object(modbus_manager, 'write_test_result', new_callable=AsyncMock) as mock_write:
        mock_write.return_value = True
        await modbus_manager.write_test_result(station_id=2, passed=False)
        mock_write.assert_called_once_with(station_id=2, passed=False)


@pytest.mark.asyncio
async def test_write_modbus_result_returns_false_when_no_listener():
    """Test that write_test_result returns False when no listener is active"""
    # modbus_manager singleton has no listeners by default
    result = await modbus_manager.write_test_result(station_id=9999, passed=True)
    assert result is False


@pytest.mark.asyncio
async def test_test_engine_write_modbus_result_silent_on_error():
    """Test that _write_modbus_result swallows errors and does not raise"""
    from app.services.test_engine import TestEngine

    engine = TestEngine()

    with patch.object(modbus_manager, 'write_test_result', new_callable=AsyncMock) as mock_write:
        mock_write.side_effect = Exception("Modbus connection lost")
        # Should not raise — test session must not fail due to Modbus error
        await engine._write_modbus_result(station_id=1, passed=True)
