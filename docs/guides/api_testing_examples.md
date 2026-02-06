# API Testing Examples

## Overview

This guide provides practical examples for testing WebPDTool APIs at different levels: unit tests for measurements, integration tests for services, and end-to-end API tests.

## Test Setup

### Prerequisites

```bash
cd backend

# Install test dependencies
pip install pytest pytest-asyncio pytest-cov pytest-mock

# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/services/test_measurements_integration.py -v
```

### Test Structure

```
backend/tests/
├── __init__.py
├── conftest.py                          # Shared fixtures
├── test_api/                            # API endpoint tests
│   ├── test_auth.py
│   ├── test_tests.py                    # Test execution API
│   └── test_measurements_api.py
├── services/                            # Service layer tests
│   ├── test_measurement_service.py
│   ├── test_test_engine.py
│   ├── test_instrument_manager.py
│   └── test_measurements_integration.py  # Measurement implementations
└── measurements/                        # Unit tests for measurements
    ├── test_base_measurement.py
    ├── test_power_measurements.py
    ├── test_relay_chassis.py
    └── test_rf_measurements.py
```

## Level 1: Unit Tests for Measurements

### Test BaseMeasurement Validation Logic

```python
# tests/measurements/test_base_measurement.py
import pytest
from decimal import Decimal
from app.measurements.implementations import DummyMeasurement


class TestBaseMeasurementValidation:
    """Test BaseMeasurement validation logic across all limit types"""

    def setup_method(self):
        """Setup common test data"""
        self.base_test_plan = {
            "item_no": 1,
            "item_name": "Test Item",
            "test_type": "DUMMY",
            "parameters": {}
        }

    def test_none_limit_always_passes(self):
        """Test NONE_LIMIT type - no validation, always passes"""
        test_plan = {
            **self.base_test_plan,
            "limit_type": "none",
            "value_type": "string"
        }

        measurement = DummyMeasurement(test_plan, {})

        # All values should pass
        assert measurement.validate_result("anything")[0] is True
        assert measurement.validate_result(123)[0] is True
        assert measurement.validate_result(999.99)[0] is True
        assert measurement.validate_result(None)[0] is True

    def test_lower_limit_validation(self):
        """Test LOWER_LIMIT type - value >= lower_limit"""
        test_plan = {
            **self.base_test_plan,
            "lower_limit": Decimal("10.0"),
            "limit_type": "lower",
            "value_type": "float"
        }

        measurement = DummyMeasurement(test_plan, {})

        # Pass cases
        passed, _ = measurement.validate_result(10.0)
        assert passed is True

        passed, _ = measurement.validate_result(15.5)
        assert passed is True

        # Fail cases
        passed, error = measurement.validate_result(9.9)
        assert passed is False
        assert "Lower failed" in error or "9.9 < 10.0" in error

    def test_upper_limit_validation(self):
        """Test UPPER_LIMIT type - value <= upper_limit"""
        test_plan = {
            **self.base_test_plan,
            "upper_limit": Decimal("100.0"),
            "limit_type": "upper",
            "value_type": "float"
        }

        measurement = DummyMeasurement(test_plan, {})

        # Pass cases
        passed, _ = measurement.validate_result(100.0)
        assert passed is True

        passed, _ = measurement.validate_result(50.5)
        assert passed is True

        # Fail cases
        passed, error = measurement.validate_result(100.1)
        assert passed is False
        assert "Upper failed" in error or "100.1 > 100.0" in error

    def test_both_limits_validation(self):
        """Test BOTH_LIMIT type - lower_limit <= value <= upper_limit"""
        test_plan = {
            **self.base_test_plan,
            "lower_limit": Decimal("10.0"),
            "upper_limit": Decimal("20.0"),
            "limit_type": "both",
            "value_type": "float"
        }

        measurement = DummyMeasurement(test_plan, {})

        # Pass cases
        passed, _ = measurement.validate_result(10.0)
        assert passed is True

        passed, _ = measurement.validate_result(15.0)
        assert passed is True

        passed, _ = measurement.validate_result(20.0)
        assert passed is True

        # Fail cases - below lower
        passed, error = measurement.validate_result(9.9)
        assert passed is False

        # Fail cases - above upper
        passed, error = measurement.validate_result(20.1)
        assert passed is False

    def test_equality_limit_validation(self):
        """Test EQUALITY_LIMIT type - value == eq_limit"""
        test_plan = {
            **self.base_test_plan,
            "eq_limit": "PASS",
            "limit_type": "equality",
            "value_type": "string"
        }

        measurement = DummyMeasurement(test_plan, {})

        # Pass case
        passed, _ = measurement.validate_result("PASS")
        assert passed is True

        # Fail cases
        passed, error = measurement.validate_result("FAIL")
        assert passed is False
        assert "Equality failed" in error

        passed, error = measurement.validate_result("pass")  # Case-sensitive
        assert passed is False

    def test_equality_limit_numeric(self):
        """Test EQUALITY_LIMIT with numeric values"""
        test_plan = {
            **self.base_test_plan,
            "eq_limit": "42",
            "limit_type": "equality",
            "value_type": "integer"
        }

        measurement = DummyMeasurement(test_plan, {})

        passed, _ = measurement.validate_result(42)
        assert passed is True

        passed, error = measurement.validate_result(43)
        assert passed is False

    def test_partial_limit_validation(self):
        """Test PARTIAL_LIMIT type - eq_limit in value (substring match)"""
        test_plan = {
            **self.base_test_plan,
            "eq_limit": "SUCCESS",
            "limit_type": "partial",
            "value_type": "string"
        }

        measurement = DummyMeasurement(test_plan, {})

        # Pass cases - substring found
        passed, _ = measurement.validate_result("Operation SUCCESS")
        assert passed is True

        passed, _ = measurement.validate_result("SUCCESS: All tests passed")
        assert passed is True

        passed, _ = measurement.validate_result("Test result: SUCCESS complete")
        assert passed is True

        # Fail cases - substring not found
        passed, error = measurement.validate_result("Operation FAILED")
        assert passed is False
        assert "Partial failed" in error

        passed, error = measurement.validate_result("ERROR occurred")
        assert passed is False

    def test_inequality_limit_validation(self):
        """Test INEQUALITY_LIMIT type - value != eq_limit"""
        test_plan = {
            **self.base_test_plan,
            "eq_limit": "ERROR",
            "limit_type": "inequality",
            "value_type": "string"
        }

        measurement = DummyMeasurement(test_plan, {})

        # Pass cases - not equal
        passed, _ = measurement.validate_result("OK")
        assert passed is True

        passed, _ = measurement.validate_result("SUCCESS")
        assert passed is True

        passed, _ = measurement.validate_result("Error")  # Case-sensitive
        assert passed is True

        # Fail case - equal
        passed, error = measurement.validate_result("ERROR")
        assert passed is False
        assert "Inequality failed" in error

    def test_value_type_string_casting(self):
        """Test value_type='string' casting"""
        test_plan = {
            **self.base_test_plan,
            "eq_limit": "123",
            "limit_type": "equality",
            "value_type": "string"
        }

        measurement = DummyMeasurement(test_plan, {})

        # Numeric input should be cast to string
        passed, _ = measurement.validate_result(123)
        assert passed is True

    def test_value_type_integer_casting(self):
        """Test value_type='integer' casting"""
        test_plan = {
            **self.base_test_plan,
            "eq_limit": "100",
            "limit_type": "equality",
            "value_type": "integer"
        }

        measurement = DummyMeasurement(test_plan, {})

        # String should be cast to integer
        passed, _ = measurement.validate_result("100")
        assert passed is True

        # Hex string should work
        passed, _ = measurement.validate_result("0x64")  # 100 in hex
        assert passed is True

    def test_value_type_float_casting(self):
        """Test value_type='float' casting"""
        test_plan = {
            **self.base_test_plan,
            "lower_limit": Decimal("10.5"),
            "upper_limit": Decimal("15.5"),
            "limit_type": "both",
            "value_type": "float"
        }

        measurement = DummyMeasurement(test_plan, {})

        # String should be cast to float
        passed, _ = measurement.validate_result("12.3")
        assert passed is True

        # Integer should work
        passed, _ = measurement.validate_result(12)
        assert passed is True

    def test_instrument_error_detection(self):
        """Test automatic detection of instrument errors"""
        test_plan = {
            **self.base_test_plan,
            "limit_type": "none",
            "value_type": "string"
        }

        measurement = DummyMeasurement(test_plan, {})

        # Should fail with "No instrument found"
        passed, error = measurement.validate_result("No instrument found")
        assert passed is False
        assert "No instrument found" in error

        # Should fail with "Error:" prefix
        passed, error = measurement.validate_result("Error: Connection timeout")
        assert passed is False
        assert "Instrument error" in error or "Error:" in error

    @pytest.mark.parametrize("measured_value,lower,upper,expected", [
        # Edge cases for BOTH_LIMIT
        (10.0, 10.0, 20.0, True),   # Exactly lower
        (20.0, 10.0, 20.0, True),   # Exactly upper
        (15.0, 10.0, 20.0, True),   # Middle
        (9.999, 10.0, 20.0, False), # Just below
        (20.001, 10.0, 20.0, False),# Just above
    ])
    def test_both_limits_edge_cases(self, measured_value, lower, upper, expected):
        """Test edge cases for both limits validation"""
        test_plan = {
            **self.base_test_plan,
            "lower_limit": Decimal(str(lower)),
            "upper_limit": Decimal(str(upper)),
            "limit_type": "both",
            "value_type": "float"
        }

        measurement = DummyMeasurement(test_plan, {})
        passed, _ = measurement.validate_result(measured_value)
        assert passed is expected
```

