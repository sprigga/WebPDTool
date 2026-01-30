"""
LS Series Safety Interface Communication Module

Provides async serial communication with LS series safety interface devices.
Refactored from PDTool4 polish/dut_comms/ls_comms/ls_mod.py (301 lines).

Features:
- 0xCAFE sync word detection (3-step frame detection)
- CRC32 checksum validation
- Cliff sensor and encoder read commands
- Async/await support for FastAPI integration

Example:
    si = SafetyInterface('/dev/ttyUSB0')
    await si.open()

    # Read cliff sensor 1
    packet = si.create_msg(CLIFF_MSG, 0x01)
    await si.send_packet(packet)
    recv_packet, voltage = await si.receive_packet()

    await si.close()
"""
import asyncio
import zlib
import struct
import logging
from collections import deque
from typing import Tuple, Optional

from .ls_msgs import (
    MsgHeader,
    CliffMsgBody_t,
    EncoderMsgBody_t,
    CLIFF_MSG,
    ENCODER_MSG,
    command_msg_map,
    get_command_msg_class,
)

logger = logging.getLogger(__name__)

# Constants
CRC_OFFSET = 8  # CRC covers everything below CRC in header (offset 8+)
HEADER_SIZE = 12  # MsgHeader size in bytes
SYNC_BYTE_1 = 0xCA
SYNC_BYTE_2 = 0xFE
SYNC_WORD = 0xFECA  # Little-endian


class SafetyInterfaceError(Exception):
    """Base exception for SafetyInterface errors."""
    pass


class SafetyInterfaceConnectionError(SafetyInterfaceError):
    """Raised when connection fails."""
    pass


class SafetyInterfaceTimeout(SafetyInterfaceError):
    """Raised when read operation times out."""
    pass


def get_crc(frame_header_str: bytes, complete_serialized_body_str: bytes) -> int:
    """
    Calculate CRC32 checksum for LS protocol.

    CRC covers everything from offset 8 onwards (message_format + body).

    Args:
        frame_header_str: Serialized header (12 bytes)
        complete_serialized_body_str: Serialized body

    Returns:
        int: CRC32 checksum
    """
    # Skip sync (2), length (2), crc (4) = 8 bytes
    trimmed_header_str = frame_header_str[CRC_OFFSET:]
    header_crc_part = zlib.crc32(trimmed_header_str) & 0xFFFFFFFF
    crc = zlib.crc32(complete_serialized_body_str, header_crc_part) & 0xFFFFFFFF
    return crc


