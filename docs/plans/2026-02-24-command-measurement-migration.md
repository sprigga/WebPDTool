# Command Measurement Migration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the stub `CommandTestMeasurement` with three dedicated measurement classes (`ComPortMeasurement`, `ConSoleMeasurement`, `TCPIPMeasurement`) that delegate to their respective modern instrument drivers, completing the lowsheen_lib migration for the command-type tests.

**Architecture:** Each new class mirrors the `PowerReadMeasurement` pattern — it reads `Instrument` from `test_params`, looks up the instrument config via `get_instrument_settings()`, gets the driver via `get_driver_class()`, acquires a connection from `get_connection_pool()`, and calls `driver.send_command(params)`. The old `CommandTestMeasurement` is commented out (not deleted) per project conventions. Registry entries for `"comport"`, `"console"`, `"tcpip"` are updated to point to the new classes.

**Tech Stack:** Python 3.11, FastAPI (backend), pytest + pytest-asyncio, `unittest.mock` for driver mocking. All code lives in `backend/app/measurements/implementations.py`.

---

### Task 1: Add `ComPortMeasurement` class

**Files:**
- Modify: `backend/app/measurements/implementations.py` (after existing `CommandTestMeasurement` block, ~line 356)
- Test: `backend/tests/test_measurements/test_command_measurements.py` (new file)

**Step 1: Write the failing test**

Create `backend/tests/test_measurements/test_command_measurements.py`:

```python
"""
Tests for ComPortMeasurement, ConSoleMeasurement, TCPIPMeasurement
"""
import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from app.measurements.implementations import ComPortMeasurement


def make_test_plan_item(parameters: dict, **kwargs) -> dict:
    return {
        "item_no": 1,
        "item_name": "CommandTest",
        "lower_limit": kwargs.get("lower_limit"),
        "upper_limit": kwargs.get("upper_limit"),
        "limit_type": kwargs.get("limit_type", "none"),
        "value_type": kwargs.get("value_type", "string"),
        "unit": "",
        "parameters": parameters,
    }


class TestComPortMeasurement:
    @pytest.mark.asyncio
    async def test_execute_returns_pass_on_response(self):
        """ComPortMeasurement calls driver.send_command and returns PASS"""
        test_plan_item = make_test_plan_item(
            {"Instrument": "ComPort_1", "Command": "0xAA\n", "Timeout": "3"},
        )
        measurement = ComPortMeasurement(test_plan_item, config={})

        mock_driver = AsyncMock()
        mock_driver.send_command = AsyncMock(return_value="OK")
        mock_driver.initialize = AsyncMock()

        mock_config = MagicMock()
        mock_config.type = "comport"

        with patch("app.measurements.implementations.get_instrument_settings") as mock_settings, \
             patch("app.measurements.implementations.get_driver_class") as mock_get_driver, \
             patch("app.measurements.implementations.get_connection_pool") as mock_pool:

            mock_settings.return_value.get_instrument.return_value = mock_config
            mock_get_driver.return_value = lambda conn: mock_driver

            mock_conn_ctx = MagicMock()
            mock_conn_ctx.__aenter__ = AsyncMock(return_value=MagicMock())
            mock_conn_ctx.__aexit__ = AsyncMock(return_value=None)
            mock_pool.return_value.get_connection.return_value = mock_conn_ctx

            result = await measurement.execute()

        assert result.result == "PASS"
        mock_driver.send_command.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_returns_error_when_instrument_not_configured(self):
        """Returns ERROR when instrument is not found in config"""
        test_plan_item = make_test_plan_item(
            {"Instrument": "ComPort_MISSING", "Command": "TEST\n"},
        )
        measurement = ComPortMeasurement(test_plan_item, config={})

        with patch("app.measurements.implementations.get_instrument_settings") as mock_settings, \
             patch("app.measurements.implementations.get_driver_class"), \
             patch("app.measurements.implementations.get_connection_pool"):

            mock_settings.return_value.get_instrument.return_value = None

            result = await measurement.execute()

        assert result.result == "ERROR"
        assert "not configured" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_execute_returns_error_when_missing_instrument_param(self):
        """Returns ERROR when Instrument parameter is absent"""
        test_plan_item = make_test_plan_item({"Command": "TEST\n"})
        measurement = ComPortMeasurement(test_plan_item, config={})

        with patch("app.measurements.implementations.get_instrument_settings"), \
             patch("app.measurements.implementations.get_driver_class"), \
             patch("app.measurements.implementations.get_connection_pool"):

            result = await measurement.execute()

        assert result.result == "ERROR"
```

