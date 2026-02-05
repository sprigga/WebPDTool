# 2303 Power Supply Driver API Analysis

## Overview

The `2303_test.py` module provides control and measurement capabilities for the Keithley 2303 power supply. This driver uses simplified SCPI commands compared to the 2260B model, offering straightforward voltage/current control with closed-loop verification.

**Model**: Keithley 2303 (likely MODEL2303 or similar variant)
**Communication Protocol**: SCPI (Standard Commands for Programmable Instruments)
**Connection Type**: VISA (via remote_instrument module)

---

## Module Dependencies

```python
from remote_instrument import instrument_iniSetting
import sys
import ast
```

- **remote_instrument**: Provides instrument initialization and VISA communication wrapper
- **sys**: Command-line argument parsing
- **ast**: Safe evaluation of string-formatted dictionaries

---

## Architecture

### Execution Flow

```
Command Line Invocation
    ↓
Parse Arguments (sequence, args dict)
    ↓
Initialize Instrument Connection
    ↓
Mode Selection: --final OR normal
    ↓
Execute: initial() OR send_cmd_to_instrument()
    ↓
Return Result/Status
```

### Mode Support

1. **Normal Operation Mode**: Set voltage/current and verify settings
2. **Cleanup Mode (`--final`)**: Turn off output for safe shutdown

---

## API Functions

### 1. `get_cmd_string(SetVolt, SetCurr)`

Generates SCPI command strings for voltage/current control and measurement.

**Parameters:**
- `SetVolt` (str): Target voltage in volts
- `SetCurr` (str): Target current in amperes

**Returns:**
- Tuple of 4 strings: `(remote_Voltcmd, remote_Currcmd, check_Voltcmd, check_Currcmd)`

**Command Mapping:**

| Purpose | SCPI Command | Description |
|---------|-------------|-------------|
| Set Voltage | `VOLT {value}` | Sets output voltage level |
| Set Current | `CURR {value}` | Sets current limit |
| Query Voltage | `MEAS:VOLT:DC?` | Measures actual output voltage |
| Query Current | `MEAS:CURR:DC?` | Measures actual output current |

**Differences from 2260B:**
- Uses identical command structure (simplified subset of SCPI)
- No optional parameters or qualifiers in commands

**Example:**
```python
cmds = get_cmd_string('5.0', '1.0')
# Returns: ('VOLT 5.0', 'CURR 1.0', 'MEAS:VOLT:DC?', 'MEAS:CURR:DC?')
```

---

### 2. `send_cmd_to_instrument(instrument, SetVolt, SetCurr)`

Executes the full sequence of setting and verifying voltage/current parameters.

**Parameters:**
- `instrument` (VISA Resource): Initialized instrument connection object
- `SetVolt` (str): Target voltage in volts
- `SetCurr` (str): Target current in amperes

**Returns:**
- `1` (int): Success - all parameters set correctly
- Error string (str): Describes which parameter(s) failed verification

**Execution Sequence:**

1. **Generate Commands**: Calls `get_cmd_string()`
2. **Command Validation**: Checks if commands are not None
3. **Write Voltage Setting**: `instrument.write("VOLT {value}")`
4. **Write Current Setting**: `instrument.write("CURR {value}")`
5. **Enable Output**: `instrument.write("OUTP ON")`
6. **Query Voltage**: Read back actual voltage with `MEAS:VOLT:DC?`
7. **Query Current**: Read back actual current with `MEAS:CURR:DC?`
8. **Verification**: Compare measured values with target values (rounded to 2 decimal places)
9. **Error Collection**: Build error list if any parameter mismatches

**Error Messages:**
- `"Error : remote command is wrong"` - Invalid command generation
- `"2303 set volt fail"` - Voltage verification failed
- `"2303 set curr fail"` - Current verification failed
- `"2303 set volt and curr fail"` - Both parameters failed verification

**Example:**
```python
result = send_cmd_to_instrument(inst, '12.0', '2.0')
# Returns: 1 (success)
# OR: "2303 set volt and curr fail" (if both mismatch)
```

---

### 3. `initial(instrument)`

Safely disables the power supply output for shutdown/cleanup operations.

**Parameters:**
- `instrument` (VISA Resource): Initialized instrument connection object

**Returns:**
- None (implicitly returns None)

**Operation:**
- Sends `OUTP OFF\n` command to disable output

**Usage Context:**
- Called when `--final` flag is passed
- Used for safe shutdown or test sequence cleanup

**Example:**
```python
initial(inst)  # Turns off power supply output
```

---

## Command-Line Interface

### Usage

```bash
# Normal operation - set voltage and current
python 2303_test.py <sequence> "<args_dict>"

# Cleanup mode - turn off output
python 2303_test.py --final "<args_dict>"
```

### Arguments

**Positional Arguments:**

1. **sequence** (str): Operation mode
   - `--final`: Cleanup mode (disable output)
   - Any other value: Normal operation mode

