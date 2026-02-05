"""
Unit tests for ComPortCommand instrument driver
"""
import pytest
import asyncio
import builtins
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from decimal import Decimal

from app.services.instruments.comport_command import ComPortCommandDriver
from app.services.instrument_connection import BaseInstrumentConnection


# ============================================================================
# Mock Connection Class
# ============================================================================

from app.core.instrument_config import InstrumentConfig, SerialAddress

class MockSerialConnection(BaseInstrumentConnection):
    """Mock serial connection for testing"""

    def __init__(self, port: str, baudrate: int = 115200, timeout: float = 3.0):
        # Create a proper config
        config = InstrumentConfig(
            id=f"comport_{port}",
            type="comport",
            name=f"Mock Serial {port}",
            connection=SerialAddress(
                type="SERIAL",
                port=port,
                baudrate=baudrate,
                timeout=int(timeout * 1000)  # Convert to ms
            )
        )
        super().__init__(config)
        self.port = port
        self.baudrate = baudrate
        self.comport_wait = 0

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
def mock_serial():
    """Mock serial.Serial object"""
    mock = MagicMock()
    mock.is_open = True
    mock.write = MagicMock()
    mock.readline = MagicMock()
    mock.flush = MagicMock()
    mock.timeout = 3.0
    return mock


@pytest.fixture
def comport_driver(mock_serial):
    """Create ComPortCommandDriver with mocked serial port"""
    config = MockSerialConnection("COM9", baudrate=115200, timeout=3.0)
    driver = ComPortCommandDriver(config)
    driver.serial_port = mock_serial
    return driver


@pytest.fixture
def mock_serial_open():
    """Context manager for mocking serial port opening"""
    with patch('serial.Serial') as mock:
        instance = MagicMock()
        instance.is_open = True
        instance.write = MagicMock()
        instance.readline = MagicMock()
        instance.flush = MagicMock()
        instance.timeout = 3.0
        mock.return_value = instance
        yield mock, instance


# ============================================================================
# Test Cases
# ============================================================================

class TestComPortCommandDriverInitialization:
    """Test driver initialization"""

    @pytest.mark.asyncio
    async def test_initialize_success(self, mock_serial_open):
        """Test successful initialization"""
        mock, instance = mock_serial_open
        config = MockSerialConnection("COM9", baudrate=115200, timeout=3.0)
        driver = ComPortCommandDriver(config)

        await driver.initialize()

        assert driver.serial_port == instance
        mock.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_with_wait(self, mock_serial_open):
        """Test initialization with comport_wait delay"""
        mock, instance = mock_serial_open
        config = MockSerialConnection("COM9", baudrate=115200, timeout=3.0)

        # Use object_setattr to add comport_wait directly to the config object
        # (bypassing Pydantic validation)
        object.__setattr__(config.config, 'comport_wait', 1)

        driver = ComPortCommandDriver(config)

        import time
        start = time.time()
        await driver.initialize()
        elapsed = time.time() - start

        assert elapsed >= 1.0
        assert driver.serial_port == instance

    @pytest.mark.asyncio
    async def test_initialize_failure(self):
        """Test initialization failure"""
        # Mock Serial() to raise SerialException (the proper exception type)
        import serial
        with patch('serial.Serial', side_effect=serial.SerialException("Port not found")):
            config = MockSerialConnection("INVALID", baudrate=115200)
            driver = ComPortCommandDriver(config)

            with pytest.raises(ConnectionError, match="Failed to connect to serial port"):
                await driver.initialize()


