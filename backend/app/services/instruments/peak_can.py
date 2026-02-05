"""
PEAK CAN Instrument Driver

CAN bus communication driver for PEAK-System PCAN hardware.
Supports CAN and CAN-FD message transmission and reception.

Based on: src/lowsheen_lib/PEAK_API/ from PDTool4

Dependencies:
    - python-can: Generic CAN interface library
    - Optional: PCAN-Basic driver for direct hardware access
"""
import asyncio
import logging
from typing import Dict, Any, Optional, List, Union
from decimal import Decimal
import struct

try:
    import can
    CAN_AVAILABLE = True
except ImportError:
    CAN_AVAILABLE = False
    can = None

from app.services.instrument_connection import BaseInstrumentConnection
from app.services.instruments.base import BaseInstrumentDriver, validate_required_params, get_param


class PEAKCANDriver(BaseInstrumentDriver):
    """
    PEAK-System PCAN hardware driver

    Supports:
    - Standard CAN (11-bit ID) and Extended CAN (29-bit ID)
    - CAN-FD (Flexible Data Rate) with up to 64 bytes
    - Message filtering
    - Configurable baud rates
    - Multiple channel support

    Connection configuration (CANAddress):
        - channel: CAN channel (e.g., 'PCAN_USBBUS1', 'PCAN_PCIBUS1')
        - interface: CAN interface type ('pcan', 'socketcan', 'virtual')
        - baudrate: Bus baud rate (e.g., 500000, 1000000)
        - fd_enabled: Enable CAN-FD mode (default: False)
    """

    def __init__(self, connection: BaseInstrumentConnection):
        """Initialize PEAK CAN driver"""
        super().__init__(connection)
        self.bus: Optional[can.Bus] = None
        self.default_timeout = 5.0

        # Check if python-can is available
        if not CAN_AVAILABLE:
            self.logger.warning("python-can library not installed. Install with: pip install python-can")

    async def initialize(self):
        """Initialize CAN bus connection"""
        if not CAN_AVAILABLE:
            raise ImportError("python-can library is required. Install with: pip install python-can")

        try:
            conn_config = self.connection.config.connection

            # Get CAN configuration
            channel = getattr(conn_config, 'channel', 'PCAN_USBBUS1')
            interface = getattr(conn_config, 'interface', 'pcan')
            baudrate = getattr(conn_config, 'baudrate', 500000)
            fd_enabled = getattr(conn_config, 'fd_enabled', False)

            # Build configuration for python-can
            config = {
                'interface': interface,
                'channel': channel,
                'bitrate': baudrate,
                'receive_own_messages': False,
            }

            # Add CAN-FD settings if enabled
            if fd_enabled:
                config['fd'] = True

            # Initialize CAN bus in thread pool
            def create_bus():
                return can.Bus(**config)

            self.bus = await asyncio.get_event_loop().run_in_executor(
                None, create_bus
            )

            self.logger.info(f"CAN bus initialized: {channel} @ {baudrate} baud (FD={fd_enabled})")

        except can.CanError as e:
            self.logger.error(f"CAN initialization error: {e}")
            raise ConnectionError(f"Failed to initialize CAN bus: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected initialization error: {e}")
            raise

    async def reset(self):
        """Reset CAN bus (reconnect)"""
        try:
            await self.close()
            await asyncio.sleep(0.5)
            await self.initialize()
            self.logger.info("CAN bus reset completed")
        except Exception as e:
            self.logger.error(f"Reset failed: {e}")
            raise

    def _parse_data_string(self, data_str: str) -> List[int]:
        """
        Parse data string to byte list

        Supports formats:
        - Hex comma-separated: "01,02,03,04" -> [0x01, 0x02, 0x03, 0x04]
        - Hex semicolon-separated: "01;02;03;04" -> [0x01, 0x02, 0x03, 0x04]
        - Hex space-separated: "01 02 03 04" -> [0x01, 0x02, 0x03, 0x04]

        Args:
            data_str: Data string

        Returns:
            List of byte values
        """
        # Replace semicolons with commas and split
        data_str = data_str.replace(';', ',').replace(' ', ',')
        parts = data_str.split(',')

        data_bytes = []
        for part in parts:
            part = part.strip()
            if part:
                try:
                    data_bytes.append(int(part, 16))
                except ValueError:
                    try:
                        data_bytes.append(int(part))
                    except ValueError:
                        self.logger.warning(f"Invalid data byte: {part}")

        return data_bytes

    async def send_can_message(self, can_id: int, data: Union[str, List[int]],
                               is_extended: bool = False, is_fd: bool = False) -> Dict[str, Any]:
        """
        Send CAN message

        Args:
            can_id: CAN identifier (11-bit for standard, 29-bit for extended)
            data: Message data (hex string or list of bytes)
            is_extended: Use extended frame format (29-bit ID)
            is_fd: Use CAN-FD format

        Returns:
            Dict with send result
        """
        if not self.bus:
            raise ConnectionError("CAN bus not initialized")

        try:
            # Parse data if string
            if isinstance(data, str):
                data_bytes = self._parse_data_string(data)
            else:
                data_bytes = data

            # Check data length
            max_length = 64 if is_fd else 8
            if len(data_bytes) > max_length:
                raise ValueError(f"Data length {len(data_bytes)} exceeds maximum {max_length}")

            # Create CAN message
            if is_fd:
                # CAN-FD message
                message = can.Message(
                    arbitration_id=can_id,
                    is_extended_id=is_extended,
                    is_fd=True,
                    data=data_bytes
                )
            else:
                # Standard CAN message
                message = can.Message(
                    arbitration_id=can_id,
                    is_extended_id=is_extended,
                    data=data_bytes
                )

            # Send message in thread pool
            def send_msg():
                self.bus.send(message)

            await asyncio.get_event_loop().run_in_executor(
                None, send_msg
            )

            self.logger.debug(f"Sent CAN message: ID={hex(can_id)}, data={data_bytes}")

            return {
                'status': 'OK',
                'can_id': can_id,
                'data': data_bytes,
                'is_extended': is_extended,
                'is_fd': is_fd
            }

        except can.CanError as e:
            self.logger.error(f"CAN send error: {e}")
            return {
                'status': 'ERROR',
                'error': str(e)
            }
        except Exception as e:
            self.logger.error(f"Send message error: {e}")
            return {
                'status': 'ERROR',
                'error': str(e)
            }

    async def receive_can_message(self, timeout: float = 5.0,
                                   filter_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Receive CAN message with timeout

        Args:
            timeout: Maximum wait time in seconds
            filter_id: Only accept messages with this ID (None for all)

        Returns:
            Dict with received message data
        """
        if not self.bus:
            raise ConnectionError("CAN bus not initialized")

        try:
            # Set up filter if specified
            if filter_id is not None:
                # Create filter list
                filters = [{"can_id": filter_id, "can_mask": 0x7FF, "extended": False}]
                self.bus.set_filters(filters)

            # Receive message with timeout
            def recv_msg():
                return self.bus.recv(timeout=timeout)

            message = await asyncio.get_event_loop().run_in_executor(
                None, recv_msg
            )

            if message is None:
                return {
                    'status': 'TIMEOUT',
                    'error': f'No message received within {timeout}s'
                }

            self.logger.debug(f"Received CAN message: ID={hex(message.arbitration_id)}, data={list(message.data)}")

            return {
                'status': 'OK',
                'can_id': message.arbitration_id,
                'data': list(message.data),
                'is_extended': message.is_extended_id,
                'is_fd': message.is_fd,
                'timestamp': message.timestamp
            }

        except can.CanError as e:
            self.logger.error(f"CAN receive error: {e}")
            return {
                'status': 'ERROR',
                'error': str(e)
            }
        except Exception as e:
            self.logger.error(f"Receive message error: {e}")
            return {
                'status': 'ERROR',
                'error': str(e)
            }
        finally:
            # Clear filters
            if filter_id is not None:
                self.bus.set_filters(None)

    async def execute_command(self, params: Dict[str, Any]) -> str:
        """
        Execute CAN command

        Parameters in params dict:
            - operation (str, required): Operation type
                - 'write', 'send': Send CAN message
                - 'read', 'receive': Receive CAN message
                - 'write_read': Send then receive
            - can_id (int, required for write): CAN identifier (hex or decimal)
            - data (str, required for write): Message data (hex format)
            - is_extended (bool, optional): Use extended frame (default: False)
            - is_fd (bool, optional): Use CAN-FD format (default: False)
            - timeout (float, optional): Receive timeout in seconds (default: 5.0)
            - filter_id (int, optional): Filter messages by ID when reading

        Returns:
            Operation result string
        """
        validate_required_params(params, ['operation'])

        operation = get_param(params, 'operation')
        timeout = float(get_param(params, 'timeout', default=self.default_timeout))

        self.logger.info(f"Executing CAN operation: {operation}")

        if operation in ('write', 'send', 'WRITE', 'SEND'):
            # Send CAN message
            can_id_param = get_param(params, 'can_id', 'id')
            data = get_param(params, 'data', 'Data', 'DATA')
            is_extended = get_param(params, 'is_extended', 'extended', default=False)
            is_fd = get_param(params, 'is_fd', 'fd', default=False)

            # Parse CAN ID
            try:
                if isinstance(can_id_param, str) and can_id_param.startswith('0x'):
                    can_id = int(can_id_param, 16)
                else:
                    can_id = int(can_id_param)
            except (ValueError, TypeError):
                raise ValueError(f"Invalid CAN ID: {can_id_param}")

            # Parse boolean flags
            if isinstance(is_extended, str):
                is_extended = is_extended.lower() in ('true', '1', 'yes', 'on')
            if isinstance(is_fd, str):
                is_fd = is_fd.lower() in ('true', '1', 'yes', 'on')

            result = await self.send_can_message(can_id, data, is_extended, is_fd)

            if result['status'] == 'OK':
                data_hex = ' '.join(f'{b:02X}' for b in result['data'])
                return f"Sent: ID={hex(result['can_id'])}, Data=[{data_hex}]"
            else:
                raise RuntimeError(f"Send failed: {result.get('error', 'Unknown error')}")

        elif operation in ('read', 'receive', 'READ', 'RECEIVE'):
            # Receive CAN message
            filter_id = get_param(params, 'filter_id', 'filter')

            if filter_id is not None:
                try:
                    if isinstance(filter_id, str) and filter_id.startswith('0x'):
                        filter_id = int(filter_id, 16)
                    else:
                        filter_id = int(filter_id)
                except (ValueError, TypeError):
                    filter_id = None

            result = await self.receive_can_message(timeout=timeout, filter_id=filter_id)

            if result['status'] == 'OK':
                data_hex = ' '.join(f'{b:02X}' for b in result['data'])
                return f"Received: ID={hex(result['can_id'])}, Data=[{data_hex}]"
            elif result['status'] == 'TIMEOUT':
                return f"Timeout: No message received"
            else:
                raise RuntimeError(f"Receive failed: {result.get('error', 'Unknown error')}")

        elif operation in ('write_read', 'send_receive', 'WRITE_READ'):
            # Send then receive
            can_id_param = get_param(params, 'can_id', 'id')
            data = get_param(params, 'data', 'Data', 'DATA')
            filter_id = get_param(params, 'filter_id', 'filter')

            # Parse CAN ID
            try:
                if isinstance(can_id_param, str) and can_id_param.startswith('0x'):
                    can_id = int(can_id_param, 16)
                else:
                    can_id = int(can_id_param)
            except (ValueError, TypeError):
                raise ValueError(f"Invalid CAN ID: {can_id_param}")

            # Send message
            send_result = await self.send_can_message(can_id, data, False, False)
            if send_result['status'] != 'OK':
                raise RuntimeError(f"Send failed: {send_result.get('error', 'Unknown error')}")

            # Wait before receiving
            await asyncio.sleep(0.1)

            # Receive response
            result = await self.receive_can_message(timeout=timeout, filter_id=filter_id)

            if result['status'] == 'OK':
                data_hex = ' '.join(f'{b:02X}' for b in result['data'])
                return f"Received: ID={hex(result['can_id'])}, Data=[{data_hex}]"
            elif result['status'] == 'TIMEOUT':
                return f"Timeout: No message received"
            else:
                raise RuntimeError(f"Receive failed: {result.get('error', 'Unknown error')}")

        else:
            raise ValueError(f"Unknown operation: {operation}")

    async def close(self):
        """Close CAN bus connection"""
        if self.bus:
            try:
                await asyncio.get_event_loop().run_in_executor(
                    None, self.bus.shutdown
                )
                self.logger.info("CAN bus closed")
            except Exception as e:
                self.logger.error(f"Error closing CAN bus: {e}")

    def __del__(self):
        """Ensure CAN bus is closed on cleanup"""
        if self.bus:
            try:
                self.bus.shutdown()
            except:
                pass
