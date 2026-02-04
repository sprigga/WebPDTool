"""
Unit tests for FTM_On Driver

WiFi Factory Test Mode automation for Qualcomm chipsets
"""
import pytest
from unittest.mock import patch, MagicMock
from app.services.instruments.ftm_on import FTMOnDriver
from app.services.instrument_connection import BaseInstrumentConnection


# ============================================================================
# Mock Connection Class
# ============================================================================

from app.core.instrument_config import InstrumentConfig, VISAAddress


class MockFTMConnection(BaseInstrumentConnection):
    """Mock FTM connection for testing"""

    def __init__(self):
        config = InstrumentConfig(
            id="ftm",
            type="FTM_ON",
            name="Mock WiFi FTM Test",
            connection=VISAAddress(
                type="VISA",
                address="TCPIP0::192.168.1.100::inst0::INSTR",
                timeout=5000
            )
        )
        super().__init__(config)

    async def connect(self) -> bool:
        self.is_connected = True
        return True

    async def disconnect(self) -> bool:
        self.is_connected = False
        return True

    async def write(self, command: str) -> None:
        pass

    async def read(self) -> str:
        return "OK"

    async def query(self, command: str) -> str:
        return "OK"


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def ftm_connection():
    """Create mock FTM connection"""
    return MockFTMConnection()


@pytest.fixture
def ftm_driver(ftm_connection):
    """Create FTMOnDriver instance"""
    driver = FTMOnDriver(ftm_connection)
    return driver


# ============================================================================
# Test Cases
# ============================================================================

class TestFTMOnDriverInitialization:
    """Test driver initialization"""

    @pytest.mark.asyncio
    async def test_initialize(self, ftm_driver):
        """Test driver initialization"""
        await ftm_driver.initialize()
        assert ftm_driver is not None


class TestFTMOnDriverFTMMode:
    """Test FTM mode control"""

    @patch('subprocess.run')
    @pytest.mark.asyncio
    async def test_open_ftm_mode(self, mock_run, ftm_driver):
        """Test opening FTM mode"""
        # Mock subprocess responses
        mock_run.return_value = MagicMock(stdout="", returncode=0)

        result = await ftm_driver.open_ftm_mode()

        # Verify 5 ADB commands were run
        assert mock_run.call_count == 5
        assert result is not None

    @pytest.mark.asyncio
    async def test_close_ftm_mode(self, ftm_driver):
        """Test closing FTM mode"""
        # Should not raise - just logs
        await ftm_driver.close_ftm_mode()


class TestFTMOnDriverTXTest:
    """Test TX power testing"""

    @patch('subprocess.run')
    @pytest.mark.asyncio
    async def test_run_tx_test_chain1(self, mock_run, ftm_driver):
        """Test TX test on chain 1"""
        mock_run.return_value = MagicMock(
            stdout="TX Test Complete: PASS",
            returncode=0
        )

        result = await ftm_driver.run_tx_test(chain=1)

        assert "PASS" in result
        mock_run.assert_called_once()

    @patch('subprocess.run')
    @pytest.mark.asyncio
    async def test_run_tx_test_chain2(self, mock_run, ftm_driver):
        """Test TX test on chain 2"""
        mock_run.return_value = MagicMock(
            stdout="TX Test Complete: PASS",
            returncode=0
        )

        result = await ftm_driver.run_tx_test(chain=2)

        assert "PASS" in result


class TestFTMOnDriverExecuteCommand:
    """Test execute_command method with PDTool4-compatible interface"""

    @patch('subprocess.run')
    @pytest.mark.asyncio
    async def test_execute_with_command(self, mock_run, ftm_driver):
        """Test executing external command"""
        mock_run.return_value = MagicMock(
            stdout="Command executed successfully",
            returncode=0
        )

        result = await ftm_driver.execute_command({
            'Command': 'python ./src/lowsheen_lib/RF_tool/FTM_On/test.py'
        })

        assert "successfully" in result
        mock_run.assert_called_once()

    @patch('subprocess.run')
    @pytest.mark.asyncio
    async def test_execute_with_chain(self, mock_run, ftm_driver):
        """Test executing TX test via Chain parameter"""
        mock_run.return_value = MagicMock(
            stdout="TX Test: PASS",
            returncode=0
        )

        result = await ftm_driver.execute_command({
            'Chain': '1'
        })

        assert "PASS" in result

    @pytest.mark.asyncio
    async def test_execute_missing_required_parameter(self, ftm_driver):
        """Test missing required parameter raises ValueError"""
        with pytest.raises(ValueError, match="Missing required parameter"):
            await ftm_driver.execute_command({})
