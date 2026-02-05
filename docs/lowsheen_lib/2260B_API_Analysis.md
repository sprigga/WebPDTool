# 2260B Power Supply Driver API Analysis

## Overview

The `2260B.py` module provides control and measurement capabilities for the Keithley 2260B DC power supply. This driver implements SCPI command-based communication for setting voltage/current parameters and verifying the output values.

**Model**: Keithley 2260B Series Programmable DC Power Supply
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

**Example:**
```python
cmds = get_cmd_string('12.5', '2.0')
# Returns: ('VOLT 12.5', 'CURR 2.0', 'MEAS:VOLT:DC?', 'MEAS:CURR:DC?')
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
- `"2260B set volt fail"` - Voltage verification failed
- `"2260B set curr fail"` - Current verification failed
- `"2260B set volt and curr fail"` - Both parameters failed verification

**Example:**
```python
result = send_cmd_to_instrument(inst, '5.0', '1.5')
# Returns: 1 (success)
# OR: "2260B set volt fail" (if voltage mismatch)
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
python 2260B.py <sequence> "<args_dict>"

# Cleanup mode - turn off output
python 2260B.py --final "<args_dict>"
```

### Arguments

**Positional Arguments:**

1. **sequence** (str): Operation mode
   - `--final`: Cleanup mode (disable output)
   - Any other value: Normal operation mode

2. **args** (str): JSON-formatted dictionary string containing:
   - `Instrument` (str): Instrument identifier (e.g., 'MODEL2260B_1')
   - `SetVolt` (str): Target voltage in volts
   - `SetCurr` (str): Target current in amperes

### Examples

**Example 1: Set 12V @ 3A**
```bash
python 2260B.py normal "{'Instrument': 'MODEL2260B_1', 'SetVolt': '12', 'SetCurr': '3'}"
```

**Example 2: Cleanup/Shutdown**
```bash
python 2260B.py --final "{'Instrument': 'MODEL2260B_1'}"
```

**Example 3: Precision Setting**
```bash
python 2260B.py test "{'Instrument': 'MODEL2260B_1', 'SetVolt': '5.25', 'SetCurr': '0.5'}"
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

**Command Format:**
```
[SOURce:]VOLTage[:LEVel][:IMMediate][:AMPLitude] {<NRf>|MIN|MAX}
```

**Simplified Usage in Driver:**
```
VOLT {value}
```

**Parameters:**
- `<NRf>`: 0 to 105% of rated output voltage in volts
- `MIN`: Minimum voltage level
- `MAX`: Maximum voltage level

**Query:**
```
[SOURce:]VOLTage[:LEVel][:IMMediate][:AMPLitude]? [MIN|MAX]
```

**Measurement Query:**
```
MEAS:VOLT:DC?
```

### Current Control

**Set Current Limit:**
```
CURR {value}
```

**Measurement Query:**
```
MEAS:CURR:DC?
```

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

### Verification Errors

The driver performs **closed-loop verification** by comparing measured values with set values:

```python
response_Volt = round(float(instrument.query("MEAS:VOLT:DC?")), 2)
response_Curr = round(float(instrument.query("MEAS:CURR:DC?")), 2)

if response_Volt != float(SetVolt):
    errors.append('volt')
if response_Curr != float(SetCurr):
    errors.append('curr')
```

**Precision:** Values are rounded to 2 decimal places for comparison

---

## Integration with PDTool4

### Calling Convention

PDTool4's measurement modules (e.g., `PowerSetMeasurement.py`) invoke this driver as a subprocess:

```python
import subprocess

args_dict = {
    'Instrument': 'MODEL2260B_1',
    'SetVolt': '12',
    'SetCurr': '3'
}

# Normal operation
result = subprocess.run(
    ['python', 'src/lowsheen_lib/2260B.py', 'normal', str(args_dict)],
    capture_output=True,
    text=True
)
print(result.stdout)  # "1" on success, error message on failure

# Cleanup
subprocess.run(
    ['python', 'src/lowsheen_lib/2260B.py', '--final', str(args_dict)]
)
```

### Test Plan CSV Configuration

In test plan CSV files, the 2260B is referenced in the "Instrument Location" column:

```csv
Item No,Item Name,Lower Limit,Upper Limit,Instrument Location,Execute Name,Case,Channel,SetVolt,SetCurr
1,Power Supply Setup,,,MODEL2260B_1,PowerSet,2260B,,12,3
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

## Limitations and Considerations

1. **No Tolerance**: The verification uses exact equality after rounding, which may cause false failures with instruments that have slight measurement drift.

2. **Synchronization**: No explicit delay between setting and measurement, assuming the instrument settles quickly.

3. **Error Recovery**: No automatic retry mechanism for failed verifications.

4. **Single Channel**: The 2260B is a single-channel power supply (unlike the 2306 dual-channel model).

5. **Subprocess Execution**: Each invocation creates a new instrument connection, which adds overhead but ensures isolation.

---

## Best Practices

1. **Instrument Initialization**: Always verify instrument connection before operations
2. **Cleanup Operations**: Use `--final` flag after test sequences to disable output
3. **Argument Formatting**: Ensure dictionary strings use single quotes around keys and values
4. **Error Handling**: Check return values for error strings
5. **Connection Management**: Allow sufficient time between rapid invocations for instrument reset

---

## Related Drivers

- **2303_test.py**: Similar API for Keithley 2303 (single channel, simplified commands)
- **2306_test.py**: Dual-channel variant for Keithley 2306 (supports channel selection)

---

## References

- Keithley 2260B Series Programmable DC Power Supply User Manual
- SCPI Command Reference for Programmable Power Supplies
- PDTool4 Test Execution Framework Documentation
