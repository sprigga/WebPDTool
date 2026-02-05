"""
ComPort Command Instrument Driver

Generic serial port communication interface for test devices
Supports configurable timeouts, multi-line responses, and various serial protocols
"""
import asyncio
import logging
from typing import Dict, Any, Optional
from decimal import Decimal

import serial
from serial import SerialException

from app.services.instrument_connection import BaseInstrumentConnection
from app.services.instruments.base import BaseInstrumentDriver, validate_required_params, get_param


class ComPortCommandDriver(BaseInstrumentDriver):
    """
    Generic COM Port command interface driver

    Supports:
    - Configurable baud rate and serial settings
    - Multi-line response handling
    - Timeout management
    - Device initialization delays
    """

    def __init__(self, connection: BaseInstrumentConnection):
        """Initialize ComPort command driver"""
        super().__init__(connection)
        self.serial_port: Optional[serial.Serial] = None
        self.default_timeout = 3.0
        self.default_baudrate = 115200

    async def initialize(self):
        """Initialize serial port connection"""
        try:
            # Get serial port configuration from connection config
            # connection.config.connection is SerialAddress for COM ports
            conn_config = self.connection.config.connection

            # Get port, baudrate, and timeout from SerialAddress
            port = getattr(conn_config, 'port', 'COM1')
            baudrate = getattr(conn_config, 'baudrate', self.default_baudrate)
            timeout_sec = getattr(conn_config, 'timeout', 5000) / 1000.0  # Convert ms to seconds

            # Open serial port in thread pool to avoid blocking
            self.serial_port = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: serial.Serial(
                    port=port,
                    baudrate=baudrate,
                    timeout=timeout_sec,
                    bytesize=getattr(conn_config, 'bytesize', 8),
                    parity=getattr(conn_config, 'parity', 'N'),
                    stopbits=getattr(conn_config, 'stopbits', 1),
                    xonxoff=False,
                    rtscts=False,
                    dsrdtr=False
                )
            )

            # Wait for device initialization if specified (from extra attributes)
            comport_wait = getattr(self.connection.config, 'comport_wait', 0)
            if comport_wait > 0:
                self.logger.info(f"Waiting {comport_wait}s for device initialization")
                await asyncio.sleep(comport_wait)

            self.logger.info(f"Serial port {port} opened successfully at {baudrate} baud")

        except SerialException as e:
            self.logger.error(f"Failed to open serial port: {e}")
            raise ConnectionError(f"Failed to connect to serial port {port}: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error during initialization: {e}")
            raise

    async def reset(self):
        """Reset device to default state (power supply reset pattern)"""
        try:
            # Send SCPI reset commands
            await self._write_command("*RST\n")
            await asyncio.sleep(0.1)
            await self._write_command("OUTP OFF\n")
            await asyncio.sleep(0.1)
            self.logger.info("Device reset completed")
        except Exception as e:
            self.logger.error(f"Reset failed: {e}")
            raise

    async def _write_command(self, command: str):
        """Write command to serial port"""
        if not self.serial_port or not self.serial_port.is_open:
            raise ConnectionError("Serial port not open")

        try:
            # Encode and send command in thread pool
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.serial_port.write(command.encode('utf-8'))
            )

            # Flush output buffer
            await asyncio.get_event_loop().run_in_executor(
                None,
                self.serial_port.flush
            )

            # Short delay for command processing
            await asyncio.sleep(0.05)

            self.logger.debug(f"Sent command: {repr(command)}")

        except Exception as e:
            self.logger.error(f"Failed to write command: {e}")
            raise

    async def _read_response(self, timeout: float = 3.0, line_count: Optional[int] = None) -> str:
        """
        Read response from serial port

        Args:
            timeout: Maximum time to wait for response (seconds)
            line_count: Expected number of lines (None for auto-detect)

        Returns:
            Response string (multi-line responses joined with \\n)
        """
        if not self.serial_port or not self.serial_port.is_open:
            raise ConnectionError("Serial port not open")

        try:
            # Set timeout for this read operation
            original_timeout = self.serial_port.timeout
            self.serial_port.timeout = timeout

            response_lines = []
            start_time = asyncio.get_event_loop().time()

            if line_count is not None:
                # Fixed line count mode
                for i in range(line_count):
                    if asyncio.get_event_loop().time() - start_time > timeout:
                        self.logger.warning(f"Timeout reading line {i+1}/{line_count}")
                        break

                    line = await asyncio.get_event_loop().run_in_executor(
                        None,
                        self.serial_port.readline
                    )

                    if line:
                        response_lines.append(line.decode('utf-8', errors='ignore').rstrip('\r\n'))
            else:
                # Auto-detect mode (read until no more data)
                empty_read_count = 0
                max_empty_reads = 3

                while empty_read_count < max_empty_reads:
                    if asyncio.get_event_loop().time() - start_time > timeout:
                        break

                    line = await asyncio.get_event_loop().run_in_executor(
                        None,
                        self.serial_port.readline
                    )

                    if line:
                        response_lines.append(line.decode('utf-8', errors='ignore').rstrip('\r\n'))
                        empty_read_count = 0
                    else:
                        empty_read_count += 1
                        await asyncio.sleep(0.1)

            # Restore original timeout
            self.serial_port.timeout = original_timeout

            response = '\n'.join(response_lines)
            self.logger.debug(f"Received response ({len(response_lines)} lines): {repr(response)}")

            return response

        except Exception as e:
            self.logger.error(f"Failed to read response: {e}")
            raise

    async def send_command(self, params: Dict[str, Any]) -> str:
        """
        Send command and read response

        Parameters in params dict:
            - Command (str, required): Command to send (supports \\n escape sequences)
            - Timeout (float, optional): Read timeout in seconds (default: 3.0)
            - ReslineCount (int, optional): Expected number of response lines (None for auto-detect)

        Returns:
            Response string from device
        """
        # Validate required parameters
        validate_required_params(params, ['Command'])

        # Get parameters
        command = get_param(params, 'Command', 'command')
        timeout = float(get_param(params, 'Timeout', 'timeout', default=self.default_timeout))
        resline_count = get_param(params, 'ReslineCount', 'resline_count', 'linecount')

        # Convert ReslineCount to int if provided
        if resline_count is not None and resline_count != '':
            try:
                resline_count = int(resline_count)
            except (ValueError, TypeError):
                resline_count = None
        else:
            resline_count = None

        # Process escape sequences in command
        if '\\n' in command:
            command = command.replace('\\n', '\n')
        if '\\r' in command:
            command = command.replace('\\r', '\r')
        if '\\t' in command:
            command = command.replace('\\t', '\t')

        self.logger.info(f"Executing command: {repr(command)} (timeout={timeout}s, lines={resline_count})")

        # Send command
        await self._write_command(command)

        # Wait for device processing (configurable settling time)
        settling_time = float(get_param(params, 'SettlingTime', 'settling_time', default=0.5))
        await asyncio.sleep(settling_time)

        # Read response
        response = await self._read_response(timeout=timeout, line_count=resline_count)

        return response

    async def query_command(self, command: str, timeout: float = 3.0, line_count: Optional[int] = None) -> str:
        """
        Query command (send and receive response)

        Args:
            command: Command to send
            timeout: Read timeout in seconds
            line_count: Expected number of response lines (None for auto-detect)

        Returns:
            Response string
        """
        params = {
            'Command': command,
            'Timeout': timeout,
            'ReslineCount': line_count
        }
        return await self.send_command(params)

    async def close(self):
        """Close serial port connection"""
        if self.serial_port and self.serial_port.is_open:
            try:
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    self.serial_port.close
                )
                self.logger.info("Serial port closed")
            except Exception as e:
                self.logger.error(f"Error closing serial port: {e}")

    def __del__(self):
        """Ensure serial port is closed on cleanup"""
        if self.serial_port and self.serial_port.is_open:
            try:
                self.serial_port.close()
            except:
                pass