### Test Specific Measurement Implementations

```python
# tests/measurements/test_power_measurements.py
import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, patch
from app.measurements.implementations import PowerReadMeasurement, PowerSetMeasurement


class TestPowerReadMeasurement:
    """Test PowerReadMeasurement implementation"""

    @pytest.mark.asyncio
    @patch('app.services.instrument_manager.instrument_manager.get_driver')
    async def test_power_read_voltage_success(self, mock_get_driver):
        """Test successful voltage measurement"""
        # Setup mock driver
        mock_driver = AsyncMock()
        mock_driver.measure_voltage.return_value = 12.05
        mock_get_driver.return_value = mock_driver

        # Create test plan
        test_plan_item = {
            "item_no": 1,
            "item_name": "12V Rail Check",
            "test_type": "POWER_READ",
            "parameters": {
                "instrument_id": "PS_001",
                "channel": 1,
                "measure_type": "voltage"
            },
            "lower_limit": Decimal("11.9"),
            "upper_limit": Decimal("12.1"),
            "limit_type": "both",
            "value_type": "float",
            "unit": "V"
        }

        # Execute measurement
        measurement = PowerReadMeasurement(test_plan_item, config={})
        result = await measurement.execute()

        # Verify result
        assert result.result == "PASS"
        assert result.measured_value == Decimal("12.05")
        assert result.item_no == 1
        assert result.item_name == "12V Rail Check"
        assert result.unit == "V"
        assert result.error_message is None

        # Verify driver was called correctly
        mock_get_driver.assert_called_once_with("PS_001")
        mock_driver.measure_voltage.assert_called_once_with(1)

    @pytest.mark.asyncio
    @patch('app.services.instrument_manager.instrument_manager.get_driver')
    async def test_power_read_current_success(self, mock_get_driver):
        """Test successful current measurement"""
        mock_driver = AsyncMock()
        mock_driver.measure_current.return_value = 0.85
        mock_get_driver.return_value = mock_driver

        test_plan_item = {
            "item_no": 2,
            "item_name": "Current Draw Check",
            "test_type": "POWER_READ",
            "parameters": {
                "instrument_id": "PS_002",
                "channel": 2,
                "measure_type": "current"
            },
            "lower_limit": Decimal("0.5"),
            "upper_limit": Decimal("1.0"),
            "limit_type": "both",
            "value_type": "float",
            "unit": "A"
        }

        measurement = PowerReadMeasurement(test_plan_item, config={})
        result = await measurement.execute()

        assert result.result == "PASS"
        assert result.measured_value == Decimal("0.85")
        mock_driver.measure_current.assert_called_once_with(2)

    @pytest.mark.asyncio
    @patch('app.services.instrument_manager.instrument_manager.get_driver')
    async def test_power_read_out_of_range_fails(self, mock_get_driver):
        """Test measurement failing validation"""
        mock_driver = AsyncMock()
        mock_driver.measure_voltage.return_value = 13.5  # Out of range
        mock_get_driver.return_value = mock_driver

        test_plan_item = {
            "item_no": 3,
            "item_name": "12V Rail Check",
            "test_type": "POWER_READ",
            "parameters": {
                "instrument_id": "PS_001",
                "channel": 1,
                "measure_type": "voltage"
            },
            "lower_limit": Decimal("11.9"),
            "upper_limit": Decimal("12.1"),
            "limit_type": "both",
            "value_type": "float"
        }

        measurement = PowerReadMeasurement(test_plan_item, config={})
        result = await measurement.execute()

        assert result.result == "FAIL"
        assert result.measured_value == Decimal("13.5")
        assert result.error_message is not None
        assert "Upper failed" in result.error_message or "13.5 > 12.1" in result.error_message

    @pytest.mark.asyncio
    @patch('app.services.instrument_manager.instrument_manager.get_driver')
    async def test_power_read_instrument_error(self, mock_get_driver):
        """Test handling of instrument errors"""
        # Simulate instrument error
        mock_get_driver.side_effect = Exception("Instrument not connected")

        test_plan_item = {
            "item_no": 4,
            "item_name": "Voltage Check",
            "test_type": "POWER_READ",
            "parameters": {
                "instrument_id": "PS_999",
                "channel": 1,
                "measure_type": "voltage"
            },
            "limit_type": "none",
            "value_type": "float"
        }

        measurement = PowerReadMeasurement(test_plan_item, config={})
        result = await measurement.execute()

        assert result.result == "ERROR"
        assert "Instrument not connected" in result.error_message


class TestPowerSetMeasurement:
    """Test PowerSetMeasurement implementation"""

    @pytest.mark.asyncio
    @patch('app.services.instrument_manager.instrument_manager.get_driver')
    async def test_power_set_voltage_success(self, mock_get_driver):
        """Test successful voltage set operation"""
        mock_driver = AsyncMock()
        mock_driver.set_voltage.return_value = None
        mock_driver.set_output_state.return_value = None
        mock_get_driver.return_value = mock_driver

        test_plan_item = {
            "item_no": 5,
            "item_name": "Set 12V Output",
            "test_type": "POWER_SET",
            "parameters": {
                "instrument_id": "PS_001",
                "channel": 1,
                "voltage": 12.0,
                "current_limit": 2.0,
                "output_state": "ON"
            },
            "limit_type": "none",
            "value_type": "string"
        }

        measurement = PowerSetMeasurement(test_plan_item, config={})
        result = await measurement.execute()

        assert result.result == "PASS"
        assert result.measured_value == "12.0"  # Set voltage

        # Verify driver calls
        mock_driver.set_voltage.assert_called_once_with(1, 12.0)
        mock_driver.set_output_state.assert_called_once_with(1, True)

    @pytest.mark.asyncio
    @patch('app.services.instrument_manager.instrument_manager.get_driver')
    async def test_power_set_with_current_limit(self, mock_get_driver):
        """Test power set with current limiting"""
        mock_driver = AsyncMock()
        mock_driver.set_voltage.return_value = None
        mock_driver.set_current.return_value = None
        mock_driver.set_output_state.return_value = None
        mock_get_driver.return_value = mock_driver

        test_plan_item = {
            "item_no": 6,
            "item_name": "Set 5V with Current Limit",
            "test_type": "POWER_SET",
            "parameters": {
                "instrument_id": "PS_002",
                "channel": 1,
                "voltage": 5.0,
                "current_limit": 1.5,
                "output_state": "ON"
            },
            "limit_type": "none",
            "value_type": "string"
        }

        measurement = PowerSetMeasurement(test_plan_item, config={})
        result = await measurement.execute()

        assert result.result == "PASS"
        mock_driver.set_voltage.assert_called_once_with(1, 5.0)
        mock_driver.set_current.assert_called_once_with(1, 1.5)
```

