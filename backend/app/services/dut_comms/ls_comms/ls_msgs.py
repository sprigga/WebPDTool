"""
LS Series Message Definitions

Defines binary message structures for LS series safety interface communication.
Refactored from PDTool4 polish/dut_comms/ls_comms/ls_msgs.py.

Message Format:
    Offset 0-1:   Sync: 0xCA 0xFE (Little Endian: 0xFECA)
    Offset 2-3:   Length: 2 bytes
    Offset 4-7:   CRC: 4 bytes
    Offset 8-9:   Message Format: 2 bytes
    Offset 10-11:  Reserved: 2 bytes
    Offset 12:     Command: 1 byte
    Offset 13:     Response Indicator: 1 byte
    Offset 14:     Sensor: 1 byte
    Offset 15+:    Params: variable
"""
from collections import OrderedDict
import struct
import ctypes
from app.services.dut_comms.common.struct_message import StructMessage as BaseStructMessage


# Re-export base class for compatibility
StructMessage = BaseStructMessage


class MsgHeader(StructMessage):
    """LS message header (12 bytes)."""
    fields = OrderedDict([
        ("sync", ctypes.c_uint16),        # 0xCAFE
        ("length", ctypes.c_uint16),      # Message body length
        ("crc", ctypes.c_uint32),         # CRC32 checksum
        ("message_format", ctypes.c_uint16),  # Message format
        ("reserved", ctypes.c_uint16),    # Reserved
    ])
    pack_str = "<HHIHH"


class CliffMsgBody_t(StructMessage):
    """Cliff sensor message body (2 bytes)."""
    fields = OrderedDict([
        ("command", ctypes.c_uint8),      # Command ID
        ("params", ctypes.c_uint8),       # Parameters
    ])
    pack_str = "<BB"


class EncoderMsgBody_t(StructMessage):
    """Encoder message body (2 bytes)."""
    fields = OrderedDict([
        ("command", ctypes.c_uint8),      # Command ID
        ("params", ctypes.c_uint8),       # Parameters
    ])
    pack_str = "<BB"


# Command type definitions
CLIFF_MSG = 0
ENCODER_MSG = 1

# Command to message class mapping
command_msg_map = {
    CLIFF_MSG: CliffMsgBody_t,
    ENCODER_MSG: EncoderMsgBody_t,
}


def get_command_msg_class(command: int):
    """
    Get message class for a given command type.

    Args:
        command: Command ID (CLIFF_MSG or ENCODER_MSG)

    Returns:
        Message class for the command

    Raises:
        ValueError: If command is unknown
    """
    if command not in command_msg_map:
        raise ValueError(f"Unknown command type: {command}")
    return command_msg_map[command]