2. **args** (str): JSON-formatted dictionary string containing:
   - `Instrument` (str): Instrument identifier (e.g., 'MODEL2303_1')
   - `SetVolt` (str): Target voltage in volts
   - `SetCurr` (str): Target current in amperes

### Examples

**Example 1: Set 5V @ 3A**
```bash
python 2303_test.py normal "{'Instrument': 'MODEL2303_1', 'SetVolt': '5', 'SetCurr': '3'}"
```

**Example 2: Cleanup/Shutdown**
```bash
python 2303_test.py --final "{'Instrument': 'MODEL2303_1'}"
```

**Example 3: Low Power Setting**
```bash
python 2303_test.py test "{'Instrument': 'MODEL2303_1', 'SetVolt': '3.3', 'SetCurr': '0.5'}"
```

---

## Exit Codes

| Exit Code | Condition | Description |
|-----------|-----------|-------------|
| 0 | Success | Operation completed successfully |
| 10 | Connection Failure | Instrument initialization failed (instrument is None) |

---

## SCPI Command Reference

### Voltage Control

**Set Voltage:**
```
VOLT {value}
```

**Query Voltage:**
```
MEAS:VOLT:DC?
```

**Parameters:**
- `{value}`: Voltage in volts (instrument-dependent range)

### Current Control

**Set Current Limit:**
```
CURR {value}
```

**Query Current:**
```
MEAS:CURR:DC?
```

**Parameters:**
- `{value}`: Current in amperes (instrument-dependent range)

### Output Control

**Enable Output:**
```
OUTP ON
```

**Disable Output:**
```
OUTP OFF
```

---

## Error Handling

### Connection Errors

```python
instrument = instrument_iniSetting(Instrument_value)
if instrument is None:
    sys.exit(10)  # Exit with code 10 for connection failure
```

### Command Validation

```python
if remote_Voltcmd is None or remote_Currcmd is None:
    return "Error : remote command is wrong"
```

**Note:** In current implementation, `get_cmd_string()` always returns non-None values, making this check defensive but not actively triggered.

### Verification Errors

The driver performs **closed-loop verification** by comparing measured values with set values:

```python
response_Volt = round(float(instrument.query("MEAS:VOLT:DC?")), 2)
response_Curr = round(float(instrument.query("MEAS:CURR:DC?")), 2)

errors = []
if response_Volt != float(SetVolt):
    errors.append('volt')
if response_Curr != float(SetCurr):
    errors.append('curr')

if not errors:
    return 1
else:
    return f"2303 set {' and '.join(errors)} fail"
```

**Precision:** Values are rounded to 2 decimal places for comparison

---

## Integration with PDTool4

### Calling Convention

PDTool4's measurement modules (e.g., `PowerSetMeasurement.py`) invoke this driver as a subprocess:

```python
import subprocess

args_dict = {
    'Instrument': 'MODEL2303_1',
    'SetVolt': '5',
    'SetCurr': '3'
}

# Normal operation
result = subprocess.run(
    ['python', 'src/lowsheen_lib/2303_test.py', 'normal', str(args_dict)],
    capture_output=True,
    text=True
)

status = result.stdout.strip()
if status == '1':
    print("Power supply configured successfully")
else:
    print(f"Error: {status}")

# Cleanup at end of test
subprocess.run(
    ['python', 'src/lowsheen_lib/2303_test.py', '--final', str(args_dict)]
)
```

### Test Plan CSV Configuration

In test plan CSV files, the 2303 is referenced in the "Instrument Location" column:

```csv
Item No,Item Name,Lower Limit,Upper Limit,Instrument Location,Execute Name,Case,SetVolt,SetCurr
1,Power Supply Setup,,,MODEL2303_1,PowerSet,2303,5,3
```

---

## Technical Specifications

### Supported Commands

| Category | Command | Query | Purpose |
|----------|---------|-------|---------|
| Voltage | `VOLT <value>` | `MEAS:VOLT:DC?` | Set/measure voltage |
| Current | `CURR <value>` | `MEAS:CURR:DC?` | Set/measure current |
| Output | `OUTP ON/OFF` | - | Enable/disable output |

### Communication Protocol

- **Interface**: VISA (Virtual Instrument Software Architecture)
- **Transport**: Typically GPIB, USB, or Ethernet (handled by VISA layer)
- **Command Format**: SCPI (Standard Commands for Programmable Instruments)
- **Termination**: Commands are terminated with newline (`\n`)

### Measurement Precision

- **Voltage/Current Rounding**: 2 decimal places
- **Comparison Method**: Exact match after rounding
- **Tolerance**: No tolerance applied (exact comparison)

---

## Code Comparison: 2303 vs 2260B

| Aspect | 2303_test.py | 2260B.py |
|--------|-------------|----------|
| Command Syntax | `VOLT {value}` | `VOLT {value}` |
| Measurement Query | `MEAS:VOLT:DC?` | `MEAS:VOLT:DC?` |
| Verification Logic | Identical | Identical |
| Error Messages | Model-specific ("2303 set...") | Model-specific ("2260B set...") |
| Channel Support | Single channel | Single channel |
| Code Structure | Identical | Identical |

