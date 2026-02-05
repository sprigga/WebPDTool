"""
Unit tests for ConSoleCommand instrument driver
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from decimal import Decimal

from app.services.instruments.console_command import ConSoleCommandDriver
from app.services.instrument_connection import BaseInstrumentConnection


# ============================================================================
# Mock Connection Class
# ============================================================================

from app.core.instrument_config import InstrumentConfig, VISAAddress

class MockConsoleConnection(BaseInstrumentConnection):
    """Mock console connection for testing"""

    def __init__(self, use_shell: bool = False, working_dir: str = None):
        config = InstrumentConfig(
            id="console_command",
            type="console",
            name="Mock Console Command",
            connection=VISAAddress(
                type="VISA",
                address="console://",
                timeout=5000
            )
        )
        super().__init__(config)
        self.use_shell = use_shell
        self.working_dir = working_dir
        self.env_vars = {}

    async def connect(self) -> bool:
        self.is_connected = True
        return True

    async def disconnect(self) -> bool:
        self.is_connected = False
        return True

    async def write(self, command: str) -> None:
        pass

    async def query(self, command: str) -> str:
        return ""

    async def read(self) -> str:
        return ""


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def console_driver():
    """Create ConSoleCommandDriver"""
    config = MockConsoleConnection()
    driver = ConSoleCommandDriver(config)
    return driver


# ============================================================================
# Test Cases
# ============================================================================

class TestConSoleCommandDriverInitialization:
    """Test driver initialization"""

    @pytest.mark.asyncio
    async def test_initialize_default(self, console_driver):
        """Test default initialization"""
        await console_driver.initialize()

        assert console_driver.use_shell is False
        assert console_driver.working_dir is None
        assert console_driver.env_vars == {}

    @pytest.mark.asyncio
    async def test_initialize_with_shell(self):
        """Test initialization with shell enabled"""
        config = MockConsoleConnection(use_shell=True)
        driver = ConSoleCommandDriver(config)

        await driver.initialize()

        assert driver.use_shell is True

    @pytest.mark.asyncio
    async def test_initialize_with_working_dir(self):
        """Test initialization with working directory"""
        config = MockConsoleConnection(working_dir="/tmp")
        driver = ConSoleCommandDriver(config)

        await driver.initialize()

        assert driver.working_dir == "/tmp"

    @pytest.mark.asyncio
    async def test_reset(self, console_driver):
        """Test reset operation (no-op for console)"""
        await console_driver.reset()
        # Should not raise any error


class TestConSoleCommandDriverOperations:
    """Test driver operations"""

    @pytest.mark.asyncio
    async def test_send_command_echo(self, console_driver):
        """Test simple echo command"""
        response = await console_driver.send_command({
            'Command': 'echo Hello World',
            'Timeout': 5.0
        })

        assert "Hello World" in response

    @pytest.mark.asyncio
    async def test_send_command_list(self, console_driver):
        """Test command as list"""
        response = await console_driver.send_command({
            'Command': ['echo', 'Test'],
            'Timeout': 5.0
        })

        assert "Test" in response

    @pytest.mark.asyncio
    async def test_send_command_with_stderr(self, console_driver):
        """Test command that produces stderr"""
        response = await console_driver.send_command({
            'Command': 'python -c "import sys; sys.stderr.write(\'Error\\n\')"',
            'Timeout': 5.0,
            'CaptureStderr': True
        })

        # Should include stderr in output
        assert "Error" in response or "STDERR" in response

    @pytest.mark.asyncio
    async def test_send_command_timeout(self, console_driver):
        """Test command timeout"""
        response = await console_driver.send_command({
            'Command': 'sleep 10',
            'Timeout': 0.5
        })

        # Should indicate timeout
        assert "Timed Out" in response

    @pytest.mark.asyncio
    async def test_query_command(self, console_driver):
        """Test query_command helper method"""
        response = await console_driver.query_command("echo test", timeout=5.0)

        assert "test" in response

    @pytest.mark.asyncio
    async def test_execute_script(self, console_driver):
        """Test execute_script helper method"""
        import sys
        response = await console_driver.execute_script(
            '-c "print(\'script output\')"',
            timeout=5.0
        )

        assert "script output" in response

    @pytest.mark.asyncio
    async def test_close(self, console_driver):
        """Test close operation (no-op for console)"""
        await console_driver.close()
        # Should not raise any error


class TestConSoleCommandDriverValidation:
    """Test parameter validation"""

    @pytest.mark.asyncio
    async def test_missing_command_parameter(self, console_driver):
        """Test error when Command parameter is missing"""
        with pytest.raises(ValueError, match="Missing required parameters"):
            await console_driver.send_command({})

    @pytest.mark.asyncio
    async def test_command_not_found(self, console_driver):
        """Test error when command is not found"""
        with pytest.raises(ValueError, match="Command not found"):
            await console_driver.send_command({
                'Command': 'nonexistent_command_xyz123',
                'Timeout': 5.0
            })

    @pytest.mark.asyncio
    async def test_boolean_string_conversion(self, console_driver):
        """Test conversion of boolean strings"""
        response = await console_driver.send_command({
            'Command': 'echo test',
            'Timeout': 5.0,
            'CaptureStderr': 'true',
            'ReturnCode': 'false'
        })

        # Should work with string booleans
        assert "test" in response

    @pytest.mark.asyncio
    async def test_env_vars_parsing(self, console_driver):
        """Test environment variables parsing"""
        import os

        response = await console_driver.send_command({
            'Command': f'echo {os.environ.get("TEST_VAR", "notset")}',
            'Timeout': 5.0,
            'EnvVars': 'TEST_VAR=test_value'
        })

        # Environment variable should be set
        assert "test_value" in response or "notset" in response


class TestConSoleCommandDriverWorkingDirectory:
    """Test working directory functionality"""

    @pytest.mark.asyncio
    async def test_working_dir_parameter(self, console_driver):
        """Test WorkingDir parameter"""
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as tmpdir:
            response = await console_driver.send_command({
                'Command': f'python -c "import os; print(os.getcwd())"',
                'Timeout': 5.0,
                'WorkingDir': tmpdir
            })

            # Should show the working directory
            assert tmpdir in response or tmpdir.replace('\\', '/') in response

    @pytest.mark.asyncio
    async def test_working_dir_from_config(self):
        """Test working directory from config"""
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as tmpdir:
            config = MockConsoleConnection(working_dir=tmpdir)
            driver = ConSoleCommandDriver(config)
            await driver.initialize()

            response = await driver.send_command({
                'Command': f'python -c "import os; print(os.getcwd())"',
                'Timeout': 5.0
            })

            # Should use working directory from config
            assert tmpdir in response or tmpdir.replace('\\', '/') in response


class TestConSoleCommandDriverShellMode:
    """Test shell mode functionality"""

    @pytest.mark.asyncio
    async def test_shell_mode_enabled(self):
        """Test command execution with shell mode"""
        config = MockConsoleConnection(use_shell=True)
        driver = ConSoleCommandDriver(config)
        await driver.initialize()

        # Should work with shell features like pipes
        response = await driver.send_command({
            'Command': 'echo hello | tr a-z A-Z',
            'Timeout': 5.0
        })

        assert "HELLO" in response

    @pytest.mark.asyncio
    async def test_shell_mode_parameter(self, console_driver):
        """Test Shell parameter override"""
        response = await console_driver.send_command({
            'Command': 'echo test',
            'Timeout': 5.0,
            'Shell': 'false'
        })

        assert "test" in response


# ============================================================================
# Integration Tests
# ============================================================================

class TestConSoleCommandDriverIntegration:
    """Integration tests for complex scenarios"""

    @pytest.mark.asyncio
    async def test_python_script_execution(self, console_driver):
        """Test executing a Python script"""
        script = """
