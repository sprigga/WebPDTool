"""
Unit tests for L6MPU instrument drivers

Tests for:
- L6MPUSSHDriver
- L6MPUSSHComPortDriver
- L6MPUPOSSHDriver
"""
import pytest
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from decimal import Decimal

from app.services.instruments.l6mpu_ssh import L6MPUSSHDriver
from app.services.instruments.l6mpu_ssh_comport import L6MPUSSHComPortDriver
from app.services.instruments.l6mpu_pos_ssh import L6MPUPOSSHDriver


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def mock_ssh_connection():
    """Create mock SSH connection"""
    mock_conn = Mock()
    mock_config = Mock()
    mock_config.id = "L6MPU_TEST"
    mock_config.type = "L6MPU_SSH"

    mock_conn_config = Mock()
    mock_conn_config.host = "192.168.5.1"
    mock_conn_config.port = 22
    mock_conn_config.username = "root"
    mock_conn_config.password = ""
    mock_conn_config.timeout = 10000

    mock_config.connection = mock_conn_config
    mock_conn.config = mock_config

    return mock_conn


@pytest.fixture
def mock_ssh_client():
    """Create mock paramiko SSH client"""
    mock_client = MagicMock()
    mock_client.exec_command.return_value = (MagicMock(), MagicMock(), MagicMock())
    return mock_client


# ============================================================================
# L6MPUSSHDriver Tests
# ============================================================================

class TestL6MPUSSHDriver:
    """Test L6MPU SSH command driver"""

    @pytest.mark.asyncio
    async def test_initialize(self, mock_ssh_connection):
        """Test SSH connection initialization"""
        with patch('paramiko.SSHClient') as mock_ssh_class:
            mock_client = MagicMock()
            mock_ssh_class.return_value = mock_client

            driver = L6MPUSSHDriver(mock_ssh_connection)
            await driver.initialize()

            assert driver.ssh_client == mock_client

    @pytest.mark.asyncio
    async def test_exec_command(self, mock_ssh_connection):
        """Test command execution via SSH"""
        with patch('paramiko.SSHClient') as mock_ssh_class:
            mock_client = MagicMock()
            stdout_mock = MagicMock()
            stdout_mock.read.return_value = b'test output'
            mock_client.exec_command.return_value = (MagicMock(), stdout_mock, MagicMock())
            mock_ssh_class.return_value = mock_client

            driver = L6MPUSSHDriver(mock_ssh_connection)
            driver.ssh_client = mock_client

            stdout, stderr = await driver._exec_command("ls -la")

            assert stdout == "test output"
            mock_client.exec_command.assert_called_once()

    @pytest.mark.asyncio
    async def test_lte_check(self, mock_ssh_connection):
        """Test LTE module SIM check"""
        with patch('paramiko.SSHClient') as mock_ssh_class:
            mock_client = MagicMock()
            stdout_mock = MagicMock()
            stdout_mock.read.return_value = b'AT+CPIN?\n+CPIN: READY\nOK'
            mock_client.exec_command.return_value = (MagicMock(), stdout_mock, MagicMock())
            mock_ssh_class.return_value = mock_client

            driver = L6MPUSSHDriver(mock_ssh_connection)
            driver.ssh_client = mock_client

            result = await driver.lte_check()

            assert result['status'] == 'OK'
            assert result['sim_ready'] is True

    @pytest.mark.asyncio
    async def test_plc_ping_test(self, mock_ssh_connection):
        """Test PLC network ping test"""
        with patch('paramiko.SSHClient') as mock_ssh_class:
            mock_client = MagicMock()

            # Mock ifconfig response
            ifconfig_stdout = MagicMock()
            ifconfig_stdout.read.return_value = b'192.168.1.100'

            # Mock ping response
            ping_stdout = MagicMock()
            ping_stdout.read.return_value = b'PING 192.168.1.100: 64 bytes\n64 bytes from 192.168.1.100: icmp_seq=0 ttl=64\n--- 192.168.1.100 ping statistics ---\n4 packets transmitted, 4 received, 0% packet loss'

            mock_client.exec_command.side_effect = [
                (MagicMock(), ifconfig_stdout, MagicMock()),
                (MagicMock(), ping_stdout, MagicMock())
            ]
            mock_ssh_class.return_value = mock_client

            driver = L6MPUSSHDriver(mock_ssh_connection)
            driver.ssh_client = mock_client

            result = await driver.plc_ping_test(interface='eth0')

            assert result['status'] == 'OK'
            assert result['interface'] == 'eth0'
            assert result['ip_address'] == '192.168.1.100'


# ============================================================================
# L6MPUSSHComPortDriver Tests
# ============================================================================

