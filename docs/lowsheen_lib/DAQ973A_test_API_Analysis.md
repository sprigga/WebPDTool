# DAQ973A_test API Analysis

## Overview

`DAQ973A_test.py` provides a command-line interface for controlling Keysight DAQ973A Data Acquisition Systems. It supports relay switching (OPEN/CLOSE) and multi-function measurements (voltage, current, resistance, temperature, etc.) through SCPI commands.

**Location:** `src/lowsheen_lib/DAQ973A_test.py`

**Supported Instrument:** Keysight DAQ973A (Modular Data Acquisition System)

**Primary Use Cases:**
- Switch relay channels for signal routing
- Measure DC/AC voltage and current
- Measure resistance, frequency, capacitance, temperature
- Diode testing and 4-wire resistance measurements

---

## Core Functions

### `check_channel_list(cmd, channels)`

Validates and formats channel numbers based on the measurement type.

**Parameters:**
- `cmd` (str): Command type ('CURR', 'VOLT', 'OPEN', 'CLOS', etc.)
- `channels` (str): Channel specification (e.g., '101', '(101, 102)')

**Returns:**
- `list`: Validated channel numbers as strings
- `None`: If validation fails

**Validation Rules:**
- **Current Measurements (`CURR`):**
  - Only channels ending with '21' or '22' are allowed
  - Example valid: '121', '222'
  - Example invalid: '101', '115'
  - Reason: DAQ973A current measurement cards typically in slots 21-22

- **Other Commands:**
  - All channels accepted (commented out validation for 01-20)
  - Originally designed to validate channels 01-25 (currently disabled)

**Example:**
```python
check_channel_list('CURR', '121')  # Returns: ['121']
check_channel_list('CURR', '(121, 122)')  # Returns: ['121', '122']
check_channel_list('VOLT', '101')  # Returns: ['101']
```

### `get_cmd_string(cmd, channels, type_=None)`

Generates SCPI command strings for the DAQ973A based on the operation type.

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
# Returns: ('ROUT:OPEN (@101)', 'ROUT:OPEN? (@101)')

get_cmd_string('CLOS', '(101,102)')
# Returns: ('ROUT:CLOS (@101,102)', 'ROUT:CLOS? (@101,102)')
```

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

get_cmd_string('RES', '102', 'DEF')
# Returns: 'MEAS:RES? (@102)'
```

### `send_cmd_to_instrument(instrument, cmd, channels, type_)`

Executes the command on the DAQ973A and returns the result.

**Parameters:**
- `instrument`: PyVISA instrument object (from `instrument_iniSetting()`)
- `cmd` (str): Command type from function_mapping
- `channels` (str): Channel specification
- `type_` (str): Measurement type (AC/DC/DEF)

**Returns:**
- **Relay Commands:** Response string from instrument (verification)
- **Measurements:** Formatted numeric result (3 decimal places)
- `None`: On error

**Execution Flow:**

**1. Relay Control (OPEN/CLOS):**
```python
# 1. Generate command and verification query
remote_cmd, check_cmd = get_cmd_string('CLOS', '101')

# 2. Write command to instrument
instrument.write('ROUT:CLOS (@101)')
time.sleep(0.1)  # Wait for relay settling

# 3. Query status to verify
response = instrument.query('ROUT:CLOS? (@101)')
# Response: '(@101,102)' (currently closed channels)
```

**2. Measurement (Non-Temperature):**
```python
# Generate and execute measurement
remote_cmd = get_cmd_string('VOLT', '101', 'DC')
response = instrument.query('MEAS:VOLT:DC? (@101)')
# Response: '+1.23456E+00' -> Formatted to '1.235'
```

**3. Temperature Measurement:**
```python
# Temperature requires warm-up query
instrument.query('MEAS:TEMP? (@101)')  # Initial query (discard)
time.sleep(2)  # Wait for sensor stabilization
response = instrument.query('MEAS:TEMP? (@101)')  # Actual reading
# Response: '+2.345E+01' -> Formatted to '23.450'
```

**Special Handling:**
- **Temperature (`TEMP`):** Two queries with 2-second delay (sensor warm-up)
- **Result Formatting:** `'{:.3f}'.format(float(response))` (3 decimal precision)

### `initial(instrument)`

Resets the DAQ973A to factory default state.

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

