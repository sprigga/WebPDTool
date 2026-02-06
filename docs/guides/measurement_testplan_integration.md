# Measurement and TestPlan Integration Guide

## Overview

This guide explains how WebPDTool's measurement system, instrument drivers, and test plans work together to execute hardware tests through the API. Understanding this integration is crucial for writing effective API tests and developing new measurement types.

## Architecture Components

### 1. TestPlan Model (`backend/app/models/testplan.py`)

The TestPlan model stores test specifications imported from CSV files. It defines what to test, how to test it, and the pass/fail criteria.

**Key Fields:**

```python
class TestPlan(Base):
    # Test identification
    item_no = Column(Integer)           # Test sequence number
    item_name = Column(String(100))     # Test description
    test_type = Column(String(50))      # Measurement type (POWER_READ, RELAY, etc.)

    # Test parameters (JSON format)
    parameters = Column(JSON)           # Flexible parameter storage

    # Pass/fail criteria
    lower_limit = Column(DECIMAL(15,6)) # Lower boundary
    upper_limit = Column(DECIMAL(15,6)) # Upper boundary
    limit_type = Column(String(50))     # Validation type (lower/upper/both/equality/partial/inequality/none)
    value_type = Column(String(50))     # Data type (string/integer/float)
    eq_limit = Column(String(100))      # Equality/partial match value

    # Execution settings
    command = Column(String(500))       # Command to execute
    timeout = Column(Integer)           # Timeout in seconds
    wait_msec = Column(Integer)         # Wait duration for WAIT measurement
```

**Example TestPlan Record:**

```json
{
  "item_no": 5,
  "item_name": "Power Supply Voltage Check",
  "test_type": "POWER_READ",
  "parameters": {
    "instrument_id": "PS_001",
    "channel": 1
  },
  "lower_limit": 11.9,
  "upper_limit": 12.1,
  "limit_type": "both",
  "value_type": "float",
  "unit": "V"
}
```

### 2. BaseMeasurement (`backend/app/measurements/base.py`)

Abstract base class that all measurements inherit from. It provides:

- **PDTool4 Compatibility:** Implements the exact validation logic from PDTool4
- **Limit Validation:** 7 limit types (lower/upper/both/equality/partial/inequality/none)
- **Value Casting:** 3 value types (string/integer/float)
- **Error Detection:** Recognizes instrument errors ("No instrument found", "Error:")

**Key Methods:**

```python
class BaseMeasurement(ABC):
    def __init__(self, test_plan_item: Dict[str, Any], config: Dict[str, Any]):
        """Initialize from TestPlan dictionary"""
        self.item_no = test_plan_item.get("item_no")
        self.item_name = test_plan_item.get("item_name")
        self.lower_limit = test_plan_item.get("lower_limit")
        self.upper_limit = test_plan_item.get("upper_limit")
        self.limit_type = LIMIT_TYPE_MAP.get(test_plan_item.get("limit_type"), NONE_LIMIT)
        self.value_type = VALUE_TYPE_MAP.get(test_plan_item.get("value_type"), StringType)
        self.test_params = test_plan_item.get("parameters", {})

    @abstractmethod
    async def execute(self) -> MeasurementResult:
        """Implement test execution logic"""
        pass

    def validate_result(self, measured_value, run_all_test="OFF") -> Tuple[bool, Optional[str]]:
        """Validate measured value against limits"""
        # PDTool4 validation logic implementation
        pass
```

**Validation Examples:**

```python
# Lower limit only (value >= 10.0)
test_plan = {
    "lower_limit": 10.0,
    "limit_type": "lower",
    "value_type": "float"
}
measurement = SomeMeasurement(test_plan, config)
passed, error = measurement.validate_result(12.5)  # True, None
passed, error = measurement.validate_result(9.5)   # False, "Lower failed: 9.5 < 10.0"

# Both limits (10.0 <= value <= 15.0)
test_plan = {
    "lower_limit": 10.0,
    "upper_limit": 15.0,
    "limit_type": "both",
    "value_type": "float"
}
passed, error = measurement.validate_result(12.5)  # True, None
passed, error = measurement.validate_result(16.0)  # False, "Upper failed: 16.0 > 15.0"

# Equality check
test_plan = {
    "eq_limit": "PASS",
    "limit_type": "equality",
    "value_type": "string"
}
passed, error = measurement.validate_result("PASS")  # True, None
passed, error = measurement.validate_result("FAIL")  # False, "Equality failed"

# Partial string match
test_plan = {
    "eq_limit": "OK",
    "limit_type": "partial",
    "value_type": "string"
}
passed, error = measurement.validate_result("Status: OK")  # True, None
passed, error = measurement.validate_result("Error")       # False, "Partial failed"
```