**Step 2: Run test to verify it fails**

```bash
cd backend && uv run pytest tests/test_measurements/test_command_measurements.py::TestComPortMeasurement -v
```

Expected: `ImportError: cannot import name 'ComPortMeasurement'`

**Step 3: Add `ComPortMeasurement` to `implementations.py`**

Find the block ending at line ~356 (after `CommandTestMeasurement`):

```python
# ============================================================================
# ComPort Measurement — replaces lowsheen_lib/ComPortCommand.py
# ============================================================================
class ComPortMeasurement(BaseMeasurement):
    """
    Sends a serial command via ComPortCommandDriver and returns the response.

    Required test_params:
        - Instrument (str): key in instrument_settings (type must be 'comport')
        - Command (str): command bytes/string to send (supports \\n escapes)

    Optional test_params:
        - Timeout (float): read timeout in seconds (default: 3.0)
        - ReslineCount (int): expected response line count (default: auto-detect)
        - ComportWait (float): seconds to wait after port open (default: 0)
        - SettlingTime (float): seconds between write and read (default: 0.5)
    """

    async def execute(self) -> MeasurementResult:
        try:
            from app.services.instrument_connection import get_connection_pool
            from app.services.instruments import get_driver_class
            from app.core.instrument_config import get_instrument_settings

            instrument_name = get_param(self.test_params, "Instrument", "instrument")
            if not instrument_name:
                return self.create_result(
                    result="ERROR",
                    error_message="Missing required parameter: Instrument"
                )

            instrument_settings = get_instrument_settings()
            config = instrument_settings.get_instrument(instrument_name)
            if config is None:
                return self.create_result(
                    result="ERROR",
                    error_message=f"Instrument '{instrument_name}' not configured"
                )

            driver_class = get_driver_class(config.type)
            if driver_class is None:
                return self.create_result(
                    result="ERROR",
                    error_message=f"No driver for instrument type '{config.type}'"
                )

            connection_pool = get_connection_pool()
            async with connection_pool.get_connection(instrument_name) as conn:
                driver = driver_class(conn)
                await driver.initialize()
                response = await driver.send_command(self.test_params)

            self.logger.info(f"ComPort response: {repr(response)}")
            measured_value = str(response) if response is not None else ""

            is_valid, error_msg = self.validate_result(measured_value)
            return self.create_result(
                result="PASS" if is_valid else "FAIL",
                measured_value=measured_value,
                error_message=error_msg if not is_valid else None
            )

        except Exception as e:
            self.logger.error(f"ComPort measurement error: {e}", exc_info=True)
            return self.create_result(result="ERROR", error_message=str(e))
```

**Step 4: Run tests to verify they pass**

```bash
cd backend && uv run pytest tests/test_measurements/test_command_measurements.py::TestComPortMeasurement -v
```

Expected: 3 tests PASS

**Step 5: Commit**

```bash
git add backend/app/measurements/implementations.py backend/tests/test_measurements/test_command_measurements.py
git commit -m "feat: add ComPortMeasurement delegating to ComPortCommandDriver"
```

---

### Task 2: Add `ConSoleMeasurement` class

**Files:**
- Modify: `backend/app/measurements/implementations.py` (after `ComPortMeasurement`)
- Test: `backend/tests/test_measurements/test_command_measurements.py` (append)

**Step 1: Write failing tests — append to test file**