class TestL6MPUSSHComPortDriver:
    """Test L6MPU SSH+Serial command driver"""

    @pytest.mark.asyncio
    async def test_initialize(self):
        """Test SSH and serial connection initialization"""
        mock_conn = Mock()
        mock_config = Mock()
        mock_config.id = "L6MPU_COMPORT_TEST"
        mock_config.type = "L6MPU_SSH_COMPORT"

        mock_conn_config = Mock()
        mock_conn_config.host = "192.168.5.1"
        mock_conn_config.port = 22
        mock_conn_config.username = "root"
        mock_conn_config.password = ""
        mock_conn_config.timeout = 10000
        mock_conn_config.serial_port = "COM3"
        mock_conn_config.baudrate = 115200

        mock_config.connection = mock_conn_config
        mock_conn.config = mock_config

        with patch('paramiko.SSHClient') as mock_ssh_class, \
             patch('serial.Serial') as mock_serial_class:

            mock_client = MagicMock()
            mock_ssh_class.return_value = mock_client
            mock_serial_class.return_value = MagicMock()

            driver = L6MPUSSHComPortDriver(mock_conn)
            await driver.initialize()

            assert driver.ssh_client == mock_client
            assert driver.serial_port is not None

    @pytest.mark.asyncio
    async def test_at_command_test(self):
        """Test AT command execution"""
        mock_conn = Mock()
        mock_config = Mock()
        mock_config.id = "L6MPU_COMPORT_TEST"
        mock_config.type = "L6MPU_SSH_COMPORT"
        mock_conn_config = Mock()
        mock_conn_config.host = "192.168.5.1"
        mock_conn_config.port = 22
        mock_conn_config.username = "root"
        mock_conn_config.password = ""
        mock_conn_config.timeout = 10000
        mock_conn_config.serial_port = "COM3"
        mock_conn_config.baudrate = 115200
        mock_config.connection = mock_conn_config
        mock_conn.config = mock_config

        with patch('paramiko.SSHClient') as mock_ssh_class, \
             patch('serial.Serial') as mock_serial_class:

            mock_client = MagicMock()
            mock_ssh_class.return_value = mock_client

            mock_serial = MagicMock()
            mock_serial.is_open = True
            mock_serial_class.return_value = mock_serial

            driver = L6MPUSSHComPortDriver(mock_conn)
            driver.ssh_client = mock_client
            driver.serial_port = mock_serial

            result = await driver.at_command_test("AT+CPIN?", timeout=2.0)

            assert result['status'] == 'OK'
            assert result['at_command'] == 'AT+CPIN?'


# ============================================================================
# L6MPUPOSSHDriver Tests
# ============================================================================

class TestL6MPUPOSSHDriver:
    """Test L6MPU Position SSH control driver"""

    @pytest.mark.asyncio
    async def test_initialize(self):
        """Test SSH connection initialization"""
        mock_conn = Mock()
        mock_config = Mock()
        mock_config.id = "L6MPU_POS_TEST"
        mock_config.type = "L6MPU_POS_SSH"

        mock_conn_config = Mock()
        mock_conn_config.host = "192.168.5.1"
        mock_conn_config.port = 22
        mock_conn_config.username = "root"
        mock_conn_config.password = ""
        mock_conn_config.timeout = 10000

        mock_config.connection = mock_conn_config
        mock_conn.config = mock_config

        with patch('paramiko.SSHClient') as mock_ssh_class:
            mock_client = MagicMock()
            mock_ssh_class.return_value = mock_client

            driver = L6MPUPOSSHDriver(mock_conn)
            await driver.initialize()

            assert driver.ssh_client == mock_client

    @pytest.mark.asyncio
    async def test_set_position(self):
        """Test position setting"""
        mock_conn = Mock()
        mock_config = Mock()
        mock_config.id = "L6MPU_POS_TEST"
        mock_config.type = "L6MPU_POS_SSH"
        mock_conn_config = Mock()
        mock_conn_config.host = "192.168.5.1"
        mock_conn_config.port = 22
        mock_conn_config.username = "root"
        mock_conn_config.password = ""
        mock_conn_config.timeout = 10000
        mock_config.connection = mock_conn_config
        mock_conn.config = mock_config

        with patch('paramiko.SSHClient') as mock_ssh_class:
            mock_client = MagicMock()
            mock_ssh_class.return_value = mock_client

            driver = L6MPUPOSSHDriver(mock_conn)
            driver.ssh_client = mock_client

            position = {'x': 100.0, 'y': 200.0, 'angle': 45.0, 'speed': 50}
            result = await driver.set_position(position)

            assert result['status'] == 'OK'
            assert result['position'] == position

    @pytest.mark.asyncio
    async def test_get_position(self):
        """Test getting current position"""
        mock_conn = Mock()
        mock_config = Mock()
        mock_config.id = "L6MPU_POS_TEST"
        mock_config.type = "L6MPU_POS_SSH"
        mock_conn_config = Mock()
        mock_conn_config.host = "192.168.5.1"
        mock_conn_config.port = 22
        mock_conn_config.username = "root"
        mock_conn_config.password = ""
        mock_conn_config.timeout = 10000
        mock_config.connection = mock_conn_config
        mock_conn.config = mock_config

        with patch('paramiko.SSHClient') as mock_ssh_class:
            mock_client = MagicMock()
            stdout_mock = MagicMock()
            stdout_mock.read.return_value = b'100.0,200.0,45.0'
            mock_client.exec_command.return_value = (MagicMock(), stdout_mock, MagicMock())
            mock_ssh_class.return_value = mock_client

            driver = L6MPUPOSSHDriver(mock_conn)
            driver.ssh_client = mock_client

            result = await driver.get_position()

            assert result['status'] == 'OK'
            assert result['position']['x'] == 100.0
            assert result['position']['y'] == 200.0
            assert result['position']['angle'] == 45.0
