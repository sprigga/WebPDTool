# APS7050 API Analysis

## Overview

**File**: `src/lowsheen_lib/APS7050.py`

**Purpose**: Command-line interface driver for GW Instek APS-7000 Series Programmable AC/DC Power Source with measurement capabilities

**Instrument Type**: AC/DC power source with built-in DMM (voltage, current, frequency, resistance, capacitance, diode, temperature measurements) and relay control

---

## Command-Line Interface

### Usage

```bash
python src/lowsheen_lib/APS7050.py <sequence> <args_dict>
```

### Parameters

- **sequence** (str): Operation mode
  - `--final`: Reset instrument to default state
  - Any other value: Execute measurement/switching operation

- **args_dict** (str): Python dictionary literal as string containing:
  - `Instrument` (str): Instrument identifier from configuration (e.g., "APS7050_1")
  - `Command` (str, optional): Raw SCPI command (takes priority over Item)
  - `Item` (str): Command type from function_mapping (used if Command not provided)
  - `Channel` (str/tuple): Channel number(s) for measurements
  - `Type` (str, optional): Measurement type for VOLT/CURR commands ("AC" or "DC")

### Example

```bash
# Send raw SCPI command
python APS7050.py "" "{'Instrument': 'APS7050_1', 'Command': '*IDN?\\n', 'Item': '', 'Channel': '', 'Type': ''}"

# Close relay on channel 205
python APS7050.py "" "{'Instrument': 'APS7050_1', 'Command': '', 'Item': 'CLOS', 'Channel': '205', 'Type': ''}"

# Measure DC voltage on channel 101
python APS7050.py "" "{'Instrument': 'APS7050_1', 'Command': '', 'Item': 'VOLT', 'Channel': '101', 'Type': 'DC'}"

# Reset instrument
python APS7050.py "--final" "{'Instrument': 'APS7050_1', 'Command': '', 'Item': '', 'Channel': '', 'Type': ''}"
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
- All other commands: Channels 01-20

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

### send_onlycmd_to_instrument(instrument, cmd)

Sends raw SCPI command directly to instrument.

**Parameters:**
- `instrument`: PyVISA instrument object
- `cmd` (str): Raw SCPI command (may include `\n` escape sequences)

**Returns:**
- `str`: Raw response from instrument

**Example:**
```python
send_onlycmd_to_instrument(inst, '*IDN?\n')
# Returns: "GW INSTEK,APS-7050,SN12345,V1.00"

send_onlycmd_to_instrument(inst, 'OUTP?\n')
# Returns: "1" (output on)
```

---

### send_cmd_to_instrument(instrument, cmd, channels, type_)

Executes command on the instrument and returns response.

**Parameters:**
- `instrument`: PyVISA instrument object
- `cmd` (str): Command type from function_mapping
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
    ├─ cmd provided (raw SCPI) → send_onlycmd_to_instrument(instrument, cmd)
    │                              ↓
    │                           Process \n escape sequences
    │                              ↓
    │                           instrument.query(cmd)
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

## Key Difference from 34970A

### Raw Command Support

**APS7050** includes `send_onlycmd_to_instrument()` function allowing direct SCPI command execution via the `Command` parameter. This provides flexibility for:
- Identification queries (`*IDN?`)
- Output control (`OUTP ON`, `OUTP OFF`)
- Configuration commands not in function_mapping

**Example:**
```python
# APS7050 supports this
args = {'Instrument': 'APS7050_1', 'Command': 'OUTP ON\n', 'Item': '', 'Channel': '', 'Type': ''}

# 34970A does not have this capability - must use predefined function_mapping
```

### Command Processing

The `\n` escape sequence handling (lines 115-120):
```python
if '\\n' in cmd:
    cmd = cmd.replace('\\n', '\n')  # Convert string literal to actual newline
else:
    cmd = cmd