**Command Categories:**

| Command | Description | Type Required | Notes |
|---------|-------------|---------------|-------|
| `OPEN` | Open relay channels | - | Verification via query |
| `CLOS` | Close relay channels | - | Verification via query |
| `VOLT` | Voltage measurement | AC/DC | AC or DC required |
| `CURR` | Current measurement | AC/DC | Channels 21-22 only |
| `RES` | 2-wire resistance | - | Default type |
| `FRES` | 4-wire resistance | - | High precision |
| `TEMP` | Temperature | - | 2-query sequence |
| `FREQ` | Frequency | - | AC signals |
| `PER` | Period | - | AC signals |
| `CAP` | Capacitance | - | Capacitor measurement |
| `DIOD` | Diode test | - | Forward voltage drop |

---

## Command-Line Interface

### Usage

```bash
python DAQ973A_test.py <sequence> <args_dict>
```

**Arguments:**
- `sequence` (str):
  - `'--final'`: Initialize/reset instrument
  - Any other value: Execute measurement
- `args_dict` (str): JSON-like dictionary containing:

**Required Keys:**
- `Instrument` (str): Instrument identifier (e.g., 'DAQ973A_1')
- `Item` (str): Command type (from function_mapping)

**Optional Keys:**
- `Channel` (str): Channel specification (default: None)
- `Type` (str): Measurement type (AC/DC/DEF)

### Examples

**1. Close Relay:**
```bash
python DAQ973A_test.py test "{'Instrument': 'DAQ973A_1', 'Item': 'CLOS', 'Channel': '101'}"
```

**2. Measure DC Voltage:**
```bash
python DAQ973A_test.py test "{'Instrument': 'DAQ973A_1', 'Item': 'VOLT', 'Channel': '101', 'Type': 'DC'}"
# Output: 1.235
```

**3. Measure Temperature:**
```bash
python DAQ973A_test.py test "{'Instrument': 'DAQ973A_1', 'Item': 'TEMP', 'Channel': '101'}"
# Output: 23.450
```

**4. Measure AC Current:**
```bash
python DAQ973A_test.py test "{'Instrument': 'DAQ973A_1', 'Item': 'CURR', 'Channel': '121', 'Type': 'AC'}"
# Output: 0.125
```

**5. Reset Instrument:**
```bash
python DAQ973A_test.py --final "{'Instrument': 'DAQ973A_1'}"
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
    'Instrument': 'DAQ973A_1',
    'Item': 'VOLT',
    'Channel': '101',
    'Type': 'DC'
}

# Execute measurement
process = subprocess.Popen(
    ['python', './src/lowsheen_lib/DAQ973A_test.py', 'test', str(args_dict)],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)
stdout, stderr = process.communicate()

# Parse result
result = float(stdout.decode('utf-8').strip())
print(f"Measured voltage: {result}V")
```

### Cleanup Call

```python
# At test completion
cleanup_args = {'Instrument': 'DAQ973A_1'}
subprocess.run([
    'python', './src/lowsheen_lib/DAQ973A_test.py',
    '--final', str(cleanup_args)
])
```

---

## Channel Numbering

### DAQ973A Channel Format

**Format:** `SMM` (Slot Module Module)
- **S:** Slot number (1-3)
- **MM:** Channel number within module (01-22)

**Examples:**
- `101` - Slot 1, Channel 01
- `122` - Slot 1, Channel 22
- `221` - Slot 2, Channel 21
- `315` - Slot 3, Channel 15

**Current Measurement Channels:**
- Typically use specialized current input cards in slots with channels 21-22
- Example: `121`, `122`, `221`, `222`

---

## Error Handling

### Instrument Connection Errors

```python
instrument = instrument_iniSetting(Instrument_value)
if instrument is None:
    print("instrument is None")
    sys.exit(10)  # Exit code 10: Connection failure
```

### Command Validation Errors

```python
# Invalid channel for current measurement
check_channel_list('CURR', '101')
# Output: "Error : channel input is wrong! (21/22)"
# Returns: None

# Missing type for voltage measurement
get_cmd_string('VOLT', '101', type_=None)
# Output: "Error : no type setting!(AC/DC)"
# Returns: None

# Invalid command
send_cmd_to_instrument(instrument, 'INVALID', '101', None)
# Output: "Invalid command: INVALID"
```

