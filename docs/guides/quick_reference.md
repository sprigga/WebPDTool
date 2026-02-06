# WebPDTool Quick Reference

## Core Integration Pattern

```
TestPlan (Database)
    ↓
BaseMeasurement (Validation Logic)
    ↓
Measurement Implementation (Test Logic)
    ↓
Instrument Driver (Hardware Control)
    ↓
MeasurementResult (PASS/FAIL/ERROR)
```

## TestPlan to Measurement Mapping

### TestPlan Fields

```python
TestPlan(
    item_no=1,                          # Test sequence number
    item_name="Voltage Check",          # Test description
    test_type="POWER_READ",             # → MEASUREMENT_REGISTRY lookup

    # Parameters (JSON) - Read by measurement
    parameters={
        "instrument_id": "PS_001",
        "channel": 1,
        "measure_type": "voltage"
    },

    # Validation criteria - Used by BaseMeasurement.validate_result()
    lower_limit=11.9,
    upper_limit=12.1,
    limit_type="both",                  # 7 types: lower/upper/both/equality/partial/inequality/none
    value_type="float",                 # 3 types: string/integer/float
    eq_limit="PASS",                    # For equality/partial/inequality types

    unit="V"
)
```

### Measurement Instance Creation

```python
# MeasurementService automatically converts TestPlan → dict
test_plan_dict = {
    "item_no": plan.item_no,
    "item_name": plan.item_name,
    "test_type": plan.test_type,
    "parameters": plan.parameters,      # Accessed via self.test_params
    "lower_limit": plan.lower_limit,    # Accessed via self.lower_limit
    "upper_limit": plan.upper_limit,    # Accessed via self.upper_limit
    "limit_type": plan.limit_type,      # Accessed via self.limit_type
    "value_type": plan.value_type,      # Accessed via self.value_type
    "unit": plan.unit
}

# Get measurement class from registry
MeasurementClass = get_measurement_class(plan.test_type)

# Create instance
measurement = MeasurementClass(test_plan_dict, config)
```

## Available Measurements

| test_type | Class | Purpose | Instruments |
|-----------|-------|---------|-------------|
| DUMMY | DummyMeasurement | Testing only | None |
| POWER_READ | PowerReadMeasurement | Read V/I from PSU | MODEL2303, IT6723C, PSW3072, etc. |
| POWER_SET | PowerSetMeasurement | Set PSU output | Same as POWER_READ |
| WAIT | WaitMeasurement | Delay execution | None |
| RELAY | RelayMeasurement | Control relay | DUT relay hardware |
| CHASSIS_ROTATION | ChassisRotationMeasurement | Rotate chassis | DUT chassis motor |
| COMMAND_TEST | CommandTestMeasurement | Execute commands | console/comport/tcpip/adb |
| RF_TOOL_LTE_TX | RF_Tool_LTE_TX_Measurement | LTE TX test | RF_Tool.exe + instruments |
| RF_TOOL_LTE_RX | RF_Tool_LTE_RX_Measurement | LTE RX test | RF_Tool.exe + instruments |
| CMW100_BLE | CMW100_BLE_Measurement | Bluetooth test | CMW100 |
| CMW100_WIFI | CMW100_WiFi_Measurement | WiFi test | CMW100 |
| L6MPU_LTE_CHECK | L6MPU_LTE_Check_Measurement | LTE module check | L6MPU (SSH) |
| L6MPU_PLC_TEST | L6MPU_PLC_Test_Measurement | PLC test | L6MPU (SSH) |
| PEAK_CAN_MESSAGE | PEAK_CAN_Message_Measurement | CAN bus test | PEAK CAN |
| SMCV100B_RF_OUTPUT | SMCV100B_RF_Output_Measurement | RF output test | SMCV100B |

### PDTool4 Compatibility Aliases

| PDTool4 test_type | Maps to | Measurement Class |
|-------------------|---------|-------------------|
| MeasureSwitchON | RELAY | RelayMeasurement |
| MeasureSwitchOFF | RELAY | RelayMeasurement |
| ChassisRotateCW | CHASSIS_ROTATION | ChassisRotationMeasurement |
| ChassisRotateCCW | CHASSIS_ROTATION | ChassisRotationMeasurement |

## Validation Logic (7 Limit Types)

### 1. none - No validation (always passes)
```python
test_plan = {
    "limit_type": "none",
    "value_type": "string"
}
# Any value passes
```