### 3. Measurement Implementations (`backend/app/measurements/implementations.py`)

17 concrete measurement classes implementing specific test logic. Each class:

1. **Inherits from BaseMeasurement**
2. **Reads parameters from `self.test_params` (TestPlan.parameters field)**
3. **Uses instrument drivers for hardware communication**
4. **Returns MeasurementResult with validation**

**Available Measurements:**

| Measurement Class | test_type | Purpose | Instrument Required |
|-------------------|-----------|---------|---------------------|
| DummyMeasurement | DUMMY | Testing/simulation | None |
| CommandTestMeasurement | COMMAND_TEST | Execute shell/serial commands | Optional (console/comport/tcpip) |
| PowerReadMeasurement | POWER_READ | Read power supply voltage/current | Power supply (MODEL2303, IT6723C, etc.) |
| PowerSetMeasurement | POWER_SET | Set power supply output | Power supply |
| WaitMeasurement | WAIT | Delay execution | None |
| RelayMeasurement | RELAY | Control relay switches | DUT relay hardware |
| ChassisRotationMeasurement | CHASSIS_ROTATION | Rotate chassis motor | DUT chassis hardware |
| RF_Tool_LTE_TX_Measurement | RF_TOOL_LTE_TX | LTE transmit test | RF instrument + RF_Tool.exe |
| RF_Tool_LTE_RX_Measurement | RF_TOOL_LTE_RX | LTE receive test | RF instrument + RF_Tool.exe |
| CMW100_BLE_Measurement | CMW100_BLE | Bluetooth test | CMW100 |
| CMW100_WiFi_Measurement | CMW100_WIFI | WiFi test | CMW100 |
| L6MPU_LTE_Check_Measurement | L6MPU_LTE_CHECK | LTE module check | L6MPU (SSH) |
| L6MPU_PLC_Test_Measurement | L6MPU_PLC_TEST | PLC communication test | L6MPU (SSH) |
| SMCV100B_RF_Output_Measurement | SMCV100B_RF_OUTPUT | RF output power test | SMCV100B |
| PEAK_CAN_Message_Measurement | PEAK_CAN_MESSAGE | CAN bus message test | PEAK CAN interface |
| SFCMeasurement | SFC_TEST | SFC web service integration | None (HTTP) |
| GetSNMeasurement | GET_SN | Get device serial number | None |
| OPJudgeMeasurement | OP_JUDGE | Operator judgment prompt | None |

**Example Implementation:**

```python
class PowerReadMeasurement(BaseMeasurement):
    """Read voltage or current from power supply"""

    async def execute(self) -> MeasurementResult:
        start_time = time.time()

        try:
            # 1. Extract parameters from TestPlan.parameters
            instrument_id = self.test_params.get("instrument_id")
            channel = self.test_params.get("channel", 1)
            measure_type = self.test_params.get("measure_type", "voltage")

            # 2. Get instrument driver from manager
            from app.services.instrument_manager import instrument_manager
            driver = await instrument_manager.get_driver(instrument_id)

            # 3. Execute measurement using driver
            if measure_type == "voltage":
                measured_value = await driver.measure_voltage(channel)
            elif measure_type == "current":
                measured_value = await driver.measure_current(channel)

            # 4. Validate result using BaseMeasurement logic
            passed, error_msg = self.validate_result(measured_value)

            # 5. Return MeasurementResult
            result_status = "PASS" if passed else "FAIL"
            duration_ms = int((time.time() - start_time) * 1000)

            return self.create_result(
                result=result_status,
                measured_value=Decimal(str(measured_value)),
                error_message=error_msg,
                execution_duration_ms=duration_ms
            )

        except Exception as e:
            self.logger.error(f"PowerRead failed: {e}")
            return self.create_result(
                result="ERROR",
                error_message=str(e)
            )
```

### 4. Instrument Drivers (`backend/app/services/instruments/`)

Provide hardware abstraction for 25+ instrument types. All drivers inherit from `BaseInstrumentDriver`.

