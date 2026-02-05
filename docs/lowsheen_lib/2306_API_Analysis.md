# 2306 Dual-Channel Power Supply Driver API Analysis

## Overview

The `2306_test.py` module provides control and measurement capabilities for the Keithley 2306 dual-channel battery simulator/power supply. Unlike the 2260B and 2303 single-channel drivers, this driver supports independent control of two output channels.

**Model**: Keithley 2306 Dual-Channel Battery/Charger Simulator
**Communication Protocol**: SCPI (Standard Commands for Programmable Instruments)
**Connection Type**: VISA (via remote_instrument module)
**Key Feature**: Dual-channel operation with independent voltage/current control

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
Parse Arguments (sequence, args dict, channels)
    ↓
Initialize Instrument Connection
    ↓
Mode Selection: --final OR normal
    ↓
Execute: initial() OR send_cmd_to_instrument()
    ↓
Channel-Specific Commands (CH1 or CH2)
    ↓
Return Result/Status
```

### Channel Support

**Channel 1**: Independent voltage/current control via `SOUR:` commands
**Channel 2**: Independent voltage/current control via `SOUR2:` commands

Both channels can be controlled simultaneously or independently within the same test sequence.

---

## API Functions

### 1. `get_cmd_string(channels, SetVolt, SetCurr)`

Generates channel-specific SCPI command strings for voltage/current control and measurement.

**Parameters:**
- `channels` (str): Channel selector - '1' or '2'
- `SetVolt` (str): Target voltage in volts
- `SetCurr` (str): Target current limit in amperes

**Returns:**
- Tuple of 4 strings: `(remote_Voltcmd, remote_Currcmd, check_Voltcmd, check_Currcmd)`

**Channel 1 Command Mapping:**

| Purpose | SCPI Command | Description |
|---------|-------------|-------------|
| Set Voltage | `SOUR:VOLT {value}` | Sets channel 1 output voltage |
| Set Current Limit | `SOUR:CURR:LIM {value}` | Sets channel 1 current limit |
| Query Voltage | `MEAS:VOLT?` | Measures channel 1 voltage |
| Query Current | `MEAS:CURR?` | Measures channel 1 current |

**Channel 2 Command Mapping:**

| Purpose | SCPI Command | Description |
|---------|-------------|-------------|
| Set Voltage | `SOUR2:VOLT {value}` | Sets channel 2 output voltage |
| Set Current Limit | `SOUR2:CURR:LIM {value}` | Sets channel 2 current limit |
| Query Voltage | `MEAS2:VOLT?` | Measures channel 2 voltage |
| Query Current | `MEAS2:CURR?` | Measures channel 2 current |

**Key Differences from Single-Channel Drivers:**
- Commands include `:CURR:LIM` instead of just `:CURR` for current limiting
- Channel 2 uses `SOUR2:` and `MEAS2:` prefixes
- No verification query implementation (commented out)

**Example:**
```python
# Channel 1
cmds_ch1 = get_cmd_string('1', '3.3', '1.0')
# Returns: ('SOUR:VOLT 3.3', 'SOUR:CURR:LIM 1.0', 'MEAS:VOLT?', 'MEAS:CURR?')

# Channel 2
cmds_ch2 = get_cmd_string('2', '5.0', '2.0')
# Returns: ('SOUR2:VOLT 5.0', 'SOUR2:CURR:LIM 2.0', 'MEAS2:VOLT?', 'MEAS2:CURR?')
```

---

### 2. `send_cmd_to_instrument(instrument, channels, SetVolt, SetCurr)`

Executes channel-specific voltage/current control with special handling for output disable.

**Parameters:**
- `instrument` (VISA Resource): Initialized instrument connection object
- `channels` (str): Channel selector - '1' or '2'
- `SetVolt` (str): Target voltage in volts
- `SetCurr` (str): Target current limit in amperes

**Returns:**
- `1` (int): Success (always returns 1 in current implementation)
- Error string (str): Describes which parameter(s) failed verification (disabled in current version)

**Execution Sequence:**

**Case 1: Disable Output (SetVolt='0' AND SetCurr='0')**
```python
if SetVolt == '0' and SetCurr == '0':
    if channels == '1':
        instrument.write("OUTP OFF\n")
    if channels == '2':
        instrument.write("OUTP2 OFF\n")