### 2. lower - Lower limit check (value >= lower)
```python
test_plan = {
    "lower_limit": 10.0,
    "limit_type": "lower",
    "value_type": "float"
}
# Pass: 10.0, 10.5, 100.0
# Fail: 9.9, 5.0
```

### 3. upper - Upper limit check (value <= upper)
```python
test_plan = {
    "upper_limit": 100.0,
    "limit_type": "upper",
    "value_type": "float"
}
# Pass: 50.0, 100.0
# Fail: 100.1, 200.0
```

### 4. both - Range check (lower <= value <= upper)
```python
test_plan = {
    "lower_limit": 10.0,
    "upper_limit": 20.0,
    "limit_type": "both",
    "value_type": "float"
}
# Pass: 10.0, 15.0, 20.0
# Fail: 9.9, 20.1
```

### 5. equality - Exact match (value == eq_limit)
```python
test_plan = {
    "eq_limit": "PASS",
    "limit_type": "equality",
    "value_type": "string"
}
# Pass: "PASS"
# Fail: "FAIL", "pass"
```

### 6. partial - Substring match (eq_limit in value)
```python
test_plan = {
    "eq_limit": "SUCCESS",
    "limit_type": "partial",
    "value_type": "string"
}
# Pass: "Operation SUCCESS", "SUCCESS: OK"
# Fail: "FAILED", "Error"
```

### 7. inequality - Not equal (value != eq_limit)
```python
test_plan = {
    "eq_limit": "ERROR",
    "limit_type": "inequality",
    "value_type": "string"
}
# Pass: "OK", "PASS"
# Fail: "ERROR"
```

## Measurement Implementation Pattern

```python
from app.measurements.base import BaseMeasurement, MeasurementResult
from decimal import Decimal
import time

class MyMeasurement(BaseMeasurement):
    """Custom measurement implementation"""

    async def execute(self) -> MeasurementResult:
        start_time = time.time()

        try:
            # 1. Extract parameters from self.test_params (TestPlan.parameters)
            param1 = self.test_params.get("param1")
            param2 = self.test_params.get("param2", "default_value")

            # 2. Get instrument driver if needed
            from app.services.instrument_manager import instrument_manager
            driver = await instrument_manager.get_driver(instrument_id)

            # 3. Perform measurement
            measured_value = await driver.some_measurement_method()

            # 4. Validate result (uses self.lower_limit, self.upper_limit, self.limit_type)
            passed, error_msg = self.validate_result(measured_value)

            # 5. Calculate execution time
            duration_ms = int((time.time() - start_time) * 1000)

            # 6. Return result
            return self.create_result(
                result="PASS" if passed else "FAIL",
                measured_value=Decimal(str(measured_value)),
                error_message=error_msg,
                execution_duration_ms=duration_ms
            )

        except Exception as e:
            self.logger.error(f"Measurement failed: {e}")
            return self.create_result(
                result="ERROR",
                error_message=str(e)
            )
```

## Instrument Driver Pattern

```python
from app.services.instruments.base import BaseInstrumentDriver
from decimal import Decimal

class MyInstrumentDriver(BaseInstrumentDriver):
    """Custom instrument driver"""

    async def initialize(self):
        """Initialize instrument to known state"""
        await self.write_command("*RST")
        await self.write_command("*CLS")

    async def reset(self):
        """Reset to default state"""
        await self.write_command("*RST")

    async def measure_voltage(self, channel: int) -> Decimal:
        """Measure voltage on specific channel"""
        command = f"MEAS:VOLT? (@{channel})"
        return await self.query_decimal(command)

    async def set_output_state(self, channel: int, state: bool):
        """Enable/disable output"""
        state_str = "ON" if state else "OFF"
        await self.write_command(f"OUTP{channel}:STAT {state_str}")
```

## API Test Execution Flow

```
1. POST /api/tests/sessions
   → Create TestSession(serial_number, station_id)
   → Returns session_id

2. POST /api/tests/sessions/{session_id}/start
   → TestEngine.execute_test_session()
   → Load TestPlan items for station
   → For each TestPlan:
       a. Convert to dict
       b. Get measurement class from registry
       c. Create measurement instance
       d. Execute measurement.execute()
       e. Save TestResult to database
   → Return session status

3. GET /api/tests/sessions/{session_id}/status
   → Check current execution status
   → Returns current_test_no, total_tests, status

4. GET /api/tests/sessions/{session_id}/results
   → Retrieve all TestResult records
   → Returns list of results with PASS/FAIL/ERROR
```

