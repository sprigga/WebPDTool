"""
Chassis Test Fixture Message Definitions

Refactored from PDTool4 polish/dut_comms/ltl_chassis_fixt_comms/chassis_msgs.py

All messages use big-endian byte order (network byte order).
Auto-registration system builds type_msg_map and req_rsp_map at module load time.
"""

import struct
import sys
from enum import Enum
from ctypes import c_uint8, c_uint16, c_uint32
from collections import OrderedDict
from inspect import isclass
from typing import Any, Dict, Type


# Global registries
type_msg_map: Dict[int, Type['LittleChassisTestMessage']] = {}
req_rsp_map: Dict[Type['LittleChassisTestMessage'], Type['LittleChassisTestMessage']] = {}
msg_packing_format_map: Dict[Type['LittleChassisTestMessage'], str] = {}
enum_map: Dict[str, Type[Enum]] = {}

# Protocol constants
SYNC_WORD = 0xA5FF00CC
TRANSPORT_OVERHEAD: int = 0  # Will be set after message registration


# Enumerations
class close_open_enum(Enum):
    """Door close/open states"""
    CLOSE = 0
    OPEN = 1


class left_right_enum(Enum):
    """Left/right encoder selection"""
    LEFT = 0
    RIGHT = 1


class status_enum(Enum):
    """Operation status codes"""
    SUCCESS = 0
    GENERAL_FAILURE = 1
    TIMEOUT_EXPIRED = 2


class operation_enum(Enum):
    """Turntable operation modes"""
    ROTATE_TO_OPTO_SWITCH = 0
    ROTATE_LEFT = 1
    ROTATE_RIGHT = 2


# Base message class
class LittleChassisTestMessage:
    """Base class for all chassis test messages"""
    msg_type: int = 0
    fields: OrderedDict = OrderedDict()
    name_type_map: OrderedDict = OrderedDict()
    field_enum_map: Dict[str, Type[Enum]] = {}

    def __init__(self):
        for name in self.fields:
            setattr(self, name, None)

    def __repr__(self):
        field_values = ', '.join(f'{name}={getattr(self, name)}' for name in self.fields)
        return f'{self.__class__.__name__}({field_values})'


# Transport messages
class TransportHeader(LittleChassisTestMessage):
    """Transport layer header"""
    msg_type = -10
    fields = OrderedDict((
        ('sync_word', c_uint32),
        ('length', c_uint16),
        ('msg_type', c_uint16),
    ))


class TransportFooter(LittleChassisTestMessage):
    """Transport layer footer with CRC16"""
    msg_type = -9
    fields = OrderedDict((
        ('crc16', c_uint16),
    ))


# Application messages
class ActuateCliffSensorDoor(LittleChassisTestMessage):
    """Command to open/close cliff sensor door"""
    msg_type = 0x10
    fields = OrderedDict((
        ('door_number', c_uint8),
        ('close_open', (c_uint8, close_open_enum)),
    ))


class ActuateCliffSensorDoorStatus(LittleChassisTestMessage):
    """Response for cliff sensor door actuation"""
    msg_type = 0x11
    fields = OrderedDict((
        ('status', (c_uint8, status_enum)),
    ))


class ReadEncoderCount(LittleChassisTestMessage):
    """Command to read encoder count"""
    msg_type = 0x12
    fields = OrderedDict((
        ('left_right', (c_uint8, left_right_enum)),
    ))


class EncoderCount(LittleChassisTestMessage):
    """Response with encoder count value"""
    msg_type = 0x13
    fields = OrderedDict((
        ('status', (c_uint8, status_enum)),
        ('count', c_uint32),
    ))


class WaitForTurntable(LittleChassisTestMessage):
    """Command to wait for turntable operation"""
    msg_type = 0x14
    fields = OrderedDict((
        ('timeout_seconds', c_uint8),
    ))


class WaitForTurntableStatus(LittleChassisTestMessage):
    """Response for turntable wait operation"""
    msg_type = 0x15
    fields = OrderedDict((
        ('status', (c_uint8, status_enum)),
    ))


class RotateTurntable(LittleChassisTestMessage):
    """Command to rotate turntable"""
    msg_type = 0x16
    fields = OrderedDict((
        ('operation', (c_uint8, operation_enum)),
        ('angle', c_uint16),
    ))


class RotateTurntableStatus(LittleChassisTestMessage):
    """Response for turntable rotation"""
    msg_type = 0x17
    fields = OrderedDict((
        ('status', (c_uint8, status_enum)),
    ))


class GetTurntableAngle(LittleChassisTestMessage):
    """Command to get current turntable angle"""
    msg_type = 0x1A
    fields = OrderedDict()


