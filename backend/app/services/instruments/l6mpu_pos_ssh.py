"""
L6MPU Position SSH Instrument Driver

SSH-based position control for L6MPU (i.MX8MP) devices.
Controls MPU positioning for robot/AMR applications.

Based on: src/lowsheen_lib/L6MPU/L6MPU_POSssh_cmd_API_Analysis.md
"""
import asyncio
import logging
from typing import Dict, Any, Optional, Tuple

import paramiko

from app.services.instrument_connection import BaseInstrumentConnection
from app.services.instruments.base import BaseInstrumentDriver, validate_required_params, get_param


class L6MPUPOSSHDriver(BaseInstrumentDriver):
    """
    L6MPU Position SSH control driver

    Supports:
    - SSH connection to i.MX8MP devices
    - MPU position control commands
    - Motor control via roboteq_cmd
    - Position query and calibration

    Connection configuration (SSHAddress):
        - host: SSH hostname or IP address
        - port: SSH port (default: 22)
        - username: SSH username (default: root)
        - password: SSH password (default: empty for key-based auth)
        - timeout: Connection timeout in milliseconds
    """

    def __init__(self, connection: BaseInstrumentConnection):
        """Initialize L6MPU Position SSH driver"""
        super().__init__(connection)
        self.ssh_client: Optional[paramiko.SSHClient] = None
        self.default_timeout = 10.0

    async def initialize(self):
        """Initialize SSH connection"""
        try:
            conn_config = self.connection.config.connection

            host = getattr(conn_config, 'host', '192.168.5.1')
            port = getattr(conn_config, 'port', 22)
            username = getattr(conn_config, 'username', 'root')
            password = getattr(conn_config, 'password', '')
            timeout_ms = getattr(conn_config, 'timeout', 10000)
            timeout = timeout_ms / 1000.0

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

            self.logger.info(f"SSH connection established to {username}@{host}:{port}")

        except paramiko.AuthenticationException as e:
            self.logger.error(f"SSH authentication failed: {e}")
            raise ConnectionError(f"SSH authentication failed: {e}")
        except paramiko.SSHException as e:
            self.logger.error(f"SSH connection error: {e}")
            raise ConnectionError(f"SSH connection error: {e}")
        except Exception as e:
            self.logger.error(f"Initialization error: {e}")
            raise

    async def reset(self):
        """Reset SSH connection (reconnect)"""
        try:
            await self.close()
            await asyncio.sleep(0.5)
            await self.initialize()
            self.logger.info("SSH connection reset completed")
        except Exception as e:
            self.logger.error(f"Reset failed: {e}")
            raise

    async def _exec_command(self, command: str, timeout: float = 5.0) -> str:
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

            self.logger.debug(f"Command: {command} -> {result}")
            return result

        except Exception as e:
            self.logger.error(f"Command execution error: {e}")
            raise

    async def set_position(self, position: Dict[str, Any]) -> Dict[str, Any]:
        """
        Set MPU position

        Args:
            position: Dict containing position parameters
                - x: X coordinate (optional)
                - y: Y coordinate (optional)
                - angle: Rotation angle in degrees (optional)
                - speed: Movement speed (optional)

        Returns:
            Dict with execution result
        """
        try:
            self.logger.info(f"Setting position: {position}")

            # Build position command
            cmd_parts = ["./NPI_tool/test/position_control"]

            if 'x' in position:
                cmd_parts.append(f"x={position['x']}")
            if 'y' in position:
                cmd_parts.append(f"y={position['y']}")
            if 'angle' in position:
                cmd_parts.append(f"angle={position['angle']}")
            if 'speed' in position:
                cmd_parts.append(f"speed={position['speed']}")

            command = ' '.join(cmd_parts)
            output = await self._exec_command(command, timeout=10.0)

            return {
                'status': 'OK',
                'position': position,
                'output': output
            }

        except Exception as e:
            self.logger.error(f"Set position error: {e}")
            return {
                'status': 'ERROR',
                'error': str(e)
            }

    async def get_position(self) -> Dict[str, Any]:
        """
        Get current MPU position

        Returns:
            Dict with current position (x, y, angle) or error
        """
        try:
            self.logger.info("Getting current position")

            # Query position
            output = await self._exec_command("./NPI_tool/test/get_position", timeout=5.0)

            # Parse position output (format: x,y,angle)
            try:
                parts = output.strip().split(',')
                if len(parts) >= 3:
                    position = {
                        'x': float(parts[0]),
                        'y': float(parts[1]),
                        'angle': float(parts[2])
                    }
                    return {
                        'status': 'OK',
                        'position': position
                    }
            except (ValueError, IndexError):
                pass

            return {
                'status': 'ERROR',
                'error': f'Invalid position output: {output}'
            }

        except Exception as e:
            self.logger.error(f"Get position error: {e}")
            return {
                'status': 'ERROR',
                'error': str(e)
            }

    async def calibrate_position(self) -> Dict[str, Any]:
        """
        Calibrate MPU position to origin

        Returns:
            Dict with calibration result
        """
        try:
            self.logger.info("Calibrating position")

            output = await self._exec_command("./NPI_tool/test/calibrate_position", timeout=15.0)

            return {
                'status': 'OK',
                'output': output
            }

        except Exception as e:
            self.logger.error(f"Calibration error: {e}")
            return {
                'status': 'ERROR',
                'error': str(e)
            }

    async def execute_command(self, params: Dict[str, Any]) -> str:
        """
        Execute position control command

        Parameters in params dict:
            - command (str, required): Command type
                - 'set': Set position (requires x, y, angle, speed)
                - 'get': Get current position
                - 'calibrate': Calibrate to origin
                - 'reset': Reset position to origin
            - x (float, optional): X coordinate for set command
            - y (float, optional): Y coordinate for set command
            - angle (float, optional): Angle for set command
            - speed (float, optional): Speed for set command
            - timeout (float, optional): Execution timeout

        Returns:
            Command result string
        """
        validate_required_params(params, ['command'])

        command = get_param(params, 'command')
        timeout = float(get_param(params, 'timeout', default=self.default_timeout))

        self.logger.info(f"Executing position command: {command}")

        if command == 'set' or command == 'SET':
            position = {
                'x': get_param(params, 'x'),
                'y': get_param(params, 'y'),
                'angle': get_param(params, 'angle'),
                'speed': get_param(params, 'speed', default=100)
            }
            result = await self.set_position(position)

            if result['status'] == 'OK':
                return result['output']
            else:
                raise RuntimeError(f"Set position failed: {result.get('error', 'Unknown error')}")

        elif command == 'get' or command == 'GET':
            result = await self.get_position()

            if result['status'] == 'OK':
                pos = result['position']
                return f"x={pos['x']},y={pos['y']},angle={pos['angle']}"
            else:
                raise RuntimeError(f"Get position failed: {result.get('error', 'Unknown error')}")

        elif command == 'calibrate' or command == 'CALIBRATE':
            result = await self.calibrate_position()

            if result['status'] == 'OK':
                return result['output']
            else:
                raise RuntimeError(f"Calibration failed: {result.get('error', 'Unknown error')}")

        elif command == 'reset' or command == 'RESET':
            # Reset position to origin
            position = {'x': 0, 'y': 0, 'angle': 0, 'speed': 50}
            result = await self.set_position(position)

            if result['status'] == 'OK':
                return result['output']
            else:
                raise RuntimeError(f"Reset failed: {result.get('error', 'Unknown error')}")

        else:
            # Try to execute as raw command
            return await self._exec_command(command, timeout=timeout)

    async def close(self):
        """Close SSH connection"""
        if self.ssh_client:
            try:
                await asyncio.get_event_loop().run_in_executor(
                    None, self.ssh_client.close
                )
                self.logger.info("SSH connection closed")
            except Exception as e:
                self.logger.error(f"Error closing SSH: {e}")

    def __del__(self):
        """Ensure SSH connection is closed on cleanup"""
        if self.ssh_client:
            try:
                self.ssh_client.close()
            except:
                pass
