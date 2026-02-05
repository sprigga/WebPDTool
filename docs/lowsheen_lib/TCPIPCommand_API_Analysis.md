# TCPIPCommand.py API Analysis

## Overview

`TCPIPCommand.py` is a TCP/IP communication utility that sends binary commands to remote devices over TCP sockets with CRC32 checksum validation. It's designed for reliable communication with industrial test equipment and embedded systems.

**File Location:** `src/lowsheen_lib/TCPIPCommand.py`
**Module Type:** Command-line utility script
**Communication Protocol:** TCP/IP with CRC32 checksum
**Primary Use Case:** Sending binary protocol commands to test devices

---

## Core Functionality

### Main Features

1. **CRC32 Checksum Calculation** - Ensures data integrity during transmission
2. **Binary Protocol Support** - Handles hexadecimal byte commands
3. **Timeout Management** - 5-second socket timeout for reliability
4. **Response Handling** - Reads and parses device responses as hexadecimal strings
5. **Command-line Interface** - Integrates with PDTool4's subprocess execution pattern

---

## API Reference

### Functions

#### `calculate_crc32(data: bytes) -> int`

Calculates CRC32 checksum of binary data.

**Parameters:**
- `data` (bytes): Binary data to calculate checksum for

**Returns:**
- `int`: CRC32 checksum value

**Implementation:**
```python
def calculate_crc32(data):
    """
    Calculate CRC32 checksum of the data
    """
    return binascii.crc32(data)
```

**Example:**
```python
message = bytes([0x31, 0x03, 0xf0, 0x00, 0x00])
checksum = calculate_crc32(message)
# checksum: integer CRC32 value
```

---

#### `read_response(sock, buffer_size=1024, delimiter=b'\n') -> str`

Reads response from TCP socket and converts to hexadecimal string format.

**Parameters:**
- `sock` (socket.socket): Connected TCP socket object
- `buffer_size` (int, optional): Maximum bytes to receive per read operation. Default: 1024
- `delimiter` (bytes, optional): Response terminator byte sequence. Default: `b'\n'`

**Returns:**
- `str`: Hexadecimal string representation of received data (space-separated bytes)

**Behavior:**
- Reads data from socket until no more data is available or delimiter is found
- Converts binary response to hex string format: `"31 03 f0 00 00"`
- Returns empty string if no data received
- Breaks after first non-empty response

**Example:**
```python
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('192.168.1.3', 12345))
response = read_response(sock)
# response: "a1 b2 c3 d4"
```

**Note:** The commented-out print statements suggest this function was previously used for debugging response parsing.

---

#### `main(TCP_IP: str, TCP_PORT: int, MESSAGE: bytes) -> str`

Main function that establishes TCP connection, sends command with CRC32, and receives response.

**Parameters:**
- `TCP_IP` (str): Target device IP address (e.g., `'192.168.1.3'`)
- `TCP_PORT` (int): Target device TCP port (e.g., `12345`)
- `MESSAGE` (bytes): Binary command to send (without CRC32)

**Returns:**
- `str`: Hexadecimal string representation of device response (space-separated bytes)
- Empty string `''` if connection or communication fails

**Process Flow:**
1. Calculate CRC32 checksum of MESSAGE
2. Append CRC32 to MESSAGE (4 bytes, big-endian)
3. Create TCP socket and connect to device
4. Send MESSAGE_WITH_CRC
5. Set 5-second socket timeout
6. Read response from device
7. Close socket
8. Return response as hex string

**Error Handling:**
- Catches all exceptions and prints error message
- Always closes socket in finally block
- Returns empty string on error

**Example:**
```python
response = main('192.168.1.3', 12345, bytes([0x31, 0x01, 0xf0, 0x00, 0x00]))
# response: "32 04 f1 01 01" (example device response)
```

---

## Command-Line Interface

### Usage

```bash
python src/lowsheen_lib/TCPIPCommand.py <test_name> <params_json>
```

### Parameters

**sys.argv[1]:** Test name identifier (not used in current implementation)
**sys.argv[2]:** JSON-like dictionary string with the following keys:

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `Command` | string | Yes | Format: `"<IP> <PORT> <BYTES>"` where BYTES are semicolon-separated hex values |
| `Timeout` | string/float | No | Socket timeout in seconds. Default: 1.0 (note: hardcoded to 5s in code) |

