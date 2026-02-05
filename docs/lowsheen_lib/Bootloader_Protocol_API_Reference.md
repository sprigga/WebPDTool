# Bootloader Protocol API Reference

## Module: bootloader_messages.py

Complete reference for protocol message definitions and packet construction.

---

## Constants

### Global Protocol Constants

```python
MAX_WRITE_PAYLOAD_SIZE = 1024
```
Maximum data bytes allowed in a single WriteRequest payload.

```python
HEADER_SIZE = 5
```
Fixed size of message header (sync + opcode + length + header_checksum).

```python
MAX_PACKET_SIZE = 1034
```
Maximum total packet size (header + max payload + CRC + checksum).

```python
SYNC_CODE = 0xE7
```
Fixed synchronization byte at start of every message.

---

## Core Functions

### make_packet()

```python
def make_packet(fmt, op_code, length, *args) -> bytearray
```

Construct a binary protocol packet with checksums.

**Parameters:**
- `fmt` (struct.Struct): Binary format structure
- `op_code` (int): Message operation code (0x01-0xFF)
- `length` (int): Payload length in bytes
- `*args`: Variable arguments for payload data

**Returns:**
- `bytearray`: Complete packet with header and checksums

**Implementation Details:**
1. Calculates header checksum: `(SYNC_CODE + op_code + length_low + length_high) & 0xFF`
2. Packs header and payload using struct format
3. Calculates message checksum: `sum(all_bytes) & 0xFF`
4. Appends message checksum as last byte

**Example:**
```python
fmt = struct.Struct('!2B H B I B')  # Header + u32 + checksum
packet = make_packet(fmt, 0x03, 5, 65536, 0)
# Creates UpdateStartRequest for 64KB image
```

---

## Base Classes

### Header

Protocol message header parser.

#### Class Attributes

```python
Fmt = struct.Struct('!2B H B')
```
Binary format: sync(u8), op_code(u8), length(u16), header_checksum(u8)

```python
DataLength = 0
```
Header has no payload data.

```python
Type = namedtuple('Header', 'sync op_code length header_checksum')
```
Named tuple for parsed header fields.

#### Methods

##### extract()

```python
@classmethod
def extract(cls, msg: bytes) -> Header.Type
```

Parse header from raw message bytes.

**Parameters:**
- `msg` (bytes): Raw message data (minimum 5 bytes)

**Returns:**
- `Header.Type`: Named tuple with (sync, op_code, length, header_checksum)

**Example:**
```python
data = b'\xe7\x01\x00\x01\x46'
header = Header.extract(data)
print(header.op_code)  # 0x01
print(header.length)   # 1
```

---

## Request/Response Message Classes

All message classes follow this pattern:
- `Fmt`: struct.Struct for binary format
- `DataLength`: Payload size excluding header
- `Type`: namedtuple for parsed data
- `OpCode`: Message operation code
- `make()`: Create message packet
- `extract()`: Parse received message

---

### VersionRequest (0x01)

Query device version information.

#### Class Attributes

```python
Fmt = struct.Struct('!2B H B B')  # 6 bytes total
DataLength = 1
OpCode = 0x01
Type = namedtuple('VersionRequest', 'sync op_code length header_checksum checksum')
```

#### Methods

##### make()

```python
@classmethod
def make(cls) -> bytearray
```

Create version request packet.

**Returns:**
- `bytearray`: 6-byte packet

**Example:**
```python
request = VersionRequest.make()
# b'\xe7\x01\x00\x01\x46\x00'
```

---

### VersionResponse (0x02)

Device version information response.

#### Class Attributes

```python
Fmt = struct.Struct('!2B H B 2B 3B 128s B')  # 139 bytes total
DataLength = 134
OpCode = 0x02
Type = namedtuple('VersionResponse',
    'sync op_code length header_checksum '
    'api_major api_minor '
    'bootloader_major bootloader_minor bootloader_build '
    'note checksum')
```

#### Methods

##### make()

```python
@classmethod
def make(cls,
         api_major: int,
         api_minor: int,
         bootloader_major: int,
         bootloader_minor: int,
         bootloader_build: int,
         note: bytes) -> bytearray
```

Create version response packet.