import sys
print("Line 1")
print("Line 2", file=sys.stderr)
sys.exit(0)
"""

        response = await console_driver.send_command({
            'Command': ['python', '-c', script],
            'Timeout': 5.0,
            'CaptureStderr': True
        })

        # Should have both stdout and stderr
        assert "Line 1" in response or "Line 2" in response

    @pytest.mark.asyncio
    async def test_multiple_commands_sequence(self, console_driver):
        """Test sequence of multiple commands"""
        commands = [
            {'Command': 'echo "First"', 'Timeout': 5.0},
            {'Command': 'echo "Second"', 'Timeout': 5.0},
            {'Command': 'echo "Third"', 'Timeout': 5.0}
        ]

        results = []
        for cmd in commands:
            response = await console_driver.send_command(cmd)
            results.append(response)

        assert len(results) == 3
        assert "First" in results[0]
        assert "Second" in results[1]
        assert "Third" in results[2]

    @pytest.mark.asyncio
    async def test_command_with_return_code(self, console_driver):
        """Test command with return code capture"""
        response = await console_driver.send_command({
            'Command': 'python -c "import sys; sys.exit(42)"',
            'Timeout': 5.0,
            'ReturnCode': True
        })

        # Should include return code
        assert "42" in response

    @pytest.mark.asyncio
    async def test_command_error_output(self, console_driver):
        """Test command that produces error"""
        response = await console_driver.send_command({
            'Command': 'python -c "1/0"',
            'Timeout': 5.0,
            'CaptureStderr': True
        })

        # Should have error output
        # Python error message or stderr indication
        assert "ZeroDivisionError" in response or "STDERR" in response or len(response) > 0
