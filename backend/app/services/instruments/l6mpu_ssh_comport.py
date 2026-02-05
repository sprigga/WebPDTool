"""
L6MPU SSH+Serial Command Instrument Driver

Hybrid SSH and serial port communication for L6MPU devices.
Supports AT command testing with local serial port and remote SSH control.

Based on: src/lowsheen_lib/L6MPU/ssh_comport.py from PDTool4
"""
import asyncio
import logging
from typing import Dict, Any, Optional

import paramiko
import serial
from serial import SerialException

from app.services.instrument_connection import BaseInstrumentConnection
from app.services.instruments.base import BaseInstrumentDriver, validate_required_params, get_param


class L6MPUSSHComPortDriver(BaseInstrumentDriver):
    """
    L6MPU SSH+Serial command interface driver

    Supports:
    - SSH connection to i.MX8MP devices
    - Local serial port for AT command communication
    - AT command testing via at_cmd_task on remote device
    - General Linux command execution
    - Operator confirmation tests (with image reference)

    Connection configuration (SSHComPortAddress):
        - host: SSH hostname or IP address
        - port: SSH port (default: 22)
        - username: SSH username (default: root)
        - password: SSH password (default: empty)
        - serial_port: Local serial port (e.g., COM3, /dev/ttyUSB0)
        - baudrate: Serial baud rate (default: 115200)
        - timeout: Connection timeout in milliseconds
    """

    def __init__(self, connection: BaseInstrumentConnection):
        """Initialize L6MPU SSH+Serial driver"""
        super().__init__(connection)
        self.ssh_client: Optional[paramiko.SSHClient] = None
        self.serial_port: Optional[serial.Serial] = None
        self.default_timeout = 5.0

    async def initialize(self):
        """Initialize SSH and serial connections"""
        try:
            # Get connection configuration
            conn_config = self.connection.config.connection

            # SSH parameters
            host = getattr(conn_config, 'host', '192.168.5.1')
            port = getattr(conn_config, 'port', 22)
            username = getattr(conn_config, 'username', 'root')
            password = getattr(conn_config, 'password', '')
            timeout_ms = getattr(conn_config, 'timeout', 10000)
            timeout = timeout_ms / 1000.0

            # Serial parameters
            serial_port_name = getattr(conn_config, 'serial_port', 'COM3')
            baudrate = getattr(conn_config, 'baudrate', 115200)

            # Establish SSH connection
            def create_ssh():
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(
                    hostname=host,
                    port=port,
                    username=username,
                    password=password,
                    timeout=timeout,
                    allow_agent=False,
                    look_for_keys=False
                )
                return client

            self.ssh_client = await asyncio.get_event_loop().run_in_executor(
                None, create_ssh
            )

            # Open serial port
            self.serial_port = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: serial.Serial(
                    port=serial_port_name,
                    baudrate=baudrate,
                    timeout=1,
                    bytesize=8,
                    parity='N',
                    stopbits=1
                )
            )

            self.logger.info(f"SSH+Serial connection established: SSH@{host}:{port}, Serial={serial_port_name}@{baudrate}")

        except paramiko.AuthenticationException as e:
            self.logger.error(f"SSH authentication failed: {e}")
            raise ConnectionError(f"SSH authentication failed: {e}")
        except SerialException as e:
            self.logger.error(f"Serial port connection failed: {e}")
            raise ConnectionError(f"Serial port connection failed: {e}")
        except Exception as e:
            self.logger.error(f"Initialization error: {e}")
            raise

    async def reset(self):
        """Reset connections (reconnect both SSH and serial)"""
        try:
            await self.close()
            await asyncio.sleep(0.5)
            await self.initialize()
            self.logger.info("Connections reset completed")
        except Exception as e:
            self.logger.error(f"Reset failed: {e}")
            raise

    async def _exec_ssh_command(self, command: str, timeout: float = 5.0) -> str:
        """Execute command via SSH and return output"""
        if not self.ssh_client:
            raise ConnectionError("SSH connection not established")

        try:
            def run_command():
                stdin, stdout, stderr = self.ssh_client.exec_command(command, timeout=timeout)
                return stdout.read().decode('utf-8', errors='ignore')

            result = await asyncio.get_event_loop().run_in_executor(
                None, run_command
            )

            self.logger.debug(f"SSH command: {command} -> {result}")
            return result

        except Exception as e:
            self.logger.error(f"SSH command error: {e}")
            raise

    async def _read_serial_response(self, timeout: float = 2.0) -> bytes:
        """Read all available data from serial port"""
        if not self.serial_port or not self.serial_port.is_open:
            raise ConnectionError("Serial port not open")

        try:
            await asyncio.sleep(timeout)
            data = await asyncio.get_event_loop().run_in_executor(
                None,
                self.serial_port.read_all
            )
            self.logger.debug(f"Serial read: {len(data)} bytes")
            return data
        except Exception as e:
            self.logger.error(f"Serial read error: {e}")
            raise

    async def at_command_test(self, at_command: str, timeout: float = 2.0) -> Dict[str, Any]:
        """
        Execute AT command test

        Starts at_cmd_task on remote device and sends AT command.
        Reads response from local serial port.

        Args:
            at_command: AT command to send (e.g., 'AT+CPIN?')
            timeout: Response timeout in seconds

        Returns:
            Dict with keys:
                - status: 'OK', 'ERROR'
                - at_command: AT command sent
                - response: Response from serial port
                - ssh_output: Output from at_cmd_task
        """
        try:
            self.logger.info(f"AT command test: {at_command}")

            # Start at_cmd_task on remote device
            ssh_output = await self._exec_ssh_command("at_cmd_task", timeout=2.0)

            # Wait for task to start
            await asyncio.sleep(0.5)

            # Send AT command via serial port
            if self.serial_port and self.serial_port.is_open:
                command_bytes = (at_command + '\r\n').encode('utf-8')
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.serial_port.write(command_bytes)
                )

            # Read response from serial port
            response_bytes = await self._read_serial_response(timeout=timeout)
            response = response_bytes.decode('utf-8', errors='ignore').strip()

            return {
                'status': 'OK',
                'at_command': at_command,
                'response': response,
                'ssh_output': ssh_output
            }

        except Exception as e:
            self.logger.error(f"AT command test error: {e}")
            return {
                'status': 'ERROR',
                'at_command': at_command,
                'error': str(e)
            }

    async def execute_command(self, params: Dict[str, Any]) -> str:
        """
        Execute command via SSH+Serial

        Parameters in params dict:
            - command (str, required): Command to execute
            - timeout (float, optional): Execution timeout in seconds (default: 5.0)
            - comport (str, optional): Override serial port (from config)
            - baudrate (int, optional): Override baud rate (from config)

        Command formats:
            - 'ATcommand:<AT_CMD>': AT command test (e.g., 'ATcommand:AT+CPIN?')
            - 'command:<CMD>': General Linux command via SSH
            - 'Confirmcommand:<CMD>': Command with operator confirmation

        Returns:
            Command output string
        """
        validate_required_params(params, ['command'])

        command = get_param(params, 'command')
        timeout = float(get_param(params, 'timeout', default=self.default_timeout))

        self.logger.info(f"Executing L6MPU SSH+Serial command: {command}")

        # Handle different command types
        if command.startswith('ATcommand:'):
            # Extract AT command
            at_command = command.split('ATcommand:', 1)[1].strip()
            result = await self.at_command_test(at_command, timeout=timeout)

            if result['status'] == 'OK':
                return result['response']
            else:
                raise RuntimeError(f"AT command test failed: {result.get('error', 'Unknown error')}")

        elif command.startswith('command:'):
            # Execute via SSH only
            actual_command = command.split('command:', 1)[1].strip()
            return await self._exec_ssh_command(actual_command, timeout=timeout)

        elif command.startswith('Confirmcommand:'):
            # Execute via SSH with confirmation note
            actual_command = command.split('Confirmcommand:', 1)[1].strip()
            output = await self._exec_ssh_command(actual_command, timeout=timeout)
            return f"CONFIRM_REQUIRED:{output}"

        else:
            # Try to detect if it's an AT command
            if command.upper().startswith('AT'):
                result = await self.at_command_test(command, timeout=timeout)
                if result['status'] == 'OK':
                    return result['response']
                else:
                    raise RuntimeError(f"AT command test failed: {result.get('error', 'Unknown error')}")
            else:
                # Execute via SSH
                return await self._exec_ssh_command(command, timeout=timeout)

    async def close(self):
        """Close SSH and serial connections"""
        if self.ssh_client:
            try:
                await asyncio.get_event_loop().run_in_executor(
                    None, self.ssh_client.close
                )
                self.logger.info("SSH connection closed")
            except Exception as e:
                self.logger.error(f"Error closing SSH: {e}")

        if self.serial_port and self.serial_port.is_open:
            try:
                await asyncio.get_event_loop().run_in_executor(
                    None, self.serial_port.close
                )
                self.logger.info("Serial port closed")
            except Exception as e:
                self.logger.error(f"Error closing serial port: {e}")

    def __del__(self):
        """Ensure connections are closed on cleanup"""
        if self.ssh_client:
            try:
                self.ssh_client.close()
            except:
                pass
        if self.serial_port and self.serial_port.is_open:
            try:
                self.serial_port.close()
            except:
                pass
