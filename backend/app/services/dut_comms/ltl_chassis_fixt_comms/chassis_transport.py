"""
Chassis Test Fixture Serial Transport Layer

Refactored from PDTool4 polish/dut_comms/ltl_chassis_fixt_comms/chassis_transport.py

Async serial communication with CRC16Kermit checksum.
Implements three-layer frame detection: Sync + Length + CRC.
"""

import asyncio
import logging
from collections import deque
from typing import Tuple, Optional
from io import BytesIO

import serial_asyncio

from .crc16_kermit import CRC16Kermit
from .chassis_msgs import (
    TransportHeader,
    TransportFooter,
    LittleChassisTestMessage,
    get_msg_size,
    serialize,
    deserialize,
    type_msg_map,
    SYNC_WORD,
    TRANSPORT_OVERHEAD,
    HEADER_SIZE,
    FOOTER_SIZE,
)


logger = logging.getLogger(__name__)


# Serial port configuration
BAUD_RATE = 9600
PARITY = 'N'
BYTESIZE = 8
STOPBITS = 1
TIMEOUT = 1.0


class ChassisTransportError(Exception):
    """Base exception for chassis transport errors"""
    pass


class ChassisCRCError(ChassisTransportError):
    """CRC checksum mismatch error"""
    pass


class ChassisTimeoutError(ChassisTransportError):
    """Communication timeout error"""
    pass


class ChassisTransport:
    """
    Async serial transport for chassis test fixture communication.

    Protocol:
    - Frame: [Header][Body][Footer]
    - Header: sync_word(4) + length(2) + msg_type(2)
    - Footer: crc16(2)
    - CRC covers entire header + body

    Example:
        async with ChassisTransport('/dev/ttyUSB0') as transport:
            msg = RotateTurntable()
            msg.operation = operation_enum.ROTATE_LEFT.value
            msg.angle = 90
            await transport.send_msg(msg)
            header, response, footer = await transport.get_msg()
    """

    def __init__(
        self,
        port: str,
        baud_rate: int = BAUD_RATE,
        timeout: float = TIMEOUT,
    ):
        """
        Initialize chassis transport.

        Args:
            port: Serial port name (e.g., '/dev/ttyUSB0', 'COM3')
            baud_rate: Baud rate (default: 9600)
            timeout: Read timeout in seconds (default: 1.0)
        """
        self.port = port
        self.baud_rate = baud_rate
        self.timeout = timeout
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None

    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

    async def connect(self):
        """Open serial connection"""
        try:
            self.reader, self.writer = await serial_asyncio.open_serial_connection(
                url=self.port,
                baudrate=self.baud_rate,
                bytesize=BYTESIZE,
                parity=PARITY,
                stopbits=STOPBITS,
            )
            logger.info(f"Connected to chassis fixture at {self.port}")
            # Wait for device to stabilize
            await asyncio.sleep(0.5)
        except Exception as e:
            raise ChassisTransportError(f"Failed to open port {self.port}: {e}")

    async def close(self):
        """Close serial connection"""
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
            self.reader = None
            self.writer = None
            logger.info(f"Closed connection to {self.port}")

    async def send_msg(self, msg_inst: LittleChassisTestMessage):
        """
        Serialize and send a message to chassis fixture.

        Args:
            msg_inst: Message instance to send

        Raises:
            ChassisTransportError: If connection is not open
        """
        if not self.writer:
            raise ChassisTransportError("Connection not open")

        # Build message
        buff = BytesIO()

        # Create header
        new_header = TransportHeader()
        new_header.sync_word = SYNC_WORD
        new_header.msg_type = msg_inst.msg_type
        new_header.length = get_msg_size(msg_inst) + TRANSPORT_OVERHEAD

        # Write header and body
        header_bytes = serialize(new_header)
        body_bytes = serialize(msg_inst)
        buff.write(header_bytes)
        buff.write(body_bytes)

        # Calculate CRC16Kermit over header + body
        crc16 = CRC16Kermit()
        crc = crc16.calculate(buff.getvalue())

        # Create footer
        new_footer = TransportFooter()
        new_footer.crc16 = crc
        footer_bytes = serialize(new_footer)
        buff.write(footer_bytes)

        # Send complete frame
        msg_bytes = buff.getvalue()
        logger.debug(f"Sending: {' '.join(f'{b:02X}' for b in msg_bytes)}")
        self.writer.write(msg_bytes)
        await self.writer.drain()

    async def get_msg(self) -> Tuple[TransportHeader, LittleChassisTestMessage, TransportFooter]:
        """
        Receive and deserialize a message from chassis fixture.

        Uses three-layer frame detection:
        1. Sync word detection (0xA5FF00CC)
        2. Length validation
        3. CRC verification

        Returns:
            Tuple of (header, message, footer)

        Raises:
            ChassisTransportError: If connection is not open
            ChassisTimeoutError: If timeout occurs during receive
            ChassisCRCError: If CRC verification fails
        """
        if not self.reader:
            raise ChassisTransportError("Connection not open")

        # Frame detection using sliding window
        frame_detector = deque(b'\xff' * HEADER_SIZE, maxlen=HEADER_SIZE)

        try:
            while True:
                # Read one byte with timeout
                try:
                    input_byte = await asyncio.wait_for(
                        self.reader.read(1),
                        timeout=self.timeout
                    )
                except asyncio.TimeoutError:
                    raise ChassisTimeoutError(f"Timeout waiting for sync word")

                if not input_byte:
                    continue

                frame_detector.append(input_byte)
                logger.debug(f"Byte: {input_byte.hex().upper()}")

                # Try to deserialize header
                header_bytes = b''.join(frame_detector)
                header = deserialize(TransportHeader, header_bytes)

                # Check sync word
                if header.sync_word == SYNC_WORD:
                    logger.debug(f"Sync detected, length={header.length}, msg_type=0x{header.msg_type:02X}")
                    break

            # Read body
            body_length = header.length - TRANSPORT_OVERHEAD
            body = await asyncio.wait_for(
                self.reader.read(body_length),
                timeout=self.timeout
            )

            # Read footer
            footer_bytes = await asyncio.wait_for(
                self.reader.read(FOOTER_SIZE),
                timeout=self.timeout
            )
            footer = deserialize(TransportFooter, footer_bytes)

            # Verify CRC
            crc16 = CRC16Kermit()
            calculated_crc = crc16.calculate(header_bytes + body)
            if calculated_crc != footer.crc16:
                raise ChassisCRCError(
                    f"CRC mismatch: expected 0x{footer.crc16:04X}, "
                    f"calculated 0x{calculated_crc:04X}"
                )

            # Deserialize message body
            msg = deserialize(type_msg_map[header.msg_type], body)
            logger.debug(f"Received: {msg}")

            return header, msg, footer

        except asyncio.TimeoutError:
            raise ChassisTimeoutError(f"Timeout during message receive")