class TestComPortCommandDriverOperations:
    """Test driver operations"""

    @pytest.mark.asyncio
    async def test_send_command_single_line(self, comport_driver):
        """Test sending command with single line response"""
        comport_driver.serial_port.readline.return_value = b"OK\r\n"

        response = await comport_driver.send_command({
            'Command': 'TEST\n',
            'Timeout': 3.0,
            'ReslineCount': 1
        })

        assert response == "OK"
        comport_driver.serial_port.write.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_command_multi_line(self, comport_driver):
        """Test sending command with multi-line response"""
        comport_driver.serial_port.readline.side_effect = [
            b"Line 1\r\n",
            b"Line 2\r\n",
            b"Line 3\r\n"
        ]

        response = await comport_driver.send_command({
            'Command': 'READ ALL\n',
            'Timeout': 3.0,
            'ReslineCount': 3
        })

        assert response == "Line 1\nLine 2\nLine 3"

    @pytest.mark.asyncio
    async def test_send_command_auto_detect(self, comport_driver):
        """Test auto-detect mode (read until no data)"""
        # Return 2 lines then empty
        comport_driver.serial_port.readline.side_effect = [
            b"Line 1\r\n",
            b"Line 2\r\n",
            b"",
            b"",
            b""
        ]

        response = await comport_driver.send_command({
            'Command': 'READ\n',
            'Timeout': 3.0
        })

        assert response == "Line 1\nLine 2"

    @pytest.mark.asyncio
    async def test_send_command_escape_sequences(self, comport_driver):
        """Test escape sequence processing"""
        comport_driver.serial_port.readline.return_value = b"Acknowledged\r\n"

        response = await comport_driver.send_command({
            'Command': 'CMD\\n\\r',  # Should be converted to actual newline/carriage return
            'Timeout': 3.0
        })

        # Verify the command was sent with proper escape conversion
        sent_data = comport_driver.serial_port.write.call_args[0][0]
        assert b'\n' in sent_data

    @pytest.mark.asyncio
    async def test_query_command(self, comport_driver):
        """Test query_command helper method"""
        comport_driver.serial_port.readline.return_value = b"12.345\r\n"

        # Use line_count=1 to read exactly one line
        response = await comport_driver.query_command("MEASURE?\n", timeout=3.0, line_count=1)

        assert response == "12.345"

    @pytest.mark.asyncio
    async def test_reset(self, comport_driver):
        """Test reset operation"""
        await comport_driver.reset()

        # Should send both reset commands
        assert comport_driver.serial_port.write.call_count >= 2

    @pytest.mark.asyncio
    async def test_close(self, comport_driver):
        """Test close operation"""
        comport_driver.serial_port.is_open = True

        await comport_driver.close()

        comport_driver.serial_port.close.assert_called_once()


class TestComPortCommandDriverValidation:
    """Test parameter validation"""

    @pytest.mark.asyncio
    async def test_missing_command_parameter(self, comport_driver):
        """Test error when Command parameter is missing"""
        with pytest.raises(ValueError, match="Missing required parameters"):
            await comport_driver.send_command({})

    @pytest.mark.asyncio
    async def test_invalid_line_count(self, comport_driver):
        """Test handling of invalid line count"""
        # Return data once, then empty reads (need 3 empties for max_empty_reads)
        comport_driver.serial_port.readline.side_effect = [
            b"Data\r\n",  # First read returns data
            b"",          # Empty read 1
            b"",          # Empty read 2
            b"",          # Empty read 3 (will exit loop here)
        ]

        # Invalid line count should be converted to None (auto-detect)
        response = await comport_driver.send_command({
            'Command': 'TEST\n',
            'ReslineCount': 'invalid'
        })

        # Should still work with auto-detect
        assert response == "Data"

    @pytest.mark.asyncio
    async def test_closed_port_error(self, comport_driver):
        """Test error handling when port is closed"""
        comport_driver.serial_port.is_open = False

        with pytest.raises(ConnectionError, match="Serial port not open"):
            await comport_driver.send_command({'Command': 'TEST\n'})


class TestComPortCommandDriverTimeout:
    """Test timeout handling"""

    @pytest.mark.asyncio
    async def test_read_timeout(self, comport_driver):
        """Test read timeout handling"""
        # Simulate timeout (empty reads)
        comport_driver.serial_port.readline.return_value = b""

        response = await comport_driver.send_command({
            'Command': 'TEST\n',
            'Timeout': 1.0
        })

        # Should return empty string on timeout
        assert response == ""

    @pytest.mark.asyncio
    async def test_partial_response_timeout(self, comport_driver):
        """Test timeout with partial response"""
        # Return 1 line then empty reads (need enough for max_empty_reads=3)
        comport_driver.serial_port.readline.side_effect = [
            b"Line 1\r\n",  # First read returns data
            b"",           # Empty read 1
            b"",           # Empty read 2
            b"",           # Empty read 3 (will exit loop here)
        ]

        response = await comport_driver.send_command({
            'Command': 'TEST\n',
            'Timeout': 1.0
        })

        # Should return partial response
        assert response == "Line 1"


# ============================================================================
# Integration Tests
# ============================================================================

class TestComPortCommandDriverIntegration:
    """Integration tests with actual serial mocking"""

    @pytest.mark.asyncio
    async def test_full_command_response_cycle(self, mock_serial_open):
        """Test complete command-response cycle"""
        mock, instance = mock_serial_open
        # Return response once, then empty reads to terminate auto-detect
        instance.readline.side_effect = [
            b"Response\r\n",
            b"",
            b"",
            b"",
        ]

        config = MockSerialConnection("COM9")
        driver = ComPortCommandDriver(config)

        await driver.initialize()
        response = await driver.send_command({'Command': 'PING\n'})
        await driver.close()

        assert response == "Response"
