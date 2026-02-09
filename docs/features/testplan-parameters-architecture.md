# TestPlan Parameters JSON Architecture

## Overview

The `parameters` JSON field in the TestPlan model is a key design pattern that enables **flexible test configuration** without schema changes. It serves as the bridge between static test plans and dynamic measurement execution, allowing the system to support diverse instrument types and measurement methods without requiring database schema modifications.

## Field Definition

**Location:** `backend/app/models/testplan.py:23`

```python
parameters = Column(JSON, nullable=True)
```

### Purpose and Significance

| Aspect | Description |
|--------|-------------|
| **Flexibility** | Store test-specific parameters without schema changes |
| **Compatibility** | PDTool4 CSV compatibility with multiple parameter formats |
| **Extensibility** | Add new instruments/tests without database migrations |
| **Validation** | Separated configuration in `MEASUREMENT_TEMPLATES` |

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     TestPlan Model                          │
│  parameters JSON: {"Instrument": "DAQ973A_1", "Channel": 101}│
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│           Measurement API (measurements.py)                  │
│  POST /execute → MeasurementRequest.test_params             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│       MEASUREMENT_TEMPLATES (instruments.py)                 │
│  Definiert Parameterstrukturen: required, optional, example  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│    Measurement Implementations (implementations.py)          │
│  BaseMeasurement subclasses → get_param() helper             │
└─────────────────────────────────────────────────────────────┘
```

## Module Relationships

| Layer | File | Role |
|-------|------|------|
| **Data** | `testplan.py:23` | `parameters` JSON column storage |
| **Config** | `instruments.py:44-130` | `MEASUREMENT_TEMPLATES` defines parameter structure |
| **API** | `measurements.py:25-31` | `test_params` request model |
| **Execution** | `implementations.py:22-27` | `get_param()` reads parameters |
| **Constants** | `measurement_constants.py` | Parameter name mappings |

## Complete Data Flow

```
┌──────────────────┐
│   CSV Import     │
│  (CSV Parser)    │
└────────┬─────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│  TestPlan.parameters = JSON Column       │
│  {"Instrument": "DAQ973A_1", ...}        │
└────────┬─────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│  MeasurementService.execute_measurement() │
│  → test_params = TestPlan.parameters      │
└────────┬─────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│  BaseMeasurement.__init__()              │
│  → self.test_params = test_params        │
└────────┬─────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│  Concrete Measurement.execute()          │
│  → get_param(test_params, "Instrument")   │
│  → driver.measure_voltage(...)           │
└──────────────────────────────────────────┘
```

## Detailed Examples

### Example 1: PowerRead - Voltage Measurement

**Step 1: TestPlan Storage**
```json
{
    "id": 1,
    "item_name": "Output Voltage Check",
    "test_type": "PowerRead",
    "switch_mode": "DAQ973A",
    "parameters": {
        "Instrument": "DAQ973A_1",
        "Channel": "101",
        "Item": "volt",
        "Type": "DC"
    },
    "lower_limit": 4.8,
    "upper_limit": 5.2
}
```

**Step 2: API Request (measurements.py)**
```python
class MeasurementRequest(BaseModel):
    measurement_type: str  # "PowerRead"
    test_point_id: str
    switch_mode: str      # "DAQ973A"
    test_params: Dict[str, Any]  # ← From TestPlan.parameters
```

**Step 3: Parameter Validation (instruments.py)**
```python
"PowerRead": {
    "DAQ973A": {
        "required": ["Instrument", "Channel", "Item", "Type"],
        "optional": ["Range", "NPLC"],
        "example": {
            "Instrument": "daq973a_1",
            "Channel": "101",
            "Item": "volt",
            "Type": "DC"
        }
    }
}
```

**Step 4: Execution (implementations.py)**
```python
class PowerReadMeasurement(BaseMeasurement):
    async def execute(self) -> MeasurementResult:
        # Extract parameters using get_param() helper
        instrument_name = get_param(self.test_params, "Instrument", "instrument")
        channel = get_param(self.test_params, "Channel", "channel")
        item = get_param(self.test_params, "Item", "item")

        # Execute actual measurement
        measured_value = await driver.measure_voltage(channels)

        # Validate result
        is_valid, error_msg = self.validate_result(measured_value)