**Parameters:**
- `api_major` (int): API major version (0-255)
- `api_minor` (int): API minor version (0-255)
- `bootloader_major` (int): Bootloader major version
- `bootloader_minor` (int): Bootloader minor version
- `bootloader_build` (int): Bootloader build number
- `note` (bytes): 128-byte note string

**Returns:**
- `bytearray`: 139-byte packet

##### extract()

```python
@classmethod
def extract(cls, msg: bytes) -> VersionResponse.Type
```

Parse version response from raw bytes.

**Parameters:**
- `msg` (bytes): Raw response (139 bytes)

**Returns:**
- `VersionResponse.Type`: Named tuple with all fields

**Raises:**
- `AssertionError`: If op_code doesn't match 0x02

**Example:**
```python
response = VersionResponse.extract(raw_data)
print(f"API: {response.api_major}.{response.api_minor}")
print(f"Bootloader: {response.bootloader_major}.{response.bootloader_minor}.{response.bootloader_build}")
print(f"Note: {response.note.decode('utf-8').rstrip('\x00')}")
```

---

### UpdateStartRequest (0x03)

Initialize firmware update session.

#### Class Attributes

```python
Fmt = struct.Struct('!2B H B I B')  # 10 bytes total
DataLength = 5
OpCode = 0x03
Type = namedtuple('UpdateStartRequest',
    'sync op_code length header_checksum image_size checksum')
```

#### Methods

##### make()

```python
@classmethod
def make(cls, image_size: int) -> bytearray
```

Create update start request.

**Parameters:**
- `image_size` (int): Total firmware size in bytes (0 to 2^32-1)

**Returns:**
- `bytearray`: 10-byte packet

**Example:**
```python
request = UpdateStartRequest.make(image_size=131072)  # 128KB
```

##### extract()

```python
@classmethod
def extract(cls, msg: bytes) -> UpdateStartRequest.Type
```

Parse update start request.

**Parameters:**
- `msg` (bytes): Raw request (10 bytes)

**Returns:**
- `UpdateStartRequest.Type`: Named tuple with image_size

---

### UpdateStartResponse (0x04)

Acknowledge firmware update start.

#### Class Attributes

```python
Fmt = struct.Struct('!2B H B B')  # 6 bytes total
DataLength = 1
OpCode = 0x04
Type = namedtuple('UpdateStartResponse',
    'sync op_code length header_checksum checksum')
```

#### Methods

##### make()

```python
@classmethod
def make(cls) -> bytearray
```

Create update start response.

**Returns:**
- `bytearray`: 6-byte packet

##### extract()

```python
@classmethod
def extract(cls, msg: bytes) -> UpdateStartResponse.Type
```

Parse update start response.

**Parameters:**
- `msg` (bytes): Raw response (6 bytes)

**Returns:**
- `UpdateStartResponse.Type`: Named tuple

---

### UpdateStopRequest (0x05)

Finalize firmware update with CRC.

#### Class Attributes

```python
Fmt = struct.Struct('!2B H B I B')  # 10 bytes total
DataLength = 5
OpCode = 0x05
Type = namedtuple('UpdateStopRequest',
    'sync op_code length header_checksum crc checksum')
```

#### Methods

##### make()

```python
@classmethod
def make(cls, crc: int) -> bytearray
```

Create update stop request with CRC.

**Parameters:**
- `crc` (int): CRC32 checksum of entire firmware image (0 to 2^32-1)

**Returns:**
- `bytearray`: 10-byte packet

**Example:**
```python
import binascii
firmware_crc = binascii.crc32(firmware_data) & 0xFFFFFFFF
request = UpdateStopRequest.make(crc=firmware_crc)
```

---

### UpdateStopResponse (0x06)

Acknowledge firmware update completion.

#### Class Attributes

```python
Fmt = struct.Struct('!2B H B i B')  # 10 bytes total (note: signed CRC)
DataLength = 5
OpCode = 0x06
Type = namedtuple('UpdateStopResponse',
    'sync op_code length header_checksum crc checksum')
```

#### Methods

##### make()

```python
@classmethod
def make(cls, crc: int) -> bytearray
```

Create update stop response.

**Parameters:**
- `crc` (int): Device-calculated CRC32 (signed integer)

**Returns:**
- `bytearray`: 10-byte packet

