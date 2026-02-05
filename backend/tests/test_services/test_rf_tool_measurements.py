"""
Unit tests for RF_Tool (MT8872A) measurement implementations
Tests the measurement classes that integrate RF_Tool driver with BaseMeasurement
"""
import pytest
from decimal import Decimal
from app.measurements.implementations import (
    RF_Tool_LTE_TX_Measurement,
    RF_Tool_LTE_RX_Measurement
)


class TestRFToolLteTxMeasurement:
    """Test suite for RF_Tool LTE TX measurement"""

    def test_initialization(self):
        """Test RF_Tool_LTE_TX_Measurement initialization"""
        test_plan_item = {
            'item_no': 1,
            'item_name': 'LTE TX Power Test',
            'test_type': 'RF_Tool_LTE_TX',
            'lower_limit': Decimal('20.0'),
            'upper_limit': Decimal('25.0'),
            'limit_type': 'both',
            'value_type': 'float',
            'unit': 'dBm',
            'parameters': {
                'instrument': 'RF_Tool_1',
                'band': 'B1',
                'channel': 100,
                'bandwidth': 10.0
            }
        }
        config = {}

        measurement = RF_Tool_LTE_TX_Measurement(test_plan_item, config)

        assert measurement.item_no == 1
        assert measurement.item_name == 'LTE TX Power Test'
        assert measurement.test_params['band'] == 'B1'
        assert measurement.test_params['channel'] == 100
        assert measurement.lower_limit == Decimal('20.0')
        assert measurement.upper_limit == Decimal('25.0')

    @pytest.mark.asyncio
    async def test_execute_pass(self):
        """Test LTE TX measurement with passing result"""
        test_plan_item = {
            'item_no': 1,
            'item_name': 'LTE TX Power Test',
            'test_type': 'RF_Tool_LTE_TX',
            'lower_limit': Decimal('20.0'),
            'upper_limit': Decimal('25.0'),
            'limit_type': 'both',
            'value_type': 'float',
            'unit': 'dBm',
            'parameters': {
                'instrument': 'RF_Tool_1',
                'band': 'B1',
                'channel': 100,
                'bandwidth': 10.0
            }
        }
        config = {}

        measurement = RF_Tool_LTE_TX_Measurement(test_plan_item, config)
        result = await measurement.execute()

        assert result.result == "PASS"
        assert result.measured_value is not None
        assert result.item_name == 'LTE TX Power Test'
        assert result.error_message is None

    @pytest.mark.asyncio
    async def test_execute_fail_out_of_limits(self):
        """Test LTE TX measurement with failing result (out of limits)"""
        test_plan_item = {
            'item_no': 2,
            'item_name': 'LTE TX Power Test High',
            'test_type': 'RF_Tool_LTE_TX',
            'lower_limit': Decimal('20.0'),
            'upper_limit': Decimal('21.0'),  # Very tight limit
            'limit_type': 'both',
            'value_type': 'float',
            'unit': 'dBm',
            'parameters': {
                'instrument': 'RF_Tool_1',
                'band': 'B3',
                'channel': 200,
                'bandwidth': 10.0
            }
        }
        config = {}

        measurement = RF_Tool_LTE_TX_Measurement(test_plan_item, config)
        result = await measurement.execute()

        # Should fail because simulated value (23.5) > upper limit (21.0)
        assert result.result == "FAIL"
        assert result.measured_value is not None
        assert result.error_message is not None

    @pytest.mark.asyncio
    async def test_execute_error_handling(self):
        """Test LTE TX measurement error handling with missing parameters"""
        test_plan_item = {
            'item_no': 3,
            'item_name': 'LTE TX Invalid',
            'test_type': 'RF_Tool_LTE_TX',
            'lower_limit': Decimal('20.0'),
            'upper_limit': Decimal('25.0'),
            'limit_type': 'both',
            'value_type': 'float',
            'unit': 'dBm',
            'parameters': {
                'instrument': 'RF_Tool_1',
                # Missing band parameter
            }
        }
        config = {}

        measurement = RF_Tool_LTE_TX_Measurement(test_plan_item, config)
        result = await measurement.execute()

        # Should handle error gracefully
        assert result.result == "ERROR"
        assert result.error_message is not None
        assert "Missing required parameter: band" in result.error_message


