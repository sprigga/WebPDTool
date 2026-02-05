"""
Unit tests for WaitTest instrument driver
"""
import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from decimal import Decimal

from app.services.instruments.wait_test import WaitTestDriver
from app.services.instrument_connection import BaseInstrumentConnection


# ============================================================================
# Mock Connection Class
# ============================================================================

from app.core.instrument_config import InstrumentConfig, VISAAddress

class MockWaitConnection(BaseInstrumentConnection):
    """Mock wait connection for testing"""

    def __init__(self, min_wait_ms: int = 0, max_wait_ms: int = 3600000):
        config = InstrumentConfig(
            id="wait_test",
            type="wait",
            name="Mock Wait Test",
            connection=VISAAddress(
                type="VISA",
                address="wait://",
                timeout=5000
            )
        )
        super().__init__(config)
        self.min_wait_ms = min_wait_ms
        self.max_wait_ms = max_wait_ms

    async def connect(self) -> bool:
        self.is_connected = True
        return True

    async def disconnect(self) -> bool:
        self.is_connected = False
        return True

    async def write(self, command: str) -> None:
        pass

    async def query(self, command: str) -> str:
        return ""

    async def read(self) -> str:
        return ""


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def wait_driver():
    """Create WaitTestDriver"""
    config = MockWaitConnection()
    driver = WaitTestDriver(config)
    return driver


# ============================================================================
# Test Cases
# ============================================================================

class TestWaitTestDriverInitialization:
    """Test driver initialization"""

    @pytest.mark.asyncio
    async def test_initialize_default(self, wait_driver):
        """Test default initialization"""
        await wait_driver.initialize()

        assert wait_driver.min_wait_ms == 0
        assert wait_driver.max_wait_ms == 3600000

    @pytest.mark.asyncio
    async def test_initialize_custom_limits(self):
        """Test initialization with custom limits"""
        config = MockWaitConnection(min_wait_ms=100, max_wait_ms=60000)
        driver = WaitTestDriver(config)

        await driver.initialize()

        assert driver.min_wait_ms == 100
        assert driver.max_wait_ms == 60000

    @pytest.mark.asyncio
    async def test_reset(self, wait_driver):
        """Test reset operation"""
        # Set a cancel event
        wait_driver.cancel_event = asyncio.Event()

        await wait_driver.reset()

        # Cancel event should be cleared
        assert wait_driver.cancel_event is None


class TestWaitTestDriverValidation:
    """Test parameter validation"""

    def test_validate_wait_time_valid(self, wait_driver):
        """Test validation of valid wait time"""
        is_valid, error = wait_driver._validate_wait_time(1000)

        assert is_valid is True
        assert error is None

    def test_validate_wait_time_negative(self, wait_driver):
        """Test validation of negative wait time"""
        is_valid, error = wait_driver._validate_wait_time(-100)

        assert is_valid is False
        assert "cannot be less than" in error

    def test_validate_wait_time_zero(self, wait_driver):
        """Test validation of zero wait time"""
        is_valid, error = wait_driver._validate_wait_time(0)

        assert is_valid is False
        assert "cannot be zero" in error

    def test_validate_wait_time_too_large(self, wait_driver):
        """Test validation of excessive wait time"""
        is_valid, error = wait_driver._validate_wait_time(4000000)

        assert is_valid is False
        assert "exceeds maximum" in error

    def test_validate_wait_time_invalid_type(self, wait_driver):
        """Test validation of invalid type"""
        is_valid, error = wait_driver._validate_wait_time("invalid")

        assert is_valid is False
        assert "must be numeric" in error


class TestWaitTestDriverOperations:
    """Test driver operations"""

    @pytest.mark.asyncio
    async def test_send_command_basic(self, wait_driver):
        """Test basic wait operation"""
        start = time.time()

        response = await wait_driver.send_command({
            'WaitmSec': 100  # 100ms
        })

        elapsed = time.time() - start

        # Should have waited approximately 100ms
        assert elapsed >= 0.09  # Allow small variance
        assert elapsed < 0.2    # But not too long
        assert "Waited for" in response

    @pytest.mark.asyncio
    async def test_send_command_one_second(self, wait_driver):
        """Test 1 second wait"""
        start = time.time()

        response = await wait_driver.send_command({
            'WaitmSec': 1000
        })

        elapsed = time.time() - start

        # Relaxed timing assertion to handle test runner overhead
        assert 0.9 < elapsed < 1.3
        assert "1.0" in response or "1 secs" in response

    @pytest.mark.asyncio
    async def test_send_command_output_format_seconds(self, wait_driver):
        """Test output format - seconds"""
        response = await wait_driver.send_command({
            'WaitmSec': 2500,
            'OutputFormat': 'seconds'
        })

        assert "2.5" in response
        assert "secs" in response
        assert "ms" not in response

    @pytest.mark.asyncio
    async def test_send_command_output_format_ms(self, wait_driver):
        """Test output format - milliseconds"""
        response = await wait_driver.send_command({
            'WaitmSec': 2500,
            'OutputFormat': 'ms'
        })

        assert "2500" in response
        assert "ms" in response

    @pytest.mark.asyncio
    async def test_send_command_output_format_both(self, wait_driver):
        """Test output format - both"""
        response = await wait_driver.send_command({
            'WaitmSec': 2500,
            'OutputFormat': 'both'
        })

        assert "2.5" in response or "2500" in response
        assert "secs" in response
        assert "ms" in response

    @pytest.mark.asyncio
    async def test_query_command(self, wait_driver):
        """Test query_command helper method"""
        start = time.time()

        response = await wait_driver.query_command(100)

        elapsed = time.time() - start

        assert elapsed >= 0.09
        assert "Waited for" in response

    @pytest.mark.asyncio
    async def test_missing_waitmsec_parameter(self, wait_driver):
        """Test error when WaitmSec parameter is missing"""
        with pytest.raises(ValueError, match="Missing required parameters"):
            await wait_driver.send_command({})

    @pytest.mark.asyncio
    async def test_invalid_waitmsec_type(self, wait_driver):
        """Test error when WaitmSec is invalid type"""
        with pytest.raises(ValueError, match="Invalid WaitmSec"):
            await wait_driver.send_command({
                'WaitmSec': 'not_a_number'
            })

    @pytest.mark.asyncio
    async def test_negative_waitmsec(self, wait_driver):
        """Test error when WaitmSec is negative"""
        with pytest.raises(ValueError, match="cannot be less"):
            await wait_driver.send_command({
                'WaitmSec': -100
            })

    @pytest.mark.asyncio
    async def test_close(self, wait_driver):
        """Test close operation"""
        wait_driver.cancel_event = asyncio.Event()

        await wait_driver.close()

        assert wait_driver.cancel_event is None