```python
from app.measurements.implementations import ConSoleMeasurement


class TestConSoleMeasurement:
    @pytest.mark.asyncio
    async def test_execute_returns_pass_on_response(self):
        """ConSoleMeasurement calls driver.send_command and returns PASS"""
        test_plan_item = make_test_plan_item(
            {"Instrument": "Console_1", "Command": "python ./scripts/check.py", "Timeout": "5"},
        )
        measurement = ConSoleMeasurement(test_plan_item, config={})

        mock_driver = AsyncMock()
        mock_driver.send_command = AsyncMock(return_value="PASS_OUTPUT")
        mock_driver.initialize = AsyncMock()

        mock_config = MagicMock()
        mock_config.type = "console"

        with patch("app.measurements.implementations.get_instrument_settings") as mock_settings, \
             patch("app.measurements.implementations.get_driver_class") as mock_get_driver, \
             patch("app.measurements.implementations.get_connection_pool") as mock_pool:

            mock_settings.return_value.get_instrument.return_value = mock_config
            mock_get_driver.return_value = lambda conn: mock_driver

            mock_conn_ctx = MagicMock()
            mock_conn_ctx.__aenter__ = AsyncMock(return_value=MagicMock())
            mock_conn_ctx.__aexit__ = AsyncMock(return_value=None)
            mock_pool.return_value.get_connection.return_value = mock_conn_ctx

            result = await measurement.execute()

        assert result.result == "PASS"
        mock_driver.send_command.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_returns_error_when_instrument_not_configured(self):
        test_plan_item = make_test_plan_item(
            {"Instrument": "Console_MISSING", "Command": "echo ok"},
        )
        measurement = ConSoleMeasurement(test_plan_item, config={})

        with patch("app.measurements.implementations.get_instrument_settings") as mock_settings, \
             patch("app.measurements.implementations.get_driver_class"), \
             patch("app.measurements.implementations.get_connection_pool"):

            mock_settings.return_value.get_instrument.return_value = None
            result = await measurement.execute()

        assert result.result == "ERROR"
        assert "not configured" in result.error_message.lower()
```

**Step 2: Run to verify fails**

```bash
cd backend && uv run pytest tests/test_measurements/test_command_measurements.py::TestConSoleMeasurement -v
```

Expected: `ImportError: cannot import name 'ConSoleMeasurement'`

**Step 3: Add `ConSoleMeasurement` to `implementations.py`**

```python
# ============================================================================
# ConSole Measurement — replaces lowsheen_lib/ConSoleCommand.py
# ============================================================================
class ConSoleMeasurement(BaseMeasurement):
    """
    Executes a system command via ConSoleCommandDriver and returns stdout.

    Required test_params:
        - Instrument (str): key in instrument_settings (type must be 'console')
        - Command (str): command string to execute

    Optional test_params:
        - Timeout (float): execution timeout in seconds (default: 5.0)
        - Shell (bool): use shell execution (default: False)
        - WorkingDir (str): working directory
    """

    async def execute(self) -> MeasurementResult:
        try:
            from app.services.instrument_connection import get_connection_pool
            from app.services.instruments import get_driver_class
            from app.core.instrument_config import get_instrument_settings

            instrument_name = get_param(self.test_params, "Instrument", "instrument")
            if not instrument_name:
                return self.create_result(
                    result="ERROR",
                    error_message="Missing required parameter: Instrument"
                )

            instrument_settings = get_instrument_settings()
            config = instrument_settings.get_instrument(instrument_name)
            if config is None:
                return self.create_result(
                    result="ERROR",
                    error_message=f"Instrument '{instrument_name}' not configured"
                )

            driver_class = get_driver_class(config.type)
            if driver_class is None:
                return self.create_result(
                    result="ERROR",
                    error_message=f"No driver for instrument type '{config.type}'"
                )

            connection_pool = get_connection_pool()
            async with connection_pool.get_connection(instrument_name) as conn:
                driver = driver_class(conn)
                await driver.initialize()
                response = await driver.send_command(self.test_params)

            self.logger.info(f"Console response: {repr(response)}")
            measured_value = str(response) if response is not None else ""

            is_valid, error_msg = self.validate_result(measured_value)
            return self.create_result(
                result="PASS" if is_valid else "FAIL",
                measured_value=measured_value,
                error_message=error_msg if not is_valid else None
            )

        except Exception as e:
            self.logger.error(f"Console measurement error: {e}", exc_info=True)
            return self.create_result(result="ERROR", error_message=str(e))
```

