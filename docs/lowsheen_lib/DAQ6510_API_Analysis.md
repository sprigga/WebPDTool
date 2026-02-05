# DAQ6510 API Analysis

## Overview

`DAQ6510.py` provides a command-line interface for controlling Keysight DAQ6510 Data Acquisition Systems. It supports relay switching (OPEN/CLOSE) and multi-function measurements (voltage, current, resistance, temperature, etc.) through SCPI commands. This is a variant of the DAQ973A driver with stricter channel validation and different relay verification logic.

**Location:** `src/lowsheen_lib/DAQ6510.py`

**Supported Instrument:** Keysight DAQ6510 (6.5-Digit Graphical Sampling Multimeter)

**Primary Use Cases:**
- Switch relay channels for signal routing with strict channel validation
- Measure DC/AC voltage and current
- Measure resistance, frequency, capacitance, temperature
- Diode testing and 4-wire resistance measurements

---

## Core Functions

### `check_channel_list(cmd, channels)`

Validates and formats channel numbers based on the measurement type with **strict validation**.

**Parameters:**
- `cmd` (str): Command type ('CURR', 'VOLT', 'OPEN', 'CLOS', etc.)
- `channels` (str): Channel specification (e.g., '101', '(101, 102)')

**Returns:**
- `list`: Validated channel numbers as strings
- `None`: If validation fails

**Validation Rules:**

**1. Current Measurements (`CURR`):**
- Only channels ending with '21' or '22' are allowed
- Example valid: '121', '222', '321', '122'
- Example invalid: '101', '115', '125'
- Reason: DAQ6510 current measurement channels are in positions 21-22

**2. Other Commands:**
- Channels must end with '01' through '25'
- Example valid: '101', '215', '325'
- Example invalid: '126', '130', '100'
- Enforced range: 01-25 per slot

**Validation Code:**
```python
if cmd == 'CURR':
    # Only channels 21-22
    if i[-2:] == '21' or i[-2:] == '22':
        channel_check.append(i)
    else:
        print("Error : channel input is wrong! (21/22)")
        return None
else:
    # Channels 01-25
    if i[-2:] in [str(num).zfill(2) for num in range(1, 26)]:
        channel_check.append(i)
    else:
        print("Error : channel input is wrong! (01~25)")
        return None
```

**Example:**
```python
check_channel_list('CURR', '121')    # ✓ Returns: ['121']
check_channel_list('CURR', '101')    # ✗ Error, returns None
check_channel_list('VOLT', '101')    # ✓ Returns: ['101']
check_channel_list('VOLT', '126')    # ✗ Error, returns None
```

### `get_cmd_string(cmd, channels, type_=None)`

Generates SCPI command strings for the DAQ6510 based on the operation type.

**Parameters:**
- `cmd` (str): Command type (see function_mapping)
- `channels` (str): Channel specification
- `type_` (str, optional):
  - For VOLT/CURR: 'AC' or 'DC'
  - For other measurements: 'DEF' (default) or specific type

**Returns:**
- **Relay Commands (OPEN/CLOS):** Tuple of (remote_cmd, check_cmd)
- **Measurement Commands:** Single command string
- `None`: If validation fails

**Command Generation Examples:**

**1. Relay Control:**
```python
get_cmd_string('OPEN', '101')
# Returns: ('ROUT:OPEN (@101)', 'ROUT:CLOS?')

get_cmd_string('CLOS', '(101,102)')
# Returns: ('ROUT:CLOS (@101,102)', 'ROUT:CLOS?')
```

