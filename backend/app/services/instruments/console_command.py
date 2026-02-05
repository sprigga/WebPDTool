"""
Console Command Instrument Driver

Generic subprocess command execution interface with timeout support
Enables execution of external commands, scripts, and system utilities
"""
import asyncio
import logging
import shlex
from typing import Dict, Any, Optional, List

from app.services.instrument_connection import BaseInstrumentConnection
from app.services.instruments.base import BaseInstrumentDriver, validate_required_params, get_param


class ConSoleCommandDriver(BaseInstrumentDriver):
    """
    Generic console command interface driver

    Supports:
    - External command execution with timeout
    - Shell command support (optional, for security)
    - Working directory and environment variable configuration
    - Stdout/stderr capture
    """

    def __init__(self, connection: BaseInstrumentConnection):
        """Initialize Console command driver"""
        super().__init__(connection)
        self.default_timeout = 5.0
        self.use_shell = False  # shell=False for security by default
        self.working_dir = None
        self.env_vars = {}

    async def initialize(self):
        """
        Initialize console command driver

        Configuration from connection.config or connection object:
            - working_dir: Working directory for command execution
            - env_vars: Dictionary of environment variables
            - use_shell: Whether to use shell=True for command execution
        """
        # No connection to establish for console commands
        # Just validate configuration (check both config and connection for compatibility)
        self.use_shell = getattr(self.connection.config, 'use_shell',
                                  getattr(self.connection, 'use_shell', False))
        self.working_dir = getattr(self.connection.config, 'working_dir',
                                     getattr(self.connection, 'working_dir', None))
        self.env_vars = getattr(self.connection.config, 'env_vars',
                                 getattr(self.connection, 'env_vars', {}))

        if self.use_shell:
            self.logger.warning("Shell mode enabled - ensure commands are sanitized!")

        self.logger.info("Console command driver initialized")

    async def reset(self):
        """Reset (no-op for console commands)"""
        self.logger.debug("Console command reset: no action needed")

    async def _execute_command(self,
                               command: str or List[str],
                               timeout: float,
                               shell: bool = None,
                               working_dir: str = None,
                               env_vars: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Execute command as subprocess

        Args:
            command: Command to execute (string or list)
            timeout: Maximum execution time in seconds
            shell: Whether to use shell execution (None = use default)
            working_dir: Working directory for command
            env_vars: Environment variables to set

        Returns:
            Dictionary with:
                - stdout: Standard output
                - stderr: Standard error (separate, not merged)
                - returncode: Process return code
                - timed_out: Whether process timed out
        """
        # Determine shell usage
        use_shell = self.use_shell if shell is None else shell

        # Prepare command list
        if isinstance(command, str):
            if use_shell:
                cmd_list = command
            else:
                # Parse command string into list using shlex
                try:
                    cmd_list = shlex.split(command)
                except ValueError as e:
                    raise ValueError(f"Failed to parse command: {e}")
        else:
            cmd_list = command

        # Prepare environment
        import os
        proc_env = os.environ.copy()
        if env_vars:
            proc_env.update(env_vars)
        if self.env_vars:
            proc_env.update(self.env_vars)

        self.logger.info(f"Executing command: {cmd_list} (timeout={timeout}s, shell={use_shell})")

        try:
            # Create subprocess - use shell for shell mode, exec for list mode
            if use_shell and isinstance(cmd_list, str):
                # Shell mode: use create_subprocess_shell with the command string
                process = await asyncio.create_subprocess_shell(
                    cmd_list,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=working_dir or self.working_dir,
                    env=proc_env
                )
            else:
                # Exec mode: use create_subprocess_exec with command list
                process = await asyncio.create_subprocess_exec(
                    *cmd_list if isinstance(cmd_list, list) else [cmd_list],
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=working_dir or self.working_dir,
                    env=proc_env
                )

            # Wait for completion with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
                timed_out = False

            except asyncio.TimeoutError:
                # Kill process on timeout
                process.kill()
                stdout, stderr = await process.communicate()
                timed_out = True
                self.logger.warning(f"Command timed out after {timeout}s, process killed")

            # Decode output
            stdout_text = stdout.decode('utf-8', errors='ignore').strip()
            stderr_text = stderr.decode('utf-8', errors='ignore').strip()

            result = {
                'stdout': stdout_text,
                'stderr': stderr_text,
                'returncode': process.returncode,
                'timed_out': timed_out
            }

            self.logger.debug(f"Command completed: returncode={result['returncode']}, "
                            f"timed_out={timed_out}, stdout_len={len(stdout_text)}")

            return result

        except FileNotFoundError as e:
            raise ValueError(f"Command not found: {cmd_list[0] if isinstance(cmd_list, list) else cmd_list}")
        except PermissionError as e:
            raise PermissionError(f"Permission denied executing command: {e}")
        except Exception as e:
            self.logger.error(f"Failed to execute command: {e}")
            raise

    async def send_command(self, params: Dict[str, Any]) -> str:
        """
        Send command and return output

        Parameters in params dict:
            - Command (str or list, required): Command to execute
            - Timeout (float, optional): Timeout in seconds (default: 5.0)
            - Shell (bool, optional): Use shell execution (default: False)
            - WorkingDir (str, optional): Working directory
            - EnvVars (dict, optional): Environment variables
            - CaptureStderr (bool, optional): Include stderr in output (default: True)
            - ReturnCode (bool, optional): Include return code in output (default: False)

        Returns:
            Command output (stdout, or stdout+stderr if CaptureStderr=True)
        """
        # Validate required parameters
        validate_required_params(params, ['Command'])

        # Get parameters
        command = get_param(params, 'Command', 'command')
        timeout = float(get_param(params, 'Timeout', 'timeout', default=self.default_timeout))
        shell = get_param(params, 'Shell', 'shell')
        working_dir = get_param(params, 'WorkingDir', 'working_dir', 'cwd')
        env_vars = get_param(params, 'EnvVars', 'env_vars', 'env')
        capture_stderr = get_param(params, 'CaptureStderr', 'capture_stderr', 'capturestderr', default=True)
        return_code = get_param(params, 'ReturnCode', 'return_code', 'returncode', default=False)

        # Convert boolean strings
        if isinstance(capture_stderr, str):
            capture_stderr = capture_stderr.lower() in ('true', '1', 'yes', 'on')
        if isinstance(return_code, str):
            return_code = return_code.lower() in ('true', '1', 'yes', 'on')
        if shell is not None and isinstance(shell, str):
            shell = shell.lower() in ('true', '1', 'yes', 'on')

        # Parse env_vars if it's a string
        if isinstance(env_vars, str):
            # Simple format: "KEY1=VALUE1,KEY2=VALUE2"
            env_vars = dict(item.split('=', 1) for item in env_vars.split(',') if '=' in item)

        # Execute command
        result = await self._execute_command(
            command=command,
            timeout=timeout,
            shell=shell,
            working_dir=working_dir,
            env_vars=env_vars
        )

        # Format output
        output_parts = []

        if result['stdout']:
            output_parts.append(result['stdout'])

        if capture_stderr and result['stderr']:
            if output_parts:
                output_parts.append("\n--- STDERR ---\n")
            output_parts.append(result['stderr'])

        if return_code:
            output_parts.append(f"\n--- Return Code: {result['returncode']} ---")

        if result['timed_out']:
            output_parts.append("\n--- Command Timed Out ---")

        return ''.join(output_parts)

    async def query_command(self, command: str, timeout: float = 5.0) -> str:
        """
        Query command (execute and return stdout)

        Args:
            command: Command to execute
            timeout: Maximum execution time in seconds

        Returns:
            Command output
        """
        params = {
            'Command': command,
            'Timeout': timeout
        }
        return await self.send_command(params)

    async def execute_script(self, script_path: str, args: List[str] = None,
                           timeout: float = 30.0) -> str:
        """
        Execute Python script

        Args:
            script_path: Path to Python script
            args: Script arguments
            timeout: Maximum execution time

        Returns:
            Script output
        """
        import sys
        command = [sys.executable, script_path]
        if args:
            command.extend(args)

        return await self.query_command(command, timeout=timeout)

    async def close(self):
        """Close console command driver (no-op)"""
        self.logger.debug("Console command driver closed")
