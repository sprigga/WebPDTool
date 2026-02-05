# PSW3072 API Analysis

## Overview

PSW3072.py is an instrument driver for the PSW30-72 programmable power supply. It provides basic voltage and current control using SCPI commands over a serial/network interface. This is a simplified driver that focuses on output control without query/readback capabilities.

**File Location:** `src/lowsheen_lib/PSW3072.py`
**Dependencies:**
- `remote_instrument.instrument_iniSetting` - Instrument connection manager
- `sys`, `ast`, `time` - Standard libraries

## Architecture

```
PSW3072.py
├── get_cmd_string()        # SCPI command formatter
├── send_command()          # Low-level command sender
├── remote_instrument()     # Main control function
├── initial()               # Output disable function
└── __main__                # CLI entry point (standalone mode)
```

## Core Functions

### 1. get_cmd_string(SetVolt, SetCurr)

Formats SCPI commands for voltage and current settings.

**Parameters:**
- `SetVolt` (str): Voltage value (e.g., "12.5")
- `SetCurr` (str): Current value (e.g., "2.0")

**Returns:**
- `tuple[str, str]`: (voltage_command, current_command)
  - Example: `("VOLT 12.5", "CURR 2.0")`

**Implementation:**
```python
def get_cmd_string(SetVolt, SetCurr):
    remote_Voltcmd = f"VOLT {SetVolt}"
    remote_Currcmd = f"CURR {SetCurr}"
    return remote_Voltcmd, remote_Currcmd
```

**SCPI Commands:**
- `VOLT <value>` - Set output voltage
- `CURR <value>` - Set current limit

---

### 2. send_command(instrument, command)

Sends a SCPI command to the instrument with proper formatting.

**Parameters:**
- `instrument`: Serial/VISA instrument object (from `instrument_iniSetting`)
- `command` (str): SCPI command without terminator

**Behavior:**
- Appends `\n` terminator to command
- Encodes to bytes before sending
- Waits 0.1 seconds after transmission

**Implementation:**
```python
def send_command(instrument, command):
    command += '\n'
    instrument.write(command.encode())
    time.sleep(0.1)
```

**Note:** The 0.1s delay ensures command processing before next operation.

---

### 3. remote_instrument(instrument, SetVolt, SetCurr)

Main control function that sets voltage/current or disables output.

**Parameters:**
- `instrument`: Instrument connection object
- `SetVolt` (str): Target voltage
- `SetCurr` (str): Target current limit

**Returns:**
- `1` (int) on success
- `str`: Error message if command validation fails

**Behavior:**

**Case 1: Disable Output** (Both parameters = "0")
```python
SetVolt='0', SetCurr='0' → Sends "OUTP OFF"
```

**Case 2: Set Voltage/Current**
```python
SetVolt='12', SetCurr='3' →
  1. Send "VOLT 12"
  2. Send "CURR 3"
  3. Send "OUTP ON"
```

**Implementation:**
```python
def remote_instrument(instrument, SetVolt, SetCurr):
    instrument.timeout = 1
    remote_Voltcmd, remote_Currcmd = get_cmd_string(SetVolt, SetCurr)

    if remote_Voltcmd is None or remote_Currcmd is None:
        return "Error : remote command is wrong"

    if SetVolt == '0' and SetCurr == '0':
        outputoff_msg = 'OUTP OFF'
        send_command(instrument, outputoff_msg)
    else:
        send_command(instrument, remote_Voltcmd)
        send_command(instrument, remote_Currcmd)
        outputon_msg = 'OUTP ON'
        send_command(instrument, outputon_msg)

    errors = []
    if errors:
        return f"PSW30-72 set {' and '.join(errors)} fail"
    else:
        return 1
```

**Note:** `errors` list is currently unused - error handling placeholder.

---

### 4. initial(instrument)

Disables power supply output during cleanup or initialization.

**Parameters:**
- `instrument`: Instrument connection object

**Returns:**
- None (implicit)

**SCPI Command:**
- `OUTP OFF` - Disable output

**Implementation:**
```python
def initial(instrument):
    outputoff_msg = 'OUTP OFF'
    send_command(instrument, outputoff_msg)
```

**Usage Context:** Called during `--final` sequence for instrument cleanup.

---

## Standalone Execution (CLI Mode)

### Command-Line Interface