class TurntableAngleRsp(LittleChassisTestMessage):
    """Response with current turntable angle"""
    msg_type = 0x1B
    fields = OrderedDict((
        ('angle', c_uint16),
    ))


# Utility functions
def get_msg_size(msg: Any) -> int:
    """Get the serialized size of a message"""
    try:
        return struct.calcsize(msg_packing_format_map[msg])
    except KeyError:
        return struct.calcsize(msg_packing_format_map[type(msg)])


def get_values(msg_inst: LittleChassisTestMessage) -> list:
    """Extract field values from message instance"""
    values = []
    for name in msg_inst.fields:
        values.append(getattr(msg_inst, name))
    return values


def serialize(msg_inst: LittleChassisTestMessage) -> bytes:
    """Serialize message to bytes"""
    return struct.pack(msg_packing_format_map[type(msg_inst)], *get_values(msg_inst))


def deserialize(msg_class: Type[LittleChassisTestMessage], msg_blob: bytes) -> LittleChassisTestMessage:
    """Deserialize bytes to message instance"""
    msg = msg_class()
    values = struct.unpack(msg_packing_format_map[msg_class], msg_blob)
    for name, value in zip(msg_class.fields, values):
        setattr(msg, name, value)
    return msg


def build_msg_packing_format(msg: Type[LittleChassisTestMessage]) -> str:
    """Build struct packing format string for message"""
    # Add type map
    msg.name_type_map = OrderedDict()
    str_source = ['!']  # Network byte order (big-endian)

    for name, definition in msg.fields.items():
        try:
            ct_type = definition[0]
        except (TypeError, IndexError):
            ct_type = definition

        format_type = ct_type._type_
        str_source.append(format_type)

        msg.name_type_map[name] = ct_type

    return ''.join(str_source)


def build_enum_map(msg: Type[LittleChassisTestMessage]) -> Dict[str, Type[Enum]]:
    """Build map of field names to enum types"""
    field_enum_map = {}
    for name, definition in msg.fields.items():
        try:
            enum = definition[1]
            field_enum_map[name] = enum
        except (TypeError, IndexError):
            pass
    return field_enum_map


# Auto-registration: Scan module and register all message classes
module = sys.modules[__name__]

for name in dir(module):
    obj = getattr(module, name)
    # Register message classes
    if hasattr(obj, 'msg_type') and hasattr(obj, 'fields'):
        msg = obj
        module.type_msg_map[msg.msg_type] = msg
        module.msg_packing_format_map[msg] = build_msg_packing_format(msg)
        msg.field_enum_map = build_enum_map(msg)

    # Register enum classes
    if obj is not Enum and isclass(obj) and issubclass(obj, Enum):
        module.enum_map[obj.__name__] = obj

# Build request-response map (even msg_type -> odd msg_type + 1)
for msg_type, msg in module.type_msg_map.items():
    if msg_type % 2 == 0 and msg_type >= 0:
        rsp_type = msg_type + 1
        if rsp_type in module.type_msg_map:
            module.req_rsp_map[msg] = module.type_msg_map[rsp_type]

# Calculate transport overhead
module.TRANSPORT_OVERHEAD = get_msg_size(module.TransportHeader) + get_msg_size(module.TransportFooter)
module.HEADER_SIZE = get_msg_size(module.TransportHeader)
module.FOOTER_SIZE = get_msg_size(module.TransportFooter)

assert module.TRANSPORT_OVERHEAD > 0, "TRANSPORT_OVERHEAD must be positive"

module.c_defines = {
    'SYNC_WORD': hex(module.SYNC_WORD),
    'TRANSPORT_OVERHEAD': module.TRANSPORT_OVERHEAD
}


if __name__ == '__main__':
    from pprint import pprint

    print("=== Message Type Map ===")
    pprint(type_msg_map)

    print("\n=== Packing Format Map ===")
    pprint(msg_packing_format_map)

    print("\n=== Request-Response Map ===")
    pprint(req_rsp_map)

    print("\n=== Message Details ===")
    for msg_type, msg in sorted(type_msg_map.items()):
        print(f"{msg_type}: {msg}")
        pprint(msg.field_enum_map)

    print("\n=== Enum Map ===")
    pprint(enum_map)

    # Test serialization
    print("\n=== Serialization Test ===")
    m = ActuateCliffSensorDoor()
    m.door_number = 4
    m.close_open = close_open_enum.OPEN.value
    print(f"Original: {m}")

    blob = serialize(m)
    print(f"Serialized: {blob.hex()}")

    recv_msg = deserialize(ActuateCliffSensorDoor, blob)
    print(f"Deserialized: {recv_msg}")
    print(f"  door_number: {recv_msg.door_number}")
    print(f"  close_open: {recv_msg.close_open}")