```

**Case 2: Normal Operation (Any other values)**
```python
instrument.write(str(remote_Voltcmd))        # Set voltage
instrument.write(str(remote_Currcmd))        # Set current limit
if channels == '1':
    instrument.write("OUTP ON")              # Enable channel 1
if channels == '2':
    instrument.write("OUTP2 ON")             # Enable channel 2
```

**Verification Status:**
- Verification code is **commented out** in current implementation (lines 41-49)
- Always returns `1` (success)
- No closed-loop verification performed

**Example:**
```python
# Enable channel 1 at 3.3V/1A
result = send_cmd_to_instrument(inst, '1', '3.3', '1.0')
# Returns: 1 (always succeeds)

# Disable channel 2
result = send_cmd_to_instrument(inst, '2', '0', '0')
# Returns: 1 (channel 2 disabled)
```

---

### 3. `initial(instrument)`

Safely disables both channels for shutdown/cleanup operations.

**Parameters:**
- `instrument` (VISA Resource): Initialized instrument connection object

**Returns:**
- None (implicitly returns None)

**Operation:**
```python
instrument.write("OUTP OFF\n")   # Disable channel 1
instrument.write("OUTP2 OFF\n")  # Disable channel 2
```

**Usage Context:**
- Called when `--final` flag is passed
- Disables **both channels** regardless of which channel was in use
- Ensures safe shutdown state

**Example:**
```python
initial(inst)  # Turns off both power supply channels
```

---

## Command-Line Interface

### Usage

```bash
# Normal operation - set voltage and current on specific channel
python 2306_test.py <sequence> "<args_dict>"

# Disable specific channel (SetVolt=0, SetCurr=0)
python 2306_test.py <sequence> "<args_dict with 0,0>"

# Cleanup mode - turn off both channels
python 2306_test.py --final "<args_dict>"
```

### Arguments

**Positional Arguments:**

1. **sequence** (str): Operation mode
   - `--final`: Cleanup mode (disable both channels)
   - Any other value: Normal operation mode

2. **args** (str): JSON-formatted dictionary string containing:
   - `Instrument` (str): Instrument identifier (e.g., 'MODEL2306_1')
   - `Channel` (str): Channel selector - '1' or '2'
   - `SetVolt` (str): Target voltage in volts
   - `SetCurr` (str): Target current limit in amperes

### Examples

**Example 1: Enable Channel 1 at 3.3V @ 1.5A**
```bash
python 2306_test.py normal "{'Instrument': 'MODEL2306_1', 'Channel': '1', 'SetVolt': '3.3', 'SetCurr': '1.5'}"
```

**Example 2: Enable Channel 2 at 5V @ 2A**
```bash
python 2306_test.py normal "{'Instrument': 'MODEL2306_1', 'Channel': '2', 'SetVolt': '5', 'SetCurr': '2'}"
```

**Example 3: Disable Channel 1**
```bash
python 2306_test.py test "{'Instrument': 'MODEL2306_1', 'Channel': '1', 'SetVolt': '0', 'SetCurr': '0'}"
```

**Example 4: Cleanup/Shutdown (Both Channels)**
```bash
python 2306_test.py --final "{'Instrument': 'MODEL2306_1'}"
```

**Example 5: From sys.argv comment (line 66)**
```bash
python 2306_test.py 2306_on "{'ValueType': 'string', 'LimitType': 'partial', 'EqLimit': 'MODEL2306', 'ExecuteName': 'PowerSet', 'case': 'MODEL2306', 'Instrument': 'model2306_1', 'Channel': '1', 'SetVolt': '0', 'SetCurr': '0'}"
```

---

## Exit Codes

| Exit Code | Condition | Description |
|-----------|-----------|-------------|
| 0 | Success | Operation completed successfully |
| 10 | Connection Failure | Instrument initialization failed (instrument is None) |

---

## SCPI Command Reference

### Channel 1 Control

**Set Voltage:**
```
SOUR:VOLT {value}
```

**Set Current Limit:**
```
SOUR:CURR:LIM {value}
```

**Query Voltage:**
```
MEAS:VOLT?
```

**Query Current:**
```
MEAS:CURR?
```

**Output Control:**
```
OUTP ON
OUTP OFF
```

### Channel 2 Control

**Set Voltage:**
```
SOUR2:VOLT {value}
```

**Set Current Limit:**
```
SOUR2:CURR:LIM {value}
```

**Query Voltage:**
```
MEAS2:VOLT?
```

**Query Current:**
```
MEAS2:CURR?
```

**Output Control:**
```
OUTP2 ON
OUTP2 OFF
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

