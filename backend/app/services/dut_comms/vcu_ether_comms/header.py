"""
VCU Communication Message Header Definition

Defines the binary message header structure for VCU Ethernet communication.
Refactored from PDTool4 polish/dut_comms/vcu_ether_comms/header.py (50 lines).

Message Header Format (12 bytes):
    Offset 0-1:   Sync: 0xCAFE (16-bit)
    Offset 2-3:   Length: Message body length (16-bit)
    Offset 4-7:   CRC32: Checksum (32-bit)
    Offset 8-9:   Message Format: Format type (16-bit)
    Offset 10-11: Reserved: Reserved field (16-bit)

The CRC32 covers everything from offset 8 onwards (message_format + body).
"""
from collections import OrderedDict
import ctypes
from app.services.dut_comms.common.struct_message import StructMessage


# Constants
MAGIC_SYNC_U16 = 0xCAFE
MESSAGE_FORMAT_BARE_NANO_PB = 1  # Protocol Buffers (NanoPB)
MESSAGE_FORMAT_C_STRUCT = 3
MAX_MESSAGE_BODY_LENGTH = 1000

# Response codes
COMM_MSG_OK = 1
COMM_MSG_GENERAL_ERROR = 2
COMM_MSG_EEPROM_DATA_CRC_FAILED = 3
COMM_MSG_EEPROM_READ_FAILED = 4


class CommMsgHeader_t(StructMessage):
    """
    VCU Communication Message Header.

    12-byte header with sync, length, CRC, and format information.
    """
    fields = OrderedDict([
        ("sync", ctypes.c_uint16),         # 0xCAFE sync word
        ("length", ctypes.c_uint16),       # Message body length
        ("crc", ctypes.c_uint32),          # CRC32 checksum
        ("message_format", ctypes.c_uint16),  # Message format (1=Protobuf, 3=C struct)
        ("reserved", ctypes.c_uint16),     # Reserved for future use
    ])
    pack_str = "<HHIHH"

    def is_valid(self) -> bool:
        """Check if header has valid sync word."""
        return self.sync == MAGIC_SYNC_U16

    def is_valid_length(self) -> bool:
        """Check if length is within valid range."""
        try:
            return self.length is not None and 0 < self.length <= MAX_MESSAGE_BODY_LENGTH
        except (TypeError, AttributeError):
            return False


def create_header(body: bytes, message_format: int = MESSAGE_FORMAT_BARE_NANO_PB) -> CommMsgHeader_t:
    """
    Create a message header for a given message body.

    Args:
        body: Serialized message body
        message_format: Message format type (default: Protocol Buffers)

    Returns:
        CommMsgHeader_t: Created header with calculated CRC
    """
    import zlib
    import struct

    header = CommMsgHeader_t()
    header.sync = MAGIC_SYNC_U16
    header.length = len(body)
    header.message_format = message_format
    header.reserved = 0

    # Calculate CRC (covers offset 8+)
    CRC_OFFSET = 8
    header_str = struct.pack("<HHIHH",
        header.sync, header.length, 0,  # CRC placeholder
        header.message_format, header.reserved
    )
    trimmed_header_str = header_str[CRC_OFFSET:]
    header_crc_part = zlib.crc32(trimmed_header_str) & 0xFFFFFFFF
    crc = zlib.crc32(body, header_crc_part) & 0xFFFFFFFF
    header.crc = crc

    return header


def calculate_crc(header_str: bytes, body_str: bytes) -> int:
    """
    Calculate CRC32 checksum for VCU protocol.

    Args:
        header_str: Serialized header (12 bytes)
        body_str: Serialized message body

    Returns:
        int: CRC32 checksum
    """
    import zlib

    CRC_OFFSET = 8
    trimmed_header_str = header_str[CRC_OFFSET:]
    header_crc_part = zlib.crc32(trimmed_header_str) & 0xFFFFFFFF
    crc = zlib.crc32(body_str, header_crc_part) & 0xFFFFFFFF
    return crc