### Test Relay and Chassis Control

```python
# tests/measurements/test_relay_chassis.py
import pytest
from decimal import Decimal
from app.measurements.implementations import RelayMeasurement, ChassisRotationMeasurement


class TestRelayMeasurement:
    """Test RelayMeasurement implementation"""

    @pytest.mark.asyncio
    async def test_relay_switch_on(self):
        """Test relay ON (OPEN) state"""
        test_plan_item = {
            "item_no": 1,
            "item_name": "Open Relay 1",
            "test_type": "RELAY",
            "parameters": {
                "relay_state": "ON",  # ON = OPEN
                "channel": 1
            },
            "limit_type": "none",
            "value_type": "float"
        }

        measurement = RelayMeasurement(test_plan_item, config={})
        result = await measurement.execute()

        assert result.result == "PASS"
        assert result.measured_value == Decimal("0")  # SWITCH_OPEN = 0
        assert result.item_name == "Open Relay 1"

    @pytest.mark.asyncio
    async def test_relay_switch_off(self):
        """Test relay OFF (CLOSED) state"""
        test_plan_item = {
            "item_no": 2,
            "item_name": "Close Relay 2",
            "test_type": "RELAY",
            "parameters": {
                "relay_state": "OFF",  # OFF = CLOSED
                "channel": 2
            },
            "limit_type": "none",
            "value_type": "float"
        }

        measurement = RelayMeasurement(test_plan_item, config={})
        result = await measurement.execute()

        assert result.result == "PASS"
        assert result.measured_value == Decimal("1")  # SWITCH_CLOSED = 1

    @pytest.mark.asyncio
    async def test_relay_pdtool4_case_parameter(self):
        """Test PDTool4 'case' parameter compatibility"""
        test_plan_item = {
            "item_no": 3,
            "item_name": "PDTool4 Relay",
            "test_type": "RELAY",
            "parameters": {
                "case": "OPEN"  # PDTool4 uses 'case' instead of 'relay_state'
            },
            "limit_type": "none",
            "value_type": "float"
        }

        measurement = RelayMeasurement(test_plan_item, config={})
        result = await measurement.execute()

        assert result.result == "PASS"
        assert result.measured_value == Decimal("0")

    @pytest.mark.asyncio
    async def test_relay_invalid_state_error(self):
        """Test error handling for invalid relay state"""
        test_plan_item = {
            "item_no": 4,
            "item_name": "Invalid Relay",
            "test_type": "RELAY",
            "parameters": {
                "relay_state": "INVALID_STATE"
            },
            "limit_type": "none",
            "value_type": "float"
        }

        measurement = RelayMeasurement(test_plan_item, config={})
        result = await measurement.execute()

        assert result.result == "ERROR"
        assert "Invalid relay_state" in result.error_message

    @pytest.mark.asyncio
    async def test_relay_missing_parameters(self):
        """Test error handling for missing parameters"""
        test_plan_item = {
            "item_no": 5,
            "item_name": "Missing Params",
            "test_type": "RELAY",
            "parameters": {},  # No relay_state or case
            "limit_type": "none",
            "value_type": "float"
        }

        measurement = RelayMeasurement(test_plan_item, config={})
        result = await measurement.execute()

        assert result.result == "ERROR"
        assert "relay_state" in result.error_message.lower() or "case" in result.error_message.lower()


class TestChassisRotationMeasurement:
    """Test ChassisRotationMeasurement implementation"""

    @pytest.mark.asyncio
    async def test_chassis_clockwise_rotation(self):
        """Test clockwise rotation"""
        test_plan_item = {
            "item_no": 10,
            "item_name": "Rotate CW",
            "test_type": "CHASSIS_ROTATION",
            "parameters": {
                "direction": "CW",
                "duration_ms": 100
            },
            "limit_type": "none",
            "value_type": "float"
        }

        measurement = ChassisRotationMeasurement(test_plan_item, config={})
        result = await measurement.execute()

        # Result depends on control script availability
        assert result.result in ("PASS", "ERROR")
        if result.result == "PASS":
            assert result.measured_value == Decimal("6")  # CLOCKWISE = 6

    @pytest.mark.asyncio
    async def test_chassis_counterclockwise_rotation(self):
        """Test counterclockwise rotation"""
        test_plan_item = {
            "item_no": 11,
            "item_name": "Rotate CCW",
            "test_type": "CHASSIS_ROTATION",
            "parameters": {
                "direction": "CCW",
                "duration_ms": 200
            },
            "limit_type": "none",
            "value_type": "float"
        }

        measurement = ChassisRotationMeasurement(test_plan_item, config={})
        result = await measurement.execute()

        assert result.result in ("PASS", "ERROR")
        if result.result == "PASS":
            assert result.measured_value == Decimal("9")  # COUNTERCLOCKWISE = 9

    @pytest.mark.asyncio
    async def test_chassis_pdtool4_case_parameter(self):
        """Test PDTool4 'case' parameter (CLOCKWISE/COUNTERCLOCKWISE)"""
        test_plan_item = {
            "item_no": 12,
            "item_name": "PDTool4 Chassis",
            "test_type": "CHASSIS_ROTATION",
            "parameters": {
                "case": "CLOCKWISE"  # PDTool4 compatibility
            },
            "limit_type": "none",
            "value_type": "float"
        }

        measurement = ChassisRotationMeasurement(test_plan_item, config={})
        result = await measurement.execute()

        assert result.result in ("PASS", "ERROR")

    @pytest.mark.asyncio
    async def test_chassis_invalid_direction_error(self):
        """Test error handling for invalid direction"""
        test_plan_item = {
            "item_no": 13,
            "item_name": "Invalid Direction",
            "test_type": "CHASSIS_ROTATION",
            "parameters": {
                "direction": "INVALID"
            },
            "limit_type": "none",
            "value_type": "float"
        }

        measurement = ChassisRotationMeasurement(test_plan_item, config={})
        result = await measurement.execute()

        assert result.result == "ERROR"
        assert "Invalid direction" in result.error_message
```