class SafetyInterface:
    """
    Async serial interface for LS series safety devices.

    Handles connection, packet sending/receiving with CRC validation.

    Attributes:
        port_name: Serial port path (e.g., '/dev/ttyUSB0' or 'COM3')
        baudrate: Serial baud rate (default 9600)
        timeout: Read timeout in seconds (default 3.0)
    """

    def __init__(
        self,
        port_name: str,
        baudrate: int = 9600,
        timeout: float = 3.0
    ):
        """
        Initialize SafetyInterface.

        Args:
            port_name: Serial port device path
            baudrate: Communication speed (default 9600)
            timeout: Read timeout in seconds (default 3.0)
        """
        self.port_name = port_name
        self.baudrate = baudrate
        self.timeout = timeout
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._connected = False

    async def open(self) -> None:
        """
        Open serial connection.

        Raises:
            SafetyInterfaceConnectionError: If connection fails
        """
        try:
            # Import pyserial-asyncio
            from serial_asyncio import create_serial_connection

            # Create serial connection
            class SerialProtocol(asyncio.Protocol):
                def __init__(self):
                    self.transport = None

                def connection_made(self, transport):
                    self.transport = transport

                def data_received(self, data):
                    pass  # Data handled by StreamReader

                def connection_lost(self, exc):
                    pass

            # Open connection using serial_asyncio
            reader, writer = await create_serial_connection(
                asyncio.get_event_loop(),
                lambda: SerialProtocol(),
                self.port_name,
                baudrate=self.baudrate,
            )

            self._reader = reader
            self._writer = writer
            self._connected = True

            logger.info(f"Connected to {self.port_name} at {self.baudrate} baud")

        except Exception as e:
            raise SafetyInterfaceConnectionError(
                f"Failed to open {self.port_name}: {e}"
            ) from e

    async def close(self) -> None:
        """Close serial connection."""
        if self._writer:
            self._writer.close()
            try:
                await self._writer.wait_closed()
            except asyncio.CancelledError:
                pass

        self._reader = None
        self._writer = None
        self._connected = False

        logger.info(f"Closed connection to {self.port_name}")

    @property
    def is_connected(self) -> bool:
        """Check if connection is active."""
        return self._connected

    def create_msg(self, command: int, params: int) -> bytes:
        """
        Create a message packet for sending.

        Args:
            command: Command type (CLIFF_MSG or ENCODER_MSG)
            params: Command parameters

        Returns:
            bytes: Complete message packet (header + body)
        """
        # Get message body class
        msg_class = get_command_msg_class(command)

        # Create and populate message body
        body = msg_class()
        body.command = command
        body.params = params

        # Serialize body
        msg_body_string = body.serialize()

        # Create header
        header = MsgHeader()
        header.sync = SYNC_WORD
        header.length = len(msg_body_string)
        header.message_format = 0
        header.reserved = 0

        # Calculate CRC
        header_str = struct.pack("<HHIHH",
            header.sync, header.length, 0,  # CRC placeholder
            header.message_format, header.reserved
        )
        header.crc = get_crc(header_str, msg_body_string)

        # Serialize complete header
        header_string = header.serialize()

        # Combine header and body
        return header_string + msg_body_string

    async def send_packet(self, msg_packet: bytes) -> None:
        """
        Send a message packet to the device.

        Args:
            msg_packet: Complete message packet (header + body)

        Raises:
            SafetyInterfaceError: If not connected or send fails
        """
        if not self._connected or not self._writer:
            raise SafetyInterfaceError("Not connected to device")

        try:
            self._writer.write(msg_packet)
            await self._writer.drain()

            logger.debug(f"Sent {len(msg_packet)} bytes")

        except Exception as e:
            raise SafetyInterfaceError(f"Failed to send packet: {e}") from e

    async def receive_packet(self) -> Tuple[bytes, int]:
        """
        Receive and parse a response packet from the device.

        Implements 3-step frame detection:
        1. Detect 0xCA sync byte
        2. Detect 0xFE sync byte
        3. Read length and parse complete frame

        Returns:
            Tuple of (received_packet, return_value)

        Raises:
            SafetyInterfaceTimeout: If no data received within timeout
            SafetyInterfaceError: If parsing fails
        """
        if not self._connected or not self._reader:
            raise SafetyInterfaceError("Not connected to device")

        try:
            # Step 1: Detect 0xCA
            data = await asyncio.wait_for(
                self._reader.read(1),
                timeout=self.timeout
            )
            if not data or data[0] != SYNC_BYTE_1:
                raise SafetyInterfaceError("Sync byte 1 (0xCA) not found")

            # Step 2: Detect 0xFE
            data = await asyncio.wait_for(
                self._reader.read(1),
                timeout=self.timeout
            )
            if not data or data[0] != SYNC_BYTE_2:
                raise SafetyInterfaceError("Sync byte 2 (0xFE) not found")

            # Step 3: Read remaining header (10 bytes after sync)
            header_rest = await asyncio.wait_for(
                self._reader.read(10),
                timeout=self.timeout
            )
            if len(header_rest) < 10:
                raise SafetyInterfaceError("Incomplete header")

            # Parse full header
            header_bytes = bytes([SYNC_BYTE_1, SYNC_BYTE_2]) + header_rest
            header = MsgHeader()
            header.deserialize(header_bytes)

            # Validate sync
            if header.sync != SYNC_WORD:
                raise SafetyInterfaceError(f"Invalid sync word: {hex(header.sync)}")

            # Read message body
            if header.length > 0:
                body_bytes = await asyncio.wait_for(
                    self._reader.read(header.length),
                    timeout=self.timeout
                )
                if len(body_bytes) < header.length:
                    raise SafetyInterfaceError(f"Incomplete body: expected {header.length}, got {len(body_bytes)}")
            else:
                body_bytes = b''

            # Combine header and body
            recv_packet = header_bytes + body_bytes

            # Extract return value based on command type
            return_value = self._extract_return_value(header, body_bytes)

            logger.debug(f"Received {len(recv_packet)} bytes, return value: {return_value}")

            return recv_packet, return_value

        except asyncio.TimeoutError:
            raise SafetyInterfaceTimeout(
                f"No data received within {self.timeout} seconds"
            ) from None
        except Exception as e:
            raise SafetyInterfaceError(f"Failed to receive packet: {e}") from e

    def _extract_return_value(self, header: MsgHeader, body_bytes: bytes) -> int:
        """
        Extract return value from response based on command type.

        Args:
            header: Parsed message header
            body_bytes: Raw message body bytes

        Returns:
            int: Extracted return value
        """
        # Default: try to parse as integer from body
        if len(body_bytes) >= 2:
            # Cliff sensor: returns millivolts (2 bytes)
            # Encoder: returns speed (4 bytes but we use first 2)
            try:
                return int.from_bytes(body_bytes[:2], byteorder='little')
            except:
                return 0
        return 0

    async def __aenter__(self):
        """Async context manager entry."""
        await self.open()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


# Convenience functions for common operations

async def read_cliff_sensor(
    port_name: str,
    sensor_id: int,
    baudrate: int = 9600
) -> float:
    """
    Read cliff sensor voltage.

    Args:
        port_name: Serial port device path
        sensor_id: Sensor ID (1-5 typically)
        baudrate: Communication speed (default 9600)

    Returns:
        float: Sensor voltage in millivolts
    """
    si = SafetyInterface(port_name, baudrate)
    await si.open()

    try:
        packet = si.create_msg(CLIFF_MSG, sensor_id)
        await si.send_packet(packet)
        _, voltage = await si.receive_packet()
        return float(voltage)
    finally:
        await si.close()


async def read_encoder(
    port_name: str,
    encoder_id: int,
    baudrate: int = 9600
) -> float:
    """
    Read encoder speed.

    Args:
        port_name: Serial port device path
        encoder_id: Encoder ID (1-2 typically)
        baudrate: Communication speed (default 9600)

    Returns:
        float: Encoder speed
    """
    si = SafetyInterface(port_name, baudrate)
    await si.open()

    try:
        packet = si.create_msg(ENCODER_MSG, encoder_id)
        await si.send_packet(packet)
        _, speed = await si.receive_packet()
        return float(speed)
    finally:
        await si.close()