##### extract()

```python
@classmethod
def extract(cls, msg: bytes) -> UpdateStopResponse.Type
```

Parse update stop response and compare CRC.

**Parameters:**
- `msg` (bytes): Raw response (10 bytes)

**Returns:**
- `UpdateStopResponse.Type`: Named tuple with device CRC

---

### WriteRequest (0x07)

Write data chunk to flash memory.

#### Class Attributes

```python
OpCode = 0x07
Type = namedtuple('WriteRequest',
    'sync op_code length header_checksum payload data_crc checksum')
```

**Note:** Format is dynamic based on payload size (max 1024 bytes).

#### Methods

##### make()

```python
@classmethod
def make(cls, data: bytes) -> bytearray
```

Create write request with data chunk and CRC.

**Parameters:**
- `data` (bytes): Data to write (1 to 1024 bytes)

**Returns:**
- `bytearray`: Variable-size packet (minimum 10 bytes)

**Raises:**
- `AssertionError`: If data length exceeds MAX_WRITE_PAYLOAD_SIZE (1024)

**Implementation:**
1. Converts data to string for struct packing (Python 2 compatibility)
2. Calculates CRC32 of data
3. Creates dynamic struct format: Header + data + CRC32 + checksum
4. Packs and returns complete packet

**Example:**
```python
chunk = bytearray([0x00] * 512)  # 512-byte chunk
request = WriteRequest.make(chunk)
# Creates ~522 byte packet (5 + 512 + 4 + 1)
```

##### extract()

```python
@classmethod
def extract(cls, msg: bytes) -> WriteRequest.Type
```

Parse write request from raw bytes.

**Parameters:**
- `msg` (bytes): Raw request (variable size)

**Returns:**
- `WriteRequest.Type`: Named tuple with payload and CRC

**Implementation:**
- Calculates payload length from header.length - CRC size - checksum size
- Creates dynamic struct format to unpack variable-length data

---

### WriteResponse (0x08)

Acknowledge successful write operation.

#### Class Attributes

```python
Fmt = struct.Struct('!2B H B B')  # 6 bytes total
DataLength = 1
OpCode = 0x08
Type = namedtuple('WriteResponse',
    'sync op_code length header_checksum checksum')
```

#### Methods

##### make()

```python
@classmethod
def make(cls) -> bytearray
```

Create write response.

**Returns:**
- `bytearray`: 6-byte packet

##### extract()

```python
@classmethod
def extract(cls, msg: bytes) -> WriteResponse.Type
```

Parse write response.

**Parameters:**
- `msg` (bytes): Raw response (6 bytes)

**Returns:**
- `WriteResponse.Type`: Named tuple

---

### ResetRequest (0x09)

Request device reset.

#### Class Attributes

```python
Fmt = struct.Struct('!2B H B B')  # 6 bytes total
DataLength = 1
OpCode = 0x09
Type = namedtuple('ResetRequest',
    'sync op_code length header_checksum checksum')
```

#### Methods

##### make()

```python
@classmethod
def make(cls) -> bytearray
```

Create reset request.

**Returns:**
- `bytearray`: 6-byte packet

**Example:**
```python
request = ResetRequest.make()
# Device will restart after receiving this
```

---

### ResetResponse (0x0A)

Acknowledge device reset.

#### Class Attributes

```python
Fmt = struct.Struct('!2B H B B')  # 6 bytes total
DataLength = 1
OpCode = 0x0A
Type = namedtuple('ResetResponse',
    'sync op_code length header_checksum checksum')
```

#### Methods

##### make()

```python
@classmethod
def make(cls) -> bytearray
```

Create reset response.

**Returns:**
- `bytearray`: 6-byte packet

**Note:** Device may not send this response if reset is immediate.

---

### ReadAddressRequest (0x0B)

Read data from memory address.

#### Class Attributes

```python
Fmt = struct.Struct('!2B H B 2I B')  # 14 bytes total
DataLength = 9
OpCode = 0x0B
Type = namedtuple('ReadAddressRequest',
    'sync op_code length header_checksum address length_to_read checksum')
```

#### Methods

##### make()

```python
@classmethod
def make(cls, address: int, length_to_read: int) -> bytearray
```

Create read address request.

