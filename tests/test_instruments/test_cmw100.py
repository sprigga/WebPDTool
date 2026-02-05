"""
Unit tests for CMW100 instrument driver

Tests both simulation mode and driver interface
Requires no physical hardware - all tests use simulation mode
"""
import pytest
import asyncio
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.instruments.cmw100 import CMW100Driver
from app.core.instrument_config import InstrumentConfig, VISAAddress


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def sim_connection():
    """Create a mock connection in simulation mode"""
    conn = MagicMock()
    conn.config = MagicMock()
    conn.config.id = "CMW100_SIM"
    conn.config.type = "CMW100"
    conn.config.connection = MagicMock()
    conn.config.connection.address = "sim://cmw100"
    conn.config.connection.timeout = 30000
    conn.config.options = {}
    return conn


@pytest.fixture
def cmw100_driver(sim_connection):
    """Create CMW100 driver instance"""
    return CMW100Driver(sim_connection)


# ============================================================================
# Initialization Tests
# ============================================================================

class TestCMW100DriverInit:
    """Tests for CMW100 driver initialization"""

    @pytest.mark.asyncio
    async def test_simulation_mode_detection(self, sim_connection):
        """Driver should detect simulation mode from sim:// address"""
        driver = CMW100Driver(sim_connection)
        assert driver.simulation_mode is True

    @pytest.mark.asyncio
    async def test_hardware_mode_detection(self):
        """Driver should detect hardware mode from real address"""
        conn = MagicMock()
        conn.config = MagicMock()
        conn.config.connection = MagicMock()
        conn.config.connection.address = "TCPIP0::192.168.1.100::INSTR"
        conn.config.id = "CMW100_1"
        conn.config.type = "CMW100"
        conn.config.options = {}

        driver = CMW100Driver(conn)
        assert driver.simulation_mode is False

    @pytest.mark.asyncio
    async def test_initialize_simulation_mode(self, cmw100_driver):
        """Initialize in simulation mode"""
        await cmw100_driver.initialize()
        # Should not raise any errors
        assert cmw100_driver.simulation_mode is True

    @pytest.mark.asyncio
    async def test_reset_simulation_mode(self, cmw100_driver):
        """Reset in simulation mode"""
        await cmw100_driver.reset()
        # Should not raise any errors


# ============================================================================
# BLE Measurement Tests
# ============================================================================

class TestBLEMeasurements:
    """Tests for BLE TX power measurements"""

    @pytest.mark.asyncio
    async def test_measure_ble_tx_power_simulation(self, cmw100_driver):
        """BLE TX power measurement in simulation mode"""
        result = await cmw100_driver.measure_ble_tx_power(
            connector=1,
            frequency=2440.0,
            expected_power=-5.0,
            burst_type="LE"
        )

        # Check result structure
        assert 'tx_power' in result
        assert 'frequency_error' in result
        assert 'delta_power' in result
        assert 'status' in result
        assert 'error' in result

        # Check types
        assert isinstance(result['tx_power'], Decimal)
        assert isinstance(result['frequency_error'], Decimal)
        assert isinstance(result['delta_power'], Decimal)
        assert result['status'] in ['PASS', 'WARN', 'ERROR']
        assert result['error'] is None

        # Check realistic values (BLE: -10 to +15 dBm)
        assert -15 <= float(result['tx_power']) <= 20

    @pytest.mark.asyncio
    async def test_measure_ble_tx_power_variations(self, cmw100_driver):
        """Multiple measurements should return different values (random variation)"""
        results = []
        for _ in range(5):
            result = await cmw100_driver.measure_ble_tx_power(
                connector=1,
                frequency=2440.0,
                expected_power=-5.0
            )
            results.append(float(result['tx_power']))

        # Results should have some variation (not all identical)
        assert len(set(results)) > 1

    @pytest.mark.asyncio
    async def test_measure_ble_invalid_connector(self, cmw100_driver):
        """Should raise ValueError for invalid connector"""
        with pytest.raises(ValueError, match="Invalid connector"):
            await cmw100_driver.measure_ble_tx_power(
                connector=9,  # Invalid (must be 1-8)
                frequency=2440.0,
                expected_power=-5.0
            )

    @pytest.mark.asyncio
    async def test_measure_ble_invalid_frequency(self, cmw100_driver):
        """Should raise ValueError for invalid frequency"""
        with pytest.raises(ValueError, match="Invalid frequency"):
            await cmw100_driver.measure_ble_tx_power(
                connector=1,
                frequency=100.0,  # Invalid (must be 2400-6000)
                expected_power=-5.0
            )

    @pytest.mark.asyncio
    async def test_ble_different_burst_types(self, cmw100_driver):
        """Should support BR, EDR, and LE burst types"""
        for burst_type in ["BR", "EDR", "LE"]:
            result = await cmw100_driver.measure_ble_tx_power(
                connector=1,
                frequency=2440.0,
                expected_power=-5.0,
                burst_type=burst_type
            )
            assert result['status'] in ['PASS', 'WARN']


# ============================================================================
# WiFi Measurement Tests
# ============================================================================