## Level 2: Service Layer Integration Tests

```python
# tests/services/test_measurement_service.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from decimal import Decimal
from app.services.measurement_service import MeasurementService


class TestMeasurementService:
    """Test MeasurementService orchestration"""

    def setup_method(self):
        """Setup test service"""
        self.service = MeasurementService()

    @pytest.mark.asyncio
    @patch('app.services.instrument_manager.instrument_manager.get_driver')
    async def test_execute_single_measurement_success(self, mock_get_driver):
        """Test successful single measurement execution"""
        # Mock instrument driver
        mock_driver = AsyncMock()
        mock_driver.measure_voltage.return_value = 12.0
        mock_get_driver.return_value = mock_driver

        # Prepare test parameters
        test_params = {
            "item_no": 1,
            "item_name": "Test Measurement",
            "test_type": "POWER_READ",
            "parameters": {
                "instrument_id": "PS_001",
                "channel": 1,
                "measure_type": "voltage"
            },
            "lower_limit": Decimal("11.5"),
            "upper_limit": Decimal("12.5"),
            "limit_type": "both",
            "value_type": "float"
        }

        # Execute measurement through service
        result = await self.service.execute_single_measurement(
            measurement_type="POWER_READ",
            test_point_id="TEST_001",
            switch_mode="PS_001",
            test_params=test_params,
            run_all_test=False
        )

        assert result.result == "PASS"
        assert result.measured_value == Decimal("12.0")

    @pytest.mark.asyncio
    async def test_execute_wait_measurement(self):
        """Test WAIT measurement execution"""
        test_params = {
            "item_no": 2,
            "item_name": "Wait 100ms",
            "test_type": "WAIT",
            "parameters": {
                "wait_time_ms": 100
            },
            "limit_type": "none",
            "value_type": "float"
        }

        result = await self.service.execute_single_measurement(
            measurement_type="WAIT",
            test_point_id="WAIT_001",
            switch_mode="",
            test_params=test_params
        )

        assert result.result == "PASS"
        assert result.measured_value == Decimal("100")

    @pytest.mark.asyncio
    async def test_unknown_measurement_type_uses_dummy(self):
        """Test unknown measurement type falls back to DummyMeasurement"""
        test_params = {
            "item_no": 3,
            "item_name": "Unknown Type",
            "test_type": "UNKNOWN_TYPE",
            "parameters": {},
            "limit_type": "none",
            "value_type": "string"
        }

        result = await self.service.execute_single_measurement(
            measurement_type="UNKNOWN_TYPE",
            test_point_id="UNKNOWN_001",
            switch_mode="",
            test_params=test_params
        )

        # Should use DummyMeasurement
        assert result.result in ("PASS", "SKIP")
```