---

## Technical Details

### SCPI Command Format

**Relay Control:**
```
ROUT:OPEN (@101,102,103)      # Open multiple channels
ROUT:CLOS (@101)               # Close single channel
ROUT:OPEN? (@101)              # Query open channels
ROUT:CLOS? (@101)              # Query closed channels
```

**Measurement Commands:**
```
MEAS:VOLT:DC? (@101)           # Measure DC voltage
MEAS:CURR:AC? (@121)           # Measure AC current
MEAS:TEMP? (@101)              # Measure temperature
MEAS:RES? (@102)               # Measure 2-wire resistance
MEAS:FRES? (@103)              # Measure 4-wire resistance
```

### Timing Considerations

| Operation | Delay | Reason |
|-----------|-------|--------|
| Relay switching | 0.1s | Mechanical relay settling time |
| Temperature measurement | 2s | Thermocouple warm-up |
| Normal measurement | None | Electronic measurement (fast) |

### Number Formatting

```python
response = '{:.3f}'.format(float(instrument.query(cmd)))
# Example: '+1.23456E+00' -> '1.235'
```

**Format Details:**
- Converts scientific notation to decimal
- 3 decimal places precision
- Returns string representation

---

## Best Practices

### 1. Channel Validation
```python
# Always validate channels before measurement
channels = check_channel_list(cmd, channel_input)
if channels is None:
    raise ValueError("Invalid channel specification")
```

### 2. Type Specification
```python
# Always specify AC/DC for voltage/current
args = {
    'Item': 'VOLT',
    'Channel': '101',
    'Type': 'DC'  # Required!
}
```

### 3. Temperature Measurement
```python
# Allow 2-second stabilization for accurate readings
if cmd == 'TEMP':
    instrument.query(remote_cmd)  # Discard first reading
    time.sleep(2)
    result = instrument.query(remote_cmd)  # Use second reading
```

### 4. Error Recovery
```python
# Always call --final to reset instrument on error
try:
    result = send_cmd_to_instrument(...)
except Exception as e:
    initial(instrument)  # Reset to known state
    raise
```

---

## Comparison with DAQ6510

| Feature | DAQ973A_test | DAQ6510 |
|---------|-------------|---------|
| Current channels | 21-22 only | 21-22 only |
| Other channels | No validation | 01-25 validated |
| Relay verification | Full query | Status-based |
| Temperature delay | 2 seconds | 2 seconds |
| Command format | Identical | Identical |

**Key Difference:** DAQ973A has relaxed channel validation (commented out), while DAQ6510 enforces strict 01-25 range.

---

## Limitations

1. **No Multi-Channel Measurements:** Each call measures single channel (even if multiple specified)
2. **No Scanning:** Doesn't support DAQ973A's scan list feature
3. **Fixed Precision:** All results formatted to 3 decimal places
4. **No Range Control:** Uses instrument auto-range (no manual range setting)
5. **No Integration Time:** Uses instrument default integration period

---

## Related Files

- `remote_instrument.py` - Instrument initialization (`instrument_iniSetting()`)
- `DAQ6510.py` - Similar driver for Keysight DAQ6510
- `PowerReadMeasurement.py` - Consumer for voltage/current measurements
- `CommandTestMeasurement.py` - Generic measurement executor

---

## Testing

### Manual Test Commands

```bash
# Test relay operation
python DAQ973A_test.py test "{'Instrument': 'DAQ973A_1', 'Item': 'CLOS', 'Channel': '101'}"
python DAQ973A_test.py test "{'Instrument': 'DAQ973A_1', 'Item': 'OPEN', 'Channel': '101'}"

# Test voltage measurement
python DAQ973A_test.py test "{'Instrument': 'DAQ973A_1', 'Item': 'VOLT', 'Channel': '101', 'Type': 'DC'}"

# Test temperature
python DAQ973A_test.py test "{'Instrument': 'DAQ973A_1', 'Item': 'TEMP', 'Channel': '101'}"

# Test reset
python DAQ973A_test.py --final "{'Instrument': 'DAQ973A_1'}"
```

### Expected Behavior
- **Connection failure:** Exit code 10, prints "instrument is None"
- **Successful measurement:** Prints numeric value (3 decimals)
- **Invalid channel:** Prints error message, returns None
- **Reset:** No output (silent success)