**Step 4: Run tests**

```bash
cd backend && uv run pytest tests/test_measurements/test_command_measurements.py::TestConSoleMeasurement -v
```

Expected: 2 tests PASS

**Step 5: Commit**

```bash
git add backend/app/measurements/implementations.py backend/tests/test_measurements/test_command_measurements.py
git commit -m "feat: add ConSoleMeasurement delegating to ConSoleCommandDriver"
```

---

### Task 3: Add `TCPIPMeasurement` class

**Files:**
- Modify: `backend/app/measurements/implementations.py` (after `ConSoleMeasurement`)
- Test: `backend/tests/test_measurements/test_command_measurements.py` (append)

**Step 1: Write failing tests — append to test file**

```python
from app.measurements.implementations import TCPIPMeasurement


class TestTCPIPMeasurement:
    @pytest.mark.asyncio
    async def test_execute_returns_pass_on_hex_response(self):
        """TCPIPMeasurement calls driver.send_command and returns PASS with hex response"""
        test_plan_item = make_test_plan_item(
            {"Instrument": "TCPIP_1", "Command": "192.168.1.3 12345 31;01;f0;00;00", "Timeout": "5"},
        )
        measurement = TCPIPMeasurement(test_plan_item, config={})

        mock_driver = AsyncMock()
        mock_driver.send_command = AsyncMock(return_value="31 03 f0 00 00")
        mock_driver.initialize = AsyncMock()

        mock_config = MagicMock()
        mock_config.type = "tcpip"

        with patch("app.measurements.implementations.get_instrument_settings") as mock_settings, \
             patch("app.measurements.implementations.get_driver_class") as mock_get_driver, \
             patch("app.measurements.implementations.get_connection_pool") as mock_pool:

            mock_settings.return_value.get_instrument.return_value = mock_config
            mock_get_driver.return_value = lambda conn: mock_driver

            mock_conn_ctx = MagicMock()
            mock_conn_ctx.__aenter__ = AsyncMock(return_value=MagicMock())
            mock_conn_ctx.__aexit__ = AsyncMock(return_value=None)
            mock_pool.return_value.get_connection.return_value = mock_conn_ctx

            result = await measurement.execute()

        assert result.result == "PASS"
        mock_driver.send_command.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_returns_error_when_instrument_not_configured(self):
        test_plan_item = make_test_plan_item(
            {"Instrument": "TCPIP_MISSING", "Command": "192.168.1.3 12345 31;01;f0"},
        )
        measurement = TCPIPMeasurement(test_plan_item, config={})

        with patch("app.measurements.implementations.get_instrument_settings") as mock_settings, \
             patch("app.measurements.implementations.get_driver_class"), \
             patch("app.measurements.implementations.get_connection_pool"):

            mock_settings.return_value.get_instrument.return_value = None
            result = await measurement.execute()

        assert result.result == "ERROR"
        assert "not configured" in result.error_message.lower()
```

**Step 2: Run to verify fails**

```bash
cd backend && uv run pytest tests/test_measurements/test_command_measurements.py::TestTCPIPMeasurement -v
```

Expected: `ImportError: cannot import name 'TCPIPMeasurement'`

**Step 3: Add `TCPIPMeasurement` to `implementations.py`**

