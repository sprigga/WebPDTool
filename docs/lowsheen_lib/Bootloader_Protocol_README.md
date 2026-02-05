# Bootloader Protocol System

## Overview

The Bootloader Protocol is a firmware update system designed for flashing embedded STM32 microcontrollers over Ethernet using UDP communication. This protocol enables reliable, verified firmware updates with built-in error handling and validation.

**Location:** `src/lowsheen_lib/tools/bootloader_protocol/`

## Key Features

- **UDP-based Communication**: Fast, connectionless protocol for firmware updates
- **Message Integrity**: Header and payload checksums with CRC32 validation
- **Binary Protocol**: Efficient binary message format with fixed header structure
- **Retry Logic**: Automatic retry mechanism for failed writes (up to 10 attempts)
- **Version Checking**: API and bootloader version compatibility verification
- **Memory Operations**: Read/write operations with address-based access
- **Error Handling**: Comprehensive error responses for failed operations

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Firmware Update Flow                    │
└─────────────────────────────────────────────────────────┘
         │
         ├─> BootloaderMessenger (Client)
         │   ├─> get_version()
         │   ├─> start_update(image_size)
         │   ├─> write(data_chunks) [loop]
         │   ├─> stop_update(crc)
         │   └─> reset()
         │
         ├─> Bootloader Messages (Protocol)
         │   ├─> Request/Response Pairs
         │   ├─> Header Structure
         │   └─> Checksum Validation
         │
         └─> LowsheenEthernetProgrammer (High-level)
             ├─> cmake/make build
             ├─> get_main_data()
             └─> reprogram_cpu_mcu()
```

## Protocol Specification

### Message Structure

All messages follow this fixed structure:

```
┌──────┬──────┬─────────┬─────────┬───────────┬──────────┐
│ Byte │ 0    │ 1       │ 2:3     │ 4         │ 5:N      │
├──────┼──────┼─────────┼─────────┼───────────┼──────────┤
│ Data │ 0xE7 │ OP_CODE │ LENGTH  │ HDR_CHKSUM│ PAYLOAD  │
│      │(sync)│         │ (u16)   │           │ + CHKSUM │
└──────┴──────┴─────────┴─────────┴───────────┴──────────┘
```

- **Byte 0**: Fixed sync code `0xE7`
- **Byte 1**: Operation code (see OpCodes below)
- **Bytes 2-3**: Remaining message length (little-endian u16)
- **Byte 4**: Header checksum (sum of bytes 0-3, masked to 8-bit)
- **Bytes 5+**: Message-specific payload
- **Last Byte**: Message checksum (sum of all bytes except last, masked to 8-bit)

### Constants

```python
MAX_WRITE_PAYLOAD_SIZE = 1024  # Maximum data per write packet
HEADER_SIZE = 5                # Fixed header size
MAX_PACKET_SIZE = 1034         # Total max packet (header + payload + checksums)
SYNC_CODE = 0xE7              # Message sync byte
```

### OpCodes

| OpCode | Name                | Direction       | Description                          |
|--------|---------------------|-----------------|--------------------------------------|
| 0x01   | VersionRequest      | Client → Device | Request version information          |
| 0x02   | VersionResponse     | Device → Client | Version information response         |
| 0x03   | UpdateStartRequest  | Client → Device | Begin firmware update session        |
| 0x04   | UpdateStartResponse | Device → Client | Acknowledge update start             |
| 0x05   | UpdateStopRequest   | Client → Device | End update with CRC                  |
| 0x06   | UpdateStopResponse  | Device → Client | Acknowledge update completion        |
| 0x07   | WriteRequest        | Client → Device | Write data chunk to flash            |
| 0x08   | WriteResponse       | Device → Client | Acknowledge write success            |
| 0x09   | ResetRequest        | Client → Device | Reset device                         |
| 0x0A   | ResetResponse       | Device → Client | Acknowledge reset                    |
| 0x0B   | ReadAddressRequest  | Client → Device | Read from memory address             |
| 0x0C   | ReadAddressResponse | Device → Client | Memory read data response            |
| 0xFF   | ErrorResponse       | Device → Client | Error occurred during operation      |

## Message Types

### 1. Version Request/Response

**Purpose**: Query bootloader and API versions

**VersionRequest (0x01)**
```
Size: 6 bytes
Payload: None (just checksum)
```

**VersionResponse (0x02)**
```
Size: 139 bytes
Payload:
  - api_major: u8
  - api_minor: u8
  - bootloader_major: u8
  - bootloader_minor: u8
  - bootloader_build: u8
  - note: 128-byte string
