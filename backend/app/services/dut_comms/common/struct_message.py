"""
StructMessage - Base class for binary message serialization/deserialization.

This is a shared base class used across all DUT communication modules (ls_comms,
ltl_chassis_fixt_comms, vcu_ether_comms) for consistent binary message handling.

Refactored from PDTool4 polish/dut_comms modules.
"""
import struct
import ctypes
from typing import Any, List
from collections import OrderedDict


class StructMessage:
    """
    Base class for binary message serialization and deserialization.

    Subclasses must define:
    - fields: OrderedDict mapping field names to ctypes types
    - pack_str: struct.pack format string

    Example:
        class MyMessage(StructMessage):
            fields = OrderedDict([
                ("command", ctypes.c_uint8),
                ("param1", ctypes.c_uint16),
            ])
            pack_str = "<BH"
    """

    fields: OrderedDict = OrderedDict()
    pack_str: str = ""

    def __init__(self):
        """Initialize all fields to None."""
        for name in self.fields:
            setattr(self, name, None)

    def get_msg_size(self) -> int:
        """Calculate the total message size in bytes."""
        return struct.calcsize(self.pack_str)

    def get_values(self) -> List[Any]:
        """Get current field values as a list."""
        return [getattr(self, name) for name in self.fields]

    def serialize(self) -> bytes:
        """
        Serialize the message to bytes.

        Returns:
            bytes: Serialized message binary data
        """
        try:
            return struct.pack(self.pack_str, *self.get_values())
        except struct.error as e:
            raise ValueError(f"Failed to serialize {self.__class__.__name__}: {e}")

    def deserialize(self, msg_blob: bytes) -> None:
        """
        Deserialize bytes into this message object.

        Args:
            msg_blob: Binary message data to deserialize

        Raises:
            ValueError: If deserialization fails
        """
        try:
            values = struct.unpack(self.pack_str, msg_blob)
            for name, value in zip(self.fields, values):
                setattr(self, name, value)
        except struct.error as e:
            raise ValueError(f"Failed to deserialize {self.__class__.__name__}: {e}")

    def __repr__(self) -> str:
        """String representation showing field values."""
        field_strs = []
        for name in self.fields:
            value = getattr(self, name)
            field_strs.append(f"{name}={value}")
        return f"{self.__class__.__name__}({', '.join(field_strs)})"


def build_msg_packing_format(msg_class: type) -> str:
    """
    Build struct packing format string from a StructMessage class.

    Args:
        msg_class: StructMessage subclass

    Returns:
        str: struct.pack format string (e.g., "<BBHI")
    """
    format_parts = ["<"]  # Little-endian by default

    for field_name, field_type in msg_class.fields.items():
        # Map ctypes to struct format characters
        type_map = {
            ctypes.c_uint8: 'B',
            ctypes.c_int8: 'b',
            ctypes.c_uint16: 'H',
            ctypes.c_int16: 'h',
            ctypes.c_uint32: 'I',
            ctypes.c_int32: 'i',
            ctypes.c_uint64: 'Q',
            ctypes.c_int64: 'q',
            ctypes.c_float: 'f',
            ctypes.c_double: 'd',
        }

        if field_type in type_map:
            format_parts.append(type_map[field_type])
        elif hasattr(field_type, '_length_'):
            # Array type
            base_type = field_type._type_
            length = field_type._length_
            format_parts.append(type_map.get(base_type, 'B') * length)
        else:
            # Default to unsigned int
            format_parts.append('I')

    return ''.join(format_parts)


def get_values(msg_inst: StructMessage) -> List[Any]:
    """
    Get field values from a message instance.

    Args:
        msg_inst: StructMessage instance

    Returns:
        List of field values in order
    """
    return [getattr(msg_inst, name) for name in msg_inst.fields]