```

### Example 2: PowerSet - Power Supply Configuration

**TestPlan parameters:**
```json
{
    "Instrument": "MODEL2306_1",
    "Channel": "1",
    "SetVolt": "5.0",
    "SetCurr": "2.0"
}
```

**Execution Flow (implementations.py:513-601):**
```python
class PowerSetMeasurement(BaseMeasurement):
    async def execute(self) -> MeasurementResult:
        # Read parameters (support multiple naming variants)
        voltage = get_param(self.test_params, "SetVolt", "Voltage", "voltage")
        current = get_param(self.test_params, "SetCurr", "Current", "current")
        channel = get_param(self.test_params, "Channel", "channel")

        # Execute configuration
        result = await driver.execute_command({
            'Channel': channel_str,
            'SetVolt': voltage_val,
            'SetCurr': current_val
        })
```

### Example 3: CommandTest - Serial Communication

**TestPlan parameters:**
```json
{
    "Port": "COM4",
    "Baud": "9600",
    "Command": "AT+VERSION",
    "keyWord": "VERSION",
    "spiltCount": "1",
    "splitLength": "10"
}
```

**Parameter Structure (instruments.py:106-128):**
```python
"CommandTest": {
    "comport": {
        "required": ["Port", "Baud", "Command"],
        "optional": ["keyWord", "spiltCount", "splitLength", "EqLimit"],
        "example": {...}
    }
}
```

### Example 4: RF_Tool_LTE_TX - RF Measurement

**TestPlan parameters:**
```json
{
    "instrument": "RF_Tool_1",
    "band": "B3",
    "channel": "1700",
    "bandwidth": 10.0
}
```

**Execution (implementations.py:926-1020):**
```python
class RF_Tool_LTE_TX_Measurement(BaseMeasurement):
    async def execute(self) -> MeasurementResult:
        band = get_param(self.test_params, 'band')
        channel = int(get_param(self.test_params, 'channel'))
        bandwidth = float(get_param(self.test_params, 'bandwidth'))

        # Call MT8872A driver
        tx_result = await driver.measure_lte_tx_power(band, channel, bandwidth)
        measured_power = tx_result['tx_power_avg']
```

## Key Design Patterns

### get_param() Helper Function

**Location:** `implementations.py:22-27`

```python
def get_param(params: Dict[str, Any], *keys: str, default=None):
    """Support parameter name variants for compatibility"""
    for key in keys:
        if key in params and params[key] not in (None, ""):
            return params[key]
    return default

# Usage example:
voltage = get_param(self.test_params, "SetVolt", "Voltage", "voltage")
# Tries SetVolt → Voltage → voltage in order
```

**Benefits:**
1. **Multi-variant Support:** Tries multiple parameter names
2. **PDTool4 Compatibility:** Supports different naming conventions
3. **Default Values:** Provides fallback options
4. **Null Safety:** Handles None and empty string cases

### JSON Parameters vs Fixed Fields

**Use JSON `parameters` for:**
- Test-type specific parameters (Instrument, Channel, SetVolt)
- Optional parameters (Range, NPLC, OVP)
- Different types with different parameter sets

**Use fixed database columns for:**
```python
# testplan.py:24-27 - Common to ALL test types
lower_limit = Column(DECIMAL(15, 6), nullable=True)
upper_limit = Column(DECIMAL(15, 6), nullable=True)
unit = Column(String(20), nullable=True)
enabled = Column(Boolean, default=True)
```

These fields are **common to all test types**, so they're designed as fixed columns.

## Parameter Validation Mechanism

### Step 1: Define Parameter Structure

```python
# instruments.py - MEASUREMENT_TEMPLATES
"PowerRead": {
    "DAQ973A": {
        "required": ["Instrument", "Channel", "Item", "Type"],
        "optional": ["Range", "NPLC"],
        "example": {
            "Instrument": "daq973a_1",
            "Channel": "101",
            "Item": "volt",
            "Type": "DC"
        }
    }
}
```

### Step 2: Validation API

```python
# measurements.py - POST /validate-params
async def validate_measurement_params(
    measurement_type: str,
    switch_mode: str,
    test_params: Dict[str, Any]
):
    validation_result = await measurement_service.validate_params(
        measurement_type="PowerRead",
        switch_mode="DAQ973A",
        test_params=test_params
    )

    return {
        "valid": validation_result["valid"],
        "missing_params": ["Instrument", "Channel"],  # Missing parameters
        "invalid_params": ["WrongParam"],  # Invalid parameters
        "suggestions": ["Parameter 'Channel' example: '101'"]
    }