class TestWiFiMeasurements:
    """Tests for WiFi TX power measurements"""

    @pytest.mark.asyncio
    async def test_measure_wifi_tx_power_simulation(self, cmw100_driver):
        """WiFi TX power measurement in simulation mode"""
        result = await cmw100_driver.measure_wifi_tx_power(
            connector=1,
            standard='ac',
            channel=36,
            bandwidth=20
        )

        # Check result structure
        assert 'tx_power' in result
        assert 'peak_power' in result
        assert 'evm_all' in result
        assert 'evm_data' in result
        assert 'evm_pilot' in result
        assert 'frequency_error' in result
        assert 'status' in result
        assert 'error' in result

        # Check types
        assert isinstance(result['tx_power'], Decimal)
        assert isinstance(result['evm_all'], Decimal)
        assert result['status'] in ['PASS', 'FAIL', 'ERROR']

        # Check realistic values (WiFi: 5-25 dBm, EVM: -35 to -50 dB)
        assert 0 <= float(result['tx_power']) <= 30
        assert -60 <= float(result['evm_all']) <= -30

    @pytest.mark.asyncio
    async def test_measure_wifi_different_standards(self, cmw100_driver):
        """Should support different WiFi standards"""
        for standard in ['b/g', 'a/g', 'n', 'ac', 'ax']:
            result = await cmw100_driver.measure_wifi_tx_power(
                connector=1,
                standard=standard,
                channel=36,
                bandwidth=20
            )
            assert result['status'] in ['PASS', 'FAIL', 'ERROR']

    @pytest.mark.asyncio
    async def test_measure_wifi_different_bandwidths(self, cmw100_driver):
        """Should support different bandwidths"""
        for bandwidth in [5, 10, 20, 40, 80]:
            result = await cmw100_driver.measure_wifi_tx_power(
                connector=1,
                standard='ac',
                channel=36,
                bandwidth=bandwidth
            )
            assert result['status'] in ['PASS', 'FAIL', 'ERROR']

    @pytest.mark.asyncio
    async def test_measure_wifi_2_4_ghz_channel(self, cmw100_driver):
        """Should handle 2.4 GHz channels (1-14)"""
        result = await cmw100_driver.measure_wifi_tx_power(
            connector=1,
            standard='n',
            channel=6,
            bandwidth=20
        )
        assert result['status'] in ['PASS', 'FAIL', 'ERROR']

    @pytest.mark.asyncio
    async def test_measure_wifi_5_ghz_channel(self, cmw100_driver):
        """Should handle 5 GHz channels (36+)"""
        result = await cmw100_driver.measure_wifi_tx_power(
            connector=1,
            standard='ac',
            channel=149,
            bandwidth=20
        )
        assert result['status'] in ['PASS', 'FAIL', 'ERROR']

    @pytest.mark.asyncio
    async def test_measure_wifi_invalid_connector(self, cmw100_driver):
        """Should raise ValueError for invalid connector"""
        with pytest.raises(ValueError, match="Invalid connector"):
            await cmw100_driver.measure_wifi_tx_power(
                connector=9,  # Invalid (must be 1-8)
                standard='ac',
                channel=36,
                bandwidth=20
            )


# ============================================================================
# EVM Analysis Tests
# ============================================================================

class TestEVMAnalysis:
    """Tests for Error Vector Magnitude measurements"""

    @pytest.mark.asyncio
    async def test_evm_values_typical_range(self, cmw100_driver):
        """EVM values should be in typical range (-35 to -50 dB)"""
        result = await cmw100_driver.measure_wifi_tx_power(
            connector=1,
            standard='ac',
            channel=36,
            bandwidth=20
        )

        evm_all = float(result['evm_all'])
        evm_data = float(result['evm_data'])
        evm_pilot = float(result['evm_pilot'])

        # Check typical EVM range
        assert -60 <= evm_all <= -25
        assert -60 <= evm_data <= -25
        assert -60 <= evm_pilot <= -25

        # Pilot usually better than data
        assert evm_pilot <= evm_data  # More negative = better

    @pytest.mark.asyncio
    async def test_pass_fail_based_on_evm(self, cmw100_driver):
        """Status should be PASS when EVM <= -25 dB"""
        # Run multiple times to get both PASS and FAIL results
        results = []
        for _ in range(20):
            result = await cmw100_driver.measure_wifi_tx_power(
                connector=1,
                standard='ac',
                channel=36,
                bandwidth=20
            )
            results.append(result['status'])

        # Should have at least some PASS results (EVM <= -25)
        assert 'PASS' in results


# ============================================================================
# Command/Query Tests (Hardware Mode)
# ============================================================================

class TestHardwareCommands:
    """Tests for hardware mode command generation"""

    @pytest.mark.asyncio
    async def test_write_command_simulation(self, cmw100_driver):
        """Write command in simulation mode"""
        # Should not raise
        await cmw100_driver.write_command("*RST")

    @pytest.mark.asyncio
    async def test_query_command_simulation(self, cmw100_driver):
        """Query command in simulation mode"""
        # Common queries should return mock responses
        response = await cmw100_driver.query_command("FETCh:BLUetooth:MEAS:MEValuation:PVTime:AVERage:POWer?")
        assert response == "15.5"

        response = await cmw100_driver.query_command("FETCh:WLAN:MEAS:MEValuation:MODulation:AVERage:EVM:ALL?")
        assert response == "-35.5"


# ============================================================================
# Configuration Tests
# ============================================================================

class TestConfiguration:
    """Tests for driver configuration"""

    @pytest.mark.asyncio
    async def test_configure_ble_measurement_simulation(self, cmw100_driver):
        """Configure BLE measurement in simulation mode"""
        # Should not raise
        await cmw100_driver.configure_ble_measurement(
            connector=1,
            frequency=2440.0,
            burst_type="LE"
        )

    @pytest.mark.asyncio
    async def test_configure_wifi_measurement_simulation(self, cmw100_driver):
        """Configure WiFi measurement in simulation mode"""
        # Should not raise
        await cmw100_driver.configure_wifi_measurement(
            connector=1,
            standard='ac',
            channel=36,
            bandwidth=20
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