**Base Driver Interface:**

```python
class BaseInstrumentDriver(ABC):
    def __init__(self, connection: BaseInstrumentConnection):
        self.connection = connection

    @abstractmethod
    async def initialize(self):
        """Initialize instrument to known state"""
        pass

    @abstractmethod
    async def reset(self):
        """Reset instrument to default state"""
        pass

    async def write_command(self, command: str):
        """Send command to instrument"""
        await self.connection.write(command)

    async def query_command(self, command: str) -> str:
        """Query instrument and return response"""
        return await self.connection.query(command)

    async def query_float(self, command: str) -> float:
        """Query and return float value"""
        response = await self.query_command(command)
        return float(response)
```

**Example Driver Usage:**

```python
# In PowerReadMeasurement.execute()
from app.services.instrument_manager import instrument_manager

# Get driver instance
driver = await instrument_manager.get_driver("PS_001")  # Returns MODEL2303Driver

# Driver-specific methods
voltage = await driver.measure_voltage(channel=1)
current = await driver.measure_current(channel=1)
```

**Available Drivers (25 types):**

```python
INSTRUMENT_DRIVERS = {
    # Power Supplies
    "DAQ973A": DAQ973ADriver,
    "MODEL2303": MODEL2303Driver,
    "MODEL2306": MODEL2306Driver,
    "IT6723C": IT6723CDriver,
    "PSW3072": PSW3072Driver,
    "APS7050": APS7050Driver,

    # RF Instruments
    "CMW100": CMW100Driver,
    "MT8872A": MT8872ADriver,
    "N5182A": N5182ADriver,
    "SMCV100B": SMCV100BDriver,

    # DUT Communication
    "L6MPU_SSH": L6MPUSSHDriver,
    "L6MPU_SSH_COMPORT": L6MPUSSHComPortDriver,
    "L6MPU_POS_SSH": L6MPUPOSSHDriver,
    "PEAK_CAN": PEAKCANDriver,

    # Other instruments
    "DAQ6510": DAQ6510Driver,
    "KEITHLEY2015": KEITHLEY2015Driver,
    "MDO34": MDO34Driver,
    "A34970A": A34970ADriver,
    "A2260B": A2260BDriver,
    "AnalogDiscovery2": AnalogDiscovery2Driver,
    "FTMOn": FTMOnDriver
}
```

### 5. Measurement Registry

Dynamic registry mapping test types to measurement classes:

```python
# From implementations.py
MEASUREMENT_REGISTRY = {
    # Standard types
    "DUMMY": DummyMeasurement,
    "COMMAND_TEST": CommandTestMeasurement,
    "POWER_READ": PowerReadMeasurement,
    "POWER_SET": PowerSetMeasurement,
    "WAIT": WaitMeasurement,
    "RELAY": RelayMeasurement,
    "CHASSIS_ROTATION": ChassisRotationMeasurement,

    # RF measurements
    "RF_TOOL_LTE_TX": RF_Tool_LTE_TX_Measurement,
    "RF_TOOL_LTE_RX": RF_Tool_LTE_RX_Measurement,
    "CMW100_BLE": CMW100_BLE_Measurement,
    "CMW100_WIFI": CMW100_WiFi_Measurement,

    # DUT measurements
    "L6MPU_LTE_CHECK": L6MPU_LTE_Check_Measurement,
    "L6MPU_PLC_TEST": L6MPU_PLC_Test_Measurement,
    "PEAK_CAN_MESSAGE": PEAK_CAN_Message_Measurement,
    "SMCV100B_RF_OUTPUT": SMCV100B_RF_Output_Measurement,

    # PDTool4 compatibility mappings
    "MeasureSwitchON": RelayMeasurement,
    "MeasureSwitchOFF": RelayMeasurement,
    "ChassisRotateCW": ChassisRotationMeasurement,
    "ChassisRotateCCW": ChassisRotationMeasurement,
}

def get_measurement_class(test_type: str):
    """Get measurement class by test type (case-insensitive)"""
    test_type_upper = test_type.upper()
    return MEASUREMENT_REGISTRY.get(test_type_upper, DummyMeasurement)
```

## Complete Data Flow

### Test Execution Flow (API → Hardware)