```python
# ============================================================================
# TCPIP Measurement — replaces lowsheen_lib/TCPIPCommand.py
# ============================================================================
class TCPIPMeasurement(BaseMeasurement):
    """
    Sends a TCP/IP socket command via TCPIPCommandDriver and returns hex response.

    Required test_params:
        - Instrument (str): key in instrument_settings (type must be 'tcpip')
        - Command (str): command in hex format "IP PORT BYTES"
                         e.g. "192.168.1.3 12345 31;01;f0;00;00"
                         or just the hex payload if IP/PORT are in instrument config

    Optional test_params:
        - Timeout (float): socket read timeout in seconds (default: 5.0)
        - UseCRC32 (bool): append CRC32 checksum to command (default: True)
        - BufferSize (int): max response bytes (default: 1024)
    """

    async def execute(self) -> MeasurementResult:
        try:
            from app.services.instrument_connection import get_connection_pool
            from app.services.instruments import get_driver_class
            from app.core.instrument_config import get_instrument_settings

            instrument_name = get_param(self.test_params, "Instrument", "instrument")
            if not instrument_name:
                return self.create_result(
                    result="ERROR",
                    error_message="Missing required parameter: Instrument"
                )

            instrument_settings = get_instrument_settings()
            config = instrument_settings.get_instrument(instrument_name)
            if config is None:
                return self.create_result(
                    result="ERROR",
                    error_message=f"Instrument '{instrument_name}' not configured"
                )

            driver_class = get_driver_class(config.type)
            if driver_class is None:
                return self.create_result(
                    result="ERROR",
                    error_message=f"No driver for instrument type '{config.type}'"
                )

            connection_pool = get_connection_pool()
            async with connection_pool.get_connection(instrument_name) as conn:
                driver = driver_class(conn)
                await driver.initialize()
                response = await driver.send_command(self.test_params)

            self.logger.info(f"TCPIP response: {repr(response)}")
            measured_value = str(response) if response is not None else ""

            is_valid, error_msg = self.validate_result(measured_value)
            return self.create_result(
                result="PASS" if is_valid else "FAIL",
                measured_value=measured_value,
                error_message=error_msg if not is_valid else None
            )

        except Exception as e:
            self.logger.error(f"TCPIP measurement error: {e}", exc_info=True)
            return self.create_result(result="ERROR", error_message=str(e))
```

**Step 4: Run tests**

```bash
cd backend && uv run pytest tests/test_measurements/test_command_measurements.py::TestTCPIPMeasurement -v
```

Expected: 2 tests PASS

**Step 5: Commit**

```bash
git add backend/app/measurements/implementations.py backend/tests/test_measurements/test_command_measurements.py
git commit -m "feat: add TCPIPMeasurement delegating to TCPIPCommandDriver"
```

---

### Task 4: Comment out old `CommandTestMeasurement` and update registry

**Files:**
- Modify: `backend/app/measurements/implementations.py` (lines ~282–355 and registry ~line 1786–1789)

**Step 1: No new tests needed** — existing tests cover the new classes. Run full measurement test suite first to confirm baseline:

```bash
cd backend && uv run pytest tests/test_measurements/ -v
```

**Step 2: Comment out `CommandTestMeasurement` body**

In `implementations.py`, locate the class definition (~line 282). Comment out the entire class body and add a deprecation note. Keep the class shell so the registry reference doesn't break immediately — then update the registry:

