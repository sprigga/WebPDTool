# Proto Utils Design Guide

This document describes the design patterns, architecture decisions, and implementation details of the `proto_utils` module.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Design Patterns](#design-patterns)
3. [Communication Protocol Design](#communication-protocol-design)
4. [Thread Safety](#thread-safety)
5. [Error Handling Strategy](#error-handling-strategy)
6. [Performance Considerations](#performance-considerations)

---

## Architecture Overview

### Layered Design

The module follows a strict layered architecture:

```
┌─────────────────────────────────────────────────────────┐
│  Application Layer (cliff_test.py)                      │
│  - TestObject: High-level motor control interface       │
└────────────────┬────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────┐
│  Communication Layer (VCUComm.py)                       │
│  - Connection management                               │
│  - Packet transmission                                 │
│  - Retry logic                                         │
└────────────────┬────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────┐
│  Protocol Layer (proto_msgs.py)                        │
│  - Message framing                                     │
│  - Serialization/deserialization                       │
│  - CRC calculation                                     │
└─────────────────────────────────────────────────────────┘
```

### Separation of Concerns

| Layer | Responsibility |
|-------|---------------|
| **Application** | Motor control logic, test orchestration |
| **Communication** | Network I/O, connection state management |
| **Protocol** | Message formatting, data integrity |

---

## Design Patterns

### 1. Facade Pattern

**TestObject** acts as a facade, simplifying the complex subsystem:

```python
# Without facade - complex, multi-step process
vcu = VCUComm()
vcu.try_cpu_stm_connect()
proto = ProtoMsgs()
msg = create_message()
header = proto._create_header(msg)
packet = proto._combine_hdr_and_body(header, msg)
vcu._send_comm_packet(packet)
response = vcu.receive_msg()
result = proto.deserialize_message(response)

# With facade - simple, single call
tester = TestObject()
result = tester.send_test_msg(drive_command1=100, drive_command2=100)
```

### 2. Template Method Pattern

Connection establishment uses template method:

```python
def _connect(self, wait_time=100, reset_on_connect=True, force_USB=False):
    # Template method defining connection algorithm
    start_time = time.time()

    while True:  # Retry loop
        if self._enable_ethernet_communication:
            # Step 1: Flush stale packets
            self._flush_stale_packets()

            # Step 2: Send connect message
            self._send_connect_message()

            # Step 3: Wait and verify response
            if self._verify_connection():
                break

        # Step 4: Check timeout
        if self._is_timeout(start_time, wait_time):
            raise Exception("Timeout")
```

### 3. Strategy Pattern

Multiple communication strategies (Ethernet, USB) can be selected:

```python
if self._enable_ethernet_communication:
    self._send_ethernet_message()
else:
    self._send_usb_message()
```

### 4. Singleton-like Behavior

**VCUComm** maintains single connection state:

```python
class VCUComm:
    def __init__(self):
        # Single socket pair for all communication
        self._connect_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._comm_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def release(self):
        # Reset connection state
        self._ethernet_connected = False
```

---

## Communication Protocol Design

### Protocol Stack

```
┌─────────────────────────────────────┐
│   Application Message               │
│   (Test Command/Response)           │
├─────────────────────────────────────┤
│   Protocol Buffers                  │
│   (Serialization)                   │
├─────────────────────────────────────┤
│   Custom Packet Format              │
│   (Header + Body + CRC)             │
├─────────────────────────────────────┤
│   UDP/IP                            │
│   (Transport)                       │
├─────────────────────────────────────┤
│   Ethernet                          │
│   (Physical)                        │
└─────────────────────────────────────┘
```

### Packet Design Rationale

#### Why UDP Instead of TCP?

| Factor | UDP Choice | Impact |
|--------|------------|--------|
| **Latency** | No connection overhead | Lower latency for motor control |
| **Speed** | No flow control | Faster transmission |
| **Overhead** | Smaller headers | Less bandwidth usage |
| **Reliability** | Best-effort only | Acceptable for real-time control |

#### Custom Header Design

```
+------+------+------+------+------+------+
| Sync | Len  | Fmt  | CRC  | ID   | TS   |
| 2B   | 2B   | 1B   | 4B   | 1B   | 4B   |
+------+------+------+------+------+------+
```

**Design Decisions:**

1. **Sync (2 bytes)**: `0xA5A5` - Distinct pattern for frame detection
2. **Length (2 bytes)**: Variable-length message support
3. **Format (1 byte)**: Protocol versioning and format negotiation
4. **CRC (4 bytes)**: CRC32 for error detection
5. **ID (1 byte)**: Message type identifier
6. **Timestamp (4 bytes)**: Timing synchronization

#### CRC Calculation Strategy

```python
def get_crc(self, header, body, header_len):
    # CRC covers everything after CRC field
    trimmed_header = header[CRC_OFFSET:header_len]
    header_crc = zlib.crc32(trimmed_header)

    # Use header CRC as seed for body CRC
    final_crc = zlib.crc32(body, header_crc)

    return final_crc & 0xFFFFFFFF  # Ensure unsigned
```

**Why this approach?**
- CRC field excluded from calculation (set to 0)
- Sequential calculation allows streaming verification
- CRC32 chosen for speed vs. error detection tradeoff

---

## Thread Safety

### Lock Strategy

Three locks protect different resources:

```python
class VCUComm:
    def __init__(self):
        self._commands_lock = Lock()      # Command serialization
        self._request_lock = Lock()       # Request serialization
        self._host_packet_lock = Lock()   # Packet transmission
```

### Lock Usage Matrix

| Lock | Protected Resource | Held During |
|------|-------------------|-------------|
| `_commands_lock` | Connection state | `try_cpu_stm_connect()` |
| `_request_lock` | Request queue | Pending requests |
| `_host_packet_lock` | Socket write | `_send_comm_packet()` |

### Thread Safety Analysis

```python
# SAFE: Multiple threads can read concurrently
def _receive_eth_msg(self, sock, size, timeout_ms=20):
    # Socket read is thread-safe in Python
    return sock.recv(size)

# SAFE: Write protected by lock
def _send_comm_packet(self, msg_to_send):
    with self._host_packet_lock:  # Critical section
        self._comm_sock.sendto(msg_to_send, ...)

# SAFE: Connection protected by lock
def try_cpu_stm_connect(self, ...):
    with self._commands_lock:  # Critical section
        self._connect(...)
```

---

## Error Handling Strategy

### Retry Philosophy

**Automatic Retry** for transient errors:

```python
def _send_comm_packet(self, msg_to_send):
    max_tries = 3
    for i in range(max_tries):
        try:
            self._send_comm_eth_msg(msg_to_send)
            break  # Success
        except USBError:
            if i == (max_tries - 1):
                raise  # Re-raise on final attempt
        except:
            pass  # Silently retry on other errors
```

### Timeout Handling

**Exponential Backoff** not used - fixed timeout for determinism:

```python
def _receive_eth_msg(self, sock, size, timeout_ms=20):
    if select.select([sock], [], [], timeout_ms/1000.0)[0]:
        return sock.recv(size)
    raise socket.error("Timeout receiving data")
```

**Response timeout strategy:**

```python
def receive_msg(self, max_bytes_to_get):
    try:
        # First attempt with standard timeout
        packet = self._receive_eth_msg(sock=self._comm_sock,
                                       size=max_bytes_to_get,
                                       timeout_ms=self.MSG_RSP_TIMEOUT_MS)
    except socket.error:
        # Single retry on timeout
        packet = self._receive_eth_msg(sock=self._comm_sock,
                                       size=max_bytes_to_get,
                                       timeout_ms=self.MSG_RSP_TIMEOUT_MS)
    return packet
```

### Connection Recovery

```python
def _send_comm_packet(self, msg_to_send):
    for i in range(max_tries):
        try:
            if self._ethernet_connected:
                self._send_comm_eth_msg(msg_to_send)
            else:
                # Auto-reconnect on disconnected state
                self.try_cpu_stm_connect()
                raise IOError
```

---

## Performance Considerations

### Buffer Management

**Pre-allocated buffers** for efficiency:

```python
def receive_msg(self, max_bytes_to_get):
    # Receive directly into specified size
    packet = self._receive_eth_msg(sock=self._comm_sock,
                                   size=max_bytes_to_get,
                                   timeout_ms=self.MSG_RSP_TIMEOUT_MS)
    return packet
```

### Socket Options

**UDP socket optimization:**

```python
# Non-blocking receive with select
if select.select([sock], [], [], timeout_ms/1000.0)[0]:
    return sock.recv(size)

# Flush stale packets without blocking
if select.select([self._connect_sock], [], [], 0.010)[0]:
    self._connect_sock.recv(4096)
```

### Message Size Limits

```python
ETHERNET_MAX_MTU_SIZE = 1500  # Standard Ethernet MTU
MAX_MESSAGE_BODY_SIZE = ETHERNET_MAX_MTU_SIZE - FW_MSG_HEADER_SIZE
```

**Rationale:**
- Fits within single Ethernet frame
- Avoids IP fragmentation
- Reduces memory allocation

### Connection Caching

```python
def _connect(self, wait_time=100, reset_on_connect=True):
    if self._enable_ethernet_communication and self._ethernet_connected:
        return  # Early exit - already connected
```

---

## Design Trade-offs

### Chosen: UDP over TCP

| Advantage | Disadvantage |
|-----------|--------------|
| Lower latency | No guaranteed delivery |
| Less overhead | No flow control |
| Simpler implementation | No congestion control |

**Mitigation:** Application-level retry and CRC validation

### Chosen: Custom Header over Standard Protocols

| Advantage | Disadvantage |
|-----------|--------------|
| Optimized for use case | Non-standard |
| Smaller overhead | Less interoperability |
| Full control | More maintenance |

### Chosen: Thread Locks over Async

| Advantage | Disadvantage |
|-----------|--------------|
| Simple implementation | Limited concurrency |
| Predictable behavior | Lower throughput |
| Easy debugging | Blocking operations |

---

## Extension Points

### Adding New Message Types

```python
# 1. Define in comm_messages_pb2.py
message NewCommand {
    uint32 param1 = 1;
    uint32 param2 = 2;
}

# 2. Extend ProtoMsgs
def create_new_command(self, param1, param2):
    msg = CommMsgBody()
    msg.new_command.param1 = param1
    msg.new_command.param2 = param2
    return self._finalize_message(msg)

# 3. Extend TestObject
def send_new_command(self, param1, param2):
    return self.send_test_msg(new_command=True, param1=param1, param2=param2)
```

### Alternative Transport Layers

```python
class VCUComm:
    def _send_comm_packet(self, msg_to_send):
        if self._transport == 'ethernet':
            self._send_ethernet(msg_to_send)
        elif self._transport == 'serial':
            self._send_serial(msg_to_send)
        elif self._transport == 'usb':
            self._send_usb(msg_to_send)
```

---

## Future Improvements

1. **Async/Await**: Migrate to `asyncio` for better concurrency
2. **Connection Pooling**: Support multiple simultaneous connections
3. **Message Queuing**: Implement request queue for batching
4. **Compression**: Add compression for large payloads
5. **Encryption**: Add security layer for sensitive data
6. **Metrics**: Add performance monitoring and logging

---

## References

- **Protocol Buffers**: [https://developers.google.com/protocol-buffers](https://developers.google.com/protocol-buffers)
- **UDP Programming**: [https://docs.python.org/3/library/socket.html](https://docs.python.org/3/library/socket.html)
- **Python Threading**: [https://docs.python.org/3/library/threading.html](https://docs.python.org/3/library/threading.html)
- **CRC32**: [https://docs.python.org/3/library/zlib.html](https://docs.python.org/3/library/zlib.html)