```
1. Frontend calls API endpoint
   POST /api/tests/sessions/{session_id}/start

2. API router (backend/app/api/tests.py)
   → Validates session exists
   → Calls test_engine.execute_test_session()

3. TestEngine (backend/app/services/test_engine.py)
   → Loads TestPlan items for station
   → For each test item:

4. TestEngine → MeasurementService
   → Converts TestPlan SQLAlchemy model to dict
   → Calls measurement_service.execute_single_measurement()

5. MeasurementService (backend/app/services/measurement_service.py)
   → Looks up measurement class from MEASUREMENT_REGISTRY
   → Creates measurement instance:
       measurement = MeasurementClass(test_plan_item_dict, config)

6. Measurement Instance (e.g., PowerReadMeasurement)
   → Reads self.test_params from TestPlan.parameters
   → Gets instrument driver from instrument_manager
   → Calls driver methods (e.g., driver.measure_voltage())

7. Instrument Driver (e.g., MODEL2303Driver)
   → Uses connection (TCPIP/Serial/SSH)
   → Sends SCPI/custom commands to hardware
   → Returns measured value

8. Measurement validates result
   → Calls self.validate_result(measured_value)
   → Uses limit_type, value_type, lower_limit, upper_limit from TestPlan
   → Returns MeasurementResult (PASS/FAIL/ERROR)

9. TestEngine saves result to database
   → Creates TestResult record
   → Links to TestSession
   → Continues to next test item

10. API returns session status to frontend
```

### Example: Complete Flow for Voltage Check

**1. TestPlan CSV Entry:**

```csv
項次,品名規格,test_type,下限值,上限值,limit_type,value_type,parameters
5,Power Voltage,POWER_READ,11.9,12.1,both,float,{"instrument_id":"PS_001","channel":1,"measure_type":"voltage"}
```

**2. Database Record (after CSV import):**

```python
TestPlan(
    id=123,
    item_no=5,
    item_name="Power Voltage",
    test_type="POWER_READ",
    lower_limit=Decimal("11.9"),
    upper_limit=Decimal("12.1"),
    limit_type="both",
    value_type="float",
    parameters={"instrument_id": "PS_001", "channel": 1, "measure_type": "voltage"},
    unit="V"
)
```

**3. API Request:**

```bash
POST /api/tests/sessions/456/start
Authorization: Bearer eyJhbGc...
Content-Type: application/json

{
  "run_all_test": false
}
```

**4. Measurement Execution:**

```python
# MeasurementService creates instance
test_plan_dict = {
    "item_no": 5,
    "item_name": "Power Voltage",
    "test_type": "POWER_READ",
    "parameters": {"instrument_id": "PS_001", "channel": 1, "measure_type": "voltage"},
    "lower_limit": Decimal("11.9"),
    "upper_limit": Decimal("12.1"),
    "limit_type": "both",
    "value_type": "float",
    "unit": "V"
}

measurement = PowerReadMeasurement(test_plan_dict, config)

# Execute measurement
result = await measurement.execute()
# PowerReadMeasurement:
#   1. Gets instrument_id="PS_001" from test_params
#   2. Gets driver from instrument_manager
#   3. Calls driver.measure_voltage(channel=1)
#   4. Gets measured_value = 12.05
#   5. Validates: 11.9 <= 12.05 <= 12.1 → PASS
#   6. Returns MeasurementResult(result="PASS", measured_value=12.05)
```

**5. Database Result:**

```python
TestResult(
    id=789,
    session_id=456,
    test_plan_id=123,
    item_no=5,
    item_name="Power Voltage",
    result="PASS",
    measured_value=Decimal("12.05"),
    lower_limit=Decimal("11.9"),
    upper_limit=Decimal("12.1"),
    unit="V",
    execution_duration_ms=150
)
```

**6. API Response:**

```json
{
  "session_id": 456,
  "status": "RUNNING",
  "current_test_no": 5,
  "total_tests": 20,
  "results": [
    {
      "item_no": 5,
      "item_name": "Power Voltage",
      "result": "PASS",
      "measured_value": 12.05,
      "lower_limit": 11.9,
      "upper_limit": 12.1,
      "unit": "V"
    }
  ]
}
```

## API Testing Guide

### Writing Integration Tests

Tests should verify the complete integration from TestPlan → Measurement → Instrument → Validation.

**Test Structure:**

