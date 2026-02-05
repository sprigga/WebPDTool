"""
Unit tests for TCPIPCommand instrument driver
"""
import pytest
import asyncio
import binascii
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from decimal import Decimal

from app.services.instruments.tcpip_command import TCPIPCommandDriver
from app.services.instrument_connection import BaseInstrumentConnection


# ============================================================================
# Mock Connection Class
# ============================================================================

from app.core.instrument_config import InstrumentConfig, TCPIPSocketAddress

class MockTCPIPConnection(BaseInstrumentConnection):
    """Mock TCP/IP connection for testing"""

    def __init__(self, address: str, timeout: float = 5.0, use_crc32: bool = True):
        # Parse address (support both VISA-style and simple format)
        if '::SOCKET' in address or '::INSTR' in address:
            # VISA-style format: TCPIP0::192.168.1.100::5025::SOCKET
            parts = address.split('::')
            host = parts[1] if len(parts) > 1 else 'localhost'
            port_str = parts[2] if len(parts) > 2 else '5025'
            port = int(port_str)
        elif ':' in address:
            # Simple format: 192.168.1.100:5025
            host, port_str = address.rsplit(':', 1)
            port = int(port_str)
        else:
            # IP only, use default port
            host = address
            port = 5025

        config = InstrumentConfig(
            id=f"tcpip_{address.replace(':', '_')}",
            type="tcpip",
            name=f"Mock TCP/IP {address}",
            connection=TCPIPSocketAddress(
                type="TCPIP_SOCKET",
                host=host,
                port=port,
                timeout=int(timeout * 1000)
            )
        )
        super().__init__(config)
        self.use_crc32 = use_crc32

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
def mock_streams():
    """Mock asyncio StreamReader and StreamWriter"""
    from unittest.mock import MagicMock
    reader = AsyncMock()
    # writer needs some methods to be regular (non-async) mocks
    writer = MagicMock()
    writer.write = MagicMock()  # write() returns None, not a coroutine
    writer.drain = AsyncMock()  # drain() is async
    writer.close = MagicMock()  # close() returns None, not a coroutine (Python 3.7+)
    writer.wait_closed = AsyncMock()  # wait_closed() is async
    writer.is_closing = MagicMock(return_value=False)
    return reader, writer


@pytest.fixture
def tcpip_driver(mock_streams):
    """Create TCPIPCommandDriver with mocked streams"""
    reader, writer = mock_streams
    config = MockTCPIPConnection("192.168.1.100:5025", timeout=5.0)
    driver = TCPIPCommandDriver(config)
    driver.reader = reader
    driver.writer = writer
    return driver


# ============================================================================
# Test Cases
# ============================================================================

class TestTCPIPCommandDriverInitialization:
    """Test driver initialization"""

    @pytest.mark.asyncio
    async def test_initialize_simple_address(self):
        """Test initialization with simple IP:port format"""
        config = MockTCPIPConnection("192.168.1.100:5025")
        driver = TCPIPCommandDriver(config)

        with patch('asyncio.open_connection') as mock_open:
            mock_reader = AsyncMock()
            mock_writer = AsyncMock()
            mock_writer.is_closing.return_value = False
            mock_open.return_value = (mock_reader, mock_writer)

            await driver.initialize()

            assert driver.reader == mock_reader
            assert driver.writer == mock_writer
            mock_open.assert_called_once_with("192.168.1.100", 5025)

    @pytest.mark.asyncio
    async def test_initialize_visa_format(self):
        """Test initialization with VISA-style address format"""
        config = MockTCPIPConnection("TCPIP0::192.168.1.100::5025::SOCKET")
        driver = TCPIPCommandDriver(config)

        with patch('asyncio.open_connection') as mock_open:
            mock_reader = AsyncMock()
            mock_writer = AsyncMock()
            mock_writer.is_closing.return_value = False
            mock_open.return_value = (mock_reader, mock_writer)

            await driver.initialize()

            mock_open.assert_called_once_with("192.168.1.100", 5025)

    @pytest.mark.asyncio
    async def test_initialize_default_port(self):
        """Test initialization with default port"""
        config = MockTCPIPConnection("192.168.1.100")
        driver = TCPIPCommandDriver(config)

        with patch('asyncio.open_connection') as mock_open:
            mock_reader = AsyncMock()
            mock_writer = AsyncMock()
            mock_writer.is_closing.return_value = False
            mock_open.return_value = (mock_reader, mock_writer)

            await driver.initialize()

            mock_open.assert_called_once_with("192.168.1.100", 5025)

    @pytest.mark.asyncio
    async def test_initialize_timeout(self):
        """Test initialization timeout"""
        config = MockTCPIPConnection("192.168.1.100:5025", timeout=2.0)
        driver = TCPIPCommandDriver(config)

        with patch('asyncio.open_connection', side_effect=asyncio.TimeoutError):
            with pytest.raises(ConnectionError, match="Connection timeout"):
                await driver.initialize()

    @pytest.mark.asyncio
    async def test_initialize_connection_refused(self):
        """Test initialization with connection refused"""
        config = MockTCPIPConnection("192.168.1.100:5025")
        driver = TCPIPCommandDriver(config)

        with patch('asyncio.open_connection', side_effect=ConnectionRefusedError):
            with pytest.raises(ConnectionError, match="Failed to connect"):
                await driver.initialize()