**Parameters:**
- `address` (int): Memory address to read from (0 to 2^32-1)
- `length_to_read` (int): Number of bytes to read (0 to 2^32-1)

**Returns:**
- `bytearray`: 14-byte packet

**Example:**
```python
# Read 256 bytes from flash address 0x08000000
request = ReadAddressRequest.make(address=0x08000000, length_to_read=256)
```

##### extract()

```python
@classmethod
def extract(cls, msg: bytes) -> ReadAddressRequest.Type
```

Parse read address request.

**Parameters:**
- `msg` (bytes): Raw request (14 bytes)

**Returns:**
- `ReadAddressRequest.Type`: Named tuple with address and length

---

### ReadAddressResponse (0x0C)

Memory read data response.

#### Class Attributes

```python
OpCode = 0x0C
Type = namedtuple('ReadAddressResponse',
    'sync op_code length header_checksum data checksum')
```

**Note:** Format is dynamic based on requested read length.

#### Methods

##### make()

```python
@classmethod
def make(cls, address: int, length_to_read: int, data: bytes) -> bytearray
```

Create read address response with data.

**Parameters:**
- `address` (int): Memory address (included in header)
- `length_to_read` (int): Number of bytes read
- `data` (bytes): Actual read data (must match length_to_read)

**Returns:**
- `bytearray`: Variable-size packet

**Raises:**
- `AssertionError`: If len(data) != length_to_read

##### extract()

```python
@classmethod
def extract(cls, msg: bytes) -> ReadAddressResponse.Type
```

Parse read address response.

**Parameters:**
- `msg` (bytes): Raw response (variable size)

**Returns:**
- `ReadAddressResponse.Type`: Named tuple with data field

**Example:**
```python
response = ReadAddressResponse.extract(raw_data)
memory_content = bytearray(response.data)
print(f"Read {len(memory_content)} bytes")
```

---

### ErrorResponse (0xFF)

Error condition notification.

#### Class Attributes

```python
Fmt = struct.Struct('!2B H B 2B')  # 7 bytes total
DataLength = 2
OpCode = 0xFF
Type = namedtuple('ErrorResponse',
    'sync op_code length header_checksum error checksum')
```

#### Error Codes

```python
UnsupportedOperation = 0x00
```
Requested operation is not supported or unrecognized opcode.

```python
IncorrectState = 0x01
```
Operation not allowed in current state (e.g., write before start_update).

```python
WriteFailed = 0x02
```
Flash write operation failed (hardware error).

#### Methods

##### make()

```python
@classmethod
def make(cls, error_code: int) -> bytearray
```

Create error response with error code.

**Parameters:**
- `error_code` (int): Error code (0x00-0x02)

**Returns:**
- `bytearray`: 7-byte packet

**Example:**
```python
error = ErrorResponse.make(ErrorResponse.WriteFailed)
```

##### extract()

```python
@classmethod
def extract(cls, msg: bytes) -> ErrorResponse.Type
```

Parse error response.

**Parameters:**
- `msg` (bytes): Raw response (7 bytes)

**Returns:**
- `ErrorResponse.Type`: Named tuple with error code

**Example:**
```python
error = ErrorResponse.extract(raw_data)
if error.error == ErrorResponse.UnsupportedOperation:
    print("Operation not supported")
elif error.error == ErrorResponse.IncorrectState:
    print("Invalid state for this operation")
elif error.error == ErrorResponse.WriteFailed:
    print("Flash write failed")
```

---

## Module: bootloader_messenger.py

Client-side communication handler for bootloader protocol.

---

## Class: BootloaderMessenger

High-level interface for bootloader communication.

### Constructor

```python
def __init__(self, server_address: Tuple[str, int], client_address: str = None)
```

Initialize UDP socket and configure connection.

**Parameters:**
- `server_address` (tuple): (IP address, port) of bootloader device
- `client_address` (str, optional): Local IP address to bind to

**Raises:**
- `socket.error`: If socket creation or binding fails

**Example:**
```python
# Connect to device at 192.168.3.100:12345
messenger = BootloaderMessenger(('192.168.3.100', 12345))

# Bind to specific local interface
messenger = BootloaderMessenger(
    ('192.168.3.100', 12345),
    client_address='192.168.3.1'
)
```