**Key Difference from DAQ973A:**
- DAQ6510 uses fixed `'ROUT:CLOS?'` for verification (doesn't include channel list)
- DAQ973A uses `'ROUT:CLOS? (@channels)'` (channel-specific query)

**2. Voltage/Current Measurement:**
```python
get_cmd_string('VOLT', '101', 'DC')
# Returns: 'MEAS:VOLT:DC? (@101)'

get_cmd_string('CURR', '121', 'AC')
# Returns: 'MEAS:CURR:AC? (@121)'
```

**3. Other Measurements:**
```python
get_cmd_string('TEMP', '101')
# Returns: 'MEAS:TEMP? (@101)'

get_cmd_string('FRES', '102')
# Returns: 'MEAS:FRES? (@102)'
```

### `send_cmd_to_instrument(instrument, cmd, channels, type_)`

Executes the command on the DAQ6510 and returns the result.

**Parameters:**
- `instrument`: PyVISA instrument object (from `instrument_iniSetting()`)
- `cmd` (str): Command type from function_mapping
- `channels` (str): Channel specification
- `type_` (str): Measurement type (AC/DC/DEF)

**Returns:**
- **Relay Commands:** '0' (success) or '1' (failure)
- **Measurements:** Formatted numeric result (3 decimal places)
- `None`: On error

**Execution Flow:**

**1. Relay Control with Status Verification (OPEN/CLOS):**
```python
# 1. Generate command
remote_cmd, check_cmd = get_cmd_string('CLOS', '101')

# 2. Write command to instrument
instrument.write('ROUT:CLOS (@101)')

# 3. Query closed channel list
response_index = instrument.query('ROUT:CLOS?')
# Response: '(@101,102,103)' - All currently closed channels

# 4. Verify success with logic
if cmd == 'OPEN':
    success = channels not in response_index
elif cmd == 'CLOS':
    success = channels in response_index
response = '0' if success else '1'
```

**Verification Logic:**
```python
response = '0' if (
    (channels in response_index and cmd == 'OPEN') or      # FAIL: channel still closed
    (channels not in response_index and cmd == 'CLOS')     # FAIL: channel not closed
) else '1'
```

**Key Difference from DAQ973A:**
- DAQ6510: Returns '0'/'1' status (success/fail)
- DAQ973A: Returns raw SCPI response string

**2. Measurement (Non-Temperature):**
```python
remote_cmd = get_cmd_string('VOLT', '101', 'DC')
response = instrument.query('MEAS:VOLT:DC? (@101)')
formatted = '{:.3f}'.format(float(response))
# Response: '+1.23456E+00' -> '1.235'
```

**3. Temperature Measurement:**
```python
# Temperature requires warm-up query
instrument.query('MEAS:TEMP? (@101)')  # Initial query (discard)
time.sleep(2)  # Wait for sensor stabilization
response = instrument.query('MEAS:TEMP? (@101)')  # Actual reading
formatted = '{:.3f}'.format(float(response))
# Response: '+2.345E+01' -> '23.450'
```

**Special Handling:**
- **Temperature (`TEMP`):** Two queries with 2-second delay (sensor stabilization)
- **Relay Commands:** Binary success/failure return ('0'/'1')
- **Result Formatting:** `'{:.3f}'.format(float(response))` (3 decimal precision)

### `initial(instrument)`

Resets the DAQ6510 to factory default state.

**Parameters:**
- `instrument`: PyVISA instrument object

**Returns:**
- None

**Behavior:**
- Sends `*RST\n` SCPI command
- Clears all settings, opens all relays
- Used during `--final` sequence (cleanup)

---

## Supported Commands

### `function_mapping` Dictionary

```python
function_mapping = {
    'OPEN', 'CLOS',                    # Relay control
    'DIOD', 'CAP', 'FREQ', 'PER',     # Digital measurements
    'FRES', 'RES', 'TEMP',            # Resistance & temperature
    'CURR', 'VOLT',                    # Current & voltage
}
```

**Command Reference:**

| Command | Description | Type Required | Channel Restriction | Notes |
|---------|-------------|---------------|---------------------|-------|
| `OPEN` | Open relay channels | - | 01-25 (not CURR) | Returns '0'/'1' |
| `CLOS` | Close relay channels | - | 01-25 (not CURR) | Returns '0'/'1' |
| `VOLT` | Voltage measurement | AC/DC | 01-25 | 3 decimal result |
| `CURR` | Current measurement | AC/DC | 21-22 only | 3 decimal result |
| `RES` | 2-wire resistance | - | 01-25 | Default type |
| `FRES` | 4-wire resistance | - | 01-25 | High precision |
| `TEMP` | Temperature | - | 01-25 | 2-query + 2s delay |
| `FREQ` | Frequency | - | 01-25 | AC signals |
| `PER` | Period | - | 01-25 | AC signals |
| `CAP` | Capacitance | - | 01-25 | Capacitor test |
| `DIOD` | Diode test | - | 01-25 | Forward voltage |

---

## Command-Line Interface

### Usage

```bash
python DAQ6510.py <sequence> <args_dict>
```

**Arguments:**
- `sequence` (str):
  - `'--final'`: Initialize/reset instrument
  - Any other value: Execute measurement
- `args_dict` (str): JSON-like dictionary containing:

**Required Keys:**
- `Instrument` (str): Instrument identifier (e.g., 'DAQ6510_1')
- `Item` (str): Command type (from function_mapping)

**Optional Keys:**
- `Channel` (str): Channel specification (default: '')
- `Type` (str): Measurement type (AC/DC/DEF)
- `sequence` (str): Alternative way to specify '--final'

### Examples

**1. Close Relay:**
```bash
python DAQ6510.py test "{'Instrument': 'DAQ6510_1', 'Item': 'CLOS', 'Channel': '101'}"
# Output: 0  (success)
```

**2. Open Relay:**
```bash
python DAQ6510.py test "{'Instrument': 'DAQ6510_1', 'Item': 'OPEN', 'Channel': '101'}"
# Output: 0  (success)
```

**3. Measure DC Voltage:**
```bash
python DAQ6510.py test "{'Instrument': 'DAQ6510_1', 'Item': 'VOLT', 'Channel': '101', 'Type': 'DC'}"
# Output: 1.235
```

**4. Measure AC Current (Valid Channel):**
```bash
python DAQ6510.py test "{'Instrument': 'DAQ6510_1', 'Item': 'CURR', 'Channel': '121', 'Type': 'AC'}"
# Output: 0.125
```

**5. Measure Temperature:**
```bash
python DAQ6510.py test "{'Instrument': 'DAQ6510_1', 'Item': 'TEMP', 'Channel': '101'}"
# Output: 23.450
```

**6. Measure 4-Wire Resistance:**
```bash
python DAQ6510.py test "{'Instrument': 'DAQ6510_1', 'Item': 'FRES', 'Channel': '102'}"
# Output: 10.123
```

**7. Reset Instrument:**
```bash
python DAQ6510.py --final "{'Instrument': 'DAQ6510_1'}"
# No output (silent success)
```

**8. Invalid Channel Example:**
```bash
python DAQ6510.py test "{'Instrument': 'DAQ6510_1', 'Item': 'CURR', 'Channel': '101'}"
# Output: Error : channel input is wrong! (21/22)
# Returns: None
```

---

## Integration with PDTool4

### Typical Call Pattern

From `PowerReadMeasurement.py` or `CommandTestMeasurement.py`:

```python
import subprocess
import ast

# Prepare command arguments
args_dict = {
    'Instrument': 'DAQ6510_1',
    'Item': 'VOLT',
    'Channel': '101',
    'Type': 'DC'
}

# Execute measurement
process = subprocess.Popen(
    ['python', './src/lowsheen_lib/DAQ6510.py', 'test', str(args_dict)],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)
stdout, stderr = process.communicate()

# Parse result
result = float(stdout.decode('utf-8').strip())
print(f"Measured voltage: {result}V")
```

### Relay Control Pattern

```python
# Close relay
close_args = {
    'Instrument': 'DAQ6510_1',
    'Item': 'CLOS',
    'Channel': '101,102'
}
result = subprocess.run(
    ['python', './src/lowsheen_lib/DAQ6510.py', 'test', str(close_args)],
    capture_output=True, text=True
)
if result.stdout.strip() == '0':
    print("Relay closed successfully")
else:
    print("Relay close failed")
```

### Cleanup Call

```python
# At test completion
cleanup_args = {'Instrument': 'DAQ6510_1'}
subprocess.run([
    'python', './src/lowsheen_lib/DAQ6510.py',
    '--final', str(cleanup_args)
])
```

---

## Channel Numbering

### DAQ6510 Channel Format

**Format:** `SMM` (Slot Module Module)
- **S:** Slot number (1-3 for DAQ6510)
- **MM:** Channel number within module (01-25)

**Examples:**
- `101` - Slot 1, Channel 01 ✓
- `122` - Slot 1, Channel 22 ✓
- `221` - Slot 2, Channel 21 ✓ (current measurement)
- `325` - Slot 3, Channel 25 ✓
- `126` - Slot 1, Channel 26 ✗ (invalid, exceeds 25)

**Current Measurement Channels:**
- **Restricted to channels 21-22** in any slot
- Example valid: `121`, `122`, `221`, `222`, `321`, `322`
- Example invalid: `101`, `115`, `123`, `220`

**Voltage/Resistance Channels:**
- **Any channel 01-25** in any slot
- Example valid: `101`, `115`, `220`, `325`
- Example invalid: `126`, `330`

---

## Error Handling

### Instrument Connection Errors

```python
instrument = instrument_iniSetting(Instrument_value)
if instrument is None:
    print("instrument is None")
    sys.exit(10)  # Exit code 10: Connection failure
```

### Channel Validation Errors

```python
# Invalid channel for current measurement
check_channel_list('CURR', '101')
# Output: "Error : channel input is wrong! (21/22)"
# Returns: None

# Invalid channel number (too high)
check_channel_list('VOLT', '126')
# Output: "Error : channel input is wrong! (01~25)"
# Returns: None
```

### Command Validation Errors

```python
# Missing type for voltage measurement
get_cmd_string('VOLT', '101', type_=None)
# Output: "Error : no type setting!(AC/DC)"
# Returns: None

# Invalid command
send_cmd_to_instrument(instrument, 'INVALID', '101', None)
# Output: "Invalid command: INVALID"
# Returns: None
```

### Relay Operation Errors

```python
# Relay failed to close
response = send_cmd_to_instrument(instrument, 'CLOS', '101', None)
if response == '1':
    print("Relay failed to close")
```

---

## Technical Details

### SCPI Command Format

**Relay Control:**
```
ROUT:OPEN (@101,102,103)      # Open multiple channels
ROUT:CLOS (@101)               # Close single channel
ROUT:CLOS?                     # Query all closed channels (no filter)
```

**Measurement Commands:**
```
MEAS:VOLT:DC? (@101)           # Measure DC voltage on channel 101
MEAS:CURR:AC? (@121)           # Measure AC current on channel 121
MEAS:TEMP? (@101)              # Measure temperature on channel 101
MEAS:RES? (@102)               # Measure 2-wire resistance
MEAS:FRES? (@103)              # Measure 4-wire resistance
```

### Relay Verification Algorithm

```python
# Write relay command
instrument.write(f'ROUT:{cmd} (@{channels})')

# Query all closed channels
response_index = instrument.query('ROUT:CLOS?')
# Example response: '(@101,102,105)'

# Verify based on command type
if cmd == 'OPEN':
    # Success if channel is NOT in closed list
    success = channels not in response_index
elif cmd == 'CLOS':
    # Success if channel IS in closed list
    success = channels in response_index

return '0' if success else '1'
```

**Example:**
```python
# Close channel 101
instrument.write('ROUT:CLOS (@101)')
response_index = instrument.query('ROUT:CLOS?')  # Returns: '(@101,102)'
'101' in '(@101,102)'  # True -> return '0' (success)

# Open channel 101
instrument.write('ROUT:OPEN (@101)')
response_index = instrument.query('ROUT:CLOS?')  # Returns: '(@102)'
'101' not in '(@102)'  # True -> return '0' (success)
```

### Timing Considerations

| Operation | Delay | Reason |
|-----------|-------|--------|
| Relay switching | None | Electronic verification via query |
| Temperature measurement | 2s | Thermocouple stabilization |
| Normal measurement | None | Electronic measurement (fast) |

### Number Formatting

```python
response = '{:.3f}'.format(float(instrument.query(cmd)))
# Example: '+1.23456E+00' -> '1.235'
# Example: '+2.34567E+01' -> '23.457'
```

**Format Details:**
- Converts scientific notation to decimal
- 3 decimal places precision
- Returns string representation

---

## Comparison with DAQ973A

| Feature | DAQ6510 | DAQ973A_test |
|---------|---------|--------------|
| **Channel Validation** | Strict (01-25) | Relaxed (commented out) |
| **Current Channels** | 21-22 only | 21-22 only |
| **Relay Verification** | Status-based ('0'/'1') | Query response string |
| **Check Command** | `ROUT:CLOS?` (all) | `ROUT:CLOS? (@channels)` |
| **Temperature Delay** | 2 seconds | 2 seconds |
| **Return Format** | Binary for relays | SCPI response for relays |

**Key Architectural Differences:**

1. **Relay Verification:**
   - **DAQ6510:** Queries all closed channels, verifies presence/absence
   - **DAQ973A:** Queries specific channels, returns raw response

2. **Channel Validation:**
   - **DAQ6510:** Enforces 01-25 range strictly
   - **DAQ973A:** Validation code commented out (accepts any)

3. **Error Reporting:**
   - **DAQ6510:** Binary success/fail for relays ('0'/'1')
   - **DAQ973A:** Raw SCPI response strings

---

## Best Practices

### 1. Channel Validation
```python
# Always validate channels before use
channels = check_channel_list(cmd, channel_input)
if channels is None:
    raise ValueError(f"Invalid channel: {channel_input} for {cmd}")
```

### 2. Relay Status Verification
```python
# Check relay operation success
result = send_cmd_to_instrument(instrument, 'CLOS', '101', None)
if result != '0':
    raise RuntimeError("Failed to close relay channel 101")
```

### 3. Type Specification for Voltage/Current
```python
# Always specify AC/DC
args = {
    'Item': 'VOLT',
    'Channel': '101',
    'Type': 'DC'  # Required for VOLT/CURR
}
```

### 4. Current Measurement Channel Selection
```python
# Only use channels 21-22 for current
valid_current_channels = ['121', '122', '221', '222', '321', '322']
if channel not in valid_current_channels:
    raise ValueError(f"Current measurement requires channels 21-22, got: {channel}")
```

### 5. Temperature Measurement
```python
# Allow 2-second stabilization
if cmd == 'TEMP':
    instrument.query(remote_cmd)  # Discard first reading
    time.sleep(2)                 # Wait for stabilization
    result = instrument.query(remote_cmd)  # Use second reading
```

### 6. Error Recovery
```python
# Always reset instrument on error
try:
    result = send_cmd_to_instrument(instrument, cmd, channels, type_)
except Exception as e:
    initial(instrument)  # Reset to known state
    raise
```

---

## Limitations

1. **No Scanning:** Doesn't support DAQ6510's scan list feature
2. **Fixed Precision:** All results formatted to 3 decimal places (not configurable)
3. **No Range Control:** Uses instrument auto-range only
4. **No Integration Time:** Uses instrument default integration period
5. **Single Channel:** Measures one channel per call (doesn't batch)
6. **No NPLC Setting:** Cannot configure integration time (NPLC - Number of Power Line Cycles)

---

## Related Files

- `remote_instrument.py` - Instrument initialization (`instrument_iniSetting()`)
- `DAQ973A_test.py` - Similar driver for Keysight DAQ973A
- `PowerReadMeasurement.py` - Consumer for voltage/current measurements
- `CommandTestMeasurement.py` - Generic measurement executor
- `oneCSV_atlas_2.py` - Test orchestrator

---

## Testing

### Manual Test Commands

```bash
# Test relay closure
python DAQ6510.py test "{'Instrument': 'DAQ6510_1', 'Item': 'CLOS', 'Channel': '101'}"
# Expected: 0

# Test relay opening
python DAQ6510.py test "{'Instrument': 'DAQ6510_1', 'Item': 'OPEN', 'Channel': '101'}"
# Expected: 0

# Test voltage measurement
python DAQ6510.py test "{'Instrument': 'DAQ6510_1', 'Item': 'VOLT', 'Channel': '101', 'Type': 'DC'}"
# Expected: numeric value (e.g., 1.235)

# Test current measurement (valid channel)
python DAQ6510.py test "{'Instrument': 'DAQ6510_1', 'Item': 'CURR', 'Channel': '121', 'Type': 'AC'}"
# Expected: numeric value (e.g., 0.125)

# Test current measurement (invalid channel)
python DAQ6510.py test "{'Instrument': 'DAQ6510_1', 'Item': 'CURR', 'Channel': '101', 'Type': 'AC'}"
# Expected: "Error : channel input is wrong! (21/22)"

# Test temperature
python DAQ6510.py test "{'Instrument': 'DAQ6510_1', 'Item': 'TEMP', 'Channel': '101'}"
# Expected: numeric value (e.g., 23.450)

# Test 4-wire resistance
python DAQ6510.py test "{'Instrument': 'DAQ6510_1', 'Item': 'FRES', 'Channel': '102'}"
# Expected: numeric value (e.g., 10.123)

# Test reset
python DAQ6510.py --final "{'Instrument': 'DAQ6510_1'}"
# Expected: no output (silent success)
```

### Expected Behavior

| Test | Expected Output | Meaning |
|------|----------------|---------|
| Relay CLOS success | `0` | Channel successfully closed |
| Relay CLOS failure | `1` | Channel failed to close |
| Relay OPEN success | `0` | Channel successfully opened |
| Voltage measurement | `1.235` | Numeric value (3 decimals) |
| Connection failure | `instrument is None` + exit 10 | No connection |
| Invalid channel | `Error : channel input is wrong!` | Validation failed |
| Reset | (no output) | Silent success |

---

## Version History

- Current implementation supports strict channel validation (01-25)
- Binary relay status return ('0'/'1') for simplified error checking
- Status-based relay verification using `ROUT:CLOS?` query

---

## Appendix: Channel Validation Reference

### Valid Channel Examples by Command

**CURR (Current Measurement):**
```
Valid:   121, 122, 221, 222, 321, 322
Invalid: 101, 115, 120, 123, 125, 201, 315
```

**All Other Commands (VOLT, RES, TEMP, etc.):**
```
Valid:   101, 105, 115, 120, 125, 201, 220, 301, 325
Invalid: 100, 126, 130, 199, 226, 330, 400
```

### Error Message Reference

```python
# Current channel error
"Error : channel input is wrong! (21/22)"
# Cause: Tried to measure current on non-21/22 channel

# General channel error
"Error : channel input is wrong! (01~25)"
# Cause: Channel number outside 01-25 range

# Type missing error
"Error : no type setting!(AC/DC)"
# Cause: VOLT or CURR command without 'Type' parameter

# Invalid command error
"Invalid command: <CMD>"
# Cause: Command not in function_mapping

# Connection error
"instrument is None"
# Cause: Failed to connect to instrument (exit code 10)
```