class TestRFToolLteRxMeasurement:
    """Test suite for RF_Tool LTE RX measurement"""

    def test_initialization(self):
        """Test RF_Tool_LTE_RX_Measurement initialization"""
        test_plan_item = {
            'item_no': 4,
            'item_name': 'LTE RX Sensitivity Test',
            'test_type': 'RF_Tool_LTE_RX',
            'lower_limit': Decimal('-95.0'),
            'upper_limit': Decimal('-80.0'),
            'limit_type': 'both',
            'value_type': 'float',
            'unit': 'dBm',
            'parameters': {
                'instrument': 'RF_Tool_1',
                'band': 'B41',
                'channel': 500,
                'test_power': -90.0,
                'min_throughput': 10.0
            }
        }
        config = {}

        measurement = RF_Tool_LTE_RX_Measurement(test_plan_item, config)

        assert measurement.item_no == 4
        assert measurement.item_name == 'LTE RX Sensitivity Test'
        assert measurement.test_params['band'] == 'B41'
        assert measurement.test_params['test_power'] == -90.0
        assert measurement.lower_limit == Decimal('-95.0')

    @pytest.mark.asyncio
    async def test_execute_pass(self):
        """Test LTE RX measurement with passing result"""
        test_plan_item = {
            'item_no': 4,
            'item_name': 'LTE RX Sensitivity Test',
            'test_type': 'RF_Tool_LTE_RX',
            'lower_limit': Decimal('-95.0'),
            'upper_limit': Decimal('-80.0'),
            'limit_type': 'both',
            'value_type': 'float',
            'unit': 'dBm',
            'parameters': {
                'instrument': 'RF_Tool_1',
                'band': 'B41',
                'channel': 500,
                'test_power': -90.0,
                'min_throughput': 10.0
            }
        }
        config = {}

        measurement = RF_Tool_LTE_RX_Measurement(test_plan_item, config)
        result = await measurement.execute()

        assert result.result == "PASS"
        assert result.measured_value is not None
        assert result.item_name == 'LTE RX Sensitivity Test'
        assert result.error_message is None

    @pytest.mark.asyncio
    async def test_execute_fail_weak_signal(self):
        """Test LTE RX measurement with weak signal (fail)"""
        test_plan_item = {
            'item_no': 5,
            'item_name': 'LTE RX Weak Signal Test',
            'test_type': 'RF_Tool_LTE_RX',
            'lower_limit': Decimal('-85.0'),  # Higher (less sensitive)
            'upper_limit': Decimal('-80.0'),
            'limit_type': 'both',
            'value_type': 'float',
            'unit': 'dBm',
            'parameters': {
                'instrument': 'RF_Tool_1',
                'band': 'B7',
                'channel': 600,
                'test_power': -95.0,  # Very weak signal
                'min_throughput': 10.0
            }
        }
        config = {}

        measurement = RF_Tool_LTE_RX_Measurement(test_plan_item, config)
        result = await measurement.execute()

        # Should fail because simulated RSSI is weak
        assert result.result == "FAIL"
        assert result.measured_value is not None
        assert result.error_message is not None

    @pytest.mark.asyncio
    async def test_execute_error_handling(self):
        """Test LTE RX measurement error handling"""
        test_plan_item = {
            'item_no': 6,
            'item_name': 'LTE RX Invalid',
            'test_type': 'RF_Tool_LTE_RX',
            'lower_limit': Decimal('-95.0'),
            'upper_limit': Decimal('-80.0'),
            'limit_type': 'both',
            'value_type': 'float',
            'unit': 'dBm',
            'parameters': {
                'instrument': 'RF_Tool_1',
                'band': None,  # Missing required parameter
            }
        }
        config = {}

        measurement = RF_Tool_LTE_RX_Measurement(test_plan_item, config)
        result = await measurement.execute()

        # Should handle error gracefully
        assert result.result == "ERROR"
        assert result.error_message is not None
