# 34970A API Analysis

## Overview

**File**: `src/lowsheen_lib/34970A.py`

**Purpose**: Command-line interface driver for Keysight/Agilent 34970A Data Acquisition/Switch Unit

**Instrument Type**: Multi-channel data acquisition and switching system with measurement capabilities (voltage, current, resistance, temperature, frequency, capacitance, diode test)

---

## Command-Line Interface

### Usage

```bash
python src/lowsheen_lib/34970A.py <sequence> <args_dict>
```

### Parameters

- **sequence** (str): Operation mode
  - `--final`: Reset instrument to default state
  - Any other value: Execute measurement/switching operation

- **args_dict** (str): Python dictionary literal as string containing:
  - `Instrument` (str): Instrument identifier from configuration (e.g., "34970A_1")
  - `Item` (str): Command type (see Function Mapping)
  - `Channel` (str/tuple): Channel number(s) in format "205" or "(101, 102)"
  - `Type` (str, optional): Measurement type for VOLT/CURR commands ("AC" or "DC")

### Example

```bash
# Close relay on channel 205
python 34970A.py "" "{'Instrument': '34970A_1', 'Item': 'CLOS', 'Channel': '205', 'Type': ''}"

# Measure DC voltage on channels 101-103
python 34970A.py "" "{'Instrument': '34970A_1', 'Item': 'VOLT', 'Channel': '(101, 102, 103)', 'Type': 'DC'}"

# Reset instrument
python 34970A.py "--final" "{'Instrument': '34970A_1', 'Item': '', 'Channel': '', 'Type': ''}"
```

---

## Function Mapping

### Supported Commands (function_mapping)

| Command | Description | Type Required | Valid Channels |
|---------|-------------|---------------|----------------|
| `OPEN` | Open relay channel(s) | No | 01-20 |
| `CLOS` | Close relay channel(s) | No | 01-20 |
| `VOLT` | Measure voltage | Yes (AC/DC) | 01-20 |
| `CURR` | Measure current | Yes (AC/DC) | 21-22 only |
| `DIOD` | Diode test | No | 01-20 |
| `RES` | Measure resistance | No | 01-20 |
| `FRES` | Measure 4-wire resistance | No | 01-20 |
| `TEMP` | Measure temperature | No | 01-20 |
| `FREQ` | Measure frequency | No | 01-20 |
| `PER` | Measure period | No | 01-20 |
| `CAP` | Measure capacitance | No | 01-20 |

---

## Core Functions

### check_channel_list(cmd, channels)

Validates channel numbers based on command type.

**Parameters:**
- `cmd` (str): Command type
- `channels` (str/tuple): Channel specification

**Returns:**
- `list`: Validated channel numbers as strings
- `None`: If validation fails (prints error message)

**Channel Validation Rules:**
- `CURR` command: Only channels ending in "21" or "22"
- All other commands: Channels 01-20 (currently accepts all, validation commented out)

**Example:**
```python
check_channel_list('CURR', '(221, 222)')  # Returns ['221', '222']
check_channel_list('CURR', '101')         # Returns None (error)
check_channel_list('VOLT', '(101, 105)') # Returns ['101', '105']
```

---

### get_cmd_string(cmd, channels, type_=None)

Constructs SCPI command strings for the instrument.

**Parameters:**
- `cmd` (str): Command type from function_mapping
- `channels` (str/tuple): Channel specification
- `type_` (str, optional): "AC" or "DC" for VOLT/CURR commands

**Returns:**
- **For OPEN/CLOS**: Tuple of (remote_cmd, check_cmd)
  ```python
  ("ROUT:CLOS (@101,102)", "ROUT:CLOS? (@101,102)")
  ```
- **For measurements**: Single command string
  ```python
  "MEAS:VOLT:DC? (@101,102,103)"
  ```
- `None`: If validation fails

**Examples:**
```python
get_cmd_string('CLOS', '205')
# Returns: ("ROUT:CLOS (@205)", "ROUT:CLOS? (@205)")

get_cmd_string('VOLT', '(101, 102)', 'DC')
# Returns: "MEAS:VOLT:DC? (@101,102)"

get_cmd_string('RES', '101')
# Returns: "MEAS:RES? (@101)"
```

---

### send_cmd_to_instrument(instrument, cmd, channels, type_)

Executes command on the instrument and returns response.

**Parameters:**
- `instrument`: PyVISA instrument object
- `cmd` (str): Command type
- `channels` (str/tuple): Channel specification
- `type_` (str): Measurement type (AC/DC) or empty string

**Returns:**
- `str`: Formatted response from instrument
  - Relay operations: Query response confirming state
  - Measurements: Float formatted to 3 decimal places
- `None`: Prints error message if command fails

**Behavior:**
- **Relay commands (OPEN/CLOS)**: Writes command, then queries to confirm
- **Temperature measurements**: Issues query twice with 2-second delay for settling
- **Other measurements**: Single query, formats result as `{:.3f}`

