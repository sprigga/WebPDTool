# LTL Chassis Fixture Communication Module

Async serial communication with chassis test fixture using CRC16-Kermit protocol.

## Quick Start

### Installation

Required dependencies (already in `pyproject.toml`):
```bash
pip install pyserial pyserial-asyncio
```

### Basic Usage

```python
from app.services.dut_comms.ltl_chassis_fixt_comms import (
    rotate_turntable,
    get_turntable_angle,
    operation_enum,
    status_enum,
)

# Rotate turntable left 90 degrees
status = await rotate_turntable('/dev/ttyUSB0', operation_enum.ROTATE_LEFT, 90)
if status == status_enum.SUCCESS:
    print("Rotation successful!")

# Get current angle
angle = await get_turntable_angle('/dev/ttyUSB0')
print(f"Current angle: {angle}°")
```

## API Reference

### High-Level Functions

#### `rotate_turntable(port, operation, angle=0, timeout=5.0)`

Rotate the turntable.

**Parameters:**
- `port` (str): Serial port name (e.g., '/dev/ttyUSB0', 'COM3')
- `operation` (operation_enum): Rotation operation
  - `ROTATE_LEFT` - Rotate counterclockwise
  - `ROTATE_RIGHT` - Rotate clockwise
  - `ROTATE_TO_OPTO_SWITCH` - Return to home position
- `angle` (int): Target angle in degrees (0-359)
- `timeout` (float): Operation timeout in seconds

**Returns:** `status_enum` (SUCCESS, GENERAL_FAILURE, TIMEOUT_EXPIRED)

**Example:**
```python
# Rotate left 45 degrees
status = await rotate_turntable('/dev/ttyUSB0', operation_enum.ROTATE_LEFT, 45)

# Return to home position
status = await rotate_turntable(
    '/dev/ttyUSB0',
    operation_enum.ROTATE_TO_OPTO_SWITCH,
    0
)
```

---

#### `get_turntable_angle(port, timeout=2.0)`

Get current turntable angle.

**Parameters:**
- `port` (str): Serial port name
- `timeout` (float): Operation timeout in seconds

**Returns:** `int` - Current angle in degrees (0-359)

**Example:**
```python
angle = await get_turntable_angle('/dev/ttyUSB0')
print(f"Current position: {angle}°")
```

---

#### `wait_for_turntable(port, timeout_seconds=30, comm_timeout=35.0)`

Wait for turntable operation to complete.

**Parameters:**
- `port` (str): Serial port name
- `timeout_seconds` (int): Fixture operation timeout (sent to fixture)
- `comm_timeout` (float): Communication timeout (should be > timeout_seconds)

**Returns:** `status_enum`

**Example:**
```python
# Start a rotation
await rotate_turntable('/dev/ttyUSB0', operation_enum.ROTATE_LEFT, 180)

# Wait for completion
status = await wait_for_turntable('/dev/ttyUSB0', timeout_seconds=10)
```

---

#### `actuate_cliff_sensor_door(port, door_number, open_door, timeout=2.0)`

Open or close a cliff sensor door.

**Parameters:**
- `port` (str): Serial port name
- `door_number` (int): Door number (0-4)
- `open_door` (bool): True to open, False to close
- `timeout` (float): Operation timeout in seconds

**Returns:** `status_enum`

**Example:**
```python
# Open door 0
status = await actuate_cliff_sensor_door('/dev/ttyUSB0', 0, True)

# Close door 2
status = await actuate_cliff_sensor_door('/dev/ttyUSB0', 2, False)
```

---

#### `read_encoder_count(port, left_encoder=True, timeout=2.0)`

Read encoder count value.

**Parameters:**
- `port` (str): Serial port name
- `left_encoder` (bool): True for left encoder, False for right
- `timeout` (float): Operation timeout in seconds

**Returns:** `Tuple[status_enum, int]` - (status, count)

**Example:**
```python
# Read left encoder
status, count = await read_encoder_count('/dev/ttyUSB0', left_encoder=True)
if status == status_enum.SUCCESS:
    print(f"Left encoder count: {count}")

# Read right encoder
status, count = await read_encoder_count('/dev/ttyUSB0', left_encoder=False)
```

---

### Low-Level API

For advanced use cases requiring full control:

```python
from app.services.dut_comms.ltl_chassis_fixt_comms import (
    ChassisTransport,
    RotateTurntable,
    GetTurntableAngle,
    operation_enum,
)

async with ChassisTransport('/dev/ttyUSB0') as transport:
    # Create and send custom message
    msg = RotateTurntable()
    msg.operation = operation_enum.ROTATE_LEFT.value
    msg.angle = 90
    await transport.send_msg(msg)

    # Receive response
    header, response, footer = await transport.get_msg()
    print(f"Status: {response.status}")
```

---

## Protocol Details

### Communication Parameters

- **Serial Port:** 9600 baud, 8N1 (8 data bits, no parity, 1 stop bit)
- **Sync Word:** 0xA5FF00CC (4 bytes, big-endian)
- **Checksum:** CRC16-Kermit
- **Byte Order:** Big-endian (network byte order)

### Frame Format

```
[Header: 8 bytes] [Body: variable] [Footer: 2 bytes]

Header:
  sync_word: 4 bytes (0xA5FF00CC)
  length:    2 bytes (total frame length)
  msg_type:  2 bytes (message type ID)

Body:
  (varies by message type)

Footer:
  crc16:     2 bytes (CRC16-Kermit over header + body)
```

### Message Types