```python
import pytest
from decimal import Decimal
from app.measurements.implementations import get_measurement_class

class TestPowerReadIntegration:
    """Integration tests for PowerReadMeasurement"""

    @pytest.mark.asyncio
    async def test_power_read_voltage_within_limits(self):
        """Test voltage measurement passing validation"""
        # 1. Create TestPlan-like dictionary
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

        # 2. Get measurement class from registry
        MeasurementClass = get_measurement_class("POWER_READ")
        assert MeasurementClass is not None

        # 3. Create measurement instance
        config = {"debug": True}  # Test configuration
        measurement = MeasurementClass(test_plan_item, config)

        # 4. Verify initialization
        assert measurement.item_no == 1
        assert measurement.lower_limit == Decimal("11.9")
        assert measurement.limit_type == "both"

        # 5. Execute measurement (requires mock instrument)
        # Note: In real tests, mock instrument_manager.get_driver()
        result = await measurement.execute()

        # 6. Verify result structure
        assert hasattr(result, "result")
        assert hasattr(result, "measured_value")
        assert hasattr(result, "error_message")
        assert result.item_no == 1
        assert result.item_name == "12V Rail Check"

        # 7. Verify validation worked
        if result.result == "PASS":
            assert Decimal("11.9") <= result.measured_value <= Decimal("12.1")

    @pytest.mark.asyncio
    async def test_power_read_voltage_out_of_range(self):
        """Test voltage measurement failing validation"""
        test_plan_item = {
            "item_no": 2,
            "item_name": "5V Rail Check",
            "test_type": "POWER_READ",
            "parameters": {
                "instrument_id": "PS_002",
                "channel": 1,
                "measure_type": "voltage"
            },
            "lower_limit": Decimal("4.9"),
            "upper_limit": Decimal("5.1"),
            "limit_type": "both",
            "value_type": "float"
        }

        measurement = PowerReadMeasurement(test_plan_item, config={})

        # Mock a measurement that exceeds upper limit
        # Test validate_result directly
        passed, error = measurement.validate_result(Decimal("5.3"))

        assert not passed
        assert "Upper failed" in error or "5.3 > 5.1" in error
```

### Testing with Different Limit Types

```python
class TestLimitTypeValidation:
    """Test all 7 limit types"""

    def test_lower_limit_only(self):
        """Test lower limit validation"""
        test_plan = {
            "item_no": 1,
            "item_name": "Min Temperature",
            "lower_limit": Decimal("25.0"),
            "limit_type": "lower",
            "value_type": "float"
        }

        measurement = DummyMeasurement(test_plan, {})

        # Should pass
        passed, _ = measurement.validate_result(Decimal("30.0"))
        assert passed

        # Should fail
        passed, error = measurement.validate_result(Decimal("20.0"))
        assert not passed
        assert "Lower failed" in error

    def test_upper_limit_only(self):
        """Test upper limit validation"""
        test_plan = {
            "item_no": 2,
            "item_name": "Max Current",
            "upper_limit": Decimal("2.0"),
            "limit_type": "upper",
            "value_type": "float"
        }

        measurement = DummyMeasurement(test_plan, {})

        passed, _ = measurement.validate_result(Decimal("1.5"))
        assert passed

        passed, error = measurement.validate_result(Decimal("2.5"))
        assert not passed
        assert "Upper failed" in error

    def test_equality_limit(self):
        """Test equality validation"""
        test_plan = {
            "item_no": 3,
            "item_name": "Status Check",
            "eq_limit": "READY",
            "limit_type": "equality",
            "value_type": "string"
        }

        measurement = DummyMeasurement(test_plan, {})

        passed, _ = measurement.validate_result("READY")
        assert passed

        passed, error = measurement.validate_result("ERROR")
        assert not passed
        assert "Equality failed" in error

    def test_partial_string_match(self):
        """Test partial string validation"""
        test_plan = {
            "item_no": 4,
            "item_name": "Log Check",
            "eq_limit": "SUCCESS",
            "limit_type": "partial",
            "value_type": "string"
        }

        measurement = DummyMeasurement(test_plan, {})

        passed, _ = measurement.validate_result("Operation SUCCESS complete")
        assert passed

        passed, error = measurement.validate_result("Operation FAILED")
        assert not passed
        assert "Partial failed" in error

    def test_inequality_limit(self):
        """Test inequality validation"""
        test_plan = {
            "item_no": 5,
            "item_name": "Not Error",
            "eq_limit": "ERROR",
            "limit_type": "inequality",
            "value_type": "string"
        }

        measurement = DummyMeasurement(test_plan, {})

        passed, _ = measurement.validate_result("OK")
        assert passed

        passed, error = measurement.validate_result("ERROR")
        assert not passed
        assert "Inequality failed" in error

    def test_none_limit(self):
        """Test no limit (always passes)"""
        test_plan = {
            "item_no": 6,
            "item_name": "Info Only",
            "limit_type": "none",
            "value_type": "string"
        }

        measurement = DummyMeasurement(test_plan, {})

        # Everything passes
        assert measurement.validate_result("anything")[0]
        assert measurement.validate_result(123)[0]
        assert measurement.validate_result(None)[0]
```

