# ComPortCommand API Analysis

## Overview

**File**: `src/lowsheen_lib/ComPortCommand.py`

**Purpose**: Command-line interface driver for serial port (COM port) communication with test devices, supporting configurable timeouts, multi-line responses, and response file logging

**Instrument Type**: Generic serial communication interface for devices like Arduino, Modbus devices, custom test fixtures, and embedded systems

---

## Command-Line Interface

### Usage

```bash
python src/lowsheen_lib/ComPortCommand.py <sequence> <args_dict>
```

### Parameters

- **sequence** (str): Operation mode
  - `--final`: Reset device (sends `*RST\n` and `OUTP OFF\n`)
  - Any other value: Execute command and read response

- **args_dict** (str): Python dictionary literal as string containing:
  - `Port` (str, required): COM port name (e.g., "COM9", "/dev/ttyUSB0")
  - `Baud` (str, required): Baud rate (e.g., "115200", "9600")
  - `Command` (str, optional): Command to send (supports escape sequences)
  - `ComportWait` (str, optional): Delay after opening port (seconds), default: 0
  - `Timeout` (str, optional): Read timeout (seconds), default: 3
  - `ReslineCount` (str, optional): Expected number of response lines, default: auto-detect
  - `content` (str, optional): File path to save response

### Example

```bash
# Send hex command to Arduino, wait 2 seconds after connection, read 10 lines
python ComPortCommand.py "" "{'Port': 'COM9', 'Baud': '115200', 'Command': '0xAA 0x06\\n', 'ComportWait': '2', 'Timeout': '5', 'ReslineCount': '10'}"

# Send text command and save response to file
python ComPortCommand.py "" "{'Port': '/dev/ttyUSB0', 'Baud': '9600', 'Command': 'READ STATUS\\n', 'content': '/tmp/status.txt'}"

# Reset device
python ComPortCommand.py "--final" "{'Port': 'COM9', 'Baud': '115200'}"
```

---

## Core Functions

### get_response(ser, timeout, ReslineCount)

Reads multi-line response from serial port with configurable termination logic.

**Parameters:**
- `ser` (serial.Serial): Opened serial port object
- `timeout` (float): Maximum time to wait for complete response (seconds)
- `ReslineCount` (int or ''): Expected number of lines, or empty string for auto-detect

**Returns:**
- `str`: Concatenated response lines separated by `\n`

**Behavior:**
- **Fixed line count mode** (`ReslineCount` is integer):
  - Reads exactly `ReslineCount` lines
  - Stops when count reached

- **Auto-detect mode** (`ReslineCount` is empty string):
  - Reads until 3 consecutive empty read attempts (300ms total)
  - Useful when response length is variable

**Timeout Logic:**
- Hard timeout: Stops after `timeout` seconds
- Soft timeout (auto-detect only): 3 consecutive empty reads with 0.1s intervals

**Example:**
```python
# Fixed line count
response = get_response(ser, 5.0, 10)  # Read exactly 10 lines, max 5 seconds

# Auto-detect
response = get_response(ser, 3.0, '')  # Read until data stops, max 3 seconds
```

**Response Format:**
```python
"Line 1\nLine 2\nLine 3"
```

---

### comport_send(ser, comport_command, timeout, ReslineCount)

**DEPRECATED** - Original implementation, replaced by `smh_write_command` + `smh_get_response`

Sends command and reads response in single operation.

**Parameters:**
- `ser` (serial.Serial): Opened serial port object
- `comport_command` (str): Command string to send
- `timeout` (float): Read timeout (seconds)
- `ReslineCount` (int or ''): Expected response lines

**Returns:**
- `str`: Response from device

**Behavior:**
- Sets `ser.timeout = timeout`
- Sends command as UTF-8 encoded bytes
- Calls `get_response()` to read reply
- Closes serial port after reading

**Status**: Commented out in main execution (line 129), kept for backward compatibility

---

### smh_write_command(ser, comport_command, timeout, ReslineCount)

Sends command to serial device (newer implementation, added 2024-07-05).

**Parameters:**
- `ser` (serial.Serial): Opened serial port object
- `comport_command` (str): Command string to send
- `timeout` (float): Not used (kept for signature compatibility)
- `ReslineCount` (int or ''): Not used (kept for signature compatibility)

**Returns:**
- `None`

**Behavior:**
- Encodes command as UTF-8 bytes
- Writes to serial port
- Flushes output buffer
- Waits 50ms for command processing
- Does NOT read response (see `smh_get_response`)

