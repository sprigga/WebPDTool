"""
Unit tests for N5182A Signal Generator Driver

Agilent N5182A MXG X-Series Signal Generator
Supports CW and ARB mode
"""
import pytest
from app.services.instruments.n5182a import N5182ADriver
from app.services.instrument_connection import BaseInstrumentConnection


# ============================================================================
# Mock Connection Class
# ============================================================================

from app.core.instrument_config import InstrumentConfig, VISAAddress


class MockN5182AConnection(BaseInstrumentConnection):
    """Mock N5182A connection for testing"""

    def __init__(self):
        config = InstrumentConfig(
            id="n5182a",
            type="N5182A",
            name="Mock N5182A",
            connection=VISAAddress(
                type="VISA",
                address="TCPIP0::192.168.1.100::inst0::INSTR",
                timeout=5000
            )
        )
        super().__init__(config)
        self._write_history: list[str] = []

    async def connect(self) -> bool:
        self.is_connected = True
        return True

    async def disconnect(self) -> bool:
        self.is_connected = False
        return True

    async def write(self, command: str) -> None:
        self._write_history.append(command)

    async def read(self) -> str:
        return "OK"

    async def query(self, command: str) -> str:
        self._write_history.append(command)

        # Return simulated response based on command
        if command == "*IDN?":
            return "AGILENT TECHNOLOGIES,N5182A,US12345678,1.0.0"
        elif "*RST" in command:
            return ""
        elif "FREQ:CW?" in command or "FREQ?" in command:
            return "10000000"
        elif "POW:AMPL?" in command:
            return "-10.0"
        elif "OUTP?" in command:
            return "1"
        else:
            return "OK"


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def n5182a_connection():
    """Create mock N5182A connection"""
    return MockN5182AConnection()


@pytest.fixture
def n5182a_driver(n5182a_connection):
    """Create N5182ADriver instance"""
    driver = N5182ADriver(n5182a_connection)
    return driver


# ============================================================================
# Test Cases
# ============================================================================

class TestN5182ADriverInitialization:
    """Test driver initialization"""

    @pytest.mark.asyncio
    async def test_initialize(self, n5182a_driver, n5182a_connection):
        """Test initialization resets instrument"""
        await n5182a_connection.connect()
        await n5182a_driver.initialize()

        assert n5182a_connection.is_connected
        assert "*RST" in n5182a_connection._write_history

    @pytest.mark.asyncio
    async def test_reset(self, n5182a_driver, n5182a_connection):
        """Test reset operation"""
        await n5182a_driver.reset()

        assert "*RST" in n5182a_connection._write_history


class TestN5182ADriverFrequencyControl:
    """Test frequency control functionality"""

    @pytest.mark.asyncio
    async def test_translate_frequency_khz(self, n5182a_driver):
        """Test frequency translation with K suffix"""
        result = n5182a_driver._translate_frequency("100K")
        assert result == "100 k"

    @pytest.mark.asyncio
    async def test_translate_frequency_mhz(self, n5182a_driver):
        """Test frequency translation with M suffix"""
        result = n5182a_driver._translate_frequency("50M")
        assert result == "50 m"

    @pytest.mark.asyncio
    async def test_translate_frequency_ghz(self, n5182a_driver):
        """Test frequency translation with G suffix"""
        result = n5182a_driver._translate_frequency("1G")
        assert result == "1 g"

    @pytest.mark.asyncio
    async def test_translate_frequency_none(self, n5182a_driver):
        """Test frequency translation with no suffix"""
        result = n5182a_driver._translate_frequency("1000")
        assert result == "1000 "

    @pytest.mark.asyncio
    async def test_set_frequency(self, n5182a_driver, n5182a_connection):
        """Test setting frequency"""
        await n5182a_driver.set_frequency("100K")

        # Driver generates "FREQ 100 kHz" (freq_scpi + "Hz")
        assert "FREQ 100 kHz" in n5182a_connection._write_history


class TestN5182ADriverAmplitudeControl:
    """Test amplitude control functionality"""

    @pytest.mark.asyncio
    async def test_set_amplitude(self, n5182a_driver, n5182a_connection):
        """Test setting amplitude"""
        await n5182a_driver.set_amplitude("-10")

        # Driver generates "POW:AMPL -10 dBm"
        assert "POW:AMPL -10 dBm" in n5182a_connection._write_history


class TestN5182ADriverOutputStateControl:
    """Test output state control functionality"""

    @pytest.mark.asyncio
    async def test_set_output_state_on(self, n5182a_driver, n5182a_connection):
        """Test turning output ON"""
        await n5182a_driver.set_output_state('ON')

        assert "OUTP:STAT ON" in n5182a_connection._write_history

    @pytest.mark.asyncio
    async def test_set_output_state_off(self, n5182a_driver, n5182a_connection):
        """Test turning output OFF"""
        await n5182a_driver.set_output_state('OFF')

        assert "OUTP:STAT OFF" in n5182a_connection._write_history


class TestN5182ADriverARBMode:
    """Test ARB waveform functionality"""

    @pytest.mark.asyncio
    async def test_set_arb_waveform_sine(self, n5182a_driver, n5182a_connection):
        """Test setting SINE waveform"""
        await n5182a_driver.set_arb_waveform('1')

        # Check that waveform name appears in write history
        assert any("SINE_TEST_WFM" in cmd for cmd in n5182a_connection._write_history)

    @pytest.mark.asyncio
    async def test_set_arb_waveform_ramp(self, n5182a_driver, n5182a_connection):
        """Test setting RAMP waveform"""
        await n5182a_driver.set_arb_waveform('2')

        # Check that waveform name appears in write history
        assert any("RAMP_TEST_WFM" in cmd for cmd in n5182a_connection._write_history)

    @pytest.mark.asyncio
    async def test_set_arb_waveform_invalid(self, n5182a_driver):
        """Test invalid waveform raises ValueError"""
        with pytest.raises(ValueError, match="Invalid waveform shape"):
            await n5182a_driver.set_arb_waveform('99')


class TestN5182ADriverExecuteCommand:
    """Test execute_command method with PDTool4-compatible interface"""

    @pytest.mark.asyncio
    async def test_execute_cw_mode(self, n5182a_driver):
        """Test CW mode execution"""
        result = await n5182a_driver.execute_command({
            'Mode': '1',
            'Frequency': '100K',
            'Amplitude': '-10',
            'Output': '2'
        })

        # Should contain frequency, power, and RF state info
        assert "FREQ:" in result
        assert "POWER:" in result
        assert "RF:" in result

    @pytest.mark.asyncio
    async def test_execute_arb_mode(self, n5182a_driver):
        """Test ARB mode execution"""
        result = await n5182a_driver.execute_command({
            'Mode': '2',
            'Shape': '1',
            'Output': '1'  # Don't trigger RST
        })

        # Should configure ARB waveform - check if waveform name appears in any command
        history = n5182a_driver.connection._write_history
        assert any("SINE_TEST_WFM" in cmd for cmd in history), f"No SINE_TEST_WFM found in: {history}"

    @pytest.mark.asyncio
    async def test_execute_reset_mode(self, n5182a_driver):
        """Test reset mode"""
        result = await n5182a_driver.execute_command({
            'Output': '0'
        })

        # Should return identification string
        assert "AGILENT" in result
