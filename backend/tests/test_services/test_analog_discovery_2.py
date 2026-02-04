"""
Unit tests for Analog Discovery 2 Driver

Digilent Analog Discovery 2 USB oscilloscope and function generator
Supports function generation (Phase 2), oscilloscope (future)
"""
import pytest
from app.services.instruments.analog_discovery_2 import AnalogDiscovery2Driver
from app.services.instrument_connection import BaseInstrumentConnection


# ============================================================================
# Mock Connection Class
# ============================================================================

from app.core.instrument_config import InstrumentConfig, VISAAddress


class MockAD2Connection(BaseInstrumentConnection):
    """Mock Analog Discovery 2 connection for testing"""

    def __init__(self):
        config = InstrumentConfig(
            id="ad2",
            type="AD2",
            name="Mock Analog Discovery 2",
            connection=VISAAddress(
                type="VISA",
                address="USB0::0x03EB::0x2401::SN12345",
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
def ad2_connection():
    """Create mock Analog Discovery 2 connection"""
    return MockAD2Connection()


@pytest.fixture
def ad2_driver(ad2_connection):
    """Create AnalogDiscovery2Driver instance"""
    driver = AnalogDiscovery2Driver(ad2_connection)
    return driver


# ============================================================================
# Test Cases
# ============================================================================

class TestAnalogDiscovery2DriverUnitConversion:
    """Test _str_to_num method"""

    @pytest.mark.asyncio
    async def test_str_to_num_k(self, ad2_driver):
        """Test conversion with K suffix"""
        assert ad2_driver._str_to_num("100K") == 100000.0

    @pytest.mark.asyncio
    async def test_str_to_num_m(self, ad2_driver):
        """Test conversion with M suffix"""
        assert ad2_driver._str_to_num("1.5M") == 1500000.0

    @pytest.mark.asyncio
    async def test_str_to_num_u(self, ad2_driver):
        """Test conversion with u (micro) suffix"""
        # Use approx for floating point comparison
        from pytest import approx
        assert ad2_driver._str_to_num("100u") == approx(0.0001)

    @pytest.mark.asyncio
    async def test_str_to_num_no_suffix(self, ad2_driver):
        """Test conversion without suffix"""
        assert ad2_driver._str_to_num("100") == 100.0

    @pytest.mark.asyncio
    async def test_str_to_num_empty(self, ad2_driver):
        """Test empty string returns 0"""
        assert ad2_driver._str_to_num("") == 0.0


class TestAnalogDiscovery2DriverFunctionSelection:
    """Test _select_function method"""

    @pytest.mark.asyncio
    async def test_select_function_by_index(self, ad2_driver):
        """Test selecting function by index"""
        assert ad2_driver._select_function('0') == 'DC'
        assert ad2_driver._select_function('1') == 'Sine'
        assert ad2_driver._select_function('2') == 'Square'

    @pytest.mark.asyncio
    async def test_select_function_invalid_index(self, ad2_driver):
        """Test invalid index returns default"""
        assert ad2_driver._select_function('99') == 'Sine'


class TestAnalogDiscovery2DriverAnalogOutput:
    """Test analog output control"""

    @pytest.mark.asyncio
    async def test_set_analog_out_simulation(self, ad2_driver):
        """Test analog output in simulation mode"""
        await ad2_driver.initialize()
        await ad2_driver.set_analog_out(
            channel=0,
            function='Sine',
            frequency=10000,
            amplitude=2.0,
            offset=0
        )
        # Should not raise in simulation mode


class TestAnalogDiscovery2DriverExecuteCommand:
    """Test execute_command method with PDTool4-compatible interface"""

    @pytest.mark.asyncio
    async def test_execute_function_generator_mode(self, ad2_driver):
        """Test function generator mode execution"""
        await ad2_driver.initialize()
        result = await ad2_driver.execute_command({
            'Mode': '1',
            'Channel': '1',
            'Function': '1',
            'Frequency': '1K',
            'Amplitude': '1',
            'Offset': '0'
        })

        assert 'OK' in result
        assert 'CH1' in result

    @pytest.mark.asyncio
    async def test_execute_oscilloscope_mode_raises_error(self, ad2_driver):
        """Test oscilloscope mode raises NotImplementedError"""
        with pytest.raises(NotImplementedError, match="Oscilloscope mode not implemented"):
            await ad2_driver.execute_command({
                'Mode': '0',
                'Channel': '1'
            })

    @pytest.mark.asyncio
    async def test_execute_missing_required_parameter(self, ad2_driver):
        """Test missing required parameter raises ValueError"""
        with pytest.raises(ValueError, match="Missing required parameters"):
            await ad2_driver.execute_command({
                'Mode': '1'
            })
