"""
Unit tests for APS7050 Instrument Driver

GW Instek APS-7000 Series Programmable AC/DC Power Source
"""
import pytest
import asyncio
from decimal import Decimal

from app.services.instruments.aps7050 import APS7050Driver
from app.services.instrument_connection import BaseInstrumentConnection


# ============================================================================
# Mock Connection Class
# ============================================================================

from app.core.instrument_config import InstrumentConfig, VISAAddress


class MockAPS7050Connection(BaseInstrumentConnection):
    """Mock APS7050 connection for testing"""

    def __init__(self):
        config = InstrumentConfig(
            id="aps7050",
            type="APS7050",
            name="Mock APS7050",
            connection=VISAAddress(
                type="VISA",
                address="TCPIP0::192.168.1.100::inst0::INSTR",
                timeout=5000
            )
        )
        super().__init__(config)
        self._write_history: list[str] = []
        self._response_count = 0

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
        self._response_count += 1

        # Return simulated response based on command
        if command == "*IDN?":
            return "GW INSTEK,APS-7050,SN12345,v1.00"
        elif "*RST" in command:
            return ""
        elif "ROUT:OPEN?" in command:
            return "1"
        elif "ROUT:CLOS?" in command:
            return "1"
        elif "MEAS:VOLT:" in command:
            return "12.345"
        elif "MEAS:CURR:" in command:
            return "2.345"
        elif "MEAS:RES?" in command:
            return "100.0"
        elif "MEAS:FRES?" in command:
            return "100.0"
        elif "MEAS:CAP?" in command:
            return "1.0e-6"
        elif "MEAS:FREQ?" in command:
            return "1.000e6"
        else:
            return "OK"


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def aps7050_connection():
    """Create mock APS7050 connection"""
    return MockAPS7050Connection()


@pytest.fixture
def aps7050_driver(aps7050_connection):
    """Create APS7050Driver instance"""
    driver = APS7050Driver(aps7050_connection)
    return driver


# ============================================================================
# Test Cases
# ============================================================================

class TestAPs7050DriverInitialization:
    """Test driver initialization"""

    @pytest.mark.asyncio
    async def test_initialize(self, aps7050_driver, aps7050_connection):
        """Test initialization resets instrument"""
        # Connect first
        await aps7050_connection.connect()

        await aps7050_driver.initialize()

        # Connection should be marked as connected
        assert aps7050_connection.is_connected
        # Write history should contain reset command
        assert "*RST" in aps7050_connection._write_history

    @pytest.mark.asyncio
    async def test_reset(self, aps7050_driver, aps7050_connection):
        """Test reset operation"""
        await aps7050_driver.reset()

        # Should have sent reset command
        assert "*RST" in aps7050_connection._write_history

    @pytest.mark.asyncio
    async def test_get_instrument_id(self, aps7050_driver):
        """Test getting instrument ID"""
        instrument_id = aps7050_driver.instrument_id
        assert instrument_id == "aps7050"

    @pytest.mark.asyncio
    async def test_get_instrument_type(self, aps7050_driver):
        """Test getting instrument type"""
        instrument_type = aps7050_driver.instrument_type
        assert instrument_type == "APS7050"


class TestAPs7050DriverVoltageMeasurement:
    """Test voltage measurement functionality"""

    @pytest.mark.asyncio
    async def test_measure_voltage_dc(self, aps7050_driver, aps7050_connection):
        """Test DC voltage measurement"""
        result = await aps7050_driver.measure_voltage(['21'], 'DC')

        assert result == Decimal('12.345')
        assert "MEAS:VOLT:DC? (@21)" in aps7050_connection._write_history

    @pytest.mark.asyncio
    async def test_measure_voltage_ac(self, aps7050_driver):
        """Test AC voltage measurement"""
        result = await aps7050_driver.measure_voltage(['10', '11'], 'AC')

        assert result == Decimal('12.345')


class TestAPs7050DriverCurrentMeasurement:
    """Test current measurement functionality"""

    @pytest.mark.asyncio
    async def test_measure_current_dc_valid_channel_21(self, aps7050_driver):
        """Test DC current measurement with valid channel 21"""
        result = await aps7050_driver.measure_current(['21'], 'DC')

        assert result == Decimal('2.345')

    @pytest.mark.asyncio
    async def test_measure_current_dc_valid_channel_22(self, aps7050_driver):
        """Test DC current measurement with valid channel 22"""
        result = await aps7050_driver.measure_current(['22'], 'DC')

        assert result == Decimal('2.345')

    @pytest.mark.asyncio
    async def test_measure_current_invalid_channel(self, aps7050_driver):
        """Test that measuring current on invalid channel raises ValueError"""
        # Channel 10 is not in CURRENT_CHANNELS (21, 22)
        with pytest.raises(ValueError, match="Current measurement only on channels"):
            await aps7050_driver.measure_current(['10'], 'DC')


class TestAPs7050DriverChannelControl:
    """Test channel open/close operations"""

    @pytest.mark.asyncio
    async def test_open_channels(self, aps7050_driver, aps7050_connection):
        """Test opening channels"""
        result = await aps7050_driver.open_channels(['21', '22'])

        assert "ROUT:OPEN (@21,22)" in aps7050_connection._write_history
        assert "ROUT:OPEN? (@21,22)" in aps7050_connection._write_history

    @pytest.mark.asyncio
    async def test_close_channels(self, aps7050_driver, aps7050_connection):
        """Test closing channels"""
        result = await aps7050_driver.close_channels(['21', '22'])

        assert "ROUT:CLOS (@21,22)" in aps7050_connection._write_history
        assert "ROUT:CLOS? (@21,22)" in aps7050_connection._write_history