async def get_serial_port(
    port_name: str,
    baud_rate: int = BAUD_RATE,
    timeout: float = TIMEOUT,
) -> ChassisTransport:
    """
    Create and connect a chassis transport instance.

    Args:
        port_name: Serial port name
        baud_rate: Baud rate (default: 9600)
        timeout: Read timeout in seconds (default: 1.0)

    Returns:
        Connected ChassisTransport instance
    """
    transport = ChassisTransport(port_name, baud_rate, timeout)
    await transport.connect()
    return transport


# Example usage
if __name__ == '__main__':
    import sys
    from . import chassis_msgs

    async def test_turntable(port_name: str):
        """Test turntable rotation"""
        async with ChassisTransport(port_name) as transport:
            # Rotate left 45 degrees
            print("Rotating left 45 degrees...")
            msg = chassis_msgs.RotateTurntable()
            msg.operation = chassis_msgs.operation_enum.ROTATE_LEFT.value
            msg.angle = 45
            await transport.send_msg(msg)
            header, response, footer = await transport.get_msg()
            print(f"Response: {response}")

            # Wait a bit
            await asyncio.sleep(1.5)

            # Rotate to home (opto switch)
            print("Rotating to home position...")
            msg = chassis_msgs.RotateTurntable()
            msg.operation = chassis_msgs.operation_enum.ROTATE_TO_OPTO_SWITCH.value
            msg.angle = 0
            await transport.send_msg(msg)
            header, response, footer = await transport.get_msg()
            print(f"Response: {response}")

            # Get current angle
            await asyncio.sleep(2)
            print("Getting current angle...")
            msg = chassis_msgs.GetTurntableAngle()
            await transport.send_msg(msg)
            header, response, footer = await transport.get_msg()
            print(f"Current angle: {response.angle} degrees")

    if len(sys.argv) < 2:
        print("Usage: python chassis_transport.py <serial_port>")
        print("Example: python chassis_transport.py /dev/ttyUSB0")
        sys.exit(1)

    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(test_turntable(sys.argv[1]))