**Format:**
```bash
python PSW3072.py <sequence> <parameters_dict>
```

**Parameters:**

1. **sequence** (sys.argv[1])
   - `--final`: Cleanup mode (disable output)
   - Any other: Normal operation mode

2. **parameters_dict** (sys.argv[2])
   - String representation of Python dictionary
   - Parsed using `ast.literal_eval()`

**Required Dictionary Keys:**
- `Instrument` (str): Instrument identifier from test_xml.ini
- `SetVolt` (str): Voltage value
- `SetCurr` (str): Current value

### Example Usage

**Example 1: Set 12V, 3A**
```bash
python PSW3072.py normal "{'Instrument': 'PSW3072_1', 'SetVolt': '12', 'SetCurr': '3'}"
```

**Example 2: Disable Output**
```bash
python PSW3072.py normal "{'Instrument': 'PSW3072_1', 'SetVolt': '0', 'SetCurr': '0'}"
```

**Example 3: Cleanup**
```bash
python PSW3072.py --final "{'Instrument': 'PSW3072_1'}"
```

### CLI Implementation

```python
if __name__ == "__main__":
    sequence = sys.argv[1]
    args = sys.argv[2]
    args = ast.literal_eval(args)  # Convert string to dict

    Instrument_value = args.get('Instrument', '')
    SetVolt = args.get('SetVolt', '')
    SetCurr = args.get('SetCurr', '')

    instrument = instrument_iniSetting(Instrument_value)

    if sequence == '--final':
        response = initial(instrument)
    elif SetVolt == '0' and SetCurr == '0':
        response = remote_instrument(instrument, SetVolt, SetCurr)
    else:
        response = remote_instrument(instrument, SetVolt, SetCurr)

    print(response)
```

**Output:**
- `1` on success
- Error message on failure

---

## SCPI Command Reference

### Commands Used

| Command | Description | Parameters |
|---------|-------------|------------|
| `VOLT <value>` | Set output voltage | Voltage in volts (numeric) |
| `CURR <value>` | Set current limit | Current in amps (numeric) |
| `OUTP ON` | Enable output | None |
| `OUTP OFF` | Disable output | None |

### Command Sequence

**Power ON Sequence:**
```
1. VOLT <value>
2. CURR <value>
3. OUTP ON
```

**Power OFF Sequence:**
```
1. OUTP OFF
```

**Note:** No queries (*IDN?, MEAS:VOLT?, etc.) are implemented.

---

## Configuration

Instrument connections are configured in `test_xml.ini`:

```ini
[Setting]
PSW3072_1 = TCPIP0::192.168.1.100::5025::SOCKET
PSW3072_2 = COM3/baud:115200
```

**Supported Connection Types:**
- TCPIP Socket (e.g., `TCPIP0::IP::PORT::SOCKET`)
- Serial (e.g., `COM3/baud:115200`)

Connection setup is handled by `remote_instrument.instrument_iniSetting()`.

---

## Error Handling

### Current Implementation

- **Command Validation:** Checks if command strings are None
- **Timeout:** Sets 1-second timeout on instrument object
- **Error List:** Placeholder `errors = []` (unused)

### Limitations

1. **No Exception Handling:** No try-except blocks
2. **No Connection Validation:** Assumes instrument is connected
3. **No Command Verification:** No error checking after SCPI commands
4. **No Value Validation:** No range checking for voltage/current values

### Potential Failures

| Scenario | Behavior |
|----------|----------|
| Invalid voltage/current | Silent failure (sent to instrument) |
| Connection lost | Python exception (unhandled) |
| Instrument error | No detection (no error queries) |
| Timeout | Python exception (unhandled) |

**Recommendation:** Add try-except blocks and error queries (SYST:ERR?) for production use.

---

## Integration with PDTool4

### Usage in Test Framework

The driver is called from measurement modules (e.g., PowerSetMeasurement.py):

```python
# Example: PowerSetMeasurement.py
subprocess.run([
    'python', 'src/lowsheen_lib/PSW3072.py',
    'normal',
    str({'Instrument': 'PSW3072_1', 'SetVolt': '12', 'SetCurr': '3'})
])
```

### Cleanup Sequence

During test finalization:

```python
subprocess.run([
    'python', 'src/lowsheen_lib/PSW3072.py',
    '--final',
    str({'Instrument': 'PSW3072_1'})
])
```

### Return Value Handling