**Example:**
```python
smh_write_command(ser, "READ VOLTAGE\n", 3.0, 10)
time.sleep(0.5)  # Additional settling time if needed
```

---

### smh_get_response(ser)

Reads single line response from serial device (newer implementation, added 2024-07-05).

**Parameters:**
- `ser` (serial.Serial): Opened serial port object

**Returns:**
- `str`: Single line response decoded as UTF-8
- `None`: If no data available or serial port closed

**Behavior:**
- Reads one line via `ser.readline()`
- Decodes as UTF-8
- Closes serial port after reading

**Example:**
```python
response = smh_get_response(ser)  # "OK\n" or "12.345\n"
```

**Note**: Unlike `get_response()`, this reads only ONE line. For multi-line responses, call multiple times or use the deprecated `comport_send()`.

---

### comport_initial(ser)

Resets device to default state (power supply reset pattern).

**Parameters:**
- `ser` (serial.Serial): Opened serial port object

**Behavior:**
- Sends `*RST\n` (SCPI reset command)
- Sends `OUTP OFF\n` (disable output)
- Does not close port

**Example:**
```python
comport_initial(ser)
# Device now in reset state with output disabled
```

---

## Data Flow

```
Command-line invocation
    ↓
Parse sys.argv[1] (sequence) and sys.argv[2] (args dict)
    ↓
Extract parameters: Port, Baud, Command, ComportWait, Timeout, ReslineCount, content
    ↓
Process escape sequences: \\n → \n in Command
    ↓
Try open serial port: serial.Serial(Port, Baud, timeout=1)
    ↓
    └─ Failure → Print error, exit(10)
    ↓
Wait ComportWait seconds (for device initialization)
    ↓
    ┌─ sequence == '--final' → comport_initial(ser)
    │
    └─ else → smh_write_command(ser, command, timeout, ReslineCount)
               ↓
               time.sleep(0.5)  # Wait for device processing
               ↓
               smh_get_response(ser) → response
    ↓
If content parameter provided:
    └─ Write response to file
    ↓
print(response) → Stdout
```

---

## Serial Port Configuration

### Automatic Settings (Not Configurable)

The driver uses these hardcoded serial port settings:

```python
serial.Serial(
    port=comport_name,
    baudrate=comport_baudrate,
    timeout=1,           # Fixed 1-second timeout for serial operations
    bytesize=8,          # 8 data bits (default)
    parity='N',          # No parity (default)
    stopbits=1,          # 1 stop bit (default)
    xonxoff=False,       # No software flow control (default)
    rtscts=False,        # No hardware flow control (default)
    dsrdtr=False         # No DSR/DTR flow control (default)
)
```

**If you need different settings**, modify the `serial.Serial()` call on line 120.

---

## Command Format

### Escape Sequences

The driver automatically converts string literal escape sequences:

```python
'\\n' → '\n' (newline)
'\\r' → Not handled, send as '\\r' if needed
'\\t' → Not handled
```

**In Test Plans:**
```csv
Command
READ VOLTAGE\\n        # Becomes: "READ VOLTAGE\n"
*IDN?\\n               # Becomes: "*IDN?\n"
0xAA 0x06\\n           # Becomes: "0xAA 0x06\n"
```

### Hex Command Format

For binary protocols, format as string:
```
0xAA 0x06 0x00 0x00\\n
```

The device firmware must parse this ASCII representation. For true binary data, modify the driver to handle `bytes.fromhex()`.

---

## Response Handling

### Auto-Detect Mode (ReslineCount='')

**Use when:**
- Response length varies by command
- Device sends variable number of lines
- Response ends with natural pause

**Example:**
```
Command: "GET STATUS\n"
Response: "STATUS OK\nVOLTAGE: 12.5V\nCURRENT: 0.5A\n"
```

Driver reads until 3 consecutive empty attempts (300ms silence).

### Fixed Line Count Mode (ReslineCount=N)

**Use when:**
- Response always has fixed number of lines
- Faster than auto-detect (no waiting for timeout)
- Critical for high-speed testing

**Example:**
```
Command: "READ ADC\n"
Response: "12345\n" (always 1 line)
ReslineCount: 1
```

### Timeout Calculation

**Recommended timeout formula:**
```
Timeout = (Expected_Lines × Line_Processing_Time) + Safety_Margin

Example:
- 10 lines × 0.1s/line + 2s safety = 3 seconds
```