class TestTCPIPCommandDriverCRC32:
    """Test CRC32 checksum functionality"""

    def test_calculate_crc32(self):
        """Test CRC32 calculation"""
        result = TCPIPCommandDriver._calculate_crc32(b'\x31\x03\xf0\x00\x00')
        assert isinstance(result, int)
        # Verify against known CRC32 value
        expected = binascii.crc32(b'\x31\x03\xf0\x00\x00')
        assert result == expected

    def test_calculate_crc32_different_data(self):
        """Test CRC32 with different data"""
        data = b'\xAA\xBB\xCC\xDD'
        result = TCPIPCommandDriver._calculate_crc32(data)
        expected = binascii.crc32(data)
        assert result == expected

    def test_bytes_to_hex_string(self):
        """Test bytes to hex string conversion"""
        driver = TCPIPCommandDriver(MockTCPIPConnection("192.168.1.100"))
        result = driver._bytes_to_hex_string(b'\x31\x03\xf0\x00\x00')
        assert result == "31 03 f0 00 00"

    def test_parse_command_hex_semicolon(self):
        """Test parsing semicolon-separated hex command"""
        driver = TCPIPCommandDriver(MockTCPIPConnection("192.168.1.100"))
        result = driver._parse_command_bytes("31;01;f0;00;00")
        assert result == b'\x31\x01\xf0\x00\x00'

    def test_parse_command_hex_space(self):
        """Test parsing space-separated hex command"""
        driver = TCPIPCommandDriver(MockTCPIPConnection("192.168.1.100"))
        result = driver._parse_command_bytes("31 01 f0 00 00")
        assert result == b'\x31\x01\xf0\x00\x00'

    def test_parse_command_plain_text(self):
        """Test parsing plain text command"""
        driver = TCPIPCommandDriver(MockTCPIPConnection("192.168.1.100"))
        result = driver._parse_command_bytes("*IDN?")
        assert result == b'*IDN?'