class TestAPs7050DriverResistanceMeasurement:
    """Test resistance measurement functionality"""

    @pytest.mark.asyncio
    async def test_measure_resistance_2wire(self, aps7050_driver):
        """Test 2-wire resistance measurement"""
        result = await aps7050_driver.measure_resistance(['21'], four_wire=False)

        assert result == Decimal('100.0')

    @pytest.mark.asyncio
    async def test_measure_resistance_4wire(self, aps7050_driver):
        """Test 4-wire resistance measurement"""
        result = await aps7050_driver.measure_resistance(['21'], four_wire=True)

        assert result == Decimal('100.0')


class TestAPs7050DriverFrequencyMeasurement:
    """Test frequency measurement functionality"""

    @pytest.mark.asyncio
    async def test_measure_frequency(self, aps7050_driver):
        """Test frequency measurement"""
        result = await aps7050_driver.measure_frequency(['21'])

        assert result == Decimal('1.000e6')


class TestAPs7050DriverExecuteCommand:
    """Test execute_command method with PDTool4-compatible interface"""

    @pytest.mark.asyncio
    async def test_execute_open_command(self, aps7050_driver):
        """Test OPEN command"""
        result = await aps7050_driver.execute_command({
            'Item': 'OPEN',
            'Channel': '21'
        })

        assert result == '1'

    @pytest.mark.asyncio
    async def test_execute_close_command(self, aps7050_driver):
        """Test CLOS command"""
        result = await aps7050_driver.execute_command({
            'Item': 'CLOS',
            'Channel': '21,22'
        })

        assert result == '1'

    @pytest.mark.asyncio
    async def test_execute_voltage_command(self, aps7050_driver):
        """Test VOLT command"""
        result = await aps7050_driver.execute_command({
            'Item': 'VOLT',
            'Channel': '21'
        })

        assert result == '12.345'

    @pytest.mark.asyncio
    async def test_execute_current_command(self, aps7050_driver):
        """Test CURR command"""
        result = await aps7050_driver.execute_command({
            'Item': 'CURR',
            'Channel': '21'
        })

        assert result == '2.345'

    @pytest.mark.asyncio
    async def test_execute_resistance_command(self, aps7050_driver):
        """Test RES command"""
        result = await aps7050_driver.execute_command({
            'Item': 'RES',
            'Channel': '21'
        })

        assert result == '100.000'

    @pytest.mark.asyncio
    async def test_execute_frequency_command(self, aps7050_driver):
        """Test FREQ command"""
        result = await aps7050_driver.execute_command({
            'Item': 'FREQ',
            'Channel': '21'
        })

        # Mock returns 1.000e6 which is 1,000,000 Hz
        assert result == '1000000.000'

    @pytest.mark.asyncio
    async def test_execute_channel_string_format(self, aps7050_driver):
        """Test channel parsing with string format"""
        result = await aps7050_driver.execute_command({
            'Item': 'FREQ',
            'Channel': '10,11,12'
        })

        assert result == '1000000.000'

    @pytest.mark.asyncio
    async def test_execute_channel_tuple_format(self, aps7050_driver):
        """Test channel parsing with tuple format"""
        result = await aps7050_driver.execute_command({
            'Item': 'FREQ',
            'Channel': (10, 11, 12)
        })

        assert result == '1000000.000'

    @pytest.mark.asyncio
    async def test_execute_channel_list_format(self, aps7050_driver):
        """Test channel parsing with list format"""
        result = await aps7050_driver.execute_command({
            'Item': 'FREQ',
            'Channel': [10, 11, 12]
        })

        assert result == '1000000.000'

    @pytest.mark.asyncio
    async def test_execute_channel_3digit_format(self, aps7050_driver):
        """Test channel parsing with 3-digit format (101 -> 01)"""
        result = await aps7050_driver.execute_command({
            'Item': 'FREQ',
            'Channel': '101'
        })

        assert result == '1000000.000'

    @pytest.mark.asyncio
    async def test_execute_missing_required_parameter(self, aps7050_driver):
        """Test missing required parameter raises ValueError"""
        with pytest.raises(ValueError, match="Missing required parameters"):
            await aps7050_driver.execute_command({
                'Item': 'VOLT'
            })

    @pytest.mark.asyncio
    async def test_execute_unknown_command(self, aps7050_driver):
        """Test unknown command raises ValueError"""
        with pytest.raises(ValueError, match="Unknown command"):
            await aps7050_driver.execute_command({
                'Item': 'UNKNOWN',
                'Channel': '21'
            })


class TestAPs7050DriverRawCommand:
    """Test raw SCPI command execution"""

    @pytest.mark.asyncio
    async def test_execute_raw_command_basic(self, aps7050_driver):
        """Test basic raw command execution"""
        result = await aps7050_driver.execute_raw_command('*IDN?')

        assert "GW" in result

    @pytest.mark.asyncio
    async def test_execute_raw_command_with_newline_escape(self, aps7050_driver):
        """Test raw command with \\n escape sequence"""
        result = await aps7050_driver.execute_raw_command('TEST\\n')

        # Should process the escape sequence
        assert "TEST" in aps7050_driver.connection._write_history[-1]

    @pytest.mark.asyncio
    async def test_execute_raw_command_via_execute_command(self, aps7050_driver):
        """Test raw command via execute_command parameter"""
        result = await aps7050_driver.execute_command({
            'Command': '*IDN?'
        })

        assert "GW" in result