**Note:** In current implementation, `get_cmd_string()` always returns non-None values for channels '1' or '2'.

### Verification Errors

**Current Status:** Verification is **disabled** (commented out)

**Commented Verification Code (lines 41-49):**
```python
# response_Volt = round(float(instrument.query(str(check_Voltcmd))), 2)
# response_Curr = round(float(instrument.query(str(check_Currcmd))), 2)

# if response_Volt != float(SetVolt):
#     print("response_Volt: "+str(response_Volt))
#     errors.append('VOLT')
# if response_Curr != float(SetCurr):
#     print("response_Curr: "+str(response_Curr))
#     errors.append('CURR')
```

**Error Message Format (if enabled):**
```python
f"2306 channel {channels} set {' and '.join(errors)} fail"
```

**Implications:**
- No closed-loop verification performed
- Assumes commands execute successfully
- Faster execution but no validation

---

## Integration with PDTool4

### Calling Convention

PDTool4's measurement modules invoke this driver as a subprocess:

```python
import subprocess

# Example: Configure channel 1
args_dict = {
    'Instrument': 'MODEL2306_1',
    'Channel': '1',
    'SetVolt': '5.0',
    'SetCurr': '2.0'
}

result = subprocess.run(
    ['python', 'src/lowsheen_lib/2306_test.py', '2306_on', str(args_dict)],
    capture_output=True,
    text=True
)

status = result.stdout.strip()
if status == '1':
    print("Channel 1 configured successfully")

# Example: Disable channel 2
args_dict_off = {
    'Instrument': 'MODEL2306_1',
    'Channel': '2',
    'SetVolt': '0',
    'SetCurr': '0'
}

subprocess.run(
    ['python', 'src/lowsheen_lib/2306_test.py', '2306_off', str(args_dict_off)]
)

# Cleanup both channels
subprocess.run(
    ['python', 'src/lowsheen_lib/2306_test.py', '--final', str(args_dict)]
)
```

### Test Plan CSV Configuration

In test plan CSV files, the 2306 is referenced with channel specification:

```csv
Item No,Item Name,Lower Limit,Upper Limit,Instrument Location,Execute Name,Case,Channel,SetVolt,SetCurr
1,Channel 1 Setup,,,MODEL2306_1,PowerSet,2306,1,3.3,1.0
2,Channel 2 Setup,,,MODEL2306_1,PowerSet,2306,2,5.0,2.0
```

---

## Technical Specifications

### Supported Commands

| Category | Channel 1 Command | Channel 2 Command | Purpose |
|----------|------------------|-------------------|---------|
| Voltage | `SOUR:VOLT <value>` | `SOUR2:VOLT <value>` | Set voltage |
| Current Limit | `SOUR:CURR:LIM <value>` | `SOUR2:CURR:LIM <value>` | Set current limit |
| Voltage Query | `MEAS:VOLT?` | `MEAS2:VOLT?` | Measure voltage |
| Current Query | `MEAS:CURR?` | `MEAS2:CURR?` | Measure current |
| Output Enable | `OUTP ON` | `OUTP2 ON` | Enable output |
| Output Disable | `OUTP OFF` | `OUTP2 OFF` | Disable output |

### Communication Protocol

- **Interface**: VISA (Virtual Instrument Software Architecture)
- **Transport**: Typically GPIB, USB, or Ethernet (handled by VISA layer)
- **Command Format**: SCPI (Standard Commands for Programmable Instruments)
- **Termination**: Commands are terminated with newline (`\n`)

### Measurement Precision

- **Verification**: Disabled in current implementation
- **Rounding**: Would be 2 decimal places (if enabled)
- **Tolerance**: No tolerance applied

---

## Code Comparison: 2306 vs Single-Channel Drivers