## Level 3: End-to-End API Tests

```python
# tests/test_api/test_measurements_api.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from decimal import Decimal
from app.main import app
from app.core.database import get_db
from app.models.testplan import TestPlan
from app.models.station import Station
from app.models.project import Project


class TestMeasurementsAPI:
    """End-to-end API tests for measurement execution"""

    @pytest.fixture
    def client(self):
        """FastAPI test client"""
        return TestClient(app)

    @pytest.fixture
    def test_token(self, client):
        """Get authentication token"""
        response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        return response.json()["access_token"]

    @pytest.fixture
    def test_database(self):
        """Setup test database with sample data"""
        db = next(get_db())

        # Create test project
        project = Project(
            project_code="TEST_PRJ",
            project_name="Test Project",
            description="Test"
        )
        db.add(project)
        db.commit()

        # Create test station
        station = Station(
            project_id=project.id,
            station_code="TEST_STN",
            station_name="Test Station"
        )
        db.add(station)
        db.commit()

        # Create test plan
        test_plan = TestPlan(
            project_id=project.id,
            station_id=station.id,
            test_plan_name="Test Plan",
            item_no=1,
            item_name="Voltage Check",
            test_type="POWER_READ",
            parameters={
                "instrument_id": "PS_001",
                "channel": 1,
                "measure_type": "voltage"
            },
            lower_limit=Decimal("11.9"),
            upper_limit=Decimal("12.1"),
            limit_type="both",
            value_type="float",
            unit="V",
            sequence_order=1
        )
        db.add(test_plan)
        db.commit()

        yield {
            "project_id": project.id,
            "station_id": station.id,
            "test_plan_id": test_plan.id
        }

        # Cleanup
        db.delete(test_plan)
        db.delete(station)
        db.delete(project)
        db.commit()

    @patch('app.services.instrument_manager.instrument_manager.get_driver')
    def test_complete_test_session_flow(
        self,
        mock_get_driver,
        client,
        test_token,
        test_database
    ):
        """Test complete flow: create session → start → check results"""
        # Mock instrument
        mock_driver = AsyncMock()
        mock_driver.measure_voltage.return_value = 12.05
        mock_get_driver.return_value = mock_driver

        headers = {"Authorization": f"Bearer {test_token}"}

        # 1. Create test session
        response = client.post(
            "/api/tests/sessions",
            json={
                "serial_number": "TEST123",
                "station_id": test_database["station_id"]
            },
            headers=headers
        )

        assert response.status_code == 201
        session_data = response.json()
        session_id = session_data["id"]
        assert session_data["serial_number"] == "TEST123"
        assert session_data["status"] == "PENDING"

        # 2. Start test execution
        response = client.post(
            f"/api/tests/sessions/{session_id}/start",
            headers=headers
        )

        assert response.status_code == 200
        start_data = response.json()
        assert start_data["status"] in ["RUNNING", "COMPLETED"]

        # 3. Get session status
        response = client.get(
            f"/api/tests/sessions/{session_id}/status",
            headers=headers
        )

        assert response.status_code == 200
        status_data = response.json()
        assert status_data["session_id"] == session_id
        assert "current_test_no" in status_data

        # 4. Get test results
        response = client.get(
            f"/api/tests/sessions/{session_id}/results",
            headers=headers
        )

        assert response.status_code == 200
        results = response.json()
        assert len(results) > 0

        first_result = results[0]
        assert first_result["result"] in ["PASS", "FAIL", "ERROR", "SKIP"]
        assert "measured_value" in first_result
        assert "item_name" in first_result

        # Verify measurement was executed
        mock_driver.measure_voltage.assert_called()

    def test_create_session_invalid_station(self, client, test_token):
        """Test creating session with invalid station ID"""
        headers = {"Authorization": f"Bearer {test_token}"}

        response = client.post(
            "/api/tests/sessions",
            json={
                "serial_number": "TEST456",
                "station_id": 99999  # Non-existent
            },
            headers=headers
        )

        assert response.status_code == 404
        assert "Station not found" in response.json()["detail"]

    def test_start_session_unauthorized(self, client):
        """Test starting session without authentication"""
        response = client.post("/api/tests/sessions/1/start")

        assert response.status_code == 401

    def test_get_results_nonexistent_session(self, client, test_token):
        """Test getting results for non-existent session"""
        headers = {"Authorization": f"Bearer {test_token}"}

        response = client.get(
            "/api/tests/sessions/99999/results",
            headers=headers
        )

        assert response.status_code == 404
```