### Command Format

The `Command` parameter must follow this pattern:
```
"<IP_ADDRESS> <PORT> <BYTE1>;<BYTE2>;<BYTE3>;..."
```

**Example:**
```
"192.168.1.3 12345 31;01;f0;00;00"
```

This translates to:
- **IP:** 192.168.1.3
- **Port:** 12345
- **Message bytes:** [0x31, 0x01, 0xf0, 0x00, 0x00]

### Example Invocations

#### Basic Command Execution
```bash
python src/lowsheen_lib/TCPIPCommand.py eth_test \
  "{'ItemKey': 'FT00-077', 'ValueType': 'string', 'LimitType': 'none', 'EqLimit': '', 'ExecuteName': 'CommandTest', 'case': 'tcpip', 'Command': '192.168.1.3 12345 31;01;f0;00;00', 'Timeout': '10'}"
```

#### Output Format
```
32 04 f1 01 01
```
(Hexadecimal response from device, space-separated bytes)

#### Error Cases

**Missing Parameters:**
```bash
python src/lowsheen_lib/TCPIPCommand.py eth_test \
  "{'Command': '192.168.1.3'}"
```
Output: `Parameter Lack`

**Connection Failure:**
```bash
python src/lowsheen_lib/TCPIPCommand.py eth_test \
  "{'Command': '192.168.1.99 12345 31;01;f0;00;00'}"
```
Output: `Error: [Errno 111] Connection refused`
(followed by empty string response)

---

## Protocol Details

### Message Structure

**Outgoing Message:**
```
[MESSAGE_BYTES] + [CRC32_4_BYTES]
```

**Example:**
- Original MESSAGE: `31 01 f0 00 00`
- CRC32 (big-endian): `a3 b2 c1 d0` (example)
- Sent MESSAGE_WITH_CRC: `31 01 f0 00 00 a3 b2 c1 d0`

### CRC32 Checksum

- **Algorithm:** Standard CRC32 (binascii.crc32)
- **Byte Order:** Big-endian (network byte order)
- **Length:** 4 bytes
- **Position:** Appended to end of message

### Socket Configuration

- **Socket Type:** TCP/IP (SOCK_STREAM)
- **Address Family:** AF_INET (IPv4)
- **Timeout:** 5 seconds (hardcoded in line 76)
- **Buffer Size:** 1024 bytes per receive operation

---

## Integration with PDTool4

### Test Plan CSV Configuration

This utility is typically invoked from CommandTest measurements with the following CSV configuration:

| Column | Example Value |
|--------|---------------|
| ExecuteName | `CommandTest` |
| case | `tcpip` |
| Command | `192.168.1.3 12345 31;01;f0;00;00` |
| Timeout | `10` |

### Execution Flow

```
CommandTestMeasurement.py
    ↓ (subprocess.run)
uv run python src/lowsheen_lib/TCPIPCommand.py <test_name> <params_json>
    ↓
TCP/IP communication with device
    ↓
Print hexadecimal response to stdout
    ↓
CommandTestMeasurement captures stdout and validates response
```

---

## Code Quality Notes

### Strengths
- ✅ CRC32 checksum ensures data integrity
- ✅ Proper socket cleanup with try/finally
- ✅ Timeout prevents indefinite blocking
- ✅ Hexadecimal output format is human-readable for debugging

### Areas for Improvement

#### 1. Unused Imports
```python
# Lines 1-3: Unused imports
import sys      # Used
import ast      # Used
import subprocess  # NOT USED - can be removed
```

#### 2. Duplicate Import
```python
# Line 1 and Line 5 both import sys
import sys  # Duplicate
```

#### 3. Timeout Inconsistency
The `Timeout` parameter is parsed from args but never used. Socket timeout is hardcoded:
```python
# Line 103: Timeout parsed but ignored
timeout = float(args['Timeout']) if 'Timeout' in args else 1.0

# Line 76: Hardcoded 5 second timeout
sock.settimeout(5)
```

**Recommendation:** Use the parsed timeout value:
```python
sock.settimeout(timeout)
```