| Aspect | 2306_test.py | 2303/2260B |
|--------|-------------|------------|
| Channel Support | Dual (1, 2) | Single |
| Voltage Command | `SOUR:VOLT` / `SOUR2:VOLT` | `VOLT` |
| Current Command | `SOUR:CURR:LIM` / `SOUR2:CURR:LIM` | `CURR` |
| Measurement Query | `MEAS:VOLT?` / `MEAS2:VOLT?` | `MEAS:VOLT:DC?` |
| Verification | Disabled (commented) | Active |
| Zero Detection | SetVolt='0' AND SetCurr='0' → Disable | No special handling |
| Cleanup | Disables both channels | Disables single output |

---

## Special Features

### 1. Zero-Value Output Disable

The driver treats `SetVolt='0'` AND `SetCurr='0'` as a special case for output disable:

```python
if SetVolt == '0' and SetCurr == '0':
    # Disable output instead of setting 0V/0A
    if channels == '1':
        instrument.write("OUTP OFF\n")
    if channels == '2':
        instrument.write("OUTP2 OFF\n")
```

**Rationale:**
- Explicit output disable vs. setting 0V/0A
- More deterministic behavior
- Matches user intent in test plans

### 2. Independent Channel Control

Each channel can be controlled independently within the same test sequence:

```python
# Enable channel 1 at 3.3V
send_cmd_to_instrument(inst, '1', '3.3', '1.0')

# Enable channel 2 at 5V (channel 1 remains active)
send_cmd_to_instrument(inst, '2', '5.0', '2.0')

# Disable only channel 1 (channel 2 remains active)
send_cmd_to_instrument(inst, '1', '0', '0')
```

### 3. Batch Cleanup

The `initial()` function disables **both channels** regardless of which was in use:

```python
def initial(instrument):
    instrument.write("OUTP OFF\n")   # Channel 1
    instrument.write("OUTP2 OFF\n")  # Channel 2
```

This ensures complete cleanup without tracking channel states.

---

## Limitations and Considerations

1. **No Verification**: Measurement queries are commented out, providing no feedback on actual output values.

2. **String Comparison for Zero**: Uses string comparison (`SetVolt == '0'`) instead of numeric comparison, which could fail with '0.0' or other formats.

3. **No Channel Validation**: No check if `channels` is '1' or '2' - invalid values silently fail to set commands.

4. **No Settling Time**: No delay between setting and enabling output.

5. **Both Channels Disabled in Cleanup**: `initial()` disables both channels, which may be undesirable if only one channel was in use.

6. **Subprocess Overhead**: Each invocation creates a new instrument connection.

---

## Best Practices

1. **Channel Specification**: Always explicitly specify channel in arguments
2. **Cleanup Operations**: Use `--final` flag after test sequences to disable both channels
3. **Zero Values**: Use '0' and '0' for both SetVolt and SetCurr to disable output
4. **Argument Formatting**: Use string values for all numeric parameters
5. **Error Handling**: Current implementation always returns 1, so check exit codes instead
6. **Independent Operations**: Multiple subprocess calls can control channels independently

---

## Testing Strategy

### Sequential Channel Testing

```bash
# Test sequence for dual-channel device
python 2306_test.py test "{'Instrument': 'MODEL2306_1', 'Channel': '1', 'SetVolt': '3.3', 'SetCurr': '1.0'}"
# Wait or perform measurement
python 2306_test.py test "{'Instrument': 'MODEL2306_1', 'Channel': '2', 'SetVolt': '5.0', 'SetCurr': '2.0'}"
# Wait or perform measurement
python 2306_test.py --final "{'Instrument': 'MODEL2306_1'}"
```

### Channel Isolation Testing

```bash
# Test channel 1 only
python 2306_test.py test "{'Instrument': 'MODEL2306_1', 'Channel': '1', 'SetVolt': '3.3', 'SetCurr': '1.0'}"
python 2306_test.py test "{'Instrument': 'MODEL2306_1', 'Channel': '1', 'SetVolt': '0', 'SetCurr': '0'}"
```

---

## Debugging

### Commented Debug Code

The original code contains commented debugging (line 81):
```python
# print(SetVolt, SetCurr)
```

And conditional debug prints (lines 85, 88):
```python
# print('85 elif')
# print('88 else')
```

These can be uncommented for troubleshooting execution flow.

### Example Invocation in Comments