```

This allows test plans to specify commands like:
```
Command: "*IDN?\\n"
```

---

## SCPI Command Format

### Raw Commands (via Command parameter)
```
*IDN?\n                    # Identify instrument
*RST\n                     # Reset
OUTP ON\n                  # Enable output
OUTP OFF\n                 # Disable output
OUTP?\n                    # Query output state
VOLT 120\n                 # Set voltage
CURR 5\n                   # Set current
```

### Relay Control (via Item parameter)
```
ROUT:OPEN (@101,102,103)   # Open channels
ROUT:CLOS (@205)           # Close channels
ROUT:OPEN? (@101,102)      # Query relay state
```

### Measurements (via Item parameter)
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
- `"Error : channel input is wrong! (01~20)"` - Invalid channel number
- `"Error : no type setting!(AC/DC)"` - Missing Type parameter for VOLT/CURR
- `"Error : remote command is wrong"` - Command construction failed
- `"Invalid command: <cmd>"` - Command not in function_mapping

---

## Integration with PDTool4

### Test Plan Configuration

In CSV test plans, configure APS7050 operations:

**Using predefined commands:**
```csv
Item,Instrument,Channel,Type,Command
VOLT,APS7050_1,101,DC,
CURR,APS7050_1,221,DC,
CLOS,APS7050_1,205,,
```

**Using raw SCPI commands:**
```csv
Item,Instrument,Channel,Type,Command
,APS7050_1,,,*IDN?\\n
,APS7050_1,,,OUTP ON\\n
,APS7050_1,,,VOLT 120\\n
```

### Subprocess Invocation Pattern

**Standard measurement:**
```python
import subprocess
import json

args = {
    'Instrument': 'APS7050_1',
    'Command': '',
    'Item': 'VOLT',
    'Channel': '101',
    'Type': 'DC'
}

result = subprocess.run(
    ['python', 'src/lowsheen_lib/APS7050.py', '', str(args)],
    capture_output=True,
    text=True
)

measured_value = result.stdout.strip()  # "12.345"
```

**Raw command:**
```python
args = {
    'Instrument': 'APS7050_1',
    'Command': '*IDN?\\n',
    'Item': '',
    'Channel': '',
    'Type': ''
}

result = subprocess.run(
    ['python', 'src/lowsheen_lib/APS7050.py', '', str(args)],
    capture_output=True,
    text=True
)

identification = result.stdout.strip()  # "GW INSTEK,APS-7050,..."
```

### Cleanup Protocol

Always call with `--final` after test sequence:

```python
subprocess.run([
    'python', 'src/lowsheen_lib/APS7050.py',
    '--final',
    str({'Instrument': 'APS7050_1', 'Command': '', 'Item': '', 'Channel': '', 'Type': ''})
])
```

---

## Dependencies

- `remote_instrument.instrument_iniSetting`: Returns PyVISA instrument object from identifier
- `time`: For temperature measurement settling time
- `sys`: Command-line argument parsing
- `ast.literal_eval`: Safe dictionary string parsing

---

## Comparison: APS7050 vs 34970A

| Feature | APS7050 | 34970A |
|---------|---------|--------|
| **Raw SCPI Commands** | ✅ Yes (via `Command` parameter) | ❌ No |
| **Function Mapping** | ✅ Same as 34970A | ✅ Same |
| **Channel Validation** | ✅ Enabled (01-20) | ⚠️ Partially disabled |
| **Measurement Types** | ✅ Same as 34970A | ✅ Same |
| **Relay Control** | ✅ Same as 34970A | ✅ Same |
| **Primary Use Case** | Power source with DMM | Data acquisition/switching |

---

## Limitations & Notes

1. **Priority**: If both `Command` and `Item` are provided, `Command` takes priority

2. **Escape Sequences**: The driver handles `\\n` → `\n` conversion for raw commands

3. **Temperature Settling**: 2-second delay hardcoded for TEMP measurements (line 82)

4. **Output Format**: All numeric measurements formatted to 3 decimal places

5. **Single Instrument Session**: Each invocation opens/closes instrument connection

6. **Error Reporting**: Uses print() for errors instead of stderr

---

## Troubleshooting

### Common Issues

**"instrument is None" Error**
- Verify instrument identifier matches configuration in `remote_instrument.py`
- Check VISA connection (USB/LAN/GPIB)
- Ensure instrument is powered on

**Raw Command Not Working**
- Verify escape sequences: Use `\\n` in test plan, converts to `\n` at runtime
- Check command syntax against APS-7000 programming manual
- Test command manually via VISA interactive tool

**Channel Validation Failures**
- Current measurements: Use channels ending in 21 or 22
- Other measurements: Use channels 01-20
- Check channel format: `"205"` or `"(101, 102, 103)"`

**Measurement Timeouts**
- Temperature measurements take 2+ seconds
- Some power source measurements may require settling time
- Increase subprocess timeout accordingly

**Type Error for VOLT/CURR**
- Must specify `Type: 'AC'` or `Type: 'DC'` in args dict
- Error: "Error : no type setting!(AC/DC)"

---

## Version History

- **Current**: Supports all measurement functions plus raw SCPI command execution
- **Notes**: Extended from 34970A driver with additional raw command capability