---

## File Output

When `content` parameter is provided, response is written to file:

```python
args = {
    'Port': 'COM9',
    'Baud': '115200',
    'Command': 'DUMP LOG\\n',
    'content': 'C:/logs/device_log.txt'  # Windows path
}
```

**Behavior:**
- Creates/overwrites file at specified path
- Writes raw response string (including newlines)
- Catches `WindowsError` only (Linux errors not caught)
- File write does NOT affect stdout output

**Use cases:**
- Save large responses (log dumps, calibration data)
- Persist responses for later analysis
- Separate pass/fail logic from data collection

---

## Error Handling

### Exit Codes
- **Exit 10**: Serial port connection failed
- **Exit 0**: Normal completion (silent exit on unhandled exceptions - line 143)

### Error Messages (Printed to Stdout)
- `"Failed to connect to the serial port"` - Port doesn't exist or in use

### Exception Handling

**Connection Errors (line 119-124):**
```python
try:
    ser = serial.Serial(comport_name, comport_baudrate, timeout=1)
except:
    print("Failed to connect to the serial port")
    sys.exit(10)
```

**Execution Errors (line 141-143):**
```python
except Exception as e:
    print(e)
    sys.exit()  # Silent exit, no error code
```

**File Write Errors (line 139-140):**
```python
except WindowsError as e:
    print(f"Error reading from the registry: {e}")  # Misleading error message
```

---

## Integration with PDTool4

### Test Plan Configuration

In CSV test plans, configure serial communication:

**Simple command:**
```csv
Port,Baud,Command,ComportWait,Timeout,ReslineCount
COM9,115200,READ STATUS\\n,0,3,1
```

**Arduino with initialization delay:**
```csv
Port,Baud,Command,ComportWait,Timeout,ReslineCount
COM5,9600,GET DATA\\n,2,5,10
```

**Save response to file:**
```csv
Port,Baud,Command,ComportWait,Timeout,ReslineCount,content
COM9,115200,DUMP LOG\\n,0,10,,C:/logs/test.txt
```

### Subprocess Invocation Pattern

**Standard command:**
```python
import subprocess
import json

args = {
    'Port': 'COM9',
    'Baud': '115200',
    'Command': 'READ VOLTAGE\\n',
    'ComportWait': '0',
    'Timeout': '3',
    'ReslineCount': '1'
}

result = subprocess.run(
    ['python', 'src/lowsheen_lib/ComPortCommand.py', '', str(args)],
    capture_output=True,
    text=True
)

response = result.stdout.strip()  # "12.345"
exit_code = result.returncode      # 0 = success, 10 = connection failed
```

**With file output:**
```python
args = {
    'Port': 'COM9',
    'Baud': '115200',
    'Command': 'GET CALIBRATION\\n',
    'content': '/tmp/cal_data.txt'
}

result = subprocess.run(
    ['python', 'src/lowsheen_lib/ComPortCommand.py', '', str(args)],
    capture_output=True,
    text=True
)

# Response in both stdout AND file
with open('/tmp/cal_data.txt', 'r') as f:
    cal_data = f.read()
```

### Cleanup Protocol

Always call with `--final` after test sequence:

```python
subprocess.run([
    'python', 'src/lowsheen_lib/ComPortCommand.py',
    '--final',
    str({'Port': 'COM9', 'Baud': '115200'})
])
```

---

## Device-Specific Examples

### Arduino Communication

```python
# Arduino takes 2 seconds to boot after serial connection opens
args = {
    'Port': 'COM5',
    'Baud': '9600',
    'Command': 'READ_SENSORS\\n',
    'ComportWait': '2',      # Wait for Arduino bootloader
    'Timeout': '5',
    'ReslineCount': '5'      # 5 sensor values
}
```

### Modbus RTU Device

```python
# Hex command for Modbus (as ASCII string)
args = {
    'Port': '/dev/ttyUSB0',
    'Baud': '19200',
    'Command': '01 03 00 00 00 0A C5 CD\\n',  # Read holding registers
    'ComportWait': '0',
    'Timeout': '2',
    'ReslineCount': '1'
}
```

### Custom Test Fixture

```python
# Multi-line response with variable length
args = {
    'Port': 'COM7',
    'Baud': '115200',
    'Command': 'RUN SELFTEST\\n',
    'ComportWait': '0',
    'Timeout': '10',
    'ReslineCount': ''       # Auto-detect (waits for silence)
}
```