**Examples:**
```python
send_cmd_to_instrument(inst, 'VOLT', '101', 'DC')
# Returns: "12.345"

send_cmd_to_instrument(inst, 'TEMP', '101', '')
# Waits 2 seconds, returns: "25.123"

send_cmd_to_instrument(inst, 'CLOS', '205', '')
# Returns: "1" (relay closed)
```

---

### initial(instrument)

Resets instrument to default state.

**Parameters:**
- `instrument`: PyVISA instrument object

**Behavior:**
- Sends `*RST\n` command
- No return value

---

## Data Flow

```
Command-line invocation
    ↓
Parse sys.argv[1] (sequence) and sys.argv[2] (args dict)
    ↓
instrument_iniSetting(Instrument_value) → PyVISA instrument object
    ↓
    ┌─ sequence == '--final' → initial(instrument) → Reset
    │
    └─ else → send_cmd_to_instrument(instrument, item, channels, type_)
                ↓
                check_channel_list(cmd, channels) → Validate channels
                ↓
                get_cmd_string(cmd, channels, type_) → Build SCPI command
                ↓
                Execute on instrument (write/query)
                ↓
                Format response (3 decimal places for measurements)
    ↓
print(response) → Stdout
```

---

## SCPI Command Format

### Relay Control
```
ROUT:OPEN (@101,102,103)   # Open channels
ROUT:CLOS (@205)           # Close channels
ROUT:OPEN? (@101,102)      # Query relay state
```

### Measurements
```
MEAS:VOLT:DC? (@101,102)   # DC voltage
MEAS:VOLT:AC? (@101)       # AC voltage
MEAS:CURR:DC? (@221,222)   # DC current (channels 21/22 only)
MEAS:RES? (@101)           # 2-wire resistance
MEAS:FRES? (@101)          # 4-wire resistance
MEAS:TEMP? (@101)          # Temperature
MEAS:FREQ? (@101)          # Frequency
MEAS:PER? (@101)           # Period
MEAS:CAP? (@101)           # Capacitance
MEAS:DIOD? (@101)          # Diode test
```

---

## Error Handling

### Exit Codes
- **Exit 10**: Instrument connection failed (`instrument is None`)
- **Exit 0**: Normal completion

### Error Messages (Printed to Stdout)
- `"Error : channel input is wrong! (21/22)"` - Invalid current measurement channel
- `"Error : channel input is wrong! (01~20)"` - Invalid channel number (if validation enabled)
- `"Error : remote command is wrong"` - Command construction failed
- `"Invalid command: <cmd>"` - Command not in function_mapping

---

## Integration with PDTool4

### Test Plan Configuration

In CSV test plans, configure 34970A measurements:

```csv
Item,Instrument,Channel,Type
VOLT,34970A_1,101,DC
CURR,34970A_1,221,DC
CLOS,34970A_1,205,
```

### Subprocess Invocation Pattern

```python
import subprocess
import json

args = {
    'Instrument': '34970A_1',
    'Item': 'VOLT',
    'Channel': '101',
    'Type': 'DC'
}

result = subprocess.run(
    ['python', 'src/lowsheen_lib/34970A.py', '', str(args)],
    capture_output=True,
    text=True
)

measured_value = result.stdout.strip()  # "12.345"
```

### Cleanup Protocol

Always call with `--final` after test sequence:

```python
subprocess.run([
    'python', 'src/lowsheen_lib/34970A.py',
    '--final',
    str({'Instrument': '34970A_1', 'Item': '', 'Channel': '', 'Type': ''})
])
```

---

## Dependencies

- `remote_instrument.instrument_iniSetting`: Returns PyVISA instrument object from identifier
- `time`: For temperature measurement settling time
- `sys`: Command-line argument parsing
- `ast.literal_eval`: Safe dictionary string parsing

---

## Limitations & Notes

1. **Channel Validation**: The 01-20 validation for non-CURR commands is currently disabled (lines 20-24 commented out)

2. **Temperature Settling**: 2-second delay hardcoded for TEMP measurements (line 75)

3. **Output Format**: All numeric measurements formatted to 3 decimal places

4. **Single Instrument Session**: Each invocation opens/closes instrument connection

5. **Error Reporting**: Uses print() for errors instead of stderr, may interfere with response parsing

6. **Channel Format Parsing**: Expects tuple string format `"(101, 102)"` with specific spacing

---

## Troubleshooting

### Common Issues

**"instrument is None" Error**
- Verify instrument identifier matches configuration in `remote_instrument.py`
- Check VISA connection (USB/LAN/GPIB)
- Ensure instrument is powered on

**Channel Validation Failures**
- Current measurements: Use channels ending in 21 or 22
- Check channel number format: `"205"` or `"(101, 102, 103)"`

**Measurement Timeouts**
- Temperature measurements take 2+ seconds
- Increase subprocess timeout accordingly

**Type Error for VOLT/CURR**
- Must specify `Type: 'AC'` or `Type: 'DC'` in args dict
- Error: "Error : no type setting!(AC/DC)"

---

## Version History

- **Current**: Supports all 34970A measurement and switching functions
- **Notes**: Originally from PDTool4 lowsheen_lib collection