## Testing Pattern

### Unit Test (Measurement)
```python
@pytest.mark.asyncio
async def test_measurement_validation():
    test_plan = {
        "item_no": 1,
        "item_name": "Test",
        "test_type": "POWER_READ",
        "parameters": {"instrument_id": "PS_001"},
        "lower_limit": Decimal("10.0"),
        "upper_limit": Decimal("20.0"),
        "limit_type": "both",
        "value_type": "float"
    }

    measurement = PowerReadMeasurement(test_plan, {})

    # Test validation
    passed, _ = measurement.validate_result(15.0)
    assert passed is True

    passed, _ = measurement.validate_result(25.0)
    assert passed is False
```

### Integration Test (with Mock)
```python
@pytest.mark.asyncio
@patch('app.services.instrument_manager.instrument_manager.get_driver')
async def test_measurement_execution(mock_get_driver):
    # Mock driver
    mock_driver = AsyncMock()
    mock_driver.measure_voltage.return_value = 12.0
    mock_get_driver.return_value = mock_driver

    # Execute measurement
    measurement = PowerReadMeasurement(test_plan, {})
    result = await measurement.execute()

    # Verify
    assert result.result == "PASS"
    assert result.measured_value == Decimal("12.0")
    mock_driver.measure_voltage.assert_called_once()
```

### API Test (End-to-End)
```python
def test_complete_session(client, test_token):
    # Create session
    response = client.post(
        "/api/tests/sessions",
        json={"serial_number": "TEST123", "station_id": 1},
        headers={"Authorization": f"Bearer {test_token}"}
    )
    session_id = response.json()["id"]

    # Start execution
    response = client.post(
        f"/api/tests/sessions/{session_id}/start",
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 200

    # Get results
    response = client.get(
        f"/api/tests/sessions/{session_id}/results",
        headers={"Authorization": f"Bearer {test_token}"}
    )
    results = response.json()
    assert len(results) > 0
```

## Common Parameter Patterns

### Power Measurements
```json
{
  "instrument_id": "PS_001",
  "channel": 1,
  "measure_type": "voltage",  // or "current"
  "settling_time_ms": 100
}
```

### Relay Control
```json
{
  "relay_state": "ON",  // ON=OPEN, OFF=CLOSED
  "channel": 1
}
```

### Chassis Rotation
```json
{
  "direction": "CW",  // or "CCW"
  "duration_ms": 100
}
```

### Command Test
```json
{
  "command": "echo test",
  "case_type": "console",  // console/comport/tcpip/android_adb
  "timeout": 5000
}
```

### RF Measurements
```json
{
  "instrument_id": "CMW_001",
  "frequency_mhz": 2450,
  "power_dbm": 10,
  "bandwidth": 20
}
```

## Error Detection

Measurements automatically detect instrument errors:

```python
# Returns (False, "No instrument found")
measured_value = "No instrument found"

# Returns (False, "Instrument error: Connection timeout")
measured_value = "Error: Connection timeout"
```

## Registry Lookup

```python
from app.measurements.implementations import get_measurement_class

# Get measurement class
MeasurementClass = get_measurement_class("POWER_READ")

# Case-insensitive
MeasurementClass = get_measurement_class("power_read")

# PDTool4 compatibility
MeasurementClass = get_measurement_class("MeasureSwitchON")  # → RelayMeasurement

# Unknown types fall back to DummyMeasurement
MeasurementClass = get_measurement_class("UNKNOWN")  # → DummyMeasurement
```

## Key Files Reference

| Component | File Path |
|-----------|-----------|
| TestPlan Model | `backend/app/models/testplan.py` |
| BaseMeasurement | `backend/app/measurements/base.py` |
| Measurements | `backend/app/measurements/implementations.py` |
| BaseInstrumentDriver | `backend/app/services/instruments/base.py` |
| Instrument Drivers | `backend/app/services/instruments/*.py` |
| MeasurementService | `backend/app/services/measurement_service.py` |
| TestEngine | `backend/app/services/test_engine.py` |
| Test API | `backend/app/api/tests.py` |

## Further Reading

- **[Measurement TestPlan Integration Guide](./measurement_testplan_integration.md)** - Comprehensive integration details
- **[API Testing Examples](./api_testing_examples.md)** - Complete test examples
- **[CLAUDE.md](../../CLAUDE.md)** - Project overview and architecture