```python
# ============================================================================
# Command Test Measurement
# ============================================================================
# 已棄用: CommandTestMeasurement 直接用 subprocess 執行 lowsheen_lib script
# 已由 ComPortMeasurement / ConSoleMeasurement / TCPIPMeasurement 取代
# 保留此 class 作為歷史參考，不再使用
# class CommandTestMeasurement(BaseMeasurement):
#     """Executes external commands/scripts"""
#
#     async def execute(self) -> MeasurementResult:
#         try:
#             # Get parameters with fallback options
#             command = get_param(self.test_params, "command") or self.test_plan_item.get("command", "")
#             timeout = get_param(self.test_params, "timeout", default=5000)
#             wait_msec = get_param(self.test_params, "wait_msec", "WaitmSec") or self.test_plan_item.get("wait_msec", 0)
#
#             if not command:
#                 return self.create_result(
#                     result="ERROR",
#                     error_message="Missing command parameter"
#                 )
#
#             self.logger.info(f"Executing command: {command}")
#
#             # Wait if specified
#             if wait_msec and isinstance(wait_msec, (int, float)):
#                 await asyncio.sleep(wait_msec / 1000.0)
#
#             # Execute command
#             timeout_seconds = timeout / 1000.0
#             process = await asyncio.create_subprocess_shell(
#                 command,
#                 stdout=asyncio.subprocess.PIPE,
#                 stderr=asyncio.subprocess.PIPE,
#                 cwd="/app"
#             )
#
#             try:
#                 stdout, stderr = await asyncio.wait_for(
#                     process.communicate(),
#                     timeout=timeout_seconds
#                 )
#             except asyncio.TimeoutError:
#                 process.kill()
#                 await process.wait()
#                 return self.create_result(
#                     result="ERROR",
#                     error_message=f"Command timeout after {timeout}ms"
#                 )
#
#             output = stdout.decode().strip()
#             error_output = stderr.decode().strip()
#
#             if process.returncode != 0:
#                 error_msg = error_output or f"Command failed with exit code {process.returncode}"
#                 self.logger.error(f"Command failed: {error_msg}")
#                 return self.create_result(result="ERROR", error_message=error_msg)
#
#             # Convert output based on value_type
#             measured_value = output
#             if self.value_type is not StringType:
#                 try:
#                     measured_value = Decimal(output) if output else None
#                 except (ValueError, TypeError):
#                     measured_value = None
#
#             # Ensure measured_value is compatible with create_result
#             if isinstance(measured_value, str):
#                 measured_value = None
#
#             is_valid, error_msg = self.validate_result(measured_value)
#             return self.create_result(
#                 result="PASS" if is_valid else "FAIL",
#                 measured_value=measured_value,
#                 error_message=error_msg if not is_valid else None
#             )
#
#         except Exception as e:
#             self.logger.error(f"Command test error: {e}", exc_info=True)
#             return self.create_result(result="ERROR", error_message=str(e))
```

**Step 3: Update registry entries**

Find the registry block (~line 1754). Update these 5 entries:

```python
# 原 CommandTestMeasurement 已棄用，改用下列三個專屬 class
# "COMMAND_TEST": CommandTestMeasurement,  # 已棄用
"COMMAND_TEST": ConSoleMeasurement,  # fallback: treat generic COMMAND_TEST as console execution
# ...
# "command": CommandTestMeasurement,  # 已棄用
"command": ConSoleMeasurement,
# "console": CommandTestMeasurement,  # 已棄用
"console": ConSoleMeasurement,
# "comport": CommandTestMeasurement,  # 已棄用
"comport": ComPortMeasurement,
# "tcpip": CommandTestMeasurement,  # 已棄用
"tcpip": TCPIPMeasurement,
```

**Step 4: Run all measurement tests**

```bash
cd backend && uv run pytest tests/test_measurements/ tests/test_services/test_comport_command.py tests/test_services/test_console_command.py tests/test_services/test_tcpip_command.py -v
```

Expected: All tests PASS

**Step 5: Commit**

```bash
git add backend/app/measurements/implementations.py
git commit -m "refactor: comment out CommandTestMeasurement, wire comport/console/tcpip to dedicated classes"
```

---

### Task 5: Final verification

**Step 1: Run the full backend test suite**

```bash
cd backend && uv run pytest --tb=short -q
```

Expected: All existing tests pass, no new failures

**Step 2: Verify registry is correct**

```bash
cd backend && uv run python -c "
from app.measurements.implementations import MEASUREMENT_REGISTRY
for key in ['comport', 'console', 'tcpip', 'COMMAND_TEST', 'command']:
    cls = MEASUREMENT_REGISTRY.get(key)
    print(f'{key:20s} -> {cls.__name__ if cls else None}')
"
```

Expected output:
```
comport              -> ComPortMeasurement
console              -> ConSoleMeasurement
tcpip                -> TCPIPMeasurement
COMMAND_TEST         -> ConSoleMeasurement
command              -> ConSoleMeasurement
```

**Step 3: Commit if any clean-up needed, otherwise done**
