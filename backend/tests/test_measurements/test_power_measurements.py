"""
Test Power Read and Power Set Measurements with Real Instrument Integration

Tests the refactored PowerReadMeasurement and PowerSetMeasurement classes
that now connect to actual instrument drivers instead of generating mock data.
"""
import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from app.measurements.implementations import PowerReadMeasurement, PowerSetMeasurement


def create_test_plan_item(item_name: str, parameters: dict, **kwargs) -> dict:
    """Helper to create test_plan_item structure matching BaseMeasurement requirements"""
    return {
        "item_no": kwargs.get("item_no", 1),
        "item_name": item_name,
        "lower_limit": kwargs.get("lower_limit"),
        "upper_limit": kwargs.get("upper_limit"),
        "limit_type": kwargs.get("limit_type", "both"),
        "value_type": kwargs.get("value_type", "float"),
        "unit": kwargs.get("unit", "V"),
        "parameters": parameters
    }


class TestPowerReadMeasurement:
    """Test PowerReadMeasurement with real instrument integration"""

    @pytest.mark.asyncio
    async def test_power_read_voltage_daq973a(self):
        """Test voltage reading from DAQ973A"""
        test_plan_item = create_test_plan_item(
            "VoltageRead",
            {"Instrument": "DAQ973A_1", "Channel": "101", "Item": "voltage"},
            lower_limit=Decimal("4.5"),
            upper_limit=Decimal("5.5")
        )
        measurement = PowerReadMeasurement(test_plan_item, config={})

        # Mock the instrument components
        mock_driver = AsyncMock()
        mock_driver.measure_voltage = AsyncMock(return_value=Decimal("5.0"))
        mock_driver.initialize = AsyncMock()

        mock_config = MagicMock()
        mock_config.type = "DAQ973A"

        with patch('app.measurements.implementations.get_instrument_settings') as mock_settings, \
             patch('app.measurements.implementations.get_driver_class') as mock_get_driver, \
             patch('app.measurements.implementations.get_connection_pool') as mock_pool:

            mock_settings.return_value.get_instrument.return_value = mock_config
            mock_get_driver.return_value = lambda conn: mock_driver

            mock_conn_ctx = MagicMock()
            mock_conn_ctx.__aenter__ = AsyncMock(return_value=MagicMock())
            mock_conn_ctx.__aexit__ = AsyncMock(return_value=None)
            mock_pool.return_value.get_connection.return_value = mock_conn_ctx

            result = await measurement.execute()

            assert result.result == "PASS"
            assert result.measured_value == Decimal("5.0")
            mock_driver.measure_voltage.assert_called_once_with(['101'])

    @pytest.mark.asyncio
    async def test_power_read_current_daq973a(self):
        """Test current reading from DAQ973A channel 121"""
        test_plan_item = create_test_plan_item(
            "CurrentRead",
            {"Instrument": "DAQ973A_1", "Channel": "121", "Item": "current"},
            lower_limit=Decimal("0.9"),
            upper_limit=Decimal("1.1"),
            unit="A"
        )
        measurement = PowerReadMeasurement(test_plan_item, config={})

        mock_driver = AsyncMock()
        mock_driver.measure_current = AsyncMock(return_value=Decimal("1.0"))
        mock_driver.initialize = AsyncMock()

        mock_config = MagicMock()
        mock_config.type = "DAQ973A"

        with patch('app.measurements.implementations.get_instrument_settings') as mock_settings, \
             patch('app.measurements.implementations.get_driver_class') as mock_get_driver, \
             patch('app.measurements.implementations.get_connection_pool') as mock_pool:

            mock_settings.return_value.get_instrument.return_value = mock_config
            mock_get_driver.return_value = lambda conn: mock_driver

            mock_conn_ctx = MagicMock()
            mock_conn_ctx.__aenter__ = AsyncMock(return_value=MagicMock())
            mock_conn_ctx.__aexit__ = AsyncMock(return_value=None)
            mock_pool.return_value.get_connection.return_value = mock_conn_ctx

            result = await measurement.execute()

            assert result.result == "PASS"
            assert result.measured_value == Decimal("1.0")
            mock_driver.measure_current.assert_called_once_with(['121'])

    @pytest.mark.asyncio
    async def test_power_read_model2306(self):
        """Test voltage reading from MODEL2306"""
        test_plan_item = create_test_plan_item(
            "VoltRead",
            {"Instrument": "MODEL2306_1", "Channel": "1", "Item": "voltage"},
            lower_limit=Decimal("11.5"),
            upper_limit=Decimal("12.5")
        )
        measurement = PowerReadMeasurement(test_plan_item, config={})

        mock_driver = AsyncMock()
        mock_driver.measure_voltage = AsyncMock(return_value=Decimal("12.0"))
        mock_driver.initialize = AsyncMock()

        mock_config = MagicMock()
        mock_config.type = "MODEL2306"

        with patch('app.measurements.implementations.get_instrument_settings') as mock_settings, \
             patch('app.measurements.implementations.get_driver_class') as mock_get_driver, \
             patch('app.measurements.implementations.get_connection_pool') as mock_pool:

            mock_settings.return_value.get_instrument.return_value = mock_config
            mock_get_driver.return_value = lambda conn: mock_driver

            mock_conn_ctx = MagicMock()
            mock_conn_ctx.__aenter__ = AsyncMock(return_value=MagicMock())
            mock_conn_ctx.__aexit__ = AsyncMock(return_value=None)
            mock_pool.return_value.get_connection.return_value = mock_conn_ctx

            result = await measurement.execute()

            assert result.result == "PASS"
            assert result.measured_value == Decimal("12.0")
            mock_driver.measure_voltage.assert_called_once_with('1')

    @pytest.mark.asyncio
    async def test_power_read_missing_instrument(self):
        """Test error when Instrument parameter is missing"""
        test_plan_item = create_test_plan_item(
            "VoltRead",
            {"Channel": "101", "Item": "voltage"}  # Missing Instrument
        )
        measurement = PowerReadMeasurement(test_plan_item, config={})

        result = await measurement.execute()

        assert result.result == "ERROR"
        assert "Missing required parameters" in result.error_message

    @pytest.mark.asyncio
    async def test_power_read_invalid_item(self):
        """Test error when Item parameter is invalid"""
        test_plan_item = create_test_plan_item(
            "InvalidRead",
            {"Instrument": "DAQ973A_1", "Channel": "101", "Item": "resistance"}
        )
        measurement = PowerReadMeasurement(test_plan_item, config={})

        result = await measurement.execute()

        assert result.result == "ERROR"
        assert "Invalid Item parameter" in result.error_message


