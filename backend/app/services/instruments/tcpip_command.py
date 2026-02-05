"""
TCPIP Command Instrument Driver

Generic TCP/IP socket communication interface for network devices
Supports binary protocol with CRC32 checksum validation
"""
import asyncio
import binascii
import logging
from typing import Dict, Any, Optional

from app.services.instrument_connection import BaseInstrumentConnection
from app.services.instruments.base import BaseInstrumentDriver, validate_required_params, get_param


class TCPIPCommandDriver(BaseInstrumentDriver):
    """
    Generic TCP/IP command interface driver

    Supports:
    - TCP socket connections
    - Binary protocol with CRC32 checksum (optional)
    - Configurable timeouts
    - Hexadecimal command format
    """

    def __init__(self, connection: BaseInstrumentConnection):
        """Initialize TCPIP command driver"""
        super().__init__(connection)
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.default_timeout = 5.0
        self.use_crc32 = True  # CRC32 enabled by default (from original PDTool4)

    async def initialize(self):
        """Initialize TCP/IP connection"""
        try:
            # Get connection config (TCPIPSocketAddress)
            conn_config = self.connection.config.connection

            # Extract host and port from TCPIPSocketAddress
            host = getattr(conn_config, 'host', 'localhost')
            port = getattr(conn_config, 'port', 5025)

            # Get timeout from config (in milliseconds, convert to seconds)
            timeout_ms = getattr(conn_config, 'timeout', 5000)
            timeout = timeout_ms / 1000.0 if timeout_ms else self.default_timeout

            # Establish TCP connection
            self.reader, self.writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=timeout
            )

            self.logger.info(f"TCP connection established to {host}:{port}")

        except asyncio.TimeoutError:
            self.logger.error(f"Connection timeout to {host}:{port}")
            raise ConnectionError(f"Connection timeout to {host}:{port}")
        except (OSError, ConnectionRefusedError) as e:
            self.logger.error(f"Failed to connect to {host}:{port}: {e}")
            raise ConnectionError(f"Failed to connect to {host}:{port}: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error during initialization: {e}")
            raise

    async def reset(self):
        """Reset device (close and reconnect)"""
        try:
            if self.writer:
                self.writer.close()
                await self.writer.wait_closed()
            await asyncio.sleep(0.5)
            await self.initialize()
            self.logger.info("Device reset completed (reconnected)")
        except Exception as e:
            self.logger.error(f"Reset failed: {e}")
            raise

    @staticmethod
    def _calculate_crc32(data: bytes) -> int:
        """
        Calculate CRC32 checksum of binary data

        Args:
            data: Binary data to calculate checksum for

        Returns:
            CRC32 checksum value
        """
        return binascii.crc32(data)

    def _parse_command_bytes(self, command: str) -> bytes:
        """
        Parse command string to bytes

        Supports multiple formats:
        - Semicolon-separated hex: "31;01;f0;00;00" -> bytes([0x31, 0x01, 0xf0, 0x00, 0x00])
        - Space-separated hex: "31 01 f0 00 00" -> bytes([0x31, 0x01, 0xf0, 0x00, 0x00])
        - Plain text: "*IDN?" -> bytes([0x2a, 0x49, 0x44, 0x4e, 0x3f])

        Args:
            command: Command string

        Returns:
            Command as bytes
        """
        # Check if it's hex format (contains semicolons or spaces between hex values)
        if ';' in command or (len(command.split()) > 1 and all(c.strip() in '0123456789abcdefABCDEF;' for c in command.replace(' ', ''))):
            # Remove semicolons and spaces, parse as hex
            hex_string = command.replace(';', '').replace(' ', '')
            return bytes.fromhex(hex_string)
        else:
            # Plain text command
            return command.encode('utf-8')

    def _bytes_to_hex_string(self, data: bytes) -> str:
        """
        Convert bytes to space-separated hexadecimal string

        Args:
            data: Binary data

        Returns:
            Hex string like "31 03 f0 00 00"
        """
        return ' '.join(f'{b:02x}' for b in data)

    async def _write_command(self, command: bytes, use_crc: bool = None):
        """
        Write command to TCP socket

        Args:
            command: Command bytes to send
            use_crc: Whether to append CRC32 checksum (None = use default)
        """
        if not self.writer or self.writer.is_closing():
            raise ConnectionError("TCP connection not open")

        try:
            # Determine CRC32 usage
            use_crc = self.use_crc32 if use_crc is None else use_crc

            if use_crc:
                # Calculate and append CRC32 checksum
                crc_value = self._calculate_crc32(command)
                # Append CRC32 as 4 bytes (big-endian)
                command_with_crc = command + crc_value.to_bytes(4, byteorder='big')
                self.logger.debug(f"Command with CRC32: {self._bytes_to_hex_string(command_with_crc)}")
            else:
                command_with_crc = command

            # Send command
            self.writer.write(command_with_crc)
            await self.writer.drain()

            self.logger.debug(f"Sent {len(command_with_crc)} bytes: {self._bytes_to_hex_string(command)}")

        except Exception as e:
            self.logger.error(f"Failed to write command: {e}")
            raise

    async def _read_response(self, timeout: float = 5.0, buffer_size: int = 1024) -> str:
        """
        Read response from TCP socket

        Args:
            timeout: Maximum time to wait for response (seconds)
            buffer_size: Maximum bytes to receive per read

        Returns:
            Response as space-separated hexadecimal string
        """
        if not self.reader:
            raise ConnectionError("TCP connection not open")

        try:
            # Read response with timeout
            data = await asyncio.wait_for(
                self.reader.read(buffer_size),
                timeout=timeout
            )

            if not data:
                self.logger.warning("No data received from device")
                return ""

            response = self._bytes_to_hex_string(data)
            self.logger.debug(f"Received {len(data)} bytes: {response}")

            return response

        except asyncio.TimeoutError:
            self.logger.warning(f"Timeout waiting for response after {timeout}s")
            return ""
        except Exception as e:
            self.logger.error(f"Failed to read response: {e}")
            raise

    async def send_command(self, params: Dict[str, Any]) -> str:
        """
        Send command and read response

        Parameters in params dict:
            - Command (str, required): Command to send
                - Hex format (semicolon-separated): "31;01;f0;00;00"
                - Hex format (space-separated): "31 01 f0 00 00"
                - Plain text: "*IDN?"
            - Timeout (float, optional): Read timeout in seconds (default: 5.0)
            - BufferSize (int, optional): Maximum bytes to read (default: 1024)
            - UseCRC32 (bool, optional): Enable CRC32 checksum (default: True)

        Returns:
            Response as space-separated hexadecimal string
        """
        # Validate required parameters
        validate_required_params(params, ['Command'])

        # Get parameters
        command = get_param(params, 'Command', 'command')
        timeout = float(get_param(params, 'Timeout', 'timeout', default=self.default_timeout))
        buffer_size = int(get_param(params, 'BufferSize', 'buffer_size', default=1024))
        use_crc = get_param(params, 'UseCRC32', 'use_crc', 'usecrc32')

        # Parse UseCRC32 boolean
        if use_crc is not None:
            if isinstance(use_crc, str):
                use_crc = use_crc.lower() in ('true', '1', 'yes', 'on')
            else:
                use_crc = bool(use_crc)

        self.logger.info(f"Executing command: {repr(command)} (timeout={timeout}s, crc={use_crc})")

        # Parse command to bytes
        command_bytes = self._parse_command_bytes(command)

        # Send command
        await self._write_command(command_bytes, use_crc=use_crc)

        # Read response
        response = await self._read_response(timeout=timeout, buffer_size=buffer_size)

        return response

    async def query_command(self, command: str, timeout: float = 5.0,
                          use_crc: bool = True) -> str:
        """
        Query command (send and receive response)

        Args:
            command: Command to send (hex or plain text)
            timeout: Read timeout in seconds
            use_crc: Whether to use CRC32 checksum

        Returns:
            Response as space-separated hexadecimal string
        """
        params = {
            'Command': command,
            'Timeout': timeout,
            'UseCRC32': use_crc
        }
        return await self.send_command(params)

    async def close(self):
        """Close TCP connection"""
        if self.writer and not self.writer.is_closing():
            try:
                self.writer.close()
                await self.writer.wait_closed()
                self.logger.info("TCP connection closed")
            except Exception as e:
                self.logger.error(f"Error closing connection: {e}")

    def __del__(self):
        """Ensure connection is closed on cleanup"""
        if self.writer and not self.writer.is_closing():
            try:
                self.writer.close()
            except:
                pass