### Testing Measurement Registry

```python
class TestMeasurementRegistry:
    """Test measurement registration and lookup"""

    def test_get_measurement_by_type(self):
        """Test getting measurement class by test_type"""
        from app.measurements.implementations import get_measurement_class

        # Test standard types
        assert get_measurement_class("POWER_READ") is PowerReadMeasurement
        assert get_measurement_class("RELAY") is RelayMeasurement
        assert get_measurement_class("WAIT") is WaitMeasurement

        # Test case-insensitive
        assert get_measurement_class("power_read") is PowerReadMeasurement
        assert get_measurement_class("Power_Read") is PowerReadMeasurement

        # Test PDTool4 compatibility
        assert get_measurement_class("MeasureSwitchON") is RelayMeasurement
        assert get_measurement_class("ChassisRotateCW") is ChassisRotationMeasurement

        # Test unknown type returns DummyMeasurement
        assert get_measurement_class("UNKNOWN_TYPE") is DummyMeasurement
```

### Mock-based API Testing

For full API endpoint testing without real hardware:

```python
import pytest
from unittest.mock import AsyncMock, patch
from decimal import Decimal
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestTestExecutionAPI:
    """Integration tests for test execution API"""

    @patch('app.services.instrument_manager.instrument_manager.get_driver')
    @pytest.mark.asyncio
    async def test_execute_test_session_success(self, mock_get_driver):
        """Test successful test session execution"""

        # 1. Mock instrument driver
        mock_driver = AsyncMock()
        mock_driver.measure_voltage.return_value = 12.05
        mock_get_driver.return_value = mock_driver

        # 2. Create test session (requires auth token)
        # Note: Setup test database with TestPlan records first
        session_data = {
            "serial_number": "TEST12345",
            "station_id": 1
        }

        response = client.post(
            "/api/tests/sessions",
            json=session_data,
            headers={"Authorization": f"Bearer {test_token}"}
        )

        assert response.status_code == 201
        session_id = response.json()["id"]

        # 3. Start test execution
        response = client.post(
            f"/api/tests/sessions/{session_id}/start",
            headers={"Authorization": f"Bearer {test_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["RUNNING", "COMPLETED"]

        # 4. Verify driver was called
        mock_driver.measure_voltage.assert_called()

        # 5. Get test results
        response = client.get(
            f"/api/tests/sessions/{session_id}/results",
            headers={"Authorization": f"Bearer {test_token}"}
        )

        assert response.status_code == 200
        results = response.json()
        assert len(results) > 0
        assert all(r["result"] in ["PASS", "FAIL", "ERROR", "SKIP"] for r in results)
```

## Best Practices

### 1. Parameter Design in TestPlan

Store all measurement-specific parameters in the `parameters` JSON field:

```python
# Good: Flexible parameter storage
parameters = {
    "instrument_id": "PS_001",
    "channel": 1,
    "measure_type": "voltage",
    "settling_time_ms": 100,
    "retry_count": 3
}

# Bad: Using fixed columns for dynamic data
command = "PS_001,1,voltage"  # Hard to parse, not extensible
```

### 2. Error Handling in Measurements

Always handle errors gracefully and return ERROR results:

```python
async def execute(self) -> MeasurementResult:
    try:
        # Measurement logic
        measured_value = await self._do_measurement()
        passed, error = self.validate_result(measured_value)

        return self.create_result(
            result="PASS" if passed else "FAIL",
            measured_value=measured_value,
            error_message=error
        )

    except InstrumentNotFoundError as e:
        self.logger.error(f"Instrument not found: {e}")
        return self.create_result(
            result="ERROR",
            error_message=f"Instrument not found: {str(e)}"
        )

    except TimeoutError as e:
        self.logger.error(f"Measurement timeout: {e}")
        return self.create_result(
            result="ERROR",
            error_message=f"Timeout: {str(e)}"
        )

    except Exception as e:
        self.logger.exception(f"Unexpected error: {e}")
        return self.create_result(
            result="ERROR",
            error_message=f"Unexpected error: {str(e)}"
        )
```

### 3. Test Data Setup

Use fixtures to create reusable test data:

```python
@pytest.fixture
def sample_test_plan_item():
    """Fixture providing standard test plan item"""
    return {
        "item_no": 1,
        "item_name": "Sample Test",
        "test_type": "POWER_READ",
        "parameters": {"instrument_id": "PS_001"},
        "lower_limit": Decimal("10.0"),
        "upper_limit": Decimal("15.0"),
        "limit_type": "both",
        "value_type": "float"
    }

@pytest.fixture
def measurement_config():
    """Fixture providing test configuration"""
    return {
        "debug": True,
        "timeout": 30,
        "retry_count": 3
    }

def test_with_fixtures(sample_test_plan_item, measurement_config):
    measurement = PowerReadMeasurement(sample_test_plan_item, measurement_config)
    assert measurement.item_no == 1
```

### 4. Validation Testing

Test all limit types your measurement supports:

```python
@pytest.mark.parametrize("measured_value,expected_pass", [
    (11.0, True),   # Within range
    (12.0, True),   # Within range
    (13.0, True),   # Within range
    (10.0, False),  # Below lower
    (14.0, False),  # Above upper
    (9.5, False),   # Below lower
    (14.5, False),  # Above upper
])
def test_voltage_validation(measured_value, expected_pass):
    test_plan = {
        "lower_limit": Decimal("11.0"),
        "upper_limit": Decimal("13.0"),
        "limit_type": "both",
        "value_type": "float"
    }

    measurement = PowerReadMeasurement(test_plan, {})
    passed, _ = measurement.validate_result(Decimal(str(measured_value)))
    assert passed == expected_pass
```

## Common Issues and Solutions

### Issue 1: Instrument Not Found

**Problem:** Measurement returns "No instrument found" error

**Solution:**
1. Check instrument_id exists in configuration
2. Verify instrument driver is registered in INSTRUMENT_DRIVERS
3. Ensure instrument is initialized in instrument_manager
4. Check network connectivity for TCPIP instruments

### Issue 2: Validation Always Fails

**Problem:** Measured values within limits still fail

**Solution:**
1. Check `value_type` matches data type (string/integer/float)
2. Verify `limit_type` is correct (lower/upper/both/equality/etc.)
3. Ensure decimal precision in limits matches measurement precision
4. Check for string/number type mismatches

### Issue 3: Parameter Not Found

**Problem:** Measurement can't find parameters from TestPlan

**Solution:**
```python
# Use get_param utility for flexible lookup
from app.services.instruments.base import get_param

# Tries multiple keys (case-insensitive)
channel = get_param(self.test_params, "channel", "Channel", "CHANNEL", default=1)
```

### Issue 4: Async/Await Errors

**Problem:** RuntimeError: "Event loop is closed" in tests

**Solution:**
```python
# Use pytest-asyncio
import pytest

@pytest.mark.asyncio  # Required decorator
async def test_async_measurement():
    measurement = PowerReadMeasurement(test_plan, config)
    result = await measurement.execute()  # await required
    assert result.result == "PASS"
```

## Summary

The integration between TestPlan, Measurements, and Instruments follows this pattern:

1. **TestPlan** defines WHAT to test (stored in database)
2. **BaseMeasurement** provides HOW to validate (PDTool4 compatibility)
3. **Measurement Implementation** executes the test logic
4. **Instrument Driver** communicates with hardware
5. **MeasurementService** orchestrates the flow
6. **API Endpoint** exposes functionality to frontend

For API testing:
- Create TestPlan-like dictionaries
- Use get_measurement_class() to get the right class
- Mock instrument drivers to avoid hardware dependencies
- Test all limit types your measurement supports
- Verify error handling returns ERROR results

This architecture maintains PDTool4 compatibility while providing a clean, testable, and extensible design.