```python
result = subprocess.run(..., capture_output=True, text=True)
if result.stdout.strip() == '1':
    # Success
else:
    # Error (stdout contains error message)
```

---

## Design Patterns

### Strengths

1. **Simple API:** Clear function signatures
2. **String Parameters:** Easy to pass via command line
3. **Dual Mode:** Normal + cleanup (--final)
4. **State Machine:** Handles "0,0" as special disable state

### Weaknesses

1. **No Error Handling:** Missing exception handling
2. **No Validation:** No parameter range checks
3. **No Readback:** Cannot verify settings
4. **No Status Queries:** Cannot check instrument errors
5. **Hard-coded Delays:** 0.1s delay may not suit all instruments

### Comparison with Other Drivers

| Feature | PSW3072 | IT6723C | 2260B |
|---------|---------|---------|-------|
| Query Support | ❌ No | ✅ Yes | ✅ Yes |
| Error Handling | ❌ Basic | ✅ Comprehensive | ✅ Comprehensive |
| Parameter Validation | ❌ No | ✅ Yes | ✅ Yes |
| Return Values | Int/String | Complex Dict | Complex Dict |

---

## Best Practices

### When Using This Driver

1. **Always handle return values:**
   ```python
   result = remote_instrument(inst, '12', '3')
   if result != 1:
       print(f"Power supply error: {result}")
   ```

2. **Always call cleanup:**
   ```python
   try:
       remote_instrument(inst, '12', '3')
       # ... test code ...
   finally:
       initial(inst)  # Disable output
   ```

3. **Validate parameters before calling:**
   ```python
   voltage = float(SetVolt)  # Will raise ValueError if invalid
   assert 0 <= voltage <= 72, "Voltage out of range"
   ```

4. **Add external timeout:**
   ```python
   import signal
   signal.alarm(5)  # 5-second timeout
   result = remote_instrument(inst, '12', '3')
   signal.alarm(0)
   ```

---

## Future Enhancements

### Recommended Improvements

1. **Add Query Functions:**
   ```python
   def query_voltage(instrument):
       return instrument.query('MEAS:VOLT?')

   def query_current(instrument):
       return instrument.query('MEAS:CURR?')
   ```

2. **Add Error Handling:**
   ```python
   def remote_instrument(instrument, SetVolt, SetCurr):
       try:
           # ... existing code ...
           error = instrument.query('SYST:ERR?')
           if 'No error' not in error:
               return f"Instrument error: {error}"
       except Exception as e:
           return f"Communication error: {str(e)}"
   ```

3. **Add Parameter Validation:**
   ```python
   VOLT_RANGE = (0, 72)
   CURR_RANGE = (0, 20)

   def validate_params(volt, curr):
       v = float(volt)
       c = float(curr)
       assert VOLT_RANGE[0] <= v <= VOLT_RANGE[1]
       assert CURR_RANGE[0] <= c <= CURR_RANGE[1]
   ```

4. **Add Verification:**
   ```python
   send_command(instrument, f'VOLT {SetVolt}')
   time.sleep(0.5)
   actual = instrument.query('VOLT?')
   if abs(float(actual) - float(SetVolt)) > 0.1:
       return f"Voltage setting failed: expected {SetVolt}, got {actual}"
   ```

---

## Appendix: Code Comments

### Original Code Comments

```python
# Line 23: Commented function call
# instrument_initial(instrument)
```

**Interpretation:** `instrument_initial()` (reset function) is intentionally disabled - PSW3072 may not need reset on connection.

### Unused Code Block

```python
# Lines 35-37: Empty errors list
errors = []
if errors:
    return f"PSW30-72 set {' and '.join(errors)} fail"
```

**Interpretation:** Error collection mechanism exists but is not implemented. This is a placeholder for future error detection.

---

## Summary

**PSW3072.py Characteristics:**

✅ **Strengths:**
- Simple, easy-to-understand API
- Fast execution (no queries)
- CLI-friendly for subprocess integration
- Clear command formatting

⚠️ **Limitations:**
- No error handling
- No parameter validation
- No measurement queries
- No verification of settings

**Use Case:** Suitable for simple power supply control in test environments where:
- Speed is prioritized over verification
- External monitoring handles error detection
- Parameter validation is done by caller
- Test plans specify safe voltage/current values

**For Production:** Consider adding error handling, validation, and query capabilities.