**Internal State:**
- Creates UDP socket (SOCK_DGRAM)
- Sets 10-second timeout
- Stores server address for all operations

---

### Methods

#### close()

```python
def close(self) -> None
```

Close UDP socket and release resources.

**Example:**
```python
try:
    messenger = BootloaderMessenger(('192.168.3.100', 12345))
    # ... perform operations ...
finally:
    messenger.close()
```

---

#### get_version()

```python
def get_version(self) -> Tuple[Tuple[int, int], Tuple[int, int, int], bytes]
```

Query device version information.

**Returns:**
- Tuple containing:
  - `api_version` (tuple): (major, minor)
  - `bootloader_version` (tuple): (major, minor, build)
  - `note` (bytes): 128-byte note string

**Raises:**
- `socket.timeout`: If no response within 10 seconds
- `RuntimeError`: If device returns ErrorResponse
- `AssertionError`: If response opcode doesn't match

**Example:**
```python
api, bootloader, note = messenger.get_version()
print(f"API: {api[0]}.{api[1]}")
print(f"Bootloader: {bootloader[0]}.{bootloader[1]}.{bootloader[2]}")
print(f"Note: {note.decode('utf-8').rstrip('\\x00')}")

# Expected output:
# API: 1.0
# Bootloader: 0.1.0
# Note: test string
```

---

#### start_update()

```python
def start_update(self, image_size: int) -> bool
```

Begin firmware update session.

**Parameters:**
- `image_size` (int): Total firmware size in bytes

**Returns:**
- `bool`: True if update started successfully, False otherwise

**Raises:**
- `socket.timeout`: If no response within 10 seconds
- `RuntimeError`: If device returns ErrorResponse

**Example:**
```python
with open('firmware.bin', 'rb') as f:
    firmware = f.read()

success = messenger.start_update(len(firmware))
if not success:
    print("Failed to start update")
```

**State Changes:**
- Device enters update mode
- Device prepares flash memory for writing
- Subsequent write() calls will be accepted

---

#### write()

```python
def write(self, data: bytes) -> bool
```

Write data chunk to flash memory.

**Parameters:**
- `data` (bytes): Data to write (1 to 1024 bytes)

**Returns:**
- `bool`: True if write succeeded, False otherwise

**Raises:**
- `socket.timeout`: If no response within 10 seconds
- `RuntimeError`: If device returns ErrorResponse
- `AssertionError`: If data length exceeds MAX_WRITE_PAYLOAD_SIZE

**Example:**
```python
# Write firmware in 512-byte chunks
chunk_size = 512
for i in range(0, len(firmware), chunk_size):
    chunk = firmware[i:i+chunk_size]
    success = messenger.write(chunk)
    if not success:
        print(f"Write failed at offset {i}")
        break
```

**Performance:**
- Typical write time: 20-100ms per chunk
- Optimal chunk size: 512 bytes (balance speed vs. reliability)
- Maximum chunk size: 1024 bytes

---

#### stop_update()

```python
def stop_update(self, crc_value: int) -> bool
```

Finalize firmware update with CRC validation.

**Parameters:**
- `crc_value` (int): CRC32 of entire firmware image

**Returns:**
- `bool`: True if CRC matches and update completed, False otherwise

**Raises:**
- `socket.timeout`: If no response within 10 seconds
- `RuntimeError`: If device returns ErrorResponse

**Example:**
```python
import binascii

# Calculate CRC of entire firmware
crc = binascii.crc32(firmware_data) & 0xFFFFFFFF

# Finalize update
success = messenger.stop_update(crc)
if success:
    print("Firmware validated and written successfully")
else:
    print("CRC mismatch - firmware corrupted")
```

**Validation:**
- Device calculates CRC of received data
- Compares with provided CRC value
- Returns success only if CRCs match

---

#### reset()

```python
def reset(self) -> bool
```

Reset device (typically after firmware update).

**Returns:**
- `bool`: True (always, if response received)

**Raises:**
- `socket.timeout`: If no response within 10 seconds
- `AssertionError`: If response opcode doesn't match

**Example:**
```python
# Reset device to apply new firmware
messenger.reset()
print("Device restarting...")

# Wait for device to reboot
time.sleep(5)

# Reconnect after reset
messenger = BootloaderMessenger(('192.168.3.100', 12345))
```