## Running Tests

### Run All Tests

```bash
cd backend

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=app --cov-report=html tests/

# View coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest tests/measurements/

# Service layer tests
pytest tests/services/

# API tests
pytest tests/test_api/

# Specific test file
pytest tests/measurements/test_power_measurements.py -v

# Specific test class
pytest tests/measurements/test_base_measurement.py::TestBaseMeasurementValidation -v

# Specific test method
pytest tests/measurements/test_power_measurements.py::TestPowerReadMeasurement::test_power_read_voltage_success -v
```

### Run Tests with Markers

```bash
# Run only async tests
pytest -m asyncio

# Run only integration tests
pytest -m integration

# Skip slow tests
pytest -m "not slow"
```

## Best Practices Summary

1. **Use Fixtures** for common test data and setup
2. **Mock External Dependencies** (instruments, databases, HTTP calls)
3. **Test All Limit Types** for measurements that use validation
4. **Test Error Conditions** (missing parameters, invalid values, timeouts)
5. **Verify API Responses** (status codes, response structure, data types)
6. **Use Parametrize** for testing multiple input/output combinations
7. **Check Coverage** regularly to identify untested code
8. **Write Descriptive Test Names** that explain what's being tested
9. **Group Related Tests** in classes for better organization
10. **Test PDTool4 Compatibility** for measurements migrated from PDTool4

## Conclusion

This testing approach provides comprehensive coverage at three levels:

- **Unit Tests**: Verify individual measurement validation logic
- **Service Tests**: Verify measurement orchestration and instrument integration
- **API Tests**: Verify complete end-to-end flows from HTTP request to database

Use these examples as templates for testing new measurements and API endpoints.
