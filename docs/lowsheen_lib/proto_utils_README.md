# Proto Utils Module Documentation

## Overview

The `proto_utils` module provides a Python interface for UDP-based communication between a host PC and an STM32 microcontroller (VCU - Vehicle Control Unit). It implements a custom protocol using Protocol Buffers for message serialization with CRC32 validation.

**Module Location:** `src/lowsheen_lib/proto_utils/`

**License:** BRAIN Corporation Beta License Agreement (2015-2018)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Host Application                         │
│                  (cliff_test.py)                            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    TestObject                                │
│  - Creates test command messages                            │
│  - Handles motor control commands                           │
│  - Manages timestamps                                        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   VCUComm                                    │
│  - Manages UDP socket connections                           │
│  - Handles connection establishment                         │
│  - Sends/receives packets                                   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  ProtoMsgs                                   │
│  - Serializes/deserializes protobuf messages                │
│  - Creates packet headers with CRC                          │
│  - Combines header and body                                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                 STM32 VCU                                    │
│            (192.168.3.100:8144)                             │
└─────────────────────────────────────────────────────────────┘
```

## Module Components

### 1. VCUComm.py
**Purpose:** Low-level UDP communication handler

**Key Features:**
- UDP socket management for connectionless communication
- Connection establishment with retry logic
- Thread-safe packet transmission
- Timeout-based message reception

**Class:** `VCUComm`

| Attribute/Method | Description |
|-----------------|-------------|
| `BASE_PORT` | Base UDP port (8124) |
| `CONNECT_ENDPOINT` | Connection endpoint offset (0x0) |
| `COMM_PORT_OFFSET` | Communication port offset (0x20) |
| `MSG_RSP_TIMEOUT_MS` | Response timeout (800ms) |
| `_STM_IP` | STM32 IP address (default: 192.168.3.100) |
| `try_cpu_stm_connect()` | Establish connection with retry |
| `_send_comm_packet()` | Send packet with retry logic |
| `receive_msg()` | Receive message with timeout |

### 2. proto_msgs.py
**Purpose:** Protocol buffer message serialization and packet framing

**Key Features:**
- Packet header creation with CRC32 validation
- Message serialization/deserialization
- Maximum message size calculation

**Class:** `ProtoMsgs`

| Attribute/Method | Description |
|-----------------|-------------|
| `ETHERNET_MAX_MTU_SIZE` | Maximum Ethernet packet size (1500 bytes) |
| `MAX_MESSAGE_BODY_SIZE` | Max protobuf message size |
| `_create_header()` | Create packet header with sync, length, CRC |
| `get_crc()` | Calculate CRC32 over header + body |
| `get_msg_from_packet()` | Extract message from received packet |
| `deserialize_message()` | Deserialize protobuf message |

### 3. cliff_test.py
**Purpose:** High-level test interface for motor control

**Key Features:**
- Test command message creation
- Timestamp generation
- Motor command transmission

**Class:** `TestObject`

| Attribute/Method | Description |
|-----------------|-------------|
| `generate_timestamp()` | Generate millisecond timestamp |
| `create_test_req_msg()` | Create test command protobuf message |
| `send_test_msg()` | Send test message and get response |

## Packet Format

### Packet Structure
```
+--------+--------+--------+--------+--------+--------+--------+--------+
|  Sync  | Length | Format |  CRC   | Msg ID |   Timestamp   |  Data   |
| (2B)   | (2B)   | (1B)   | (4B)   | (1B)   |     (4B)      | (nB)    |
+--------+--------+--------+--------+--------+--------+--------+--------+
         ↑                   ↑        ↑
         |                   |        |
    MAGIC_SYNC_U16    CRC calculated  |
                         from here    |
                                      |
                              CRC_OFFSET = 8
```

### Header Fields
- **Sync:** `MAGIC_SYNC_U16` - Packet synchronization marker
- **Length:** Message body length in bytes
- **Format:** `MESSAGE_FORMAT_BARE_NANO_PB` - Protocol buffer format
- **CRC:** CRC32 checksum (covers Format + Msg ID + Timestamp + Data)

## Communication Protocol

### Connection Sequence
```
Host                      STM32
 │                          │
 ├──── "connect 11" ───────▶│
 │◄──── "connect 11" ───────┤
 │                          │
 │   Connected              │
