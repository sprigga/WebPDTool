"""
Unit tests for PEAK CAN and SMCV100B instrument drivers

Tests for:
- PEAKCANDriver
- SMCV100BDriver
"""
import pytest
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from decimal import Decimal

from app.services.instruments.peak_can import PEAKCANDriver
from app.services.instruments.smcv100b import SMCV100BDriver


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def mock_can_connection():
    """Create mock CAN connection"""
    mock_conn = Mock()
    mock_config = Mock()
    mock_config.id = "PEAK_CAN_TEST"
    mock_config.type = "PEAK_CAN"

    mock_conn_config = Mock()
    mock_conn_config.channel = "PCAN_USBBUS1"
    mock_conn_config.interface = "pcan"
    mock_conn_config.baudrate = 500000
    mock_conn_config.fd_enabled = False

    mock_config.connection = mock_conn_config
    mock_conn.config = mock_config

    return mock_conn


@pytest.fixture
def mock_smcv_connection():
    """Create mock SMCV100B connection"""
    mock_conn = Mock()
    mock_config = Mock()
    mock_config.id = "SMCV100B_TEST"
    mock_config.type = "SMCV100B"

    mock_conn_config = Mock()
    mock_conn_config.__str__ = Mock(return_value="TCPIP0::192.168.1.200::5025::SOCKET")

    mock_config.connection = mock_conn_config
    mock_conn.config = mock_config

    return mock_conn


# ============================================================================
# PEAKCANDriver Tests
# ============================================================================

class TestPEAKCANDriver:
    """Test PEAK CAN driver"""

    def test_parse_data_string(self):
        """Test data string parsing"""
        mock_conn = Mock()
        mock_config = Mock()
        mock_config.id = "PEAK_CAN_TEST"
        mock_config.type = "PEAK_CAN"
        mock_conn_config = Mock()
        mock_conn_config.channel = "PCAN_USBBUS1"
        mock_conn_config.interface = "pcan"
        mock_conn_config.baudrate = 500000
        mock_conn_config.fd_enabled = False
        mock_config.connection = mock_conn_config
        mock_conn.config = mock_config

        driver = PEAKCANDriver(mock_conn)

        # Test comma-separated hex
        result = driver._parse_data_string("01,02,03,04")
        assert result == [0x01, 0x02, 0x03, 0x04]

        # Test semicolon-separated hex
        result = driver._parse_data_string("01;02;03;04")
        assert result == [0x01, 0x02, 0x03, 0x04]

        # Test space-separated hex
        result = driver._parse_data_string("01 02 03 04")
        assert result == [0x01, 0x02, 0x03, 0x04]

    @pytest.mark.asyncio
    async def test_send_can_message(self, mock_can_connection):
        """Test sending CAN message"""
        with patch('app.services.instruments.peak_can.CAN_AVAILABLE', True):
            with patch('app.services.instruments.peak_can.can') as mock_can:
                mock_bus = MagicMock()
                mock_can.Bus.return_value = mock_bus

                driver = PEAKCANDriver(mock_can_connection)
                driver.bus = mock_bus

                result = await driver.send_can_message(
                    can_id=0x100,
                    data="01,02,03,04",
                    is_extended=False,
                    is_fd=False
                )

                assert result['status'] == 'OK'
                assert result['can_id'] == 0x100
                assert result['data'] == [0x01, 0x02, 0x03, 0x04]

    @pytest.mark.asyncio
    async def test_receive_can_message(self, mock_can_connection):
        """Test receiving CAN message"""
        with patch('app.services.instruments.peak_can.CAN_AVAILABLE', True):
            with patch('app.services.instruments.peak_can.can') as mock_can:
                mock_bus = MagicMock()
                mock_message = MagicMock()
                mock_message.arbitration_id = 0x100
                mock_message.is_extended_id = False
                mock_message.is_fd = False
                mock_message.data = [0x01, 0x02, 0x03, 0x04]
                mock_message.timestamp = 123456.789
                mock_bus.recv.return_value = mock_message
                mock_can.Bus.return_value = mock_bus

                driver = PEAKCANDriver(mock_can_connection)
                driver.bus = mock_bus

                result = await driver.receive_can_message(timeout=5.0)

                assert result['status'] == 'OK'
                assert result['can_id'] == 0x100
                assert result['data'] == [0x01, 0x02, 0x03, 0x04]

    @pytest.mark.asyncio
    async def test_execute_command_write(self, mock_can_connection):
        """Test execute_command with write operation"""
        with patch('app.services.instruments.peak_can.CAN_AVAILABLE', True):
            with patch('app.services.instruments.peak_can.can') as mock_can:
                mock_bus = MagicMock()
                mock_can.Bus.return_value = mock_bus

                driver = PEAKCANDriver(mock_can_connection)
                driver.bus = mock_bus

                params = {
                    'operation': 'write',
                    'can_id': '0x100',
                    'data': '01,02,03,04'
                }

                result = await driver.execute_command(params)

                assert "Sent:" in result
                assert "ID=0x100" in result