---

## Dependencies

- `serial` (pySerial): Serial port communication
- `time`: Delays and timeouts
- `sys`: Command-line argument parsing and exit codes
- `ast.literal_eval`: Safe dictionary string parsing

---

## Limitations & Notes

1. **Fixed Serial Settings**: 8N1 format hardcoded, no support for 7E1, 7O1, etc.

2. **Binary Protocol Support**: Limited to ASCII representation of hex bytes

3. **Single Command Per Invocation**: Cannot send command sequences (open → command → close)

4. **Response Line Limit**: No maximum line count protection, device can cause memory issues

5. **Error Handling**:
   - File write error message misleading ("Error reading from the registry")
   - Silent exception exit without proper error reporting

6. **Port Close Timing**: Port closed in `get_response()` and `smh_get_response()`, may interfere with device cleanup

7. **Deprecated Function**: `comport_send()` still in codebase but unused (line 54-61)

---

## Implementation Notes (2024-07-05 Update)

### Why Two Response Functions?

The code was updated on 2024-07-05 by "polo" to split command sending and response reading:

**Old pattern (comport_send):**
```python
response = comport_send(ser, command, timeout, ReslineCount)
```

**New pattern (smh_write_command + smh_get_response):**
```python
smh_write_command(ser, command, timeout, ReslineCount)
time.sleep(0.5)  # Allow device processing time
response = smh_get_response(ser)
```

**Reason**: Allows manual delay insertion between command and response for devices requiring settling time.

### Debug Output

The code contains commented print statements for debugging:
```python
# print(f'get line_response: {line_response}')  # Line 24
# print(f'update response: {response}')          # Line 30 (ACTIVE)
# print(f'try {end_count} time: No data')       # Line 42
```

Line 30 is **active** - every line read is printed to stdout, which may interfere with response parsing if test code doesn't expect debug output.

---

## Troubleshooting

### Common Issues

**"Failed to connect to the serial port" Error**
- Verify port exists: `ls /dev/tty*` (Linux) or Device Manager (Windows)
- Check if port in use by another process
- Verify user has permissions (Linux: `sudo usermod -a -G dialout $USER`)
- Windows: Check COM port number in Device Manager

**Timeout Errors (No Response)**
- Increase `Timeout` parameter
- Check device is powered and responding
- Verify baud rate matches device configuration
- Use serial terminal (PuTTY, screen) to test manually

**Garbled Response**
- Check baud rate matches device
- Verify device uses 8N1 format (8 data bits, no parity, 1 stop bit)
- Check cable quality (especially for long runs)

**Arduino Won't Respond**
- Increase `ComportWait` to 2+ seconds (bootloader delay)
- Check Arduino Serial.begin() baud rate matches
- Verify Arduino sketch running and ready

**Incomplete Multi-Line Response**
- Use fixed `ReslineCount` if response length is known
- Increase `Timeout` for auto-detect mode
- Check device sends all lines within timeout period

**Response Contains Debug Output**
- Line 30 prints every line received
- Comment out: `# print(f'update response: {response}')`
- Rebuild if using compiled .exe

---

## Migration Guide

### From comport_send to smh_* Functions

If you have old code using `comport_send()`:

**Before:**
```python
response = comport_send(ser, "READ\\n", 3, 1)
```

**After:**
```python
smh_write_command(ser, "READ\\n", 3, 1)
time.sleep(0.5)  # Add settling time if needed
response = smh_get_response(ser)
```

### Adding Binary Protocol Support

To send true binary data (not ASCII hex):

```python
# Add new function
def send_binary_command(ser, hex_string):
    """Send binary command from hex string like 'AA0600'"""
    binary_data = bytes.fromhex(hex_string.replace(' ', ''))
    ser.write(binary_data)
    ser.flush()
    time.sleep(0.05)

# Usage
send_binary_command(ser, 'AA 06 00 00')
```

---

## Version History

- **2024-07-05**: Added `smh_write_command` and `smh_get_response` functions (by polo)
- **Prior**: Original implementation with `comport_send` function
- **Current**: Hybrid implementation with both old and new functions

---

## Related Documentation

- [remote_instrument.py](remote_instrument.md) - PyVISA instrument initialization (for VISA devices)
- [Test Plan CSV Format](../test_plan_format.md) - How to configure serial communication in test plans