```

### Message Exchange
```
Host                      STM32
 │                          │
 ├──── Test Command ───────▶│
 │   (with CRC)             │
 │                          │
 │◄──── Test Response ──────┤
 │   (with CRC)             │
```

## Usage Examples

### Basic Connection
```python
from lowsheen_lib.proto_utils.VCUComm import VCUComm

# Create VCU communication object
vcu = VCUComm(STM_IP="192.168.3.100")

# Connect to STM32
vcu.try_cpu_stm_connect(reset_on_connect=False)
```

### Sending Test Commands
```python
from lowsheen_lib.proto_utils.cliff_test import TestObject

# Create test object
tester = TestObject()

# Send motor command
response = tester.send_test_msg(
    motor_timestamp=0,
    drive_command1=0.5,    # Left PWM
    drive_command2=0.5,    # Right PWM
    state_flags=268,       # State flags
    imu_flags=6            # IMU flags
)

print(response)
```

### Custom Message Creation
```python
from lowsheen_lib.proto_utils.proto_msgs import ProtoMsgs
from comm_messages_pb2 import CommMsgBody

# Create message handler
proto = ProtoMsgs()

# Create protobuf message
msg = CommMsgBody()
msg.test_command_req.timestamp = proto.generate_timestamp()
msg.test_command_req.pwm_left = 100

# Serialize
body_data = msg.SerializeToString()

# Create header with CRC
header = proto._create_header(body_data)

# Combine
packet = proto._combine_hdr_and_body(header, body_data)
```

## Thread Safety

The module implements thread-safe communication using three locks:

| Lock | Purpose |
|------|---------|
| `_commands_lock` | Protects command sending during connection |
| `_request_lock` | Protects request operations |
| `_host_packet_lock` | Protects packet transmission |

## Constants

### Port Configuration
- `BASE_PORT`: 8124
- `CONNECT_ENDPOINT`: 0x00
- `COMM_PORT_OFFSET`: 0x20
- **Connect Port:** 8124 (BASE_PORT + CONNECT_ENDPOINT)
- **Comm Port:** 8144 (BASE_PORT + COMM_PORT_OFFSET)

### Timing
- `MSG_RSP_TIMEOUT_MS`: 800ms (default response timeout)
- Connection retry interval: 100ms

### Message Limits
- `ETHERNET_MAX_MTU_SIZE`: 1500 bytes
- `FW_MSG_HEADER_SIZE`: Defined in header module

## Dependencies

### External Modules
- `socket` - UDP socket communication
- `select` - Socket polling for timeouts
- `threading.Lock` - Thread synchronization
- `zlib` - CRC32 calculation
- `io.StringIO` - Buffer operations

### Internal Modules
- `header` - Header structure definitions
- `comm_messages_pb2` - Protocol buffer definitions

## Error Handling

### Connection Errors
```python
try:
    vcu.try_cpu_stm_connect()
except Exception as e:
    print(f"Connection failed: {e}")
```

### Transmission Errors
The `_send_comm_packet()` method implements automatic retry (max 3 attempts).

### Timeout Errors
```python
try:
    data = vcu.receive_msg(max_bytes_to_get)
except socket.error:
    print("Timeout waiting for response")
```

## Testing

Run the test script:
```bash
cd src/lowsheen_lib/proto_utils
python cliff_test.py
```

## Related Documentation

- [Agilent_N5182A_API_Analysis.md](./Agilent_N5182A_API_Analysis.md) - Signal generator API
- [AnalogDiscovery2_API_Analysis.md](./AnalogDiscovery2_API_Analysis.md) - oscilloscope API
- [CMW100_API_Analysis.md](./CMW100_API_Analysis.md) - CMW100 analyzer API
- [PEAK_API_Analysis.md](./PEAK_API_Analysis.md) - PEAK CAN interface API