```

**Example Usage:**
```python
api_version, bootloader_version, note = messenger.get_version()
# Returns: ((1, 0), (0, 1, 0), 'test string...')
```

### 2. Update Start Request/Response

**Purpose**: Initialize firmware update session

**UpdateStartRequest (0x03)**
```
Size: 10 bytes
Payload:
  - image_size: u32 (total firmware size in bytes)
```

**UpdateStartResponse (0x04)**
```
Size: 6 bytes
Payload: None (just checksum)
```

**Example Usage:**
```python
success = messenger.start_update(image_size=65536)
```

### 3. Write Request/Response

**Purpose**: Write firmware data chunks to flash memory

**WriteRequest (0x07)**
```
Size: Variable (max 1034 bytes)
Payload:
  - data: variable length (max 1024 bytes)
  - data_crc: u32 (CRC32 of data)
```

**WriteResponse (0x08)**
```
Size: 6 bytes
Payload: None (just checksum)
```

**Example Usage:**
```python
# Write 512-byte chunks
for i in range(len(firmware_data) // 512):
    index = i * 512
    success = messenger.write(firmware_data[index:index+512])
```

### 4. Update Stop Request/Response

**Purpose**: Finalize firmware update with CRC validation

**UpdateStopRequest (0x05)**
```
Size: 10 bytes
Payload:
  - crc: u32 (CRC32 of entire firmware image)
```

**UpdateStopResponse (0x06)**
```
Size: 10 bytes
Payload:
  - crc: i32 (device-calculated CRC, signed)
```

**Example Usage:**
```python
import binascii
crc = binascii.crc32(firmware_data) & 0xFFFFFFFF
success = messenger.stop_update(crc)
```

### 5. Reset Request/Response

**Purpose**: Reset the device (usually after successful update)

**ResetRequest (0x09)**
```
Size: 6 bytes
Payload: None
```

**ResetResponse (0x0A)**
```
Size: 6 bytes
Payload: None
```

### 6. Read Address Request/Response

**Purpose**: Read data from specific memory address

**ReadAddressRequest (0x0B)**
```
Size: 14 bytes
Payload:
  - address: u32 (memory address)
  - length_to_read: u32 (number of bytes)
```

**ReadAddressResponse (0x0C)**
```
Size: Variable
Payload:
  - data: variable length bytes
```

**Example Usage:**
```python
response = messenger.read_address(address=0x08000000, length=256)
data = response.data
```

### 7. Error Response

**Purpose**: Indicate error conditions

**ErrorResponse (0xFF)**
```
Size: 7 bytes
Payload:
  - error: u8 (error code)

Error Codes:
  0x00 = UnsupportedOperation
  0x01 = IncorrectState
  0x02 = WriteFailed
```

## Module Reference

### bootloader_messages.py

**Purpose**: Protocol message definitions and packet construction

**Key Functions:**

- `make_packet(fmt, op_code, length, *args)` - Construct binary packet with checksums

**Key Classes:**

All message classes follow this pattern:
- `Fmt`: struct.Struct for binary packing
- `DataLength`: Payload size (excluding header)
- `Type`: namedtuple for parsed messages
- `OpCode`: Message operation code
- `make()`: Class method to create message
- `extract()`: Class method to parse received message

**Example:**
```python
# Create version request
request = VersionRequest.make()

# Parse version response
response = VersionResponse.extract(received_data)
print(f"API: {response.api_major}.{response.api_minor}")
print(f"Bootloader: {response.bootloader_major}.{response.bootloader_minor}")
```

### bootloader_messenger.py

**Purpose**: Client-side communication handler

**Class: BootloaderMessenger**

```python
messenger = BootloaderMessenger(
    server_address=('192.168.3.100', 12345),
    client_address=None  # Optional local IP binding
)
```

**Methods:**

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `get_version()` | None | `(api_version, bootloader_version, note)` | Query device versions |
| `start_update()` | `image_size: int` | `bool` | Start firmware update |
| `write()` | `data: bytes` | `bool` | Write data chunk |
| `stop_update()` | `crc_value: int` | `bool` | Finalize update |
| `reset()` | None | `bool` | Reset device |
| `read_address()` | `address: int, length: int` | `ReadAddressResponse` | Read memory |
| `send_and_recv()` | `msg: bytes` | `bytes` | Low-level send/receive |
| `close()` | None | None | Close socket |

**Configuration:**
- Timeout: 10 seconds (configurable via `socket.settimeout()`)
- Protocol: UDP (SOCK_DGRAM)
- Max packet size: 1034 bytes

**Error Handling:**
- Raises `RuntimeError` on ErrorResponse
- Raises `socket.timeout` on communication timeout
- Validates response OpCodes with assertions

### bootloader_test_server.py

**Purpose**: UDP server for testing bootloader protocol

**Functionality:**
- Simulates bootloader device for testing
- Responds to all protocol messages
- Uses fake flash memory (700KB bytearray)
- Can load base firmware image

**Usage:**
```bash
uv run python bootloader_test_server.py base_firmware.bin
```

**Server Configuration:**
```python
UDP_IP = "127.0.0.1"
UDP_PORT = 12345
FAKE_FLASH = bytearray(700000)
```

**Handlers:**
- `handle_version_request()` - Returns version info
- `handle_update_start_request()` - Validates image size
- `handle_update_write_request()` - Writes to fake flash
- `handle_update_stop_request()` - Acknowledges completion
- `handle_reset_request()` - Simulates reset
- `handle_read_request()` - Reads from fake flash

### reprogram_ethernet.py

**Purpose**: High-level firmware programming tool

**Class: LowsheenEthernetProgrammer**

```python
programmer = LowsheenEthernetProgrammer(
    lowsheen_dir='/opt/shining_software/catkin_ws/src/lowsheen/',
    option_list=['-DMACHINE=ice_mk1'],
    STM_IP='192.168.3.100',
    STM_PORT=12345
)
```

**Key Methods:**

| Method | Description |
|--------|-------------|
| `cmake()` | Run CMake to configure build |
| `make()` | Compile firmware (mule.bin) |
| `get_main_data(filename)` | Extract and validate firmware image |
| `reprogram_cpu_mcu(retries=10)` | Flash firmware with retry logic |
| `cleanup()` | Remove temporary build files |

**Firmware Image Structure:**

```python
# Memory layout
PREBOOT_IMG_START = 0*1024        # 0 KB
PREBOOT_IMG_END = 32*1024         # 32 KB
POST_IMG_START = 512*1024         # 512 KB

# Image header (512 bytes at POST_IMG_START)
IMG_HEADER_SIZE = 512
IMG_HEADER_TESTED_OFFSET = 0       # Status: tested
IMG_HEADER_GOOD_OFFSET = 4         # Status: good
IMG_HEADER_RETRY_COUNT_OFFSET = 8  # Retry counter
IMG_HEADER_IMAGES_MATCH_OFFSET = 12 # Match flag
IMG_HEADER_MAGIC_OFFSET = 24       # Magic: 0x01234567
IMG_HEADER_VERSION_OFFSET = 28     # Version: 2
IMG_HEADER_LENGTH_OFFSET = 32      # Image length
IMG_HEADER_CRC_OFFSET = 36         # CRC32 checksum

# Status values
STATUS_TESTING = 0x900d0bad
STATUS_GOOD = 0x900d900d
STATUS_UNTESTED = 0xFFFFFFFF
```

**Command-line Usage:**
```bash
# Auto-detect machine type
uv run python reprogram_ethernet.py

# Specify machine type
uv run python reprogram_ethernet.py --machine ice_mk2

# Skip cmake/make steps
uv run python reprogram_ethernet.py --no-cmake --no-make

# Custom lowsheen directory
uv run python reprogram_ethernet.py --dir /path/to/lowsheen

# Set retry count
uv run python reprogram_ethernet.py --retries 5
```

**Supported Machine Types:**
- `ice_mk1` - ICE Mark 1
- `ice_mk2` - ICE Mark 2
- `minuteman` - Minuteman platform
- `nss_scrubber` - NSS Scrubber
- `tennant_t7` - Tennant T7
- `little` - Little platform

## Complete Firmware Update Workflow

### Standard Update Sequence

```python
from bootloader_messenger import BootloaderMessenger
import binascii
import math

# 1. Connect to device
server_address = ('192.168.3.100', 12345)
messenger = BootloaderMessenger(server_address)

try:
    # 2. Verify versions
    api_version, bootloader_version, note = messenger.get_version()
    print(f"API: {api_version}, Bootloader: {bootloader_version}")

    # Check compatibility
    assert api_version == (1, 0), "Incompatible API version"
    assert bootloader_version == (0, 1, 0), "Incompatible bootloader version"

    # 3. Load firmware image
    with open('firmware.bin', 'rb') as f:
        firmware_data = bytearray(f.read())

    # 4. Start update session
    success = messenger.start_update(len(firmware_data))
    if not success:
        raise Exception("Failed to start update")

    # 5. Write firmware in 512-byte chunks
    packets_count = int(math.ceil(len(firmware_data) / 512.0))

    for i in range(packets_count):
        index = i * 512
        chunk = firmware_data[index:index + 512]
        success = messenger.write(chunk)

        if not success:
            raise Exception(f"Write failed at packet {i}")

        # Progress reporting
        progress = (i + 1) / packets_count * 100
        print(f"Progress: {progress:.1f}%")

    # 6. Finalize with CRC check
    crc = binascii.crc32(firmware_data) & 0xFFFFFFFF
    success = messenger.stop_update(crc)

    if not success:
        raise Exception("CRC validation failed")

    # 7. Reset device to apply new firmware
    messenger.reset()
    print("Firmware update completed successfully!")

except Exception as e:
    print(f"Error during update: {e}")

finally:
    messenger.close()
```

### High-level Update (Using LowsheenEthernetProgrammer)

```python
from reprogram_ethernet import LowsheenEthernetProgrammer

# Initialize programmer
programmer = LowsheenEthernetProgrammer(
    lowsheen_dir='/opt/shining_software/catkin_ws/src/lowsheen/',
    option_list=['-DMACHINE=ice_mk2'],
    STM_IP='192.168.3.100',
    STM_PORT=12345
)

# Build firmware
programmer.cmake()  # Configure build
programmer.make()   # Compile firmware

# Flash with automatic retry
programmer.reprogram_cpu_mcu(retries=10)

# Cleanup temporary files
programmer.cleanup()
```

## Error Handling

### Common Error Scenarios

**1. Communication Timeout**
```python
try:
    messenger.get_version()
except socket.timeout:
    print("Device not responding - check network connection")
```

**2. Version Mismatch**
```python
api_version, bootloader_version, _ = messenger.get_version()
if bootloader_version != (0, 1, 0):
    raise Exception(f"Incompatible bootloader: {bootloader_version}")
```

**3. Write Failure**
```python
success = messenger.write(data_chunk)
if not success:
    # Automatic retry in reprogram_cpu_mcu()
    retry_count += 1
```

**4. CRC Mismatch**
```python
success = messenger.stop_update(expected_crc)
if not success:
    # Device detected corrupted firmware
    # Re-flash required
```

**5. ErrorResponse from Device**
```python
# Automatically raised as RuntimeError
try:
    messenger.send_and_recv(request)
except RuntimeError as e:
    if "error: 0" in str(e):
        print("UnsupportedOperation")
    elif "error: 1" in str(e):
        print("IncorrectState")
    elif "error: 2" in str(e):
        print("WriteFailed")
```

## Testing

### Unit Testing with Test Server

**Terminal 1: Start test server**
```bash
cd src/lowsheen_lib/tools/bootloader_protocol
uv run python bootloader_test_server.py test_firmware.bin
```

**Terminal 2: Run client tests**
```bash
uv run python bootloader_messenger.py
```

**Expected Output:**
```
INFO:BootloaderMessenger:Will be sending messages to localhost:12345
(1, 0) (0, 1, 0) 'test string'
Progress: 1.95%
Progress: 3.91%
...
Progress: 100.00%
INFO:BootloaderMessenger:closing socket
```

### Manual Testing Commands

```python
# Test version query
from bootloader_messenger import BootloaderMessenger
m = BootloaderMessenger(('localhost', 12345))
print(m.get_version())

# Test write operation
test_data = bytearray([i & 0xFF for i in range(512)])
m.start_update(512)
m.write(test_data)
m.stop_update(binascii.crc32(test_data) & 0xFFFFFFFF)

# Test read operation
response = m.read_address(0x08000000, 64)
print(binascii.hexlify(response.data))
```

## Network Configuration

### Typical Setup

```
┌──────────────┐         Ethernet          ┌──────────────┐
│   Host PC    │ ◄─────────────────────► │ STM32 Device │
│  192.168.3.1 │      UDP Port 12345      │192.168.3.100 │
└──────────────┘                           └──────────────┘
```

### Firewall Configuration

**Linux:**
```bash
# Allow UDP port 12345
sudo ufw allow 12345/udp
```

**Windows:**
```cmd
# Add inbound rule for UDP 12345
netsh advfirewall firewall add rule name="Bootloader" dir=in action=allow protocol=UDP localport=12345
```

### Testing Connectivity

```bash
# Check if device is reachable
ping 192.168.3.100

# Monitor UDP traffic (tcpdump)
sudo tcpdump -i eth0 udp port 12345 -X

# Monitor UDP traffic (Wireshark)
# Filter: udp.port == 12345
```

## Performance Characteristics

### Timing Estimates

| Operation | Typical Duration | Notes |
|-----------|------------------|-------|
| Version query | 10-50 ms | Single request/response |
| Update start | 10-50 ms | Initializes flash memory |
| Write (512 bytes) | 20-100 ms | Depends on flash speed |
| Complete update (64KB) | 5-15 seconds | 128 writes @ ~100ms each |
| Complete update (256KB) | 20-60 seconds | 512 writes @ ~100ms each |
| CRC validation | 50-200 ms | Device-side calculation |
| Reset | 10-50 ms | Device restarts |

### Optimization Tips

1. **Use maximum chunk size (512 bytes)** for fastest throughput
2. **Minimize retries** by ensuring stable network connection
3. **Pre-calculate CRC** before starting update to validate locally
4. **Batch operations** when possible (protocol already does this)
5. **Monitor progress** to detect stalled transfers early

## Security Considerations

### Current Limitations

⚠️ **This protocol has minimal security features:**

- ❌ No authentication - anyone can flash firmware
- ❌ No encryption - firmware transmitted in clear text
- ❌ No signature verification - no protection against malicious firmware
- ⚠️ Basic checksum only - can detect corruption but not tampering

### Recommended Enhancements

For production environments, consider adding:

1. **Authentication**: Challenge-response or pre-shared key
2. **Encryption**: TLS/DTLS for UDP or AES encryption
3. **Signature Verification**: RSA/ECDSA signature on firmware images
4. **Rollback Protection**: Version number enforcement
5. **Secure Boot**: Verify bootloader integrity on device

### Safe Usage

- Use on **isolated networks only**
- Implement **physical access controls** during flashing
- **Validate firmware images** before flashing
- **Log all update attempts** for audit trail
- **Test firmware** in safe environment first

## Troubleshooting

### Common Issues

**Problem: socket.timeout after 10 seconds**
- **Cause**: Device not responding, wrong IP/port, network issue
- **Solution**:
  - Verify device IP: `ping 192.168.3.100`
  - Check port availability: `nc -u -z 192.168.3.100 12345`
  - Ensure device is in bootloader mode
  - Check firewall settings

**Problem: "Received error: 1" (IncorrectState)**
- **Cause**: Operation sent out of sequence
- **Solution**: Follow proper sequence: start_update → write → stop_update

**Problem: CRC validation fails**
- **Cause**: Data corruption during transmission
- **Solution**:
  - Check network stability
  - Enable retry logic (already in `reprogram_cpu_mcu()`)
  - Verify source firmware file integrity

**Problem: "Image does not match a valid image"**
- **Cause**: Invalid firmware header structure
- **Solution**:
  - Check magic value: 0x01234567
  - Verify header version: 2
  - Ensure status fields are 0xFFFFFFFF initially

**Problem: Version mismatch errors**
- **Cause**: Incompatible bootloader or API version
- **Solution**: Update device bootloader or use compatible protocol version

### Debug Mode

Enable detailed logging:

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Now all send/recv operations are logged
messenger = BootloaderMessenger(('192.168.3.100', 12345))
# Output: sending 6 bytes: "e701000146"
#         received 139 bytes: "e702008646..."
```

### Packet Inspection

Use `binascii.hexlify()` to inspect packets:

```python
import binascii

request = VersionRequest.make()
print(binascii.hexlify(request))
# Output: e701000146
#         ││││││└─ checksum
#         │││││└── header checksum
#         ││││└─── length (0x0001)
#         │││└──── opcode (0x01)
#         ││└───── sync (0xE7)
```

## Dependencies

### Required Python Packages

```python
import struct      # Binary data packing (built-in)
import zlib        # CRC32 calculation (built-in)
import socket      # UDP communication (built-in)
import binascii    # Hexadecimal conversion (built-in)
import logging     # Debug logging (built-in)
import subprocess  # Build system calls (built-in)
import argparse    # CLI parsing (built-in)
import math        # Packet count calculation (built-in)
import os          # File operations (built-in)
```

### External Dependencies

```python
# From lowsheen_lib package
from lowsheen_lib.lowsheen_stm_interface import LowsheenSTMInterface
from lowsheen_lib.lowsheen_utils import machine_id_to_name
```

**Note**: All protocol modules use Python standard library only, except `reprogram_ethernet.py` which requires the lowsheen_lib package.

## API Reference Summary

### Quick Reference Card

```python
# 1. Import
from bootloader_messenger import BootloaderMessenger

# 2. Connect
m = BootloaderMessenger(('192.168.3.100', 12345))

# 3. Version Check
api, bootloader, note = m.get_version()

# 4. Flash Firmware
m.start_update(image_size)
for chunk in chunks:
    m.write(chunk)
m.stop_update(crc32(firmware))

# 5. Cleanup
m.reset()
m.close()
```

### Message Size Reference

| Message | Request Size | Response Size |
|---------|--------------|---------------|
| Version | 6 bytes | 139 bytes |
| UpdateStart | 10 bytes | 6 bytes |
| Write | 5 + data + 5 bytes | 6 bytes |
| UpdateStop | 10 bytes | 10 bytes |
| Reset | 6 bytes | 6 bytes |
| ReadAddress | 14 bytes | 5 + data + 1 bytes |
| Error | N/A | 7 bytes |

## Version History

**Protocol Version: 1.0**
- API Version: (1, 0)
- Bootloader Version: (0, 1, 0)
- Initial implementation with all core features

**Supported Features:**
- ✅ Firmware flashing over UDP
- ✅ Version querying
- ✅ CRC validation
- ✅ Memory read operations
- ✅ Device reset
- ✅ Error reporting
- ✅ Retry logic

**Known Limitations:**
- ⚠️ No security/authentication
- ⚠️ UDP only (no TCP option)
- ⚠️ Single connection at a time
- ⚠️ 10-second timeout (fixed)

## Related Documentation

- **LowsheenSTMInterface**: STM32 communication interface
- **Lowsheen Utils**: Utility functions for machine identification
- **Firmware Build System**: CMake/Make configuration for mule.bin

## Support

For issues or questions:
1. Check troubleshooting section above
2. Enable debug logging for detailed diagnostics
3. Verify network connectivity with ping/tcpdump
4. Review test server behavior for protocol validation

---

**Last Updated**: 2026-02-04
**Protocol Version**: 1.0
**Maintainer**: PDTool4 Development Team
