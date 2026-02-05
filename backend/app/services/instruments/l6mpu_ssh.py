"""
L6MPU SSH Command Instrument Driver

SSH-based control for L6MPU (i.MX8MP embedded system).
Supports LTE module testing, PLC network connectivity, and general Linux command execution.

Based on: src/lowsheen_lib/L6MPU/ssh_cmd.py from PDTool4
"""
import asyncio
import logging
from typing import Dict, Any, Optional, Tuple

import paramiko
from decimal import Decimal

from app.services.instrument_connection import BaseInstrumentConnection
from app.services.instruments.base import BaseInstrumentDriver, validate_required_params, get_param


class L6MPUSSHDriver(BaseInstrumentDriver):
    """
    L6MPU SSH command interface driver

    Supports:
    - SSH connection to i.MX8MP devices
    - LTE module AT command testing via microcom
    - PLC network connectivity (eth0/eth1) ping tests
    - General Linux shell command execution
    - Operator confirmation tests (with image reference)

    Connection configuration (SSHAddress):
        - host: SSH hostname or IP address
        - port: SSH port (default: 22)
        - username: SSH username (default: root)
        - password: SSH password (default: empty for key-based auth)
        - timeout: Connection timeout in milliseconds
    """

    def __init__(self, connection: BaseInstrumentConnection):
        """Initialize L6MPU SSH driver"""
        super().__init__(connection)
        self.ssh_client: Optional[paramiko.SSHClient] = None
        self.shell: Optional[paramiko.Channel] = None
        self.default_timeout = 10.0

    async def initialize(self):
        """Initialize SSH connection"""
        try:
            # Get SSH connection configuration
            conn_config = self.connection.config.connection

            host = getattr(conn_config, 'host', '192.168.5.1')
            port = getattr(conn_config, 'port', 22)
            username = getattr(conn_config, 'username', 'root')
            password = getattr(conn_config, 'password', '')
            timeout_ms = getattr(conn_config, 'timeout', 10000)
            timeout = timeout_ms / 1000.0

            # Create SSH client in thread pool
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
            self.logger.error(f"Unexpected error during initialization: {e}")
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

    async def _exec_command(self, command: str, timeout: float = 5.0) -> Tuple[str, str]:
        """
        Execute command via SSH

        Args:
            command: Command to execute
            timeout: Execution timeout in seconds

        Returns:
            Tuple of (stdout, stderr)
        """
        if not self.ssh_client:
            raise ConnectionError("SSH connection not established")

        try:
            # Execute command in thread pool
            def run_command():
                stdin, stdout, stderr = self.ssh_client.exec_command(command, timeout=timeout)
                stdout_str = stdout.read().decode('utf-8', errors='ignore')
                stderr_str = stderr.read().decode('utf-8', errors='ignore')
                return stdout_str, stderr_str

            stdout, stderr = await asyncio.get_event_loop().run_in_executor(
                None, run_command
            )

            self.logger.debug(f"Command: {command} -> stdout: {stdout}, stderr: {stderr}")
            return stdout, stderr

        except paramiko.SSHException as e:
            self.logger.error(f"SSH command execution error: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Command execution error: {e}")
            raise

    async def lte_check(self, timeout: float = 5.0) -> Dict[str, Any]:
        """
        Check LTE module SIM card status

        Uses microcom to connect to LTE module on /dev/ttyUSB3
        and send AT+CPIN? command to check SIM status.

        Args:
            timeout: Command timeout in seconds

        Returns:
            Dict with keys:
                - status: 'OK', 'ERROR', 'TIMEOUT'
                - response: AT command response
                - sim_ready: True if SIM is ready
        """
        try:
            self.logger.info("Checking LTE module SIM status")

            # Send AT command via microcom
            # microcom -t 2000 -s 115200 /dev/ttyUSB3
            command = "microcom -t 2000 -s 115200 /dev/ttyUSB3"

            def run_lte_check():
                stdin, stdout, stderr = self.ssh_client.exec_command(command, timeout=timeout)

                # Send AT command
                stdin.write("AT+CPIN?\n")
                stdin.flush()

                # Wait for response
                asyncio.get_event_loop().run_in_executor(None, lambda: asyncio.sleep(1.5))

                # Read response
                response = stdout.read().decode('utf-8', errors='ignore')
                return response

            response = await asyncio.get_event_loop().run_in_executor(
                None, run_lte_check
            )

            # Check for SIM ready response
            sim_ready = "+CPIN: READY" in response or "READY" in response

            return {
                'status': 'OK' if response else 'TIMEOUT',
                'response': response,
                'sim_ready': sim_ready
            }

        except Exception as e:
            self.logger.error(f"LTE check error: {e}")
            return {
                'status': 'ERROR',
                'response': str(e),
                'sim_ready': False
            }

    async def plc_ping_test(self, interface: str = 'eth0', count: int = 4) -> Dict[str, Any]:
        """
        Test PLC network connectivity via ping

        Args:
            interface: Network interface (eth0 or eth1)
            count: Number of ping packets

        Returns:
            Dict with keys:
                - status: 'OK', 'ERROR'
                - interface: Network interface used
                - ip_address: IP address of interface
                - ping_result: Ping output
                - packet_loss: Packet loss percentage
        """
        try:
            self.logger.info(f"Testing PLC {interface} connectivity")

            # Get IP address of interface
            ip_cmd = f"ifconfig {interface} | grep 'inet ' | awk '{{print $2}}'"
            ip_stdout, _ = await self._exec_command(ip_cmd, timeout=2.0)

            ip_address = ip_stdout.strip()
            if not ip_address:
                return {
                    'status': 'ERROR',
                    'interface': interface,
                    'error': f'No IP address assigned to {interface}'
                }

            # Perform ping test
            ping_cmd = f"ping -c {count} {ip_address}"
            ping_stdout, ping_stderr = await self._exec_command(ping_cmd, timeout=10.0)

            # Parse packet loss
            packet_loss = None
            if 'packet loss' in ping_stdout or '% packet' in ping_stdout:
                for line in ping_stdout.split('\n'):
                    if 'packet loss' in line or '% packet' in line:
                        try:
                            # Extract percentage
                            parts = line.split(',')
                            for part in parts:
                                if '%' in part:
                                    packet_loss = float(part.strip().split('%')[0].strip())
                                    break
                        except:
                            pass
                        break

            return {
                'status': 'OK',
                'interface': interface,
                'ip_address': ip_address,
                'ping_result': ping_stdout,
                'packet_loss': packet_loss
            }

        except Exception as e:
            self.logger.error(f"PLC ping test error: {e}")
            return {
                'status': 'ERROR',
                'interface': interface,
                'error': str(e)
            }

    async def execute_command(self, params: Dict[str, Any]) -> str:
        """
        Execute command via SSH

        Parameters in params dict:
            - command (str, required): Command to execute
            - timeout (float, optional): Execution timeout in seconds (default: 5.0)
            - type (str, optional): Command type
                - 'LTE': LTE module check
                - 'PLC1': PLC1 (eth0) network test
                - 'PLC2': PLC2 (eth1) network test
                - 'ATcommand:<cmd>': AT command (not directly supported, use ssh_comport instead)
                - 'command:<cmd>': General Linux command
                - 'Confirmcommand:<cmd>': Command with operator confirmation

        Returns:
            Command output string
        """
        validate_required_params(params, ['command'])

        command = get_param(params, 'command')
        timeout = float(get_param(params, 'timeout', default=self.default_timeout))

        self.logger.info(f"Executing L6MPU SSH command: {command}")

        # Check command type
        if command == 'LTE' or command.startswith('LTE'):
            result = await self.lte_check(timeout=timeout)
            if result['status'] == 'OK':
                return result['response']
            else:
                raise RuntimeError(f"LTE check failed: {result.get('error', 'Unknown error')}")

        elif command == 'PLC1' or command.startswith('PLC1'):
            result = await self.plc_ping_test(interface='eth0')
            if result['status'] == 'OK':
                return result['ping_result']
            else:
                raise RuntimeError(f"PLC1 test failed: {result.get('error', 'Unknown error')}")

        elif command == 'PLC2' or command.startswith('PLC2'):
            result = await self.plc_ping_test(interface='eth1')
            if result['status'] == 'OK':
                return result['ping_result']
            else:
                raise RuntimeError(f"PLC2 test failed: {result.get('error', 'Unknown error')}")

        elif command.startswith('command:'):
            # Extract actual command after 'command:'
            actual_command = command.split('command:', 1)[1].strip()
            stdout, stderr = await self._exec_command(actual_command, timeout=timeout)
            return stdout if stdout else stderr

        elif command.startswith('Confirmcommand:'):
            # For confirmation commands, execute and return result
            # Note: In web environment, confirmation should be handled by UI
            actual_command = command.split('Confirmcommand:', 1)[1].strip()
            stdout, stderr = await self._exec_command(actual_command, timeout=timeout)
            return f"CONFIRM_REQUIRED:{stdout if stdout else stderr}"

        else:
            # Treat as direct command
            stdout, stderr = await self._exec_command(command, timeout=timeout)
            return stdout if stdout else stderr

    async def close(self):
        """Close SSH connection"""
        if self.ssh_client:
            try:
                await asyncio.get_event_loop().run_in_executor(
                    None, self.ssh_client.close
                )
                self.logger.info("SSH connection closed")
            except Exception as e:
                self.logger.error(f"Error closing SSH connection: {e}")

    def __del__(self):
        """Ensure SSH connection is closed on cleanup"""
        if self.ssh_client:
            try:
                self.ssh_client.close()
            except:
                pass