# ============================================================================
# SMCV100BDriver Tests
# ============================================================================

class TestSMCV100BDriver:
    """Test SMCV100B driver"""

    @pytest.mark.asyncio
    async def test_configure_dab(self, mock_smcv_connection):
        """Test DAB configuration"""
        with patch('app.services.instruments.smcv100b.RSMCV_AVAILABLE', True):
            with patch('app.services.instruments.smcv100b.RsSmcv') as mock_rsmcv:
                mock_instr = MagicMock()
                mock_rsmcv.return_value = mock_instr

                driver = SMCV100BDriver(mock_smcv_connection)
                driver.instrument = mock_instr

                result = await driver.configure_dab(
                    frequency=220e6,
                    power=-10.0,
                    transport_file="test.ts"
                )

                assert result['status'] == 'OK'
                assert result['mode'] == 'DAB'
                assert result['frequency'] == 220e6
                assert result['power'] == -10.0

    @pytest.mark.asyncio
    async def test_configure_am(self, mock_smcv_connection):
        """Test AM configuration"""
        with patch('app.services.instruments.smcv100b.RSMCV_AVAILABLE', True):
            with patch('app.services.instruments.smcv100b.RsSmcv') as mock_rsmcv:
                mock_instr = MagicMock()
                mock_rsmcv.return_value = mock_instr

                driver = SMCV100BDriver(mock_smcv_connection)
                driver.instrument = mock_instr

                result = await driver.configure_am(
                    frequency=1000e6,
                    power=-20.0
                )

                assert result['status'] == 'OK'
                assert result['mode'] == 'AM'
                assert result['frequency'] == 1000e6
                assert result['power'] == -20.0

    @pytest.mark.asyncio
    async def test_configure_fm(self, mock_smcv_connection):
        """Test FM configuration"""
        with patch('app.services.instruments.smcv100b.RSMCV_AVAILABLE', True):
            with patch('app.services.instruments.smcv100b.RsSmcv') as mock_rsmcv:
                mock_instr = MagicMock()
                mock_rsmcv.return_value = mock_instr

                driver = SMCV100BDriver(mock_smcv_connection)
                driver.instrument = mock_instr

                result = await driver.configure_fm(
                    frequency=98.5e6,
                    power=-15.0
                )

                assert result['status'] == 'OK'
                assert result['mode'] == 'FM'
                assert result['frequency'] == 98.5e6
                assert result['power'] == -15.0

    @pytest.mark.asyncio
    async def test_set_rf_output(self, mock_smcv_connection):
        """Test RF output control"""
        with patch('app.services.instruments.smcv100b.RSMCV_AVAILABLE', True):
            with patch('app.services.instruments.smcv100b.RsSmcv') as mock_rsmcv:
                mock_instr = MagicMock()
                mock_rsmcv.return_value = mock_instr

                driver = SMCV100BDriver(mock_smcv_connection)
                driver.instrument = mock_instr

                # Test enable
                result = await driver.set_rf_output(enable=True)
                assert result['status'] == 'OK'
                assert result['rf_enabled'] is True

                # Test disable
                result = await driver.set_rf_output(enable=False)
                assert result['status'] == 'OK'
                assert result['rf_enabled'] is False

    @pytest.mark.asyncio
    async def test_execute_command(self, mock_smcv_connection):
        """Test execute_command with various modes"""
        with patch('app.services.instruments.smcv100b.RSMCV_AVAILABLE', True):
            with patch('app.services.instruments.smcv100b.RsSmcv') as mock_rsmcv:
                mock_instr = MagicMock()
                mock_rsmcv.return_value = mock_instr

                driver = SMCV100BDriver(mock_smcv_connection)
                driver.instrument = mock_instr

                # Test DAB mode
                params = {
                    'mode': 'DAB',
                    'frequency': 220,
                    'power': -10,
                    'file': 'test.ts'
                }
                result = await driver.execute_command(params)
                assert "DAB enabled" in result

                # Test AM mode
                params = {
                    'mode': 'AM',
                    'frequency': 1000,
                    'power': -20
                }
                result = await driver.execute_command(params)
                assert "AM enabled" in result

                # Test FM mode
                params = {
                    'mode': 'FM',
                    'frequency': 98.5,
                    'power': -15
                }
                result = await driver.execute_command(params)
                assert "FM enabled" in result