class TestWaitTestDriverAdvanced:
    """Test advanced wait functionality"""

    @pytest.mark.asyncio
    async def test_wait_dynamic_condition_met(self, wait_driver):
        """Test dynamic wait when condition is met"""
        call_count = [0]

        async def callback():
            call_count[0] += 1
            return call_count[0] >= 3  # Condition met after 3 calls

        response = await wait_driver.wait_dynamic(callback, max_wait_ms=1000, poll_interval_ms=10)

        assert "Condition met" in response
        assert call_count[0] >= 3

    @pytest.mark.asyncio
    async def test_wait_dynamic_timeout(self, wait_driver):
        """Test dynamic wait timeout"""
        async def callback():
            return False  # Never true

        response = await wait_driver.wait_dynamic(callback, max_wait_ms=100, poll_interval_ms=10)

        assert "Timeout" in response
        assert "condition not met" in response

    @pytest.mark.asyncio
    async def test_wait_between(self, wait_driver):
        """Test random wait between min and max"""
        min_ms = 50
        max_ms = 150

        start = time.time()
        response = await wait_driver.wait_between(min_ms, max_ms)
        elapsed = time.time() - start

        # Should be within range (with some tolerance)
        assert elapsed >= (min_ms / 1000) * 0.9
        assert elapsed <= (max_ms / 1000) * 1.1
        assert "Random wait" in response or "Waited for" in response

    @pytest.mark.asyncio
    async def test_wait_between_invalid_range(self, wait_driver):
        """Test wait_between with invalid range"""
        with pytest.raises(ValueError, match="must be less than"):
            await wait_driver.wait_between(200, 100)


class TestWaitTestDriverEdgeCases:
    """Test edge cases and boundary conditions"""

    @pytest.mark.asyncio
    async def test_minimum_wait(self, wait_driver):
        """Test minimum wait time (1ms)"""
        start = time.time()

        response = await wait_driver.send_command({
            'WaitmSec': 1
        })

        elapsed = time.time() - start

        # Very short wait, but should still complete
        assert "Waited for" in response
        # May not be exactly 1ms due to scheduler precision
        assert elapsed < 0.1  # Should be fast

    @pytest.mark.asyncio
    async def test_large_wait_value(self, wait_driver):
        """Test large but valid wait value"""
        config = MockWaitConnection(max_wait_ms=10000)  # 10 second limit for testing
        driver = WaitTestDriver(config)
        await driver.initialize()

        # This should be within limit
        response = await driver.send_command({
            'WaitmSec': 500  # 500ms
        })

        assert "Waited for" in response

    @pytest.mark.asyncio
    async def test_string_waitmsec_conversion(self, wait_driver):
        """Test WaitmSec as string (should be converted)"""
        response = await wait_driver.send_command({
            'WaitmSec': '100'  # String that can be converted to int
        })

        assert "Waited for" in response

    @pytest.mark.asyncio
    async def test_float_waitmsec_conversion(self, wait_driver):
        """Test WaitmSec as float (should be converted to int)"""
        response = await wait_driver.send_command({
            'WaitmSec': 100.5  # Float
        })

        assert "Waited for" in response


# ============================================================================
# Integration Tests
# ============================================================================

class TestWaitTestDriverIntegration:
    """Integration tests for complex scenarios"""

    @pytest.mark.asyncio
    async def test_sequence_of_waits(self, wait_driver):
        """Test sequence of multiple waits"""
        waits = [50, 100, 50]  # Total 200ms

        start = time.time()
        for wait_ms in waits:
            response = await wait_driver.send_command({'WaitmSec': wait_ms})
        elapsed = time.time() - start

        # Total wait time should be approximately sum of waits
        assert elapsed >= 0.15  # At least 150ms (with tolerance)
        assert elapsed < 0.3    # But not too long

    @pytest.mark.asyncio
    async def test_dynamic_wait_real_world_scenario(self, wait_driver):
        """Test dynamic wait simulating real-world condition"""
        # Simulate device booting
        boot_progress = [0]

        async def check_boot_complete():
            boot_progress[0] += 25
            return boot_progress[0] >= 100

        response = await wait_driver.wait_dynamic(
            check_boot_complete,
            max_wait_ms=500,
            poll_interval_ms=10
        )

        assert "Condition met" in response

    @pytest.mark.asyncio
    async def test_cancellation_during_wait(self, wait_driver):
        """Test cancellation of wait"""
        # Start a long wait but don't await it
        task = asyncio.create_task(wait_driver.send_command({'WaitmSec': 10000}))

        # Wait a bit
        await asyncio.sleep(0.1)

        # Cancel the task
        task.cancel()

        # Should raise CancelledError
        with pytest.raises(asyncio.CancelledError):
            await task
