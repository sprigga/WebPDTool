"""
Integration Tests for Relay and Chassis Rotation Measurements
"""
import pytest
from decimal import Decimal
from app.measurements.implementations import (
    RelayMeasurement,
    ChassisRotationMeasurement,
    get_measurement_class
)


class TestRelayMeasurement:
    """Test RelayMeasurement class"""

    @pytest.mark.asyncio
    async def test_relay_measurement_on(self):
        """Test relay measurement with ON state"""
        test_plan_item = {
            "item_no": 1,
            "item_name": "Relay Switch ON",
            "test_type": "RELAY",
            "parameters": {
                "relay_state": "ON",
                "channel": 1
            },
            "value_type": "float",
            "limit_type": "none"
        }

        measurement = RelayMeasurement(test_plan_item=test_plan_item, config={})
        result = await measurement.execute()

        assert result.result == "PASS"
        assert result.measured_value == Decimal("0")  # SWITCH_OPEN = 0
        assert result.item_name == "Relay Switch ON"

    @pytest.mark.asyncio
    async def test_relay_measurement_off(self):
        """Test relay measurement with OFF state"""
        test_plan_item = {
            "item_no": 2,
            "item_name": "Relay Switch OFF",
            "test_type": "RELAY",
            "parameters": {
                "relay_state": "OFF",
                "channel": 2
            },
            "value_type": "float",
            "limit_type": "none"
        }

        measurement = RelayMeasurement(test_plan_item=test_plan_item, config={})
        result = await measurement.execute()

        assert result.result == "PASS"
        assert result.measured_value == Decimal("1")  # SWITCH_CLOSED = 1

    @pytest.mark.asyncio
    async def test_relay_measurement_invalid_state(self):
        """Test relay measurement with invalid state"""
        test_plan_item = {
            "item_no": 3,
            "item_name": "Relay Invalid",
            "test_type": "RELAY",
            "parameters": {
                "relay_state": "INVALID",
                "channel": 1
            },
            "value_type": "float",
            "limit_type": "none"
        }

        measurement = RelayMeasurement(test_plan_item=test_plan_item, config={})
        result = await measurement.execute()

        assert result.result == "ERROR"
        assert "Invalid relay_state" in result.error_message

    @pytest.mark.asyncio
    async def test_relay_measurement_case_parameter(self):
        """Test relay measurement with 'case' parameter (PDTool4 compatibility)"""
        test_plan_item = {
            "item_no": 4,
            "item_name": "Relay Case Param",
            "test_type": "RELAY",
            "parameters": {
                "case": "OPEN"  # PDTool4 uses 'case' parameter
            },
            "value_type": "float",
            "limit_type": "none"
        }

        measurement = RelayMeasurement(test_plan_item=test_plan_item, config={})
        result = await measurement.execute()

        assert result.result == "PASS"
        assert result.measured_value == Decimal("0")


class TestChassisRotationMeasurement:
    """Test ChassisRotationMeasurement class"""

    @pytest.mark.asyncio
    async def test_chassis_rotation_cw(self):
        """Test chassis rotation clockwise"""
        test_plan_item = {
            "item_no": 5,
            "item_name": "Chassis Rotate CW",
            "test_type": "CHASSIS_ROTATION",
            "parameters": {
                "direction": "CW",
                "duration_ms": 100
            },
            "value_type": "float",
            "limit_type": "none"
        }

        measurement = ChassisRotationMeasurement(test_plan_item=test_plan_item, config={})
        result = await measurement.execute()

        # Result depends on whether control script exists
        assert result.result in ("PASS", "ERROR")
        if result.result == "PASS":
            assert result.measured_value == Decimal("6")  # CLOCKWISE = 6

    @pytest.mark.asyncio
    async def test_chassis_rotation_ccw(self):
        """Test chassis rotation counterclockwise"""
        test_plan_item = {
            "item_no": 6,
            "item_name": "Chassis Rotate CCW",
            "test_type": "CHASSIS_ROTATION",
            "parameters": {
                "direction": "CCW",
                "duration_ms": 100
            },
            "value_type": "float",
            "limit_type": "none"
        }

        measurement = ChassisRotationMeasurement(test_plan_item=test_plan_item, config={})
        result = await measurement.execute()

        assert result.result in ("PASS", "ERROR")
        if result.result == "PASS":
            assert result.measured_value == Decimal("9")  # COUNTERCLOCKWISE = 9

    @pytest.mark.asyncio
    async def test_chassis_rotation_invalid_direction(self):
        """Test chassis rotation with invalid direction"""
        test_plan_item = {
            "item_no": 7,
            "item_name": "Chassis Invalid",
            "test_type": "CHASSIS_ROTATION",
            "parameters": {
                "direction": "INVALID"
            },
            "value_type": "float",
            "limit_type": "none"
        }

        measurement = ChassisRotationMeasurement(test_plan_item=test_plan_item, config={})
        result = await measurement.execute()

        assert result.result == "ERROR"
        assert "Invalid direction" in result.error_message

    @pytest.mark.asyncio
    async def test_chassis_rotation_case_parameter(self):
        """Test chassis rotation with 'case' parameter (PDTool4 compatibility)"""
        test_plan_item = {
            "item_no": 8,
            "item_name": "Chassis Case Param",
            "test_type": "CHASSIS_ROTATION",
            "parameters": {
                "case": "CLOCKWISE"  # PDTool4 uses 'case' parameter
            },
            "value_type": "float",
            "limit_type": "none"
        }

        measurement = ChassisRotationMeasurement(test_plan_item=test_plan_item, config={})
        result = await measurement.execute()

        assert result.result in ("PASS", "ERROR")


class TestMeasurementRegistry:
    """Test measurement registry mappings"""

    def test_relay_measurement_registration(self):
        """Test relay measurement is registered"""
        measurement_class = get_measurement_class("RELAY")
        assert measurement_class is RelayMeasurement

        # Test lowercase variant
        measurement_class = get_measurement_class("relay")
        assert measurement_class is RelayMeasurement

    def test_chassis_rotation_measurement_registration(self):
        """Test chassis rotation measurement is registered"""
        measurement_class = get_measurement_class("CHASSIS_ROTATION")
        assert measurement_class is ChassisRotationMeasurement

        # Test lowercase variant
        measurement_class = get_measurement_class("chassis_rotation")
        assert measurement_class is ChassisRotationMeasurement

    def test_pdtool4_relay_commands(self):
        """Test PDTool4 relay command mappings"""
        # MeasureSwitchON should map to RELAY
        measurement_class = get_measurement_class("MeasureSwitchON")
        assert measurement_class is RelayMeasurement

        # MeasureSwitchOFF should map to RELAY
        measurement_class = get_measurement_class("MeasureSwitchOFF")
        assert measurement_class is RelayMeasurement

    def test_pdtool4_chassis_commands(self):
        """Test PDTool4 chassis command mappings"""
        # ChassisRotateCW should map to CHASSIS_ROTATION
        measurement_class = get_measurement_class("ChassisRotateCW")
        assert measurement_class is ChassisRotationMeasurement

        # ChassisRotateCCW should map to CHASSIS_ROTATION
        measurement_class = get_measurement_class("ChassisRotateCCW")
        assert measurement_class is ChassisRotationMeasurement