```

### Step 3: Runtime Validation (instruments.py:229-286)

```python
def validate_params(
    measurement_type: str,
    switch_mode: str,
    params: Dict[str, Any]
) -> Dict[str, Any]:
    """Validate measurement parameters against template"""

    template = get_template(measurement_type, switch_mode)

    # Check required parameters
    required = template.get("required", [])
    missing = [param for param in required if param not in params]

    # Check for unknown parameters
    optional = template.get("optional", [])
    valid_params = set(required + optional)
    invalid = [param for param in params.keys() if param not in valid_params]

    return {
        "valid": len(missing) == 0,
        "missing_params": missing,
        "invalid_params": invalid,
        "suggestions": suggestions
    }
```

## Complete Execution Flow

```
┌─────────────────────────────────────────────────────────────┐
│  1. CSV Import / Frontend UI                               │
│     → Create test plan with JSON parameters                  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  2. Test Model (test_plans table)                           │
│     parameters = '{"Instrument": "DAQ973A_1", ...}'        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  3. TestEngine.execute_test_session()                       │
│     → Read TestPlan, parse parameters JSON                  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  4. MeasurementService.execute_measurement()                │
│     → Select Measurement class by test_type + switch_mode   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  5. Concrete Measurement (implementations.py)               │
│     → get_param() extracts JSON parameters                  │
│     → Call Instrument Driver for measurement                │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  6. Instrument Driver (services/instruments/)               │
│     → Connect via VISA/Serial/TCP                           │
│     → Execute SCPI commands or vendor protocols             │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  7. validate_result()                                       │
│     → Compare measured_value with lower/upper_limit         │
│     → Return PASS/FAIL + error_message                      │
└─────────────────────────────────────────────────────────────┘
```

## Design Advantages

`★ Insight ─────────────────────────────────────`
**Three Key Advantages of JSON Parameters:**
1. **Schema-less Extension:** Add new instruments by updating MEASUREMENT_TEMPLATES only
2. **Validation Separation:** MEASUREMENT_TEMPLATES defines required/optional parameters
3. **Readability:** JSON format is easy to debug and manually edit, PDTool4 CSV compatible
`─────────────────────────────────────────────────`

### Summary Table

| Layer | Responsibility | JSON Usage |
|-------|----------------|------------|
| **Database** | TestPlan.parameters | `JSON` column stores raw parameters |
| **Config** | MEASUREMENT_TEMPLATES | Defines parameter structure and examples |
| **API** | MeasurementRequest | `test_params: Dict[str, Any]` |
| **Execution** | get_param() | `get_param(params, "Key1", "key1")` |
| **Validation** | validate_params() | Checks required parameter completeness |

## Common Measurement Types

| Test Type | Required Parameters | Example |
|-----------|---------------------|---------|
| **PowerRead** | Instrument, Channel, Item, Type | `{"Instrument": "DAQ973A_1", "Channel": "101", "Item": "volt", "Type": "DC"}` |
| **PowerSet** | Instrument, SetVolt, SetCurr | `{"Instrument": "MODEL2306_1", "SetVolt": "5.0", "SetCurr": "2.0"}` |
| **CommandTest** | Port, Baud, Command | `{"Port": "COM4", "Baud": "9600", "Command": "AT+VERSION"}` |
| **RF_Tool_LTE_TX** | instrument, band, channel | `{"instrument": "RF_Tool_1", "band": "B3", "channel": 1700}` |
| **CMW100_BLE** | instrument, connector, frequency | `{"instrument": "CMW100_1", "connector": 1, "frequency": 2440.0}` |

## Related Documentation

- [Measurement Implementation](./measurement-implementations.md) - How measurements use parameters
- [Configuration Architecture](./configuration-architecture.md) - Settings and configuration management
- [Instrument Configuration](../development/instrument-config.md) - Instrument driver setup

## Summary

The TestPlan `parameters` JSON field implements a flexible, extensible architecture for instrument measurement configuration:

1. **Separation of Concerns**
   - Configuration logic in `instruments.py`
   - Business logic in `implementations.py`
   - Storage in `testplan.py`

2. **Flexibility**
   - Add new instruments without database changes
   - Support multiple parameter formats
   - Easy to extend and maintain

3. **Validation**
   - Template-based parameter validation
   - Required vs optional parameters
   - Automatic error checking

4. **Compatibility**
   - PDTool4 CSV format support
   - Multi-variant parameter naming
   - Backward compatible design

This architecture enables the system to dynamically scale to support new instrument types and measurement methods without requiring database schema modifications, achieving high flexibility and maintainability.