Line 66 shows an example `sys.argv` structure for testing:
```python
# sys.argv = ['2306_test.py', '2306_on', "{'ValueType': 'string', 'LimitType': 'partial', 'EqLimit': 'MODEL2306', 'ExecuteName': 'PowerSet', 'case': 'MODEL2306', 'Instrument': 'model2306_1', 'Channel': '1', 'SetVolt': '0', 'SetCurr': '0'}"]
```

This can be uncommented for unit testing without command-line invocation.

---

## Future Enhancement Suggestions

1. **Re-enable Verification**:
   ```python
   response_Volt = round(float(instrument.query(str(check_Voltcmd))), 2)
   response_Curr = round(float(instrument.query(str(check_Currcmd))), 2)

   if abs(response_Volt - float(SetVolt)) > 0.1:  # 100mV tolerance
       errors.append('VOLT')
   ```

2. **Channel Validation**:
   ```python
   def get_cmd_string(channels, SetVolt, SetCurr):
       if channels not in ['1', '2']:
           raise ValueError(f"Invalid channel: {channels}. Must be '1' or '2'")
       # ... rest of function
   ```

3. **Numeric Zero Comparison**:
   ```python
   if float(SetVolt) == 0.0 and float(SetCurr) == 0.0:
       # Disable output
   ```

4. **Selective Cleanup**:
   ```python
   def initial(instrument, channels=None):
       """Disable specific channel or all channels if channels is None"""
       if channels is None or channels == '1':
           instrument.write("OUTP OFF\n")
       if channels is None or channels == '2':
           instrument.write("OUTP2 OFF\n")
   ```

5. **State Tracking**:
   ```python
   # Persist channel states to avoid redundant commands
   channel_states = {'1': False, '2': False}
   ```

---

## Related Drivers

- **2260B.py**: Single-channel power supply with active verification
- **2303_test.py**: Single-channel power supply with identical command structure
- Both use simpler command syntax (`VOLT` vs `SOUR:VOLT`)

---

## Troubleshooting

### Problem: Channel doesn't turn on

**Possible Causes:**
1. Invalid channel specification (not '1' or '2')
2. Instrument in error state
3. Over-current/over-voltage protection triggered

**Solutions:**
- Verify channel parameter is string '1' or '2'
- Send `*CLS` (clear status) command before operations
- Check instrument front panel for error indicators
- Query instrument errors: `SYST:ERR?`

### Problem: Cannot disable specific channel

**Current Limitation:** Using `--final` disables both channels.

**Workaround:** Use normal mode with SetVolt='0' and SetCurr='0':
```bash
python 2306_test.py test "{'Instrument': 'MODEL2306_1', 'Channel': '1', 'SetVolt': '0', 'SetCurr': '0'}"
```

### Problem: No verification feedback

**Current Status:** Verification is intentionally disabled (commented out).

**Options:**
1. Uncomment verification code (lines 41-49)
2. Perform external measurement verification
3. Use instrument front panel to verify settings

### Problem: Unexpected behavior with '0.0' values

**Issue:** String comparison `SetVolt == '0'` doesn't match '0.0' or '0.00'

**Solution:** Normalize to single zero format in test plans, or modify code to use numeric comparison:
```python
if float(SetVolt) == 0.0 and float(SetCurr) == 0.0:
```

---

## Keithley 2306 Instrument Overview

### Key Features

- **Dual Independent Channels**: Each channel can source or sink current
- **Battery Simulation**: Can simulate battery discharge profiles
- **Programmable Current Limit**: Protects DUT from overcurrent
- **Precision Measurement**: Simultaneously source and measure

### Typical Applications

1. **Battery-Powered Device Testing**: Simulate battery under various load conditions
2. **Dual-Voltage Systems**: Power 3.3V and 5V circuits simultaneously
3. **Current Profiling**: Measure device current consumption dynamically
4. **Charger Testing**: Test battery charger behavior

### Physical Specifications (Typical)

- **Channel 1 Voltage Range**: 0-15V
- **Channel 1 Current Range**: 0-5A
- **Channel 2 Voltage Range**: 0-15V
- **Channel 2 Current Range**: 0-5A
- **Interfaces**: GPIB, USB, RS-232 (model-dependent)

---

## References

- Keithley 2306 Battery/Charger Simulator User Manual
- SCPI Command Reference for Keithley 2300 Series
- PDTool4 Test Execution Framework Documentation
- Python VISA Documentation: https://pyvisa.readthedocs.io/