| Request | Response | Type ID | Description |
|---------|----------|---------|-------------|
| ActuateCliffSensorDoor | ActuateCliffSensorDoorStatus | 0x10/0x11 | Open/close cliff sensor door |
| ReadEncoderCount | EncoderCount | 0x12/0x13 | Read encoder count |
| WaitForTurntable | WaitForTurntableStatus | 0x14/0x15 | Wait for turntable operation |
| RotateTurntable | RotateTurntableStatus | 0x16/0x17 | Rotate turntable |
| GetTurntableAngle | TurntableAngleRsp | 0x1A/0x1B | Get current angle |

---

## Enumerations

### `operation_enum`

Turntable rotation operations:

```python
operation_enum.ROTATE_TO_OPTO_SWITCH  # Value: 0 - Return to home position
operation_enum.ROTATE_LEFT            # Value: 1 - Rotate counterclockwise
operation_enum.ROTATE_RIGHT           # Value: 2 - Rotate clockwise
```

### `status_enum`

Operation status codes:

```python
status_enum.SUCCESS           # Value: 0 - Operation successful
status_enum.GENERAL_FAILURE   # Value: 1 - Operation failed
status_enum.TIMEOUT_EXPIRED   # Value: 2 - Operation timed out
```

### `close_open_enum`

Door states:

```python
close_open_enum.CLOSE  # Value: 0 - Close door
close_open_enum.OPEN   # Value: 1 - Open door
```

### `left_right_enum`

Encoder selection:

```python
left_right_enum.LEFT   # Value: 0 - Left encoder
left_right_enum.RIGHT  # Value: 1 - Right encoder
```

---

## Error Handling

### Exception Hierarchy

```
ChassisTransportError (base exception)
├── ChassisCRCError          # CRC checksum mismatch
└── ChassisTimeoutError      # Communication timeout
```

### Example

```python
from app.services.dut_comms.ltl_chassis_fixt_comms import (
    rotate_turntable,
    ChassisTransportError,
    ChassisTimeoutError,
    operation_enum,
)

try:
    status = await rotate_turntable('/dev/ttyUSB0', operation_enum.ROTATE_LEFT, 90)
except ChassisTimeoutError:
    print("Communication timeout - check hardware connection")
except ChassisTransportError as e:
    print(f"Transport error: {e}")
```

---

## Complete Example

```python
import asyncio
from app.services.dut_comms.ltl_chassis_fixt_comms import (
    rotate_turntable,
    get_turntable_angle,
    actuate_cliff_sensor_door,
    read_encoder_count,
    operation_enum,
    status_enum,
)

async def test_chassis_fixture():
    """Complete chassis fixture test sequence"""
    port = '/dev/ttyUSB0'

    print("=== Chassis Fixture Test ===\n")

    # 1. Get initial angle
    print("1. Getting current turntable angle...")
    angle = await get_turntable_angle(port)
    print(f"   Current angle: {angle}°\n")

    # 2. Rotate left 45 degrees
    print("2. Rotating left 45°...")
    status = await rotate_turntable(port, operation_enum.ROTATE_LEFT, 45)
    print(f"   Status: {status.name}\n")

    await asyncio.sleep(1)

    # 3. Check new angle
    print("3. Verifying new angle...")
    angle = await get_turntable_angle(port)
    print(f"   Current angle: {angle}°\n")

    # 4. Return to home
    print("4. Returning to home position...")
    status = await rotate_turntable(port, operation_enum.ROTATE_TO_OPTO_SWITCH, 0)
    print(f"   Status: {status.name}\n")

    await asyncio.sleep(2)

    # 5. Read encoders
    print("5. Reading encoders...")
    status_l, count_l = await read_encoder_count(port, left_encoder=True)
    status_r, count_r = await read_encoder_count(port, left_encoder=False)
    print(f"   Left:  {count_l} (status: {status_l.name})")
    print(f"   Right: {count_r} (status: {status_r.name})\n")

    # 6. Open cliff sensor door
    print("6. Opening cliff sensor door 0...")
    status = await actuate_cliff_sensor_door(port, 0, True)
    print(f"   Status: {status.name}\n")

    await asyncio.sleep(1)

    # 7. Close cliff sensor door
    print("7. Closing cliff sensor door 0...")
    status = await actuate_cliff_sensor_door(port, 0, False)
    print(f"   Status: {status.name}\n")

    print("=== Test Complete ===")

# Run the test
if __name__ == '__main__':
    asyncio.run(test_chassis_fixture())
```

---

## Testing

Run unit tests:

```bash
pytest tests/services/test_chassis_comms.py -v
```

Test with actual hardware:

```bash
# Edit port name in chassis_api.py main section
python -m app.services.dut_comms.ltl_chassis_fixt_comms.chassis_api /dev/ttyUSB0
```

---

## Troubleshooting

### Port Access Issues

**Linux:**
```bash
# Add user to dialout group
sudo usermod -a -G dialout $USER
# Log out and log back in

# Or set permissions temporarily
sudo chmod 666 /dev/ttyUSB0
```

**Windows:**
- Check Device Manager for COM port number
- Ensure no other program is using the port

### Communication Failures

1. **Check baud rate:** Must be 9600
2. **Check cable:** Ensure proper TX/RX connections
3. **Check power:** Fixture must be powered on
4. **Check sync word:** Verify fixture firmware uses 0xA5FF00CC

### CRC Errors

- Verify byte order (big-endian)
- Check fixture firmware CRC implementation
- Enable debug logging to inspect raw frames

---

## References

- **CRC16-Kermit:** Implementation in `crc16_kermit.py`
- **Protocol Spec:** See `chassis_msgs.py` for message definitions
- **PDTool4 Original:** `polish/dut_comms/ltl_chassis_fixt_comms/`

---

**Last Updated:** 2026-01-30
**Version:** 1.0