#### 4. Incomplete Error Response Handling
The `read_response()` function has commented-out debugging code that suggests incomplete implementation:
```python
# Lines 30-34: Commented debugging code
# response += hex_string
# try:
# print("Raw response:",hex_spaced_string)
# except:
# print("Raw response:"+response.decode('utf-8'))
```

#### 5. Parameter Validation
Missing validation for:
- IP address format
- Port range (1-65535)
- Byte values (0x00-0xFF)

**Recommendation:**
```python
if len(CommandList) < 3:
    response = "Parameter Lack"
elif not (1 <= TCP_PORT <= 65535):
    response = "Invalid port number"
else:
    # Proceed with connection
```

---

## Security Considerations

### Potential Vulnerabilities

1. **No Input Validation**
   - IP address is not validated (could be malformed)
   - Port number could be out of valid range
   - Byte values are not range-checked

2. **Error Information Disclosure**
   - Line 81: `print("Error:", e)` exposes full exception details
   - Could reveal network topology or system information

3. **Socket Resource Exhaustion**
   - No connection pooling or rate limiting
   - Rapid invocations could exhaust system sockets

4. **No Authentication/Encryption**
   - Communication is plaintext over TCP
   - CRC32 provides integrity but not confidentiality
   - No device authentication mechanism

### Recommendations for Production Use

1. Validate all inputs (IP, port, byte values)
2. Implement connection retry logic with exponential backoff
3. Consider TLS/SSL for sensitive communications
4. Add authentication mechanism if supported by device
5. Implement rate limiting for repeated invocations
6. Log errors to file instead of stdout for security

---

## Usage Examples

### Example 1: Power On Command
```python
# Command: Power on device at 192.168.1.10:5000
# Message: [0x50, 0x4F, 0x57, 0x31]  # "POW1" in hex

response = main('192.168.1.10', 5000, bytes([0x50, 0x4F, 0x57, 0x31]))
# Expected response: "4F 4B" (ASCII "OK")
```

### Example 2: Read Status Command
```python
# Command: Read status from device at 192.168.1.3:12345
# Message: [0x31, 0x01, 0xf0, 0x00, 0x00]

response = main('192.168.1.3', 12345, bytes([0x31, 0x01, 0xf0, 0x00, 0x00]))
# Expected response: "32 01 00 01 05" (example status bytes)
```

### Example 3: Command-Line Test
```bash
# From PDTool4 test plan execution
uv run python src/lowsheen_lib/TCPIPCommand.py eth_test \
  "{'ItemKey': 'COMM-001', 'Command': '192.168.1.3 12345 31;03;f0;00;00', 'Timeout': '5'}"

# Expected stdout:
# 32 04 f1 01 01
```

---

## Related Files

- **CommandTestMeasurement.py** - Measurement class that invokes this script
- **ConSoleCommand.py** - Similar utility for serial port commands
- **src/lowsheen_lib/proto_utils.py** - Protocol buffer utilities for structured messages

---

## Version History

**Current Version:** 1.0 (inferred from code analysis)

**Known Issues:**
- Timeout parameter is parsed but not used (hardcoded to 5 seconds)
- Duplicate sys import
- Unused subprocess import
- No input validation

---

## Testing Recommendations

### Unit Tests Needed

1. **CRC32 Calculation**
   ```python
   def test_crc32_known_values():
       assert calculate_crc32(b'\x31\x03\xf0\x00\x00') == expected_value
   ```

2. **Response Parsing**
   ```python
   def test_read_response_hex_format():
       # Mock socket with known data
       response = read_response(mock_socket)
       assert response == "31 03 f0"
   ```

3. **Parameter Parsing**
   ```python
   def test_command_parsing():
       cmd = "192.168.1.3 12345 31;01;f0"
       # Test parsing logic
   ```

4. **Error Handling**
   ```python
   def test_connection_refused():
       response = main('192.168.1.99', 99999, bytes([0x00]))
       assert response == ""
   ```

---

## Conclusion

`TCPIPCommand.py` provides essential TCP/IP communication functionality for PDTool4's test equipment control. While the core functionality is solid, the implementation would benefit from:

1. Input validation and sanitization
2. Using the parsed timeout parameter
3. Removing unused/duplicate imports
4. Adding comprehensive error handling
5. Implementing unit tests

The CRC32 checksum feature is particularly valuable for ensuring data integrity in industrial environments where communication reliability is critical.