**Note:** Device may disconnect immediately after reset, preventing response delivery.

---

#### read_address()

```python
def read_address(self, address: int, length: int) -> ReadAddressResponse.Type
```

Read data from specific memory address.

**Parameters:**
- `address` (int): Memory address (0 to 2^32-1)
- `length` (int): Number of bytes to read (0 to 2^32-1)

**Returns:**
- `ReadAddressResponse.Type`: Named tuple with data field

**Raises:**
- `socket.timeout`: If no response within 10 seconds
- `RuntimeError`: If device returns ErrorResponse
- `AssertionError`: If response opcode doesn't match

**Example:**
```python
# Read 256 bytes from flash memory
response = messenger.read_address(address=0x08000000, length=256)
data = bytearray(response.data)

print(f"Read {len(data)} bytes:")
print(binascii.hexlify(data[:16]))  # Print first 16 bytes

# Common memory regions:
# 0x08000000 - Flash memory start (STM32)
# 0x20000000 - SRAM start (STM32)
# 0x1FFFF7E0 - Unique device ID (STM32)
```

---

#### send_and_recv()

```python
def send_and_recv(self, msg: bytes) -> bytes
```

Low-level send/receive operation.

**Parameters:**
- `msg` (bytes): Raw message packet to send

**Returns:**
- `bytes`: Raw response packet

**Raises:**
- `socket.timeout`: If no response within 10 seconds
- `RuntimeError`: If device returns ErrorResponse
- `AssertionError`: If packet exceeds MAX_PACKET_SIZE

**Example:**
```python
# Direct message sending (advanced usage)
request = VersionRequest.make()
response = messenger.send_and_recv(request)
header = Header.extract(response)
print(f"Received opcode: 0x{header.op_code:02X}")
```

**Internal Behavior:**
1. Sends packet via UDP to server address
2. Waits for response (10-second timeout)
3. Checks for ErrorResponse opcode
4. Raises RuntimeError if error detected
5. Returns raw response bytes

---

## Usage Patterns

### Complete Firmware Update

```python
from bootloader_messenger import BootloaderMessenger
import binascii
import math

def flash_firmware(ip: str, port: int, firmware_path: str) -> bool:
    """Flash firmware to device."""
    messenger = BootloaderMessenger((ip, port))

    try:
        # 1. Check version compatibility
        api, bootloader, _ = messenger.get_version()
        if api != (1, 0):
            raise Exception(f"Incompatible API version: {api}")

        # 2. Load firmware
        with open(firmware_path, 'rb') as f:
            firmware = bytearray(f.read())

        # 3. Start update
        if not messenger.start_update(len(firmware)):
            raise Exception("Failed to start update")

        # 4. Write firmware in chunks
        chunk_size = 512
        total_chunks = int(math.ceil(len(firmware) / float(chunk_size)))

        for i in range(total_chunks):
            offset = i * chunk_size
            chunk = firmware[offset:offset + chunk_size]

            if not messenger.write(chunk):
                raise Exception(f"Write failed at chunk {i}")

            # Progress callback
            progress = (i + 1) / float(total_chunks) * 100
            print(f"Progress: {progress:.1f}%")

        # 5. Finalize with CRC
        crc = binascii.crc32(firmware) & 0xFFFFFFFF
        if not messenger.stop_update(crc):
            raise Exception("CRC validation failed")

        # 6. Reset device
        messenger.reset()
        return True

    except Exception as e:
        print(f"Flash failed: {e}")
        return False

    finally:
        messenger.close()

# Usage
success = flash_firmware('192.168.3.100', 12345, 'firmware.bin')
```

### Error Handling Best Practices