**Key Insight:** The 2303 driver is functionally identical to the 2260B driver, differing only in:
1. File name and error message branding
2. Potential instrument-specific voltage/current ranges (not enforced in code)

This suggests both instruments use the same SCPI command subset, simplifying maintenance and testing.

---

## Limitations and Considerations

1. **No Tolerance**: Verification uses exact equality after rounding, which may cause false failures with instruments that have slight measurement drift.

2. **No Settling Time**: No explicit delay between setting and measurement. Assumes fast instrument response.

3. **Error Recovery**: No automatic retry mechanism for failed verifications.

4. **Single Channel**: The 2303 is a single-channel power supply (unlike the 2306 dual-channel model).

5. **Subprocess Overhead**: Each invocation creates a new instrument connection, adding latency but ensuring isolation.

6. **Command Validation**: The `if remote_Voltcmd is None` check is defensive but never triggered in current implementation.

---

## Best Practices

1. **Instrument Initialization**: Always verify instrument connection before operations
2. **Cleanup Operations**: Use `--final` flag after test sequences to disable output
3. **Argument Formatting**: Ensure dictionary strings use single quotes around keys and values
4. **Error Handling**: Check return values - `1` for success, descriptive strings for failures
5. **Connection Management**: Allow sufficient time between rapid invocations for instrument reset
6. **Testing Without Hardware**: Use instrument simulators or mock objects for development

---

## Testing Without Hardware

For development without physical instruments:

```python
# Example test harness
class MockInstrument:
    def __init__(self):
        self.voltage = 0
        self.current = 0
        self.output = False

    def write(self, cmd):
        if 'VOLT' in cmd:
            self.voltage = float(cmd.split()[1])
        elif 'CURR' in cmd:
            self.current = float(cmd.split()[1])
        elif 'OUTP ON' in cmd:
            self.output = True
        elif 'OUTP OFF' in cmd:
            self.output = False

    def query(self, cmd):
        if 'MEAS:VOLT' in cmd:
            return str(self.voltage)
        elif 'MEAS:CURR' in cmd:
            return str(self.current)

# Test the driver logic
mock_inst = MockInstrument()
result = send_cmd_to_instrument(mock_inst, '5.0', '2.0')
assert result == 1
```

---

## Related Drivers

- **2260B.py**: Functionally identical API for Keithley 2260B model
- **2306_test.py**: Dual-channel variant for Keithley 2306 (supports channel selection)

---

## Troubleshooting

### Problem: "2303 set volt fail" or "2303 set curr fail"

**Possible Causes:**
1. Instrument not fully settled after setting
2. Rounding mismatch (e.g., 5.005V set, 5.01V measured)
3. Instrument calibration drift
4. Current compliance limiting voltage output

**Solutions:**
- Add settling delay between setting and measurement
- Implement tolerance-based comparison instead of exact equality
- Check instrument calibration
- Verify current limit is sufficient for load

### Problem: Exit code 10 (connection failure)

**Possible Causes:**
1. Instrument not powered on
2. VISA address incorrect in instrument configuration
3. VISA driver not installed
4. Instrument busy with another connection

**Solutions:**
- Verify instrument power and VISA address
- Check VISA resource manager: `python -m pyvisa info`
- Ensure no other software is connected to instrument
- Review `remote_instrument.py` configuration

### Problem: "Error : remote command is wrong"

**Possible Causes:**
- This error is defensive and shouldn't occur in normal operation
- Possible modification of `get_cmd_string()` returning None

**Solutions:**
- Review recent code changes to `get_cmd_string()`
- Ensure function returns 4-tuple of strings

---

## Future Enhancement Suggestions

1. **Tolerance-Based Verification**:
   ```python
   TOLERANCE = 0.05  # 5% tolerance
   if abs(response_Volt - float(SetVolt)) / float(SetVolt) > TOLERANCE:
       errors.append('volt')
   ```

2. **Settling Time**:
   ```python
   import time
   instrument.write("OUTP ON")
   time.sleep(0.5)  # 500ms settling time
   response_Volt = float(instrument.query("MEAS:VOLT:DC?"))
   ```

3. **Retry Logic**:
   ```python
   MAX_RETRIES = 3
   for attempt in range(MAX_RETRIES):
       if verify_settings():
           return 1
       time.sleep(0.2)
   return "2303 set volt and curr fail after retries"
   ```

4. **Range Validation**:
   ```python
   MAX_VOLTAGE = 15.0
   MAX_CURRENT = 5.0
   if float(SetVolt) > MAX_VOLTAGE:
       return f"Error: Voltage {SetVolt}V exceeds maximum {MAX_VOLTAGE}V"
   ```

---

## References

- Keithley 2303 Power Supply User Manual
- SCPI Command Reference for Programmable Power Supplies
- PDTool4 Test Execution Framework Documentation
- Python VISA Documentation: https://pyvisa.readthedocs.io/