class TestPowerSetMeasurement:
    """Test PowerSetMeasurement with real instrument integration"""

    @pytest.mark.asyncio
    async def test_power_set_model2303(self):
        """Test power set on MODEL2303"""
        test_plan_item = create_test_plan_item(
            "PowerSet",
            {"Instrument": "MODEL2303_1", "SetVolt": "12.0", "SetCurr": "2.0"}
        )
        measurement = PowerSetMeasurement(test_plan_item, config={})

        mock_driver = AsyncMock()
        mock_driver.execute_command = AsyncMock(return_value='1')
        mock_driver.initialize = AsyncMock()

        mock_config = MagicMock()
        mock_config.type = "MODEL2303"

        with patch('app.measurements.implementations.get_instrument_settings') as mock_settings, \
             patch('app.measurements.implementations.get_driver_class') as mock_get_driver, \
             patch('app.measurements.implementations.get_connection_pool') as mock_pool:

            mock_settings.return_value.get_instrument.return_value = mock_config
            mock_get_driver.return_value = lambda conn: mock_driver

            mock_conn_ctx = MagicMock()
            mock_conn_ctx.__aenter__ = AsyncMock(return_value=MagicMock())
            mock_conn_ctx.__aexit__ = AsyncMock(return_value=None)
            mock_pool.return_value.get_connection.return_value = mock_conn_ctx

            result = await measurement.execute()

            assert result.result == "PASS"
            assert result.measured_value == Decimal("1.0")
            mock_driver.execute_command.assert_called_once()

    @pytest.mark.asyncio
    async def test_power_set_model2306(self):
        """Test power set on MODEL2306 channel 2"""
        test_plan_item = create_test_plan_item(
            "PowerSet",
            {"Instrument": "MODEL2306_1", "Channel": "2", "SetVolt": "5.0", "SetCurr": "1.0"}
        )
        measurement = PowerSetMeasurement(test_plan_item, config={})

        mock_driver = AsyncMock()
        mock_driver.execute_command = AsyncMock(return_value='1')
        mock_driver.initialize = AsyncMock()

        mock_config = MagicMock()
        mock_config.type = "MODEL2306"

        with patch('app.measurements.implementations.get_instrument_settings') as mock_settings, \
             patch('app.measurements.implementations.get_driver_class') as mock_get_driver, \
             patch('app.measurements.implementations.get_connection_pool') as mock_pool:

            mock_settings.return_value.get_instrument.return_value = mock_config
            mock_get_driver.return_value = lambda conn: mock_driver

            mock_conn_ctx = MagicMock()
            mock_conn_ctx.__aenter__ = AsyncMock(return_value=MagicMock())
            mock_conn_ctx.__aexit__ = AsyncMock(return_value=None)
            mock_pool.return_value.get_connection.return_value = mock_conn_ctx

            result = await measurement.execute()

            assert result.result == "PASS"
            mock_driver.execute_command.assert_called_once()

    @pytest.mark.asyncio
    async def test_power_set_it6723c(self):
        """Test power set on IT6723C"""
        test_plan_item = create_test_plan_item(
            "PowerSet",
            {"Instrument": "IT6723C_1", "Voltage": "24.0", "Current": "3.0"}
        )
        measurement = PowerSetMeasurement(test_plan_item, config={})

        mock_driver = AsyncMock()
        mock_driver.execute_command = AsyncMock(return_value='1')
        mock_driver.initialize = AsyncMock()

        mock_config = MagicMock()
        mock_config.type = "IT6723C"

        with patch('app.measurements.implementations.get_instrument_settings') as mock_settings, \
             patch('app.measurements.implementations.get_driver_class') as mock_get_driver, \
             patch('app.measurements.implementations.get_connection_pool') as mock_pool:

            mock_settings.return_value.get_instrument.return_value = mock_config
            mock_get_driver.return_value = lambda conn: mock_driver

            mock_conn_ctx = MagicMock()
            mock_conn_ctx.__aenter__ = AsyncMock(return_value=MagicMock())
            mock_conn_ctx.__aexit__ = AsyncMock(return_value=None)
            mock_pool.return_value.get_connection.return_value = mock_conn_ctx

            result = await measurement.execute()

            assert result.result == "PASS"
            mock_driver.execute_command.assert_called_once()

    @pytest.mark.asyncio
    async def test_power_set_aps7050(self):
        """Test power set on APS7050 (generic interface)"""
        test_plan_item = create_test_plan_item(
            "PowerSet",
            {"Instrument": "APS7050_1", "SetVolt": "15.0", "SetCurr": "1.5"}
        )
        measurement = PowerSetMeasurement(test_plan_item, config={})

        mock_driver = AsyncMock()
        mock_driver.set_voltage = AsyncMock()
        mock_driver.set_current = AsyncMock()
        mock_driver.set_output = AsyncMock()
        mock_driver.measure_voltage = AsyncMock(return_value=Decimal("15.0"))
        mock_driver.initialize = AsyncMock()

        mock_config = MagicMock()
        mock_config.type = "APS7050"

        with patch('app.measurements.implementations.get_instrument_settings') as mock_settings, \
             patch('app.measurements.implementations.get_driver_class') as mock_get_driver, \
             patch('app.measurements.implementations.get_connection_pool') as mock_pool:

            mock_settings.return_value.get_instrument.return_value = mock_config
            mock_get_driver.return_value = lambda conn: mock_driver

            mock_conn_ctx = MagicMock()
            mock_conn_ctx.__aenter__ = AsyncMock(return_value=MagicMock())
            mock_conn_ctx.__aexit__ = AsyncMock(return_value=None)
            mock_pool.return_value.get_connection.return_value = mock_conn_ctx

            result = await measurement.execute()

            assert result.result == "PASS"
            mock_driver.set_voltage.assert_called_once_with(15.0)
            mock_driver.set_current.assert_called_once_with(1.5)
            mock_driver.set_output.assert_called_once_with(True)

    @pytest.mark.asyncio
    async def test_power_set_driver_error(self):
        """Test handling of driver error messages"""
        test_plan_item = create_test_plan_item(
            "PowerSet",
            {"Instrument": "MODEL2303_1", "SetVolt": "12.0", "SetCurr": "2.0"}
        )
        measurement = PowerSetMeasurement(test_plan_item, config={})

        mock_driver = AsyncMock()
        mock_driver.execute_command = AsyncMock(return_value='2303 set volt fail')
        mock_driver.initialize = AsyncMock()

        mock_config = MagicMock()
        mock_config.type = "MODEL2303"

        with patch('app.measurements.implementations.get_instrument_settings') as mock_settings, \
             patch('app.measurements.implementations.get_driver_class') as mock_get_driver, \
             patch('app.measurements.implementations.get_connection_pool') as mock_pool:

            mock_settings.return_value.get_instrument.return_value = mock_config
            mock_get_driver.return_value = lambda conn: mock_driver

            mock_conn_ctx = MagicMock()
            mock_conn_ctx.__aenter__ = AsyncMock(return_value=MagicMock())
            mock_conn_ctx.__aexit__ = AsyncMock(return_value=None)
            mock_pool.return_value.get_connection.return_value = mock_conn_ctx

            result = await measurement.execute()

            assert result.result == "FAIL"
            assert "2303 set volt fail" in result.error_message

    @pytest.mark.asyncio
    async def test_power_set_missing_parameters(self):
        """Test error when voltage/current parameters are missing"""
        test_plan_item = create_test_plan_item(
            "PowerSet",
            {"Instrument": "MODEL2303_1"}  # Missing SetVolt and SetCurr
        )
        measurement = PowerSetMeasurement(test_plan_item, config={})

        result = await measurement.execute()

        assert result.result == "ERROR"
        assert "Missing required parameters" in result.error_message

    @pytest.mark.asyncio
    async def test_power_set_invalid_voltage(self):
        """Test error when voltage value is invalid"""
        test_plan_item = create_test_plan_item(
            "PowerSet",
            {"Instrument": "MODEL2303_1", "SetVolt": "invalid", "SetCurr": "2.0"}
        )
        measurement = PowerSetMeasurement(test_plan_item, config={})

        result = await measurement.execute()

        assert result.result == "ERROR"
        assert "Invalid voltage or current value" in result.error_message


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