```python
import socket
import time

def robust_flash(ip, port, firmware_data, max_retries=3):
    """Flash firmware with retry logic."""
    for attempt in range(max_retries):
        try:
            messenger = BootloaderMessenger((ip, port))

            # Check version
            api, bootloader, _ = messenger.get_version()

            # Start update
            messenger.start_update(len(firmware_data))

            # Write with progress tracking
            chunk_size = 512
            failed_chunks = []

            for i in range(0, len(firmware_data), chunk_size):
                chunk = firmware_data[i:i+chunk_size]
                success = messenger.write(chunk)

                if not success:
                    failed_chunks.append(i)

            # Retry failed chunks
            for offset in failed_chunks:
                chunk = firmware_data[offset:offset+chunk_size]
                if not messenger.write(chunk):
                    raise Exception(f"Retry failed at {offset}")

            # Finalize
            crc = binascii.crc32(firmware_data) & 0xFFFFFFFF
            if messenger.stop_update(crc):
                messenger.reset()
                messenger.close()
                return True

        except socket.timeout:
            print(f"Attempt {attempt+1}: Timeout - retrying...")
            time.sleep(2)

        except RuntimeError as e:
            if "error: 2" in str(e):  # WriteFailed
                print(f"Attempt {attempt+1}: Write failed - retrying...")
                time.sleep(2)
            else:
                raise

        except Exception as e:
            print(f"Attempt {attempt+1}: {e}")
            raise

        finally:
            try:
                messenger.close()
            except:
                pass

    return False
```

### Memory Inspection

```python
def dump_flash_memory(ip, port, start_addr, length, output_file):
    """Dump flash memory to file."""
    messenger = BootloaderMessenger((ip, port))

    try:
        chunk_size = 256  # Read in 256-byte chunks
        with open(output_file, 'wb') as f:
            for offset in range(0, length, chunk_size):
                addr = start_addr + offset
                read_len = min(chunk_size, length - offset)

                response = messenger.read_address(addr, read_len)
                f.write(response.data)

                progress = (offset + read_len) / float(length) * 100
                print(f"Dumped: {progress:.1f}%")

        print(f"Memory dumped to {output_file}")

    finally:
        messenger.close()

# Dump 64KB of flash
dump_flash_memory('192.168.3.100', 12345,
                  start_addr=0x08000000,
                  length=65536,
                  output_file='flash_dump.bin')
```

---

## Error Codes Reference

| Error Code | Name | Description | Recovery |
|------------|------|-------------|----------|
| 0x00 | UnsupportedOperation | Invalid or unrecognized opcode | Check protocol version compatibility |
| 0x01 | IncorrectState | Operation not valid in current state | Follow correct message sequence |
| 0x02 | WriteFailed | Flash write operation failed | Retry write operation |

---

## Performance Tuning

### Optimal Parameters

```python
# Recommended settings
CHUNK_SIZE = 512          # Balance between speed and reliability
READ_TIMEOUT = 10         # Socket timeout in seconds
MAX_RETRIES = 10          # Flash operation retries
RETRY_DELAY = 0.5         # Delay between retries (seconds)

# For slower networks
CHUNK_SIZE = 256
READ_TIMEOUT = 30

# For faster networks (LAN)
CHUNK_SIZE = 1024         # Maximum allowed
READ_TIMEOUT = 5
```

### Throughput Calculation

```python
# Theoretical throughput
chunk_size = 512          # bytes
latency = 0.05            # 50ms round-trip
throughput = chunk_size / latency  # 10,240 bytes/sec

# For 256KB firmware
firmware_size = 256 * 1024
estimated_time = firmware_size / throughput  # ~25 seconds
```

---

## Thread Safety

**Warning:** BootloaderMessenger is **NOT thread-safe**.

Do not share instances across threads without locking:

```python
import threading

lock = threading.Lock()
messenger = BootloaderMessenger(('192.168.3.100', 12345))

def thread_safe_write(data):
    with lock:
        return messenger.write(data)
```

Better approach: **Create separate instances per thread**:

```python
def worker_thread(ip, port, data):
    messenger = BootloaderMessenger((ip, port))
    try:
        messenger.write(data)
    finally:
        messenger.close()
```

---

## Logging and Debugging

Enable debug logging for detailed packet inspection:

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Now all send/recv operations are logged
messenger = BootloaderMessenger(('192.168.3.100', 12345))
```

Custom packet inspection:

```python
import binascii

class DebugMessenger(BootloaderMessenger):
    def send_and_recv(self, msg):
        print(f"TX: {binascii.hexlify(msg)}")
        response = super().send_and_recv(msg)
        print(f"RX: {binascii.hexlify(response)}")
        return response
```

---

**Last Updated**: 2026-02-04
**API Version**: 1.0