class TestTCPIPCommandDriverOperations:
    """Test driver operations"""

    @pytest.mark.asyncio
    async def test_send_command_with_crc32(self, tcpip_driver):
        """Test sending command with CRC32 checksum"""
        tcpip_driver.reader.read.return_value = b'\x32\x04\xf1\x01\x01'

        response = await tcpip_driver.send_command({
            'Command': '31;01;f0;00;00',
            'Timeout': 5.0
        })

        # Verify response format
        assert ' ' in response  # Space-separated hex

        # Verify writer was called
        tcpip_driver.writer.write.assert_called()
        tcpip_driver.writer.drain.assert_called()

    @pytest.mark.asyncio
    async def test_send_command_without_crc32(self, tcpip_driver):
        """Test sending command without CRC32"""
        tcpip_driver.reader.read.return_value = b'OK'

        response = await tcpip_driver.send_command({
            'Command': '*IDN?',
            'Timeout': 5.0,
            'UseCRC32': 'false'
        })

        # Should not have CRC32 appended
        call_args = tcpip_driver.writer.write.call_args[0][0]
        # Length should be command only (no 4-byte CRC)
        assert len(call_args) == len('*IDN?')

    @pytest.mark.asyncio
    async def test_send_command_plain_text(self, tcpip_driver):
        """Test sending plain text command"""
        tcpip_driver.reader.read.return_value = b'Model123,SN456,Ver1.0'

        response = await tcpip_driver.send_command({
            'Command': '*IDN?',
            'Timeout': 5.0
        })

        # Should convert response to hex string
        assert isinstance(response, str)

    @pytest.mark.asyncio
    async def test_query_command(self, tcpip_driver):
        """Test query_command helper method"""
        tcpip_driver.reader.read.return_value = b'\x12\x34'

        response = await tcpip_driver.query_command('31;01', timeout=5.0)

        assert isinstance(response, str)
        tcpip_driver.writer.write.assert_called()

    @pytest.mark.asyncio
    async def test_read_response_timeout(self, tcpip_driver):
        """Test read timeout handling"""
        tcpip_driver.reader.read.side_effect = asyncio.TimeoutError

        response = await tcpip_driver.send_command({
            'Command': '31;01',
            'Timeout': 1.0
        })

        # Should return empty string on timeout
        assert response == ""

    @pytest.mark.asyncio
    async def test_reset(self, tcpip_driver):
        """Test reset operation"""
        # Get reference to original writer to verify it was closed
        original_writer = tcpip_driver.writer

        with patch('asyncio.open_connection') as mock_open:
            # Setup mock for reconnection
            from unittest.mock import MagicMock
            mock_reader = AsyncMock()
            mock_writer = MagicMock()
            mock_writer.write = MagicMock()
            mock_writer.drain = AsyncMock()
            mock_writer.close = MagicMock()
            mock_writer.wait_closed = AsyncMock()
            mock_writer.is_closing = MagicMock(return_value=False)
            mock_open.return_value = (mock_reader, mock_writer)

            await tcpip_driver.reset()

            # Original writer should have been closed
            original_writer.close.assert_called()
            original_writer.wait_closed.assert_called()

            # New writer should be set
            assert tcpip_driver.writer == mock_writer

    @pytest.mark.asyncio
    async def test_close(self, tcpip_driver):
        """Test close operation"""
        tcpip_driver.writer.is_closing.return_value = False

        await tcpip_driver.close()

        tcpip_driver.writer.close.assert_called()
        tcpip_driver.writer.wait_closed.assert_called()


class TestTCPIPCommandDriverValidation:
    """Test parameter validation"""

    @pytest.mark.asyncio
    async def test_missing_command_parameter(self, tcpip_driver):
        """Test error when Command parameter is missing"""
        with pytest.raises(ValueError, match="Missing required parameters"):
            await tcpip_driver.send_command({})

    @pytest.mark.asyncio
    async def test_closed_connection_error(self, tcpip_driver):
        """Test error when connection is closed"""
        tcpip_driver.writer.is_closing.return_value = True

        with pytest.raises(ConnectionError, match="TCP connection not open"):
            await tcpip_driver.send_command({'Command': 'TEST'})

    @pytest.mark.asyncio
    async def test_invalid_hex_command(self, tcpip_driver):
        """Test handling of invalid hex command"""
        # Invalid hex should be treated as plain text
        tcpip_driver.reader.read.return_value = b'OK'

        response = await tcpip_driver.send_command({
            'Command': 'invalid hex!@#',
            'Timeout': 5.0
        })

        # Should still work as plain text
        tcpip_driver.writer.write.assert_called()


# ============================================================================
# Integration Tests
# ============================================================================

class TestTCPIPCommandDriverIntegration:
    """Integration tests with connection mocking"""

    @pytest.mark.asyncio
    async def test_full_communication_cycle(self):
        """Test complete communication cycle"""
        config = MockTCPIPConnection("192.168.1.100:5025")

        with patch('asyncio.open_connection') as mock_open:
            from unittest.mock import MagicMock
            mock_reader = AsyncMock()
            mock_writer = MagicMock()
            mock_writer.write = MagicMock()
            mock_writer.drain = AsyncMock()
            mock_writer.close = MagicMock()
            mock_writer.wait_closed = AsyncMock()
            mock_writer.is_closing = MagicMock(return_value=False)
            mock_reader.read.return_value = b'\x32\x04\xf1\x01\x01'
            mock_open.return_value = (mock_reader, mock_writer)

            driver = TCPIPCommandDriver(config)

            await driver.initialize()
            response = await driver.send_command({
                'Command': '31;01;f0;00;00'
            })
            await driver.close()

            assert isinstance(response, str)
            mock_writer.write.assert_called()
            mock_writer.close.assert_called()
