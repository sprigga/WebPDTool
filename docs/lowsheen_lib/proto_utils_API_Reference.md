# Proto Utils API Reference

Complete API reference for the `proto_utils` module.

## Table of Contents

1. [VCUComm Class](#vcucomm-class)
2. [ProtoMsgs Class](#protomsgs-class)
3. [TestObject Class](#testobject-class)

---

## VCUComm Class

**File:** `src/lowsheen_lib/proto_utils/VCUComm.py`

Python interface between host and STM32 device using UDP sockets.

### Class Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `CONNECT_ENDPOINT` | int | `0x00` | Connection endpoint offset |
| `COMM_PORT_OFFSET` | int | `0x20` | Communication port offset |
| `BASE_PORT` | int | `8124` | Base UDP port number |
| `MSG_RSP_TIMEOUT_MS` | int | `800` | Message response timeout in milliseconds |

### Constructor

```python
VCUComm(STM_IP="192.168.3.100", enable_ethernet_communication=True)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `STM_IP` | str | `"192.168.3.100"` | IP address of STM32 device |
| `enable_ethernet_communication` | bool | `True` | Enable Ethernet communication |

**Example:**
```python
vcu = VCUComm(STM_IP="192.168.3.100")
```

### Methods

#### try_cpu_stm_connect()

Establish connection to STM32 device with retry logic.

```python
try_cpu_stm_connect(num_tries=100, test_version=True, reset_on_connect=True)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `num_tries` | int | `100` | Maximum connection attempts (min 30 if reset_on_connect=True) |
| `test_version` | bool | `True` | Test version compatibility |
| `reset_on_connect` | bool | `True` | Reset device on connection |

**Raises:**
- `Exception` - If connection fails after all retries

**Example:**
```python
vcu = VCUComm()
try:
    vcu.try_cpu_stm_connect(num_tries=50, reset_on_connect=False)
    print("Connected successfully")
except Exception as e:
    print(f"Connection failed: {e}")
```

#### _send_comm_packet()

Send a communication packet with automatic retry.

```python
_send_comm_packet(msg_to_send)
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `msg_to_send` | bytes | Serialized message to send |

**Behavior:**
- Attempts to send packet up to 3 times
- Automatically reconnects if not connected
- Thread-safe (uses `_host_packet_lock`)

**Example:**
```python
packet = create_test_packet()
vcu._send_comm_packet(packet)
```

#### receive_msg()

Receive a message from the communication socket.

```python
receive_msg(max_bytes_to_get)
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `max_bytes_to_get` | int | Maximum bytes to receive |

**Returns:**
- `bytes` - Received packet data

**Raises:**
- `socket.error` - If timeout occurs (after 800ms)

**Example:**
```python
try:
    data = vcu.receive_msg(1500)
    print(f"Received {len(data)} bytes")
except socket.error:
    print("Receive timeout")
```

#### flush_rcv_queue()

Flush any garbage data in the receive queue.

```python
flush_rcv_queue()
```

**Example:**
```python
vcu.flush_rcv_queue()  # Clean receive buffer
```

#### release()

Release the connection and reset state.

```python
release()
```

**Example:**
```python
vcu.release()  # Disconnect
```

---

## ProtoMsgs Class

**File:** `src/lowsheen_lib/proto_utils/proto_msgs.py`

Handles protocol buffer message serialization and packet framing.

### Class Attributes

| Attribute | Type | Value | Description |
|-----------|------|-------|-------------|
| `CRC_OFFSET` | int | `8` | Byte offset where CRC calculation starts |
| `ETHERNET_MAX_MTU_SIZE` | int | `1500` | Maximum Ethernet packet size |
| `MAX_MESSAGE_BODY_SIZE` | int | `1500 - FW_MSG_HEADER_SIZE` | Maximum protobuf message size |

### Constructor

```python
ProtoMsgs()
```

**Example:**
```python
proto = ProtoMsgs()
```

### Methods

#### _create_header()

Create a packet header with sync, length, and CRC.

```python
_create_header(body_data)
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `body_data` | bytes | Serialized message body |

**Returns:**
- `bytes` - Serialized packet header

**Header Structure:**
```
+--------+--------+--------+--------+
|  Sync  | Length | Format |  CRC   |
| (2B)   | (2B)   | (1B)   | (4B)   |
+--------+--------+--------+--------+
```

**Example:**
```python
body = msg.SerializeToString()
header = proto._create_header(body)
```

#### get_crc()

Calculate CRC32 checksum for header and body.

```python
get_crc(incomplete_link_header_str, complete_serialized_body_str, header_len)
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `incomplete_link_header_str` | CommMsgHeader_t | Header object (CRC field will be calculated) |
| `complete_serialized_body_str` | bytes | Serialized message body |
| `header_len` | int | Header length in bytes |

**Returns:**
- `int` - CRC32 checksum (32-bit unsigned)

**Algorithm:**
1. Extract header bytes from CRC_OFFSET to header_len
2. Calculate CRC32 of header portion
3. Calculate CRC32 of body using header CRC as seed
4. Return combined CRC32

**Example:**
```python
crc = proto.get_crc(header, body, header_size)
```

#### _combine_hdr_and_body()

Combine header and body into complete packet.

```python
_combine_hdr_and_body(header_data, body_data)
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `header_data` | bytes | Serialized packet header |
| `body_data` | bytes | Serialized message body |

**Returns:**
- `bytes` - Complete packet (header + body)

**Example:**
```python
packet = proto._combine_hdr_and_body(header, body)
```

#### get_msg_from_packet()

Extract message body from received packet.

```python
get_msg_from_packet(rcvd_data)
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `rcvd_data` | bytes | Received packet data |

**Returns:**
- `bytes` - Message body (without header) or `None` if sync invalid

**Validation:**
- Checks `MAGIC_SYNC_U16` for packet validity
- Uses header length field to extract message

**Example:**
```python
msg_body = proto.get_msg_from_packet(received_packet)
if msg_body:
    print(f"Message: {msg_body}")
```

#### deserialize_message()

Deserialize protobuf message from packet.

```python
deserialize_message(rcvd_data)
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `rcvd_data` | bytes | Received packet data |

**Returns:**
- `CommMsgBody` - Deserialized protobuf message

**Example:**
```python
response = proto.deserialize_message(received_packet)
print(response.test_command_rsp.timestamp)
```

#### get_max_fw_proto_msg_size()

Get maximum firmware protocol message size.

```python
get_max_fw_proto_msg_size()
```

**Returns:**
- `int` - Maximum message size including header

**Example:**
```python
max_size = proto.get_max_fw_proto_msg_size()
buffer = bytearray(max_size)
```

---

## TestObject Class

**File:** `src/lowsheen_lib/proto_utils/cliff_test.py`

High-level interface for creating and sending test commands.

### Class Attributes

| Attribute | Type | Value | Description |
|-----------|------|-------|-------------|
| `CRC_OFFSET` | int | `8` | Byte offset for CRC calculation |

### Constructor

```python
TestObject()
```

**Initializes:**
- Internal `ProtoMsgs` instance
- Initialization timestamp for relative time calculation

**Example:**
```python
tester = TestObject()
```

### Methods

#### generate_timestamp()

Generate a millisecond timestamp relative to initialization.

```python
generate_timestamp()
```

**Returns:**
- `int` - Milliseconds since object creation

**Example:**
```python
ts = tester.generate_timestamp()
print(f"Timestamp: {ts} ms")
```

#### create_test_req_msg()

Create a test command request message.

```python
create_test_req_msg(motor_timestamp, timestamp=0, drive_command1=0,
                   drive_command2=0, state_flags=0, imu_flags=0,
                   beep_type=-1, vac=-1)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `motor_timestamp` | int | required | Motor command timestamp |
| `timestamp` | int | `0` | Message timestamp (0 = auto-generate) |
| `drive_command1` | int | `0` | Left PWM drive command |
| `drive_command2` | int | `0` | Right PWM drive command |
| `state_flags` | int | `0` | State flags bitmask |
| `imu_flags` | int | `0` | IMU flags |
| `beep_type` | int | `-1` | Beep type (-1 = no beep) |
| `vac` | int | `-1` | VAC value |

**Returns:**
- `bytes` - Complete packet with header and serialized body

**Example:**
```python
packet = tester.create_test_req_msg(
    motor_timestamp=12345,
    drive_command1=100,
    drive_command2=100,
    state_flags=268
)
```

#### send_test_msg()

Send test message and wait for response.

```python
send_test_msg(motor_timestamp=0, timestamp=0, drive_command1=0,
              drive_command2=0, state_flags=0, imu_flags=0,
              beep_type=-1, vac=-1)
```

**Parameters:** Same as `create_test_req_msg()`

**Returns:**
- `CommMsgBody` - Response message from STM32

**Process:**
1. Creates VCUComm instance
2. Connects to STM32
3. Creates and sends test request
4. Waits for response
5. Deserializes and returns response

**Example:**
```python
response = tester.send_test_msg(
    motor_timestamp=0,
    drive_command1=0.5,
    drive_command2=0.5,
    state_flags=268,
    imu_flags=6
)
print(f"Response timestamp: {response.test_command_rsp.timestamp}")
```

---

## Protocol Buffer Messages

### CommMsgBody

The main message structure defined in `comm_messages_pb2.py`.

#### Test Command Request Fields

| Field | Type | Description |
|-------|------|-------------|
| `test_command_req.timestamp` | uint32 | Message timestamp in milliseconds |
| `test_command_req.pwm_left` | int32 | Left motor PWM command |
| `test_command_req.pwm_right` | int32 | Right motor PWM command |
| `test_command_req.state_flags` | uint32 | State flags bitmask |
| `test_command_req.imu_flags` | uint32 | IMU configuration flags |
| `test_command_req.beep_type` | int32 | Beep type (-1 for none) |
| `test_command_req.vac` | int32 | VAC value |
| `test_command_req.motor_command_timestamp` | uint32 | Motor command reference timestamp |

#### Test Command Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `test_command_rsp.timestamp` | uint32 | Response timestamp |
| `test_command_rsp.timestamp_us` | uint32 | Microsecond timestamp |
| `test_command_rsp.status` | uint32 | Command status code |

---

## Constants

### Header Constants

```python
MAGIC_SYNC_U16 = 0xA5A5           # Packet synchronization
MESSAGE_FORMAT_BARE_NANO_PB = 1   # Protocol buffer format
FW_MSG_HEADER_SIZE = 10           # Firmware header size (bytes)
```

### Port Configuration

```python
BASE_PORT = 8124
CONNECT_ENDPOINT = 0x00
COMM_PORT_OFFSET = 0x20

# Calculated ports
CONNECT_PORT = BASE_PORT + CONNECT_ENDPOINT  # 8124
COMM_PORT = BASE_PORT + COMM_PORT_OFFSET     # 8144
```

---

## Complete Example

```python
#!/usr/bin/env python
from lowsheen_lib.proto_utils.cliff_test import TestObject
import time

# Create test interface
tester = TestObject()

# Connect and send motor command
try:
    response = tester.send_test_msg(
        motor_timestamp=0,
        drive_command1=100,   # Left motor at 100
        drive_command2=100,   # Right motor at 100
        state_flags=268,      # Enable state
        imu_flags=6           # Enable IMU
    )

    print(f"Timestamp: {response.test_command_rsp.timestamp}")
    print(f"Status: {response.test_command_rsp.status}")

except Exception as e:
    print(f"Error: {e}")
```

---

## Error Codes

| Error | Description | Solution |
|-------|-------------|----------|
| `Timeout trying to connect to Mule` | Connection timeout | Check STM32 IP address and network connection |
| `Timeout receiving data` | Response timeout | Check if STM32 is running and responsive |
| `USBError` | USB communication error | Check USB cable and connection |
