"""
Measurement Implementations
Concrete measurement classes for various test types
"""
from decimal import Decimal
from typing import Dict, Any, Optional
import asyncio
import random
import os  # 新增: 用於檢查檔案存在性

from app.measurements.base import (
    BaseMeasurement,
    MeasurementResult,
    StringType
)
from app.config import settings

# 修改: 移除 module-level imports，改為在 execute() 中使用 lazy imports，以避免循環 import
# 原有程式碼 (已註釋):
# try:
#     from app.services.instrument_connection import get_connection_pool
#     from app.services.instruments import get_driver_class
#     from app.core.instrument_config import get_instrument_settings
# except ImportError:
#     get_connection_pool = None  # type: ignore
#     get_driver_class = None  # type: ignore
#     get_instrument_settings = None  # type: ignore
#
# 保留 module-level 變數供 unittest.mock.patch 使用 (patchable via app.measurements.implementations.<name>)
get_connection_pool = None  # type: ignore
get_driver_class = None  # type: ignore
get_instrument_settings = None  # type: ignore


# ============================================================================
# Helper Functions
# ============================================================================
def get_param(params: Dict[str, Any], *keys: str, default=None):
    """Get parameter value trying multiple keys"""
    for key in keys:
        if key in params and params[key] not in (None, ""):
            return params[key]
    return default


# ============================================================================
# Dummy Measurement - For Testing
# ============================================================================
class DummyMeasurement(BaseMeasurement):
    """Returns random values for testing purposes"""

    async def execute(self) -> MeasurementResult:
        try:
            await asyncio.sleep(0.1)

            # Generate value based on limits with 80% pass rate
            if self.lower_limit is not None and self.upper_limit is not None:
                if random.random() < 0.8:
                    range_size = float(self.upper_limit - self.lower_limit)
                    measured_value = self.lower_limit + Decimal(random.uniform(0.1, 0.9) * range_size)
                else:
                    if random.random() < 0.5:
                        measured_value = self.lower_limit - Decimal(abs(random.gauss(1, 0.5)))
                    else:
                        measured_value = self.upper_limit + Decimal(abs(random.gauss(1, 0.5)))
            else:
                measured_value = Decimal(random.uniform(0, 100))

            is_valid, error_msg = self.validate_result(measured_value)
            return self.create_result(
                result="PASS" if is_valid else "FAIL",
                measured_value=measured_value,
                error_message=error_msg if not is_valid else None
            )
        except Exception as e:
            self.logger.error(f"Dummy measurement error: {e}")
            return self.create_result(result="ERROR", error_message=str(e))


# ============================================================================
# Other Measurement - Custom Script Execution
# ============================================================================
class OtherMeasurement(BaseMeasurement):
    """
    Executes custom Python scripts (PDTool4 'Other' measurement type).

    Maps switch_mode (case_type) to script files:
    - test123 → scripts/test123.py
    - 123_1 → scripts/123_1.py
    - WAIT_FIX_5sec → scripts/WAIT_FIX_5sec.py
    - etc.

    Supports UseResult parameter for dependency injection.
    """

    async def execute(self) -> MeasurementResult:
        try:
            # 修正方案 A: 優先使用 switch_mode 欄位取得腳本名稱
            # 原有程式碼: 優先使用 case_type
            # 新實作: switch_mode -> case_type -> item_name (向後相容)
            switch_mode = (
                self.test_plan_item.get("switch_mode", "") or
                self.test_plan_item.get("case_type", "") or
                self.test_plan_item.get("item_name", "")  # Fallback to item_name
            ).strip()

            if not switch_mode:
                return self.create_result(
                    result="ERROR",
                    error_message="Missing switch_mode or case_type (script name)"
                )

            # 修正: 優先使用 test_params (前端已經替換 use_result 為實際測量值)
            # 原有程式碼: 優先使用 test_plan_item (資料庫值)，這會導致前端替換的值被忽略
            # 說明:
            #   - test_params.use_result: 前端已將 "123_1" 替換為 "123.0" (實際測量值)
            #   - test_plan_item.use_result: 資料庫原始值 "123_1" (測項名稱)
            #   - 應該優先使用 test_params 的值，因為那是已經處理過的實際測量值

            # 新增: 詳細日誌追蹤 use_result 的來源和值
            self.logger.info(f"[DEBUG] test_plan_item keys: {list(self.test_plan_item.keys())}")
            self.logger.info(f"[DEBUG] test_params keys: {list(self.test_params.keys()) if self.test_params else 'None'}")
            self.logger.info(f"[DEBUG] use_result from test_plan_item (原始值): {self.test_plan_item.get('use_result')}")
            self.logger.info(f"[DEBUG] use_result from test_params (前端替換值): {get_param(self.test_params, 'use_result', 'UseResult')}")

            # 修正: 優先使用 test_params (前端替換後的值)，只有當 test_params 沒有時才使用 test_plan_item
            use_result = get_param(self.test_params, "use_result", "UseResult") or self.test_plan_item.get("use_result")
            timeout = get_param(self.test_params, "timeout", "Timeout") or self.test_plan_item.get("timeout", 5000)
            wait_msec = get_param(self.test_params, "wait_msec", "WaitmSec") or self.test_plan_item.get("wait_msec", 0)

            self.logger.info(f"[DEBUG] Final use_result value: {use_result}")
            self.logger.info(f"[DEBUG] timeout: {timeout}, wait_msec: {wait_msec}")

            # 新增: 當 switch_mode 為 "script" 時，從 command 欄位讀取腳本路徑或命令
            # 這是通用腳本執行模式，允許在「命令」欄位中指定完整的腳本路徑或命令
            if switch_mode.lower() == "script":
                # 從 command 欄位讀取
                command = self.test_plan_item.get("command", "").strip()
                if not command:
                    return self.create_result(
                        result="ERROR",
                        error_message="switch_mode='script' requires 'command' field to specify script path or command"
                    )

                self.logger.info(f"Executing command from 'command' field: {command}")

                # Wait if specified
                if wait_msec and isinstance(wait_msec, (int, float)):
                    await asyncio.sleep(wait_msec / 1000.0)

                # Build command arguments
                args = []
                if use_result:
                    # UseResult: 使用之前測試項目的結果作為參數
                    args.append(str(use_result))

                # Execute command (使用 shell 模式執行 command 欄位中的內容)
                timeout_seconds = timeout / 1000.0
                full_command = command
                if args:
                    full_command = f"{command} {' '.join(args)}"

                process = await asyncio.create_subprocess_shell(
                    full_command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # backend/app
                )
            else:
                # 原有邏輯: 從 switch_mode 構建腳本路徑
                # Build script path
                # 原有程式碼: 假設腳本在 src/lowsheen_lib/testUTF/ 目錄
                # 第一次修改: 腳本移到 backend/scripts/ 目錄，使用硬編碼 /app/scripts/ 路徑
                # 第二次修改: 使用環境感知的路徑解析，支援本地和容器環境
                # 路徑解析邏輯:
                #   - 相對路徑 (如 "scripts"): 從 backend 目錄計算
                #   - 絕對路徑 (如 "/app/scripts"): 直接使用
                #   - __file__ 位置: backend/app/measurements/implementations.py
                #   - backend 目錄需向上三層: implementations.py → measurements → app → backend
                script_name = switch_mode.replace(".", "_")  # test123 or 123_1 or WAIT_FIX_5sec

                # 從配置檔取得腳本目錄，支援相對路徑和絕對路徑
                scripts_dir = settings.SCRIPTS_DIR

                # 如果是相對路徑，轉換為絕對路徑（相對於 backend 目錄）
                if not os.path.isabs(scripts_dir):
                    # __file__ = backend/app/measurements/implementations.py
                    # 需要回到 backend 目錄（向上三層：implementations.py → measurements → app → backend）
                    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                    scripts_dir = os.path.join(backend_dir, scripts_dir)

                script_path = os.path.join(scripts_dir, f"{script_name}.py")

                self.logger.info(f"Executing Other script: {script_path}")
                self.logger.info(f"Scripts directory: {scripts_dir}")

                # 新增: 檢查腳本檔案是否存在
                if not os.path.exists(script_path):
                    error_msg = f"Script not found: {script_path} (scripts_dir: {scripts_dir})"
                    self.logger.error(error_msg)
                    return self.create_result(
                        result="ERROR",
                        error_message=error_msg
                    )

                # Wait if specified
                if wait_msec and isinstance(wait_msec, (int, float)):
                    await asyncio.sleep(wait_msec / 1000.0)

                # Build command arguments
                args = []
                if use_result:
                    # UseResult: 使用之前測試項目的結果作為參數
                    args.append(str(use_result))

                # Execute script
                timeout_seconds = timeout / 1000.0
                cmd = ["python3", script_path] + args

                # 新增: 日誌顯示實際執行的命令
                self.logger.info(f"[DEBUG] Executing command: {' '.join(cmd)}")
                self.logger.info(f"[DEBUG] use_result parameter: {use_result} (type: {type(use_result).__name__})")

                # 使用腳本目錄作為工作目錄
                cwd = scripts_dir

                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=cwd
                )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout_seconds
                )
            except asyncio.TimeoutError:
                process.kill()
                return self.create_result(
                    result="ERROR",
                    error_message=f"Script timeout after {timeout_seconds}s"
                )

            # Check return code
            if process.returncode != 0:
                error_msg = stderr.decode().strip() if stderr else f"Script failed with code {process.returncode}"
                return self.create_result(
                    result="ERROR",
                    error_message=error_msg
                )

            # Parse output
            output = stdout.decode().strip()
            self.logger.info(f"Script output: {output}")

            # Try to convert to number, fallback to string
            # 修正: 對於整數類型的輸出，保持整數格式而非浮點數
            # 例如: "123" → 123 (整數) 而非 123.0 (浮點數)
            try:
                # 先嘗試解析為整數
                if output.isdigit() or (output.startswith('-') and output[1:].isdigit()):
                    measured_value = int(output)
                    self.logger.info(f"[DEBUG] Parsed as integer: {measured_value}")
                else:
                    # 嘗試解析為浮點數
                    measured_value = float(output)
                    self.logger.info(f"[DEBUG] Parsed as float: {measured_value}")
            except ValueError:
                # String result (e.g., "Hello World!")
                # 修正: 使用 StringType.cast() 而非 StringType()
                measured_value = StringType.cast(output)
                self.logger.info(f"[DEBUG] Parsed as string: {measured_value}")

            # Validate result
            is_valid, error_msg = self.validate_result(measured_value)

            return self.create_result(
                result="PASS" if is_valid else "FAIL",
                measured_value=measured_value,
                error_message=error_msg if not is_valid else None
            )

        except FileNotFoundError:
            return self.create_result(
                result="ERROR",
                error_message=f"Script not found: {script_path}"
            )
        except Exception as e:
            self.logger.error(f"Other measurement error: {e}", exc_info=True)
            return self.create_result(result="ERROR", error_message=str(e))


# ============================================================================
# Command Test Measurement
# ============================================================================
class CommandTestMeasurement(BaseMeasurement):
    """Executes external commands/scripts"""

    async def execute(self) -> MeasurementResult:
        try:
            # Get parameters with fallback options
            command = get_param(self.test_params, "command") or self.test_plan_item.get("command", "")
            timeout = get_param(self.test_params, "timeout", default=5000)
            wait_msec = get_param(self.test_params, "wait_msec", "WaitmSec") or self.test_plan_item.get("wait_msec", 0)

            if not command:
                return self.create_result(
                    result="ERROR",
                    error_message="Missing command parameter"
                )

            self.logger.info(f"Executing command: {command}")

            # Wait if specified
            if wait_msec and isinstance(wait_msec, (int, float)):
                await asyncio.sleep(wait_msec / 1000.0)

            # Execute command
            timeout_seconds = timeout / 1000.0
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd="/app"
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout_seconds
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return self.create_result(
                    result="ERROR",
                    error_message=f"Command timeout after {timeout}ms"
                )

            output = stdout.decode().strip()
            error_output = stderr.decode().strip()

            if process.returncode != 0:
                error_msg = error_output or f"Command failed with exit code {process.returncode}"
                self.logger.error(f"Command failed: {error_msg}")
                return self.create_result(result="ERROR", error_message=error_msg)

            # Convert output based on value_type
            measured_value = output
            if self.value_type is not StringType:
                try:
                    measured_value = Decimal(output) if output else None
                except (ValueError, TypeError):
                    measured_value = None

            # Ensure measured_value is compatible with create_result
            if isinstance(measured_value, str):
                measured_value = None

            is_valid, error_msg = self.validate_result(measured_value)
            return self.create_result(
                result="PASS" if is_valid else "FAIL",
                measured_value=measured_value,
                error_message=error_msg if not is_valid else None
            )

        except Exception as e:
            self.logger.error(f"Command test error: {e}", exc_info=True)
            return self.create_result(result="ERROR", error_message=str(e))



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
            # 修改: 讀取 module-level 變數 (可被 unittest.mock.patch 替換)；若仍為 None 則 lazy import
            # 原有程式碼 (已簡化): 移除不必要的 _self_module 間接引用
            import app.measurements.implementations as _m
            _gcp = _m.get_connection_pool
            _gdc = _m.get_driver_class
            _gis = _m.get_instrument_settings
            if _gcp is None:
                from app.services.instrument_connection import get_connection_pool as _gcp
                from app.services.instruments import get_driver_class as _gdc
                from app.core.instrument_config import get_instrument_settings as _gis

            instrument_name = get_param(self.test_params, "Instrument", "instrument")
            if not instrument_name:
                return self.create_result(
                    result="ERROR",
                    error_message="Missing required parameter: Instrument"
                )

            instrument_settings = _gis()
            config = instrument_settings.get_instrument(instrument_name)
            if config is None:
                return self.create_result(
                    result="ERROR",
                    error_message=f"Instrument '{instrument_name}' not configured"
                )

            driver_class = _gdc(config.type)
            if driver_class is None:
                return self.create_result(
                    result="ERROR",
                    error_message=f"No driver for instrument type '{config.type}'"
                )

            connection_pool = _gcp()
            async with connection_pool.get_connection(instrument_name) as conn:
                driver = driver_class(conn)
                await driver.initialize()
                response = await driver.send_command(self.test_params)

            self.logger.info(f"ComPort response: {repr(response)}")
            response_str = str(response) if response is not None else ""

            # 修改: 依 value_type 決定 measured_value，與 CommandTestMeasurement 一致
            # 原有程式碼 (BUG): measured_value=None (總是 None，丟失實際回應值)
            measured_value = response_str
            if self.value_type is not StringType:
                try:
                    measured_value = Decimal(response_str) if response_str else None
                except (ValueError, TypeError):
                    measured_value = None

            # Ensure measured_value is compatible with create_result (no str)
            if isinstance(measured_value, str):
                measured_value = None

            is_valid, error_msg = self.validate_result(measured_value if measured_value is not None else response_str)
            return self.create_result(
                result="PASS" if is_valid else "FAIL",
                measured_value=measured_value,
                error_message=error_msg if not is_valid else None
            )

        except Exception as e:
            self.logger.error(f"ComPort measurement error: {e}", exc_info=True)
            return self.create_result(result="ERROR", error_message=str(e))

# ============================================================================

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
            # 修改: 讀取 module-level 變數 (可被 unittest.mock.patch 替換)；若仍為 None 則 lazy import
            import app.measurements.implementations as _m
            _gcp = _m.get_connection_pool
            _gdc = _m.get_driver_class
            _gis = _m.get_instrument_settings
            if _gcp is None:
                from app.services.instrument_connection import get_connection_pool as _gcp
                from app.services.instruments import get_driver_class as _gdc
                from app.core.instrument_config import get_instrument_settings as _gis

            instrument_name = get_param(self.test_params, "Instrument", "instrument")
            if not instrument_name:
                return self.create_result(
                    result="ERROR",
                    error_message="Missing required parameter: Instrument"
                )

            instrument_settings = _gis()
            config = instrument_settings.get_instrument(instrument_name)
            if config is None:
                return self.create_result(
                    result="ERROR",
                    error_message=f"Instrument '{instrument_name}' not configured"
                )

            driver_class = _gdc(config.type)
            if driver_class is None:
                return self.create_result(
                    result="ERROR",
                    error_message=f"No driver for instrument type '{config.type}'"
                )

            connection_pool = _gcp()
            async with connection_pool.get_connection(instrument_name) as conn:
                driver = driver_class(conn)
                await driver.initialize()
                response = await driver.send_command(self.test_params)

            self.logger.info(f"Console response: {repr(response)}")
            response_str = str(response) if response is not None else ""

            # 依 value_type 決定 measured_value，與 ComPortMeasurement 一致
            measured_value = response_str
            if self.value_type is not StringType:
                try:
                    measured_value = Decimal(response_str) if response_str else None
                except (ValueError, TypeError):
                    measured_value = None

            # Ensure measured_value is compatible with create_result (no str)
            if isinstance(measured_value, str):
                measured_value = None

            is_valid, error_msg = self.validate_result(measured_value if measured_value is not None else response_str)
            return self.create_result(
                result="PASS" if is_valid else "FAIL",
                measured_value=measured_value,
                error_message=error_msg if not is_valid else None
            )

        except Exception as e:
            self.logger.error(f"Console measurement error: {e}", exc_info=True)
            return self.create_result(result="ERROR", error_message=str(e))


# ============================================================================
# TCPIP Measurement — replaces lowsheen_lib/TCPIPCommand.py
# ============================================================================
class TCPIPMeasurement(BaseMeasurement):
    """
    Sends a TCP/IP socket command via TCPIPCommandDriver and returns hex response.

    Required test_params:
        - Instrument (str): key in instrument_settings (type must be 'tcpip')
        - Command (str): command in hex format e.g. "31;01;f0;00;00" or plain text

    Optional test_params:
        - Timeout (float): socket read timeout in seconds (default: 5.0)
        - UseCRC32 (bool): append CRC32 checksum to command (default: True)
        - BufferSize (int): max response bytes (default: 1024)
    """

    async def execute(self) -> MeasurementResult:
        try:
            # 修改: 讀取 module-level 變數 (可被 unittest.mock.patch 替換)；若仍為 None 則 lazy import
            import app.measurements.implementations as _m
            _gcp = _m.get_connection_pool
            _gdc = _m.get_driver_class
            _gis = _m.get_instrument_settings
            if _gcp is None:
                from app.services.instrument_connection import get_connection_pool as _gcp
                from app.services.instruments import get_driver_class as _gdc
                from app.core.instrument_config import get_instrument_settings as _gis

            instrument_name = get_param(self.test_params, "Instrument", "instrument")
            if not instrument_name:
                return self.create_result(
                    result="ERROR",
                    error_message="Missing required parameter: Instrument"
                )

            instrument_settings = _gis()
            config = instrument_settings.get_instrument(instrument_name)
            if config is None:
                return self.create_result(
                    result="ERROR",
                    error_message=f"Instrument '{instrument_name}' not configured"
                )

            driver_class = _gdc(config.type)
            if driver_class is None:
                return self.create_result(
                    result="ERROR",
                    error_message=f"No driver for instrument type '{config.type}'"
                )

            connection_pool = _gcp()
            async with connection_pool.get_connection(instrument_name) as conn:
                driver = driver_class(conn)
                await driver.initialize()
                response = await driver.send_command(self.test_params)

            self.logger.info(f"TCPIP response: {repr(response)}")
            response_str = str(response) if response is not None else ""

            # 依 value_type 決定 measured_value，與 ConSoleMeasurement 一致
            measured_value = response_str
            if self.value_type is not StringType:
                try:
                    measured_value = Decimal(response_str) if response_str else None
                except (ValueError, TypeError):
                    measured_value = None

            # Ensure measured_value is compatible with create_result (no str)
            if isinstance(measured_value, str):
                measured_value = None

            is_valid, error_msg = self.validate_result(measured_value if measured_value is not None else response_str)
            return self.create_result(
                result="PASS" if is_valid else "FAIL",
                measured_value=measured_value,
                error_message=error_msg if not is_valid else None
            )

        except Exception as e:
            self.logger.error(f"TCPIP measurement error: {e}", exc_info=True)
            return self.create_result(result="ERROR", error_message=str(e))

# Power Measurements
# ============================================================================
class PowerReadMeasurement(BaseMeasurement):
    """
    Reads voltage/current from power supply/measurement instruments.

    Parameters:
        Instrument: Instrument name from config (e.g., 'DAQ973A_1', 'MODEL2303_1')
        Channel: Channel number (e.g., '101', '1', '121' for DAQ973A current)
        Item: What to measure ('voltage', 'volt', 'current', 'curr')

    Supported Instruments:
        - DAQ973A: Voltage (channels 101-120), Current (channels 121-122)
        - DAQ6510: Voltage and Current measurements
        - MODEL2303: Voltage and Current readback
        - MODEL2306: Voltage and Current readback per channel
        - IT6723C: Voltage and Current readback
        - KEITHLEY2015: DMM measurements
        - APS7050: Power supply readback
        - PSW3072: Power supply readback
        - A2260B: Power supply readback

    Integration: Refactored from PDTool4 mock data to real instrument drivers
    """

    async def execute(self) -> MeasurementResult:
        try:
            # Import required modules lazily to avoid circular imports
            from app.services.instrument_connection import get_connection_pool
            from app.services.instruments import get_driver_class
            from app.core.instrument_config import get_instrument_settings

            # Get and validate parameters
            instrument_name = get_param(self.test_params, "Instrument", "instrument")
            channel = get_param(self.test_params, "Channel", "channel")
            item = get_param(self.test_params, "Item", "item")

            if not all([instrument_name, item]):
                return self.create_result(
                    result="ERROR",
                    error_message="Missing required parameters: Instrument, Item (Channel optional for some instruments)"
                )

            # Normalize item name (voltage/volt/current/curr)
            item_lower = str(item).lower()
            if item_lower in ('voltage', 'volt', 'v'):
                measure_type = 'voltage'
            elif item_lower in ('current', 'curr', 'i', 'a'):
                measure_type = 'current'
            else:
                return self.create_result(
                    result="ERROR",
                    error_message=f"Invalid Item parameter: {item} (must be 'voltage' or 'current')"
                )

            self.logger.info(f"Reading {measure_type} from {instrument_name} channel {channel}")

            # Get instrument configuration
            instrument_settings = get_instrument_settings()
            config = instrument_settings.get_instrument(instrument_name)
            if config is None:
                return self.create_result(
                    result="ERROR",
                    error_message=f"Instrument {instrument_name} not found in configuration"
                )

            # Get driver class
            driver_class = get_driver_class(config.type)
            if driver_class is None:
                return self.create_result(
                    result="ERROR",
                    error_message=f"No driver found for instrument type: {config.type}"
                )

            # Get connection and create driver
            connection_pool = get_connection_pool()
            async with connection_pool.get_connection(instrument_name) as conn:
                driver = driver_class(conn)

                # Initialize if needed
                if not hasattr(driver, '_initialized'):
                    await driver.initialize()
                    driver._initialized = True

                # Execute measurement based on instrument type and measure_type
                measured_value = await self._measure_with_driver(
                    driver, config.type, measure_type, channel
                )

                # Validate result
                is_valid, error_msg = self.validate_result(measured_value)
                return self.create_result(
                    result="PASS" if is_valid else "FAIL",
                    measured_value=measured_value,
                    error_message=error_msg if not is_valid else None
                )

        except Exception as e:
            self.logger.error(f"Power read error: {e}", exc_info=True)
            return self.create_result(result="ERROR", error_message=str(e))

    async def _measure_with_driver(
        self,
        driver,
        instrument_type: str,
        measure_type: str,
        channel: Optional[str]
    ) -> Decimal:
        """
        Execute measurement based on instrument type.

        Args:
            driver: Instrument driver instance
            instrument_type: Type of instrument
            measure_type: 'voltage' or 'current'
            channel: Channel number (if applicable)

        Returns:
            Measured value as Decimal
        """
        # DAQ973A / DAQ6510 - Multi-channel DMM
        if instrument_type in ('DAQ973A', 'DAQ6510'):
            if not channel:
                raise ValueError(f"{instrument_type} requires Channel parameter")

            channels = [str(channel)]  # Driver expects list of channels

            if measure_type == 'voltage':
                return await driver.measure_voltage(channels)
            else:  # current
                # Validate current channels for DAQ973A
                if instrument_type == 'DAQ973A' and channel not in ['121', '122']:
                    raise ValueError(
                        f"DAQ973A current measurement requires channel 121 or 122, got {channel}"
                    )
                return await driver.measure_current(channels)

        # MODEL2303 - Dual Channel Power Supply
        elif instrument_type == 'MODEL2303':
            if measure_type == 'voltage':
                return await driver.measure_voltage()
            else:  # current
                return await driver.measure_current()

        # MODEL2306 - Dual Channel Power Supply (channel-specific)
        elif instrument_type == 'MODEL2306':
            channel_str = str(channel) if channel else '1'
            if channel_str not in ['1', '2']:
                raise ValueError(f"MODEL2306 requires channel '1' or '2', got {channel_str}")

            if measure_type == 'voltage':
                return await driver.measure_voltage(channel_str)
            else:  # current
                return await driver.measure_current(channel_str)

        # IT6723C - Single Channel High Power Supply
        elif instrument_type == 'IT6723C':
            if measure_type == 'voltage':
                return await driver.measure_voltage()
            else:  # current
                return await driver.measure_current()

        # KEITHLEY2015 - DMM
        elif instrument_type == 'KEITHLEY2015':
            if measure_type == 'voltage':
                return await driver.measure_voltage()
            else:  # current
                return await driver.measure_current()

        # APS7050 / PSW3072 / A2260B - Power Supplies with generic interface
        elif instrument_type in ('APS7050', 'PSW3072', 'A2260B', '2260B'):
            if measure_type == 'voltage':
                return await driver.measure_voltage()
            else:  # current
                return await driver.measure_current()

        # A34970A - Similar to DAQ973A
        elif instrument_type == '34970A':
            if not channel:
                raise ValueError(f"{instrument_type} requires Channel parameter")

            channels = [str(channel)]

            if measure_type == 'voltage':
                return await driver.measure_voltage(channels)
            else:  # current
                return await driver.measure_current(channels)

        else:
            raise ValueError(
                f"Instrument type {instrument_type} not supported for power read measurement. "
                f"Supported: DAQ973A, DAQ6510, MODEL2303, MODEL2306, IT6723C, KEITHLEY2015, "
                f"APS7050, PSW3072, A2260B, 34970A"
            )


class PowerSetMeasurement(BaseMeasurement):
    """
    Sets voltage/current on power supply instruments.

    Parameters:
        Instrument: Instrument name from config (e.g., 'MODEL2303_1', 'MODEL2306_1', 'IT6723C_1')
        SetVolt/Voltage: Target voltage in volts
        SetCurr/Current: Target current limit in amperes
        Channel: Channel number (for multi-channel supplies like MODEL2306)

    Supported Instruments:
        - MODEL2303: Dual-channel power supply (0-20V, 0-3A)
        - MODEL2306: Dual-channel battery simulator (channel 1 or 2)
        - IT6723C: High-power programmable supply (up to 150V, 10A)
        - APS7050: General purpose power supply
        - PSW3072: Programmable power supply
        - A2260B: High-power supply (0-60V, 0-10A)

    Special Behavior:
        - MODEL2306: If both SetVolt=0 AND SetCurr=0, turns OFF the output
        - Otherwise: Sets voltage, current, and enables output
        - Validates set values by reading back (with tolerance check)

    Integration: Refactored from PDTool4 mock implementation to real drivers
    """

    async def execute(self) -> MeasurementResult:
        try:
            # Import required modules lazily to avoid circular imports
            from app.services.instrument_connection import get_connection_pool
            from app.services.instruments import get_driver_class
            from app.core.instrument_config import get_instrument_settings

            # Get and validate parameters
            instrument_name = get_param(self.test_params, "Instrument", "instrument")
            voltage = get_param(self.test_params, "SetVolt", "Voltage", "voltage", "set_volt")
            current = get_param(self.test_params, "SetCurr", "Current", "current", "set_curr")
            channel = get_param(self.test_params, "Channel", "channel")

            if not instrument_name:
                return self.create_result(
                    result="ERROR",
                    error_message="Missing required parameter: Instrument"
                )

            if voltage is None or current is None:
                return self.create_result(
                    result="ERROR",
                    error_message="Missing required parameters: SetVolt/Voltage and SetCurr/Current"
                )

            # Convert to float
            try:
                voltage_val = float(voltage)
                current_val = float(current)
            except (ValueError, TypeError) as e:
                return self.create_result(
                    result="ERROR",
                    error_message=f"Invalid voltage or current value: {e}"
                )

            self.logger.info(
                f"Setting power on {instrument_name}: V={voltage_val}V, I={current_val}A"
                + (f", Channel={channel}" if channel else "")
            )

            # Get instrument configuration
            instrument_settings = get_instrument_settings()
            config = instrument_settings.get_instrument(instrument_name)
            if config is None:
                return self.create_result(
                    result="ERROR",
                    error_message=f"Instrument {instrument_name} not found in configuration"
                )

            # Get driver class
            driver_class = get_driver_class(config.type)
            if driver_class is None:
                return self.create_result(
                    result="ERROR",
                    error_message=f"No driver found for instrument type: {config.type}"
                )

            # Get connection and create driver
            connection_pool = get_connection_pool()
            async with connection_pool.get_connection(instrument_name) as conn:
                driver = driver_class(conn)

                # Initialize if needed
                if not hasattr(driver, '_initialized'):
                    await driver.initialize()
                    driver._initialized = True

                # Execute power set based on instrument type
                result_msg = await self._set_power_with_driver(
                    driver, config.type, voltage_val, current_val, channel
                )

                # Check result message ('1' = success in PDTool4 convention)
                if result_msg == '1':
                    return self.create_result(
                        result="PASS",
                        measured_value=Decimal("1.0")
                    )
                else:
                    # Driver returned error message
                    return self.create_result(
                        result="FAIL",
                        measured_value=Decimal("0.0"),
                        error_message=result_msg
                    )

        except Exception as e:
            self.logger.error(f"Power set error: {e}", exc_info=True)
            return self.create_result(result="ERROR", error_message=str(e))

    async def _set_power_with_driver(
        self,
        driver,
        instrument_type: str,
        voltage: float,
        current: float,
        channel: Optional[str]
    ) -> str:
        """
        Execute power set command based on instrument type.

        Args:
            driver: Instrument driver instance
            instrument_type: Type of instrument
            voltage: Target voltage
            current: Target current limit
            channel: Channel number (if applicable)

        Returns:
            '1' on success, error message string on failure (PDTool4 convention)
        """
        # MODEL2303 - Dual Channel Power Supply
        if instrument_type == 'MODEL2303':
            # Use execute_command for PDTool4-compatible interface
            result = await driver.execute_command({
                'SetVolt': voltage,
                'SetCurr': current
            })
            return result

        # MODEL2306 - Dual Channel Battery Simulator
        elif instrument_type == 'MODEL2306':
            channel_str = str(channel) if channel else '1'
            if channel_str not in ['1', '2']:
                return f"MODEL2306 requires channel '1' or '2', got {channel_str}"

            # Use execute_command for PDTool4-compatible interface
            result = await driver.execute_command({
                'Channel': channel_str,
                'SetVolt': voltage,
                'SetCurr': current
            })
            return result

        # IT6723C - High Power Supply
        elif instrument_type == 'IT6723C':
            # Use execute_command for PDTool4-compatible interface
            result = await driver.execute_command({
                'SetVolt': voltage,
                'SetCurr': current
            })
            return result

        # APS7050 / PSW3072 / A2260B - Generic Power Supplies
        elif instrument_type in ('APS7050', 'PSW3072', 'A2260B', '2260B'):
            # These drivers should have set_voltage, set_current, set_output methods
            try:
                await driver.set_voltage(voltage)
                await driver.set_current(current)
                await driver.set_output(True)

                # Verify by reading back
                measured_volt = await driver.measure_voltage()
                volt_tolerance = abs(voltage * 0.05)  # 5% tolerance
                if abs(float(measured_volt) - voltage) > volt_tolerance:
                    return f"{instrument_type} voltage set failed: set={voltage}V, measured={measured_volt}V"

                self.logger.info(f"{instrument_type} power set successful: V={measured_volt}V")
                return '1'

            except Exception as e:
                return f"{instrument_type} power set failed: {str(e)}"

        else:
            return (
                f"Instrument type {instrument_type} not supported for power set measurement. "
                f"Supported: MODEL2303, MODEL2306, IT6723C, APS7050, PSW3072, A2260B"
            )


# ============================================================================
# SFC Measurement
# ============================================================================
class SFCMeasurement(BaseMeasurement):
    """Integrates with manufacturing execution systems"""

    async def execute(self) -> MeasurementResult:
        try:
            sfc_mode = get_param(self.test_params, "Mode", default="webStep1_2")
            self.logger.info(f"Executing SFC test with mode: {sfc_mode}")

            await asyncio.sleep(0.5)

            return self.create_result(result="PASS", measured_value=Decimal("1.0"))

        except Exception as e:
            self.logger.error(f"SFC test error: {e}")
            return self.create_result(result="ERROR", error_message=str(e))


# ============================================================================
# Get Serial Number Measurement
# ============================================================================
class GetSNMeasurement(BaseMeasurement):
    """Acquires device serial numbers"""

    async def execute(self) -> MeasurementResult:
        try:
            sn_type = get_param(self.test_params, "Type", default="SN")
            self.logger.info(f"Acquiring {sn_type} from device")

            await asyncio.sleep(0.1)

            # Return placeholder or provided serial number
            sn_value = get_param(self.test_params, "SerialNumber", default=f"SN{random.randint(100000, 999999)}")

            return self.create_result(result="PASS", measured_value=Decimal("1.0"))

        except Exception as e:
            self.logger.error(f"Serial number acquisition error: {e}")
            return self.create_result(result="ERROR", error_message=str(e))


# ============================================================================
# Operator Judgment Measurement
# ============================================================================
class OPJudgeMeasurement(BaseMeasurement):
    """Awaits operator confirmation for subjective tests"""

    async def execute(self) -> MeasurementResult:
        try:
            judgment_type = get_param(self.test_params, "Type", default="YorN")
            self.logger.info(f"Operator judgment: {judgment_type}")

            expected = get_param(self.test_params, "Expected", default="PASS")
            actual = get_param(self.test_params, "Result", default=expected)

            measured_value = Decimal("1.0") if actual == "PASS" else Decimal("0.0")
            # Ensure actual is a valid result string
            if actual not in ("PASS", "FAIL", "SKIP", "ERROR"):
                actual = "PASS"
            return self.create_result(result=str(actual), measured_value=measured_value)

        except Exception as e:
            self.logger.error(f"Operator judgment error: {e}")
            return self.create_result(result="ERROR", error_message=str(e))


# ============================================================================
# Wait Measurement
# ============================================================================
class WaitMeasurement(BaseMeasurement):
    """Waits for specified time duration"""

    async def execute(self) -> MeasurementResult:
        try:
            # Get wait time from multiple possible sources
            wait_msec = (
                get_param(self.test_params, "wait_msec", "WaitmSec") or
                self.test_plan_item.get("wait_msec", 0)
            )

            # 修正: 將字串型別的數值轉換為數字
            # 原有程式碼: 直接檢查型別，如果是字串 "1000" 會失敗
            # 修改: 先嘗試轉換為數字，再進行驗證
            try:
                if isinstance(wait_msec, str):
                    wait_msec = int(wait_msec)
                elif not isinstance(wait_msec, (int, float)):
                    wait_msec = 0
            except (ValueError, TypeError):
                wait_msec = 0

            if not isinstance(wait_msec, (int, float)) or wait_msec <= 0:
                return self.create_result(
                    result="ERROR",
                    error_message=f"wait mode requires wait_msec > 0, got: {wait_msec} (type: {type(wait_msec).__name__})"
                )

            wait_seconds = wait_msec / 1000
            self.logger.info(f"Waiting {wait_msec}ms ({wait_seconds}s)")

            await asyncio.sleep(wait_seconds)

            return self.create_result(result="PASS", measured_value=Decimal("1.0"))

        except Exception as e:
            self.logger.error(f"Wait measurement error: {e}")
            return self.create_result(result="ERROR", error_message=str(e))


# ============================================================================
# Relay Control Measurement
# ============================================================================
class RelayMeasurement(BaseMeasurement):
    """
    Controls relay switching for DUT testing.
    Maps to PDTool4's MeasureSwitchON/OFF functionality.
    """

    async def execute(self) -> MeasurementResult:
        try:
            from app.services.dut_comms import get_relay_controller, RelayState

            # Get relay parameters
            relay_state = get_param(self.test_params, "relay_state", "case", "switch")
            channel = get_param(self.test_params, "channel", default=1)
            device_path = get_param(self.test_params, "device_path", default="/dev/ttyUSB0")

            # Normalize state parameter
            if isinstance(relay_state, str):
                relay_state = relay_state.upper()

            # Map state to RelayState enum
            if relay_state in ["ON", "OPEN", "0", "SWITCH_OPEN"]:
                target_state = RelayState.SWITCH_OPEN
            elif relay_state in ["OFF", "CLOSED", "1", "SWITCH_CLOSED"]:
                target_state = RelayState.SWITCH_CLOSED
            else:
                return self.create_result(
                    result="ERROR",
                    error_message=f"Invalid relay_state: {relay_state}. Expected ON/OFF or OPEN/CLOSED"
                )

            # Get relay controller
            relay_controller = get_relay_controller(device_path=device_path)

            # Set relay state
            state_name = "ON" if target_state == RelayState.SWITCH_OPEN else "OFF"
            self.logger.info(f"Setting relay channel {channel} to {state_name}")

            success = await relay_controller.set_relay_state(target_state, channel)

            if not success:
                return self.create_result(
                    result="ERROR",
                    error_message=f"Failed to set relay to {state_name}"
                )

            return self.create_result(
                result="PASS",
                measured_value=Decimal(str(target_state))
            )

        except Exception as e:
            self.logger.error(f"Relay measurement error: {e}", exc_info=True)
            return self.create_result(result="ERROR", error_message=str(e))


# ============================================================================
# Chassis Rotation Measurement
# ============================================================================
class ChassisRotationMeasurement(BaseMeasurement):
    """
    Controls chassis fixture rotation for DUT positioning.
    Maps to PDTool4's MyThread_CW/CCW functionality.
    """

    async def execute(self) -> MeasurementResult:
        try:
            from app.services.dut_comms import get_chassis_controller, RotationDirection

            # Get rotation parameters
            direction = get_param(self.test_params, "direction", "case")
            duration_ms = get_param(self.test_params, "duration_ms", "duration")
            device_path = get_param(self.test_params, "device_path", default="/dev/ttyACM0")

            # Normalize direction parameter
            if isinstance(direction, str):
                direction = direction.upper()

            # Map direction to RotationDirection enum
            if direction in ["CW", "CLOCKWISE", "6"]:
                target_direction = RotationDirection.CLOCKWISE
            elif direction in ["CCW", "COUNTERCLOCKWISE", "9"]:
                target_direction = RotationDirection.COUNTERCLOCKWISE
            else:
                return self.create_result(
                    result="ERROR",
                    error_message=f"Invalid direction: {direction}. Expected CW/CCW or CLOCKWISE/COUNTERCLOCKWISE"
                )

            # Convert duration to int if provided
            if duration_ms and isinstance(duration_ms, str):
                try:
                    duration_ms = int(duration_ms)
                except ValueError:
                    duration_ms = None

            # Get chassis controller
            chassis_controller = get_chassis_controller(
                device_path=device_path,
                config=self.config
            )

            # Execute rotation
            direction_name = "CLOCKWISE" if target_direction == RotationDirection.CLOCKWISE else "COUNTERCLOCKWISE"
            self.logger.info(f"Rotating chassis {direction_name}")

            success = await chassis_controller.rotate(target_direction, duration_ms)

            if not success:
                return self.create_result(
                    result="ERROR",
                    error_message=f"Failed to rotate chassis {direction_name}"
                )

            return self.create_result(
                result="PASS",
                measured_value=Decimal(str(target_direction))
            )

        except Exception as e:
            self.logger.error(f"Chassis rotation measurement error: {e}", exc_info=True)
            return self.create_result(result="ERROR", error_message=str(e))


# ============================================================================
# RF_Tool (MT8872A) Measurements
# ============================================================================
class RF_Tool_LTE_TX_Measurement(BaseMeasurement):
    """
    LTE TX measurement using RF_Tool (MT8872A).
    Measures LTE transmit power, channel power, and spectral characteristics.

    Parameters:
        instrument: Instrument name in config (default: 'RF_Tool_1')
        band: LTE band (e.g., 'B1', 'B3', 'B7', 'B38', 'B41')
        channel: Channel number
        bandwidth: Channel bandwidth in MHz (default: 10.0)

    Integration: Uses MT8872ADriver from backend/app/services/instruments/mt8872a.py
    """

    async def execute(self) -> MeasurementResult:
        try:
            # Import required modules lazily to avoid circular imports
            from app.services.instrument_connection import get_connection_pool
            from app.services.instruments import get_driver_class
            from app.core.instrument_config import get_instrument_settings

            # Get and validate parameters
            instrument_name = get_param(self.test_params, 'instrument', default='RF_Tool_1')
            band = get_param(self.test_params, 'band')
            channel = get_param(self.test_params, 'channel')
            bandwidth = get_param(self.test_params, 'bandwidth', default=10.0)

            # Validate required parameters
            if band is None:
                return self.create_result(
                    result="ERROR",
                    error_message="Missing required parameter: band"
                )
            if channel is None:
                return self.create_result(
                    result="ERROR",
                    error_message="Missing required parameter: channel"
                )

            try:
                channel = int(channel)
                bandwidth = float(bandwidth)
            except (ValueError, TypeError) as e:
                return self.create_result(
                    result="ERROR",
                    error_message=f"Invalid parameter type: {e}"
                )

            self.logger.info(f"RF_Tool LTE TX measurement: band={band}, channel={channel}, bw={bandwidth}MHz")

            # Get instrument configuration
            instrument_settings = get_instrument_settings()
            config = instrument_settings.get_instrument(instrument_name)
            if config is None:
                return self.create_result(
                    result="ERROR",
                    error_message=f"Instrument {instrument_name} not found in configuration"
                )

            # Get driver class
            driver_class = get_driver_class(config.type)
            if driver_class is None:
                return self.create_result(
                    result="ERROR",
                    error_message=f"No driver found for instrument type: {config.type}"
                )

            # Get connection and create driver
            connection_pool = get_connection_pool()
            async with connection_pool.get_connection(instrument_name) as conn:
                driver = driver_class(conn)

                # Initialize if needed
                if not hasattr(driver, '_initialized'):
                    await driver.initialize()
                    driver._initialized = True

                # Execute measurement using real driver
                tx_result = await driver.measure_lte_tx_power(band, channel, bandwidth)

            # Check for measurement errors
            if tx_result.get('status') == 'ERROR':
                error_msg = tx_result.get('error', 'Unknown error')
                return self.create_result(result="ERROR", error_message=error_msg)

            # Extract measured power value
            measured_power = tx_result['tx_power_avg']

            # Validate against limits
            is_valid, error_msg = self.validate_result(measured_power)

            # Generate error message for BOTH_LIMIT if validation failed
            if not is_valid and error_msg is None:
                if self.lower_limit is not None and self.upper_limit is not None:
                    error_msg = f"Value {measured_power} outside range [{self.lower_limit}, {self.upper_limit}]"
                elif self.lower_limit is not None:
                    error_msg = f"Value {measured_power} < lower limit {self.lower_limit}"
                elif self.upper_limit is not None:
                    error_msg = f"Value {measured_power} > upper limit {self.upper_limit}"

            return self.create_result(
                result="PASS" if is_valid else "FAIL",
                measured_value=measured_power,
                error_message=error_msg if not is_valid else None
            )

        except Exception as e:
            self.logger.error(f"RF_Tool LTE TX measurement error: {e}", exc_info=True)
            return self.create_result(result="ERROR", error_message=str(e))


class RF_Tool_LTE_RX_Measurement(BaseMeasurement):
    """
    LTE RX sensitivity measurement using RF_Tool (MT8872A).
    Measures DUT receiver performance at various signal levels.

    Parameters:
        instrument: Instrument name in config (default: 'RF_Tool_1')
        band: LTE band (e.g., 'B1', 'B3', 'B7', 'B38', 'B41')
        channel: Channel number
        test_power: Signal generator power in dBm (default: -90.0)
        min_throughput: Minimum throughput threshold in Mbps (default: 10.0)

    Integration: Uses MT8872ADriver from backend/app/services/instruments/mt8872a.py
    """

    async def execute(self) -> MeasurementResult:
        try:
            # Import required modules lazily to avoid circular imports
            from app.services.instrument_connection import get_connection_pool
            from app.services.instruments import get_driver_class
            from app.core.instrument_config import get_instrument_settings

            # Get and validate parameters
            instrument_name = get_param(self.test_params, 'instrument', default='RF_Tool_1')
            band = get_param(self.test_params, 'band')
            channel = get_param(self.test_params, 'channel')
            test_power = get_param(self.test_params, 'test_power', default=-90.0)
            min_throughput = get_param(self.test_params, 'min_throughput', default=10.0)

            # Validate required parameters
            if band is None:
                return self.create_result(
                    result="ERROR",
                    error_message="Missing required parameter: band"
                )
            if channel is None:
                return self.create_result(
                    result="ERROR",
                    error_message="Missing required parameter: channel"
                )

            try:
                channel = int(channel)
                test_power = float(test_power)
                min_throughput = float(min_throughput)
            except (ValueError, TypeError) as e:
                return self.create_result(
                    result="ERROR",
                    error_message=f"Invalid parameter type: {e}"
                )

            self.logger.info(f"RF_Tool LTE RX measurement: band={band}, channel={channel}, power={test_power}dBm")

            # Get instrument configuration
            instrument_settings = get_instrument_settings()
            config = instrument_settings.get_instrument(instrument_name)
            if config is None:
                return self.create_result(
                    result="ERROR",
                    error_message=f"Instrument {instrument_name} not found in configuration"
                )

            # Get driver class
            driver_class = get_driver_class(config.type)
            if driver_class is None:
                return self.create_result(
                    result="ERROR",
                    error_message=f"No driver found for instrument type: {config.type}"
                )

            # Get connection and create driver
            connection_pool = get_connection_pool()
            async with connection_pool.get_connection(instrument_name) as conn:
                driver = driver_class(conn)

                # Initialize if needed
                if not hasattr(driver, '_initialized'):
                    await driver.initialize()
                    driver._initialized = True

                # Execute measurement using real driver
                rx_result = await driver.measure_lte_rx_sensitivity(band, channel, test_power, min_throughput)

            # Check for measurement errors
            if rx_result.get('status') == 'ERROR':
                error_msg = rx_result.get('error', 'Unknown error')
                return self.create_result(result="ERROR", error_message=error_msg)

            # Extract RSSI value
            rssi = rx_result['rssi']

            # Validate against limits
            is_valid, error_msg = self.validate_result(rssi)

            # Generate error message for BOTH_LIMIT if validation failed
            if not is_valid and error_msg is None:
                if self.lower_limit is not None and self.upper_limit is not None:
                    error_msg = f"Value {rssi} outside range [{self.lower_limit}, {self.upper_limit}]"
                elif self.lower_limit is not None:
                    error_msg = f"Value {rssi} < lower limit {self.lower_limit}"
                elif self.upper_limit is not None:
                    error_msg = f"Value {rssi} > upper limit {self.upper_limit}"

            return self.create_result(
                result="PASS" if is_valid else "FAIL",
                measured_value=rssi,
                error_message=error_msg if not is_valid else None
            )

        except Exception as e:
            self.logger.error(f"RF_Tool LTE RX measurement error: {e}", exc_info=True)
            return self.create_result(result="ERROR", error_message=str(e))


# ============================================================================
# CMW100 Measurements
# ============================================================================
class CMW100_BLE_Measurement(BaseMeasurement):
    """
    Bluetooth LE measurement using CMW100.
    Measures BLE TX power, frequency error, and modulation characteristics.

    Parameters:
        instrument: Instrument name in config (default: 'CMW100_1')
        connector: RF connector number (default: 1)
        frequency: Frequency in MHz (default: 2440.0)
        expected_power: Expected TX power in dBm (default: -5.0)

    Integration: Uses CMW100Driver from backend/app/services/instruments/cmw100.py
    """

    async def execute(self) -> MeasurementResult:
        try:
            # Import required modules lazily to avoid circular imports
            from app.services.instrument_connection import get_connection_pool
            from app.services.instruments import get_driver_class
            from app.core.instrument_config import get_instrument_settings

            # Get parameters
            instrument_name = get_param(self.test_params, 'instrument', default='CMW100_1')
            connector = int(get_param(self.test_params, 'connector', default=1))
            frequency = float(get_param(self.test_params, 'frequency', default=2440.0))
            expected_power = float(get_param(self.test_params, 'expected_power', default=-5.0))
            burst_type = get_param(self.test_params, 'burst_type', default='LE')

            self.logger.info(f"CMW100 BLE measurement: connector={connector}, freq={frequency}MHz")

            # Get instrument configuration
            instrument_settings = get_instrument_settings()
            config = instrument_settings.get_instrument(instrument_name)
            if config is None:
                return self.create_result(
                    result="ERROR",
                    error_message=f"Instrument {instrument_name} not found in configuration"
                )

            # Get driver class
            driver_class = get_driver_class(config.type)
            if driver_class is None:
                return self.create_result(
                    result="ERROR",
                    error_message=f"No driver found for instrument type: {config.type}"
                )

            # Get connection and create driver
            connection_pool = get_connection_pool()
            async with connection_pool.get_connection(instrument_name) as conn:
                driver = driver_class(conn)

                # Initialize if needed
                if not hasattr(driver, '_initialized'):
                    await driver.initialize()
                    driver._initialized = True

                # Execute measurement using real driver
                ble_result = await driver.measure_ble_tx_power(connector, frequency, expected_power, burst_type)

            # Check for measurement errors
            if ble_result.get('status') == 'ERROR':
                error_msg = ble_result.get('error', 'Unknown error')
                return self.create_result(result="ERROR", error_message=error_msg)

            # Extract measured power value
            measured_power = ble_result['tx_power']

            # Validate against limits
            is_valid, error_msg = self.validate_result(measured_power)

            # Generate error message if validation failed
            if not is_valid and error_msg is None:
                if self.lower_limit is not None and self.upper_limit is not None:
                    error_msg = f"Value {measured_power} outside range [{self.lower_limit}, {self.upper_limit}]"
                elif self.lower_limit is not None:
                    error_msg = f"Value {measured_power} < lower limit {self.lower_limit}"
                elif self.upper_limit is not None:
                    error_msg = f"Value {measured_power} > upper limit {self.upper_limit}"

            return self.create_result(
                result="PASS" if is_valid else "FAIL",
                measured_value=measured_power,
                error_message=error_msg if not is_valid else None
            )

        except Exception as e:
            self.logger.error(f"CMW100 BLE measurement error: {e}", exc_info=True)
            return self.create_result(result="ERROR", error_message=str(e))


class CMW100_WiFi_Measurement(BaseMeasurement):
    """
    WiFi measurement using CMW100.
    Measures WiFi TX power, EVM, and spectral mask compliance.

    Parameters:
        instrument: Instrument name in config (default: 'CMW100_1')
        connector: RF connector number (default: 1)
        standard: WiFi standard ('a/g', 'ac', 'ax') (default: 'ac')
        channel: WiFi channel number (default: 36)
        bandwidth: Channel bandwidth in MHz (default: 20)

    Integration: Uses CMW100Driver from backend/app/services/instruments/cmw100.py
    """

    async def execute(self) -> MeasurementResult:
        try:
            # Import required modules lazily to avoid circular imports
            from app.services.instrument_connection import get_connection_pool
            from app.services.instruments import get_driver_class
            from app.core.instrument_config import get_instrument_settings

            # Get parameters
            instrument_name = get_param(self.test_params, 'instrument', default='CMW100_1')
            connector = int(get_param(self.test_params, 'connector', default=1))
            standard = get_param(self.test_params, 'standard', default='ac')
            channel = int(get_param(self.test_params, 'channel', default=36))
            bandwidth = int(get_param(self.test_params, 'bandwidth', default=20))
            expected_power = get_param(self.test_params, 'expected_power')

            self.logger.info(f"CMW100 WiFi measurement: connector={connector}, std={standard}, ch={channel}, bw={bandwidth}MHz")

            # Get instrument configuration
            instrument_settings = get_instrument_settings()
            config = instrument_settings.get_instrument(instrument_name)
            if config is None:
                return self.create_result(
                    result="ERROR",
                    error_message=f"Instrument {instrument_name} not found in configuration"
                )

            # Get driver class
            driver_class = get_driver_class(config.type)
            if driver_class is None:
                return self.create_result(
                    result="ERROR",
                    error_message=f"No driver found for instrument type: {config.type}"
                )

            # Get connection and create driver
            connection_pool = get_connection_pool()
            async with connection_pool.get_connection(instrument_name) as conn:
                driver = driver_class(conn)

                # Initialize if needed
                if not hasattr(driver, '_initialized'):
                    await driver.initialize()
                    driver._initialized = True

                # Execute measurement using real driver
                wifi_result = await driver.measure_wifi_tx_power(
                    connector, standard, channel, bandwidth,
                    float(expected_power) if expected_power else None
                )

            # Check for measurement errors
            if wifi_result.get('status') == 'ERROR':
                error_msg = wifi_result.get('error', 'Unknown error')
                return self.create_result(result="ERROR", error_message=error_msg)

            # Extract measured power value
            measured_power = wifi_result['tx_power']

            # Validate against limits
            is_valid, error_msg = self.validate_result(measured_power)

            # Generate error message if validation failed
            if not is_valid and error_msg is None:
                if self.lower_limit is not None and self.upper_limit is not None:
                    error_msg = f"Value {measured_power} outside range [{self.lower_limit}, {self.upper_limit}]"
                elif self.lower_limit is not None:
                    error_msg = f"Value {measured_power} < lower limit {self.lower_limit}"
                elif self.upper_limit is not None:
                    error_msg = f"Value {measured_power} > upper limit {self.upper_limit}"

            return self.create_result(
                result="PASS" if is_valid else "FAIL",
                measured_value=measured_power,
                error_message=error_msg if not is_valid else None
            )

        except Exception as e:
            self.logger.error(f"CMW100 WiFi measurement error: {e}", exc_info=True)
            return self.create_result(result="ERROR", error_message=str(e))


# ============================================================================
# L6MPU SSH Measurements
# ============================================================================
class L6MPU_LTE_Check_Measurement(BaseMeasurement):
    """
    LTE module SIM card check using L6MPU SSH driver.
    Checks SIM card status via microcom and AT+CPIN? command.

    Parameters:
        instrument: Instrument name in config (default: 'L6MPU_1')
        timeout: Command timeout in seconds (default: 5.0)

    Integration: Uses L6MPUSSHDriver from backend/app/services/instruments/l6mpu_ssh.py
    """

    async def execute(self) -> MeasurementResult:
        try:
            # Import required modules lazily
            from app.services.instrument_connection import get_connection_pool
            from app.services.instruments import get_driver_class
            from app.core.instrument_config import get_instrument_settings

            # Get parameters
            instrument_name = get_param(self.test_params, 'instrument', default='L6MPU_1')
            timeout = float(get_param(self.test_params, 'timeout', default=5.0))

            self.logger.info(f"L6MPU LTE check: instrument={instrument_name}")

            # Get instrument configuration
            instrument_settings = get_instrument_settings()
            config = instrument_settings.get_instrument(instrument_name)
            if config is None:
                return self.create_result(
                    result="ERROR",
                    error_message=f"Instrument {instrument_name} not found in configuration"
                )

            # Get driver class
            driver_class = get_driver_class(config.type)
            if driver_class is None:
                return self.create_result(
                    result="ERROR",
                    error_message=f"No driver found for instrument type: {config.type}"
                )

            # Get connection and create driver
            connection_pool = get_connection_pool()
            async with connection_pool.get_connection(instrument_name) as conn:
                driver = driver_class(conn)

                # Initialize if needed
                if not hasattr(driver, '_initialized'):
                    await driver.initialize()
                    driver._initialized = True

                # Execute LTE check
                result = await driver.lte_check(timeout=timeout)

            # Check result
            if result.get('status') == 'ERROR':
                return self.create_result(result="ERROR", error_message=result.get('error', 'Unknown error'))

            # SIM ready indicates success
            is_valid = result.get('sim_ready', False)
            measured_value = Decimal("1.0") if is_valid else Decimal("0.0")

            return self.create_result(
                result="PASS" if is_valid else "FAIL",
                measured_value=measured_value,
                error_message=None if is_valid else "SIM card not ready"
            )

        except Exception as e:
            self.logger.error(f"L6MPU LTE check error: {e}", exc_info=True)
            return self.create_result(result="ERROR", error_message=str(e))


class L6MPU_PLC_Test_Measurement(BaseMeasurement):
    """
    PLC network connectivity test using L6MPU SSH driver.
    Tests PLC connectivity via ping on eth0/eth1 interfaces.

    Parameters:
        instrument: Instrument name in config (default: 'L6MPU_1')
        interface: Network interface ('eth0' or 'eth1') (default: 'eth0')
        count: Number of ping packets (default: 4)

    Integration: Uses L6MPUSSHDriver from backend/app/services/instruments/l6mpu_ssh.py
    """

    async def execute(self) -> MeasurementResult:
        try:
            # Import required modules lazily
            from app.services.instrument_connection import get_connection_pool
            from app.services.instruments import get_driver_class
            from app.core.instrument_config import get_instrument_settings

            # Get parameters
            instrument_name = get_param(self.test_params, 'instrument', default='L6MPU_1')
            interface = get_param(self.test_params, 'interface', default='eth0')
            count = int(get_param(self.test_params, 'count', default=4))

            self.logger.info(f"L6MPU PLC test: instrument={instrument_name}, interface={interface}")

            # Get instrument configuration
            instrument_settings = get_instrument_settings()
            config = instrument_settings.get_instrument(instrument_name)
            if config is None:
                return self.create_result(
                    result="ERROR",
                    error_message=f"Instrument {instrument_name} not found in configuration"
                )

            # Get driver class
            driver_class = get_driver_class(config.type)
            if driver_class is None:
                return self.create_result(
                    result="ERROR",
                    error_message=f"No driver found for instrument type: {config.type}"
                )

            # Get connection and create driver
            connection_pool = get_connection_pool()
            async with connection_pool.get_connection(instrument_name) as conn:
                driver = driver_class(conn)

                # Initialize if needed
                if not hasattr(driver, '_initialized'):
                    await driver.initialize()
                    driver._initialized = True

                # Execute PLC ping test
                result = await driver.plc_ping_test(interface=interface, count=count)

            # Check result
            if result.get('status') == 'ERROR':
                return self.create_result(result="ERROR", error_message=result.get('error', 'Unknown error'))

            # Success if ping completed without 100% packet loss
            packet_loss = result.get('packet_loss', 100)
            is_valid = packet_loss < 100

            # Use packet loss inverse as measured value (0% loss = 1.0, 100% loss = 0.0)
            measured_value = Decimal(str((100 - packet_loss) / 100.0))

            return self.create_result(
                result="PASS" if is_valid else "FAIL",
                measured_value=measured_value,
                error_message=None if is_valid else f"100% packet loss"
            )

        except Exception as e:
            self.logger.error(f"L6MPU PLC test error: {e}", exc_info=True)
            return self.create_result(result="ERROR", error_message=str(e))


# ============================================================================
# SMCV100B Measurements
# ============================================================================
class SMCV100B_RF_Output_Measurement(BaseMeasurement):
    """
    RF signal generation using SMCV100B.
    Supports DAB, AM, FM modulation modes.

    Parameters:
        instrument: Instrument name in config (default: 'SMCV100B_1')
        mode: Modulation mode ('DAB', 'AM', 'FM', 'IQ', 'RF')
        frequency: Carrier frequency in MHz (required for RF modes)
        power: RF power in dBm (required for RF modes)
        file: Transport stream file (required for DAB mode)
        enable: Enable/disable for IQ/RF modes

    Integration: Uses SMCV100BDriver from backend/app/services/instruments/smcv100b.py
    """

    async def execute(self) -> MeasurementResult:
        try:
            # Import required modules lazily
            from app.services.instrument_connection import get_connection_pool
            from app.services.instruments import get_driver_class
            from app.core.instrument_config import get_instrument_settings

            # Get parameters
            instrument_name = get_param(self.test_params, 'instrument', default='SMCV100B_1')
            mode = get_param(self.test_params, 'mode', default='FM')
            frequency = get_param(self.test_params, 'frequency')
            power = get_param(self.test_params, 'power')
            transport_file = get_param(self.test_params, 'file')
            enable = get_param(self.test_params, 'enable', default=True)

            self.logger.info(f"SMCV100B RF output: mode={mode}")

            # Get instrument configuration
            instrument_settings = get_instrument_settings()
            config = instrument_settings.get_instrument(instrument_name)
            if config is None:
                return self.create_result(
                    result="ERROR",
                    error_message=f"Instrument {instrument_name} not found in configuration"
                )

            # Get driver class
            driver_class = get_driver_class(config.type)
            if driver_class is None:
                return self.create_result(
                    result="ERROR",
                    error_message=f"No driver found for instrument type: {config.type}"
                )

            # Build command params
            cmd_params = {'mode': mode}

            if frequency is not None:
                cmd_params['frequency'] = float(frequency)
            if power is not None:
                cmd_params['power'] = float(power)
            if transport_file is not None:
                cmd_params['file'] = transport_file
            if enable is not None:
                if isinstance(enable, str):
                    enable = enable.lower() in ('true', '1', 'yes', 'on')
                cmd_params['enable'] = enable

            # Get connection and create driver
            connection_pool = get_connection_pool()
            async with connection_pool.get_connection(instrument_name) as conn:
                driver = driver_class(conn)

                # Initialize if needed
                if not hasattr(driver, '_initialized'):
                    await driver.initialize()
                    driver._initialized = True

                # Execute RF output command
                output = await driver.execute_command(cmd_params)

            # Success if command completed
            return self.create_result(
                result="PASS",
                measured_value=Decimal("1.0")
            )

        except Exception as e:
            self.logger.error(f"SMCV100B RF output error: {e}", exc_info=True)
            return self.create_result(result="ERROR", error_message=str(e))


# ============================================================================
# PEAK CAN Measurements
# ============================================================================
class PEAK_CAN_Message_Measurement(BaseMeasurement):
    """
    CAN message communication using PEAK-System PCAN hardware.
    Supports CAN and CAN-FD message transmission and reception.

    Parameters:
        instrument: Instrument name in config (default: 'PEAK_CAN_1')
        operation: Operation type ('write', 'read', 'write_read')
        can_id: CAN identifier (hex or decimal)
        data: Message data (hex comma-separated string)
        is_extended: Use extended frame format (29-bit ID)
        is_fd: Use CAN-FD format
        timeout: Receive timeout in seconds
        filter_id: Filter messages by ID when reading

    Integration: Uses PEAKCANDriver from backend/app/services/instruments/peak_can.py
    """

    async def execute(self) -> MeasurementResult:
        try:
            # Import required modules lazily
            from app.services.instrument_connection import get_connection_pool
            from app.services.instruments import get_driver_class
            from app.core.instrument_config import get_instrument_settings

            # Get parameters
            instrument_name = get_param(self.test_params, 'instrument', default='PEAK_CAN_1')
            operation = get_param(self.test_params, 'operation', default='read')

            self.logger.info(f"PEAK CAN operation: {operation}")

            # Get instrument configuration
            instrument_settings = get_instrument_settings()
            config = instrument_settings.get_instrument(instrument_name)
            if config is None:
                return self.create_result(
                    result="ERROR",
                    error_message=f"Instrument {instrument_name} not found in configuration"
                )

            # Get driver class
            driver_class = get_driver_class(config.type)
            if driver_class is None:
                return self.create_result(
                    result="ERROR",
                    error_message=f"No driver found for instrument type: {config.type}"
                )

            # Build command params
            cmd_params = {'operation': operation}

            # Add optional parameters
            for key in ['can_id', 'id', 'data', 'is_extended', 'extended', 'is_fd', 'fd', 'timeout', 'filter_id', 'filter']:
                value = get_param(self.test_params, key)
                if value is not None:
                    # Normalize key names
                    param_key = key
                    if key == 'id':
                        param_key = 'can_id'
                    elif key == 'extended':
                        param_key = 'is_extended'
                    elif key == 'fd':
                        param_key = 'is_fd'
                    elif key == 'filter':
                        param_key = 'filter_id'
                    cmd_params[param_key] = value

            # Get connection and create driver
            connection_pool = get_connection_pool()
            async with connection_pool.get_connection(instrument_name) as conn:
                driver = driver_class(conn)

                # Initialize if needed
                if not hasattr(driver, '_initialized'):
                    await driver.initialize()
                    driver._initialized = True

                # Execute CAN command
                output = await driver.execute_command(cmd_params)

            # Check for error in output
            if 'Error' in output or 'ERROR' in output:
                return self.create_result(result="ERROR", error_message=output)

            # Success
            return self.create_result(
                result="PASS",
                measured_value=Decimal("1.0")
            )

        except Exception as e:
            self.logger.error(f"PEAK CAN error: {e}", exc_info=True)
            return self.create_result(result="ERROR", error_message=str(e))


# ============================================================================
# Measurement Registry
# ============================================================================
MEASUREMENT_REGISTRY = {
    "DUMMY": DummyMeasurement,
    "COMMAND_TEST": CommandTestMeasurement,
    "POWER_READ": PowerReadMeasurement,
    "POWER_SET": PowerSetMeasurement,
    "SFC_TEST": SFCMeasurement,
    "GET_SN": GetSNMeasurement,
    "OP_JUDGE": OPJudgeMeasurement,
    "WAIT": WaitMeasurement,
    "RELAY": RelayMeasurement,
    "CHASSIS_ROTATION": ChassisRotationMeasurement,
    "OTHER": OtherMeasurement,  # 修改: 使用 OtherMeasurement 執行自定義腳本，而非 DummyMeasurement 的隨機值
    "FINAL": DummyMeasurement,
    # RF_Tool (MT8872A) measurements
    "RF_TOOL_LTE_TX": RF_Tool_LTE_TX_Measurement,
    "RF_TOOL_LTE_RX": RF_Tool_LTE_RX_Measurement,
    # CMW100 measurements
    "CMW100_BLE": CMW100_BLE_Measurement,
    "CMW100_WIFI": CMW100_WiFi_Measurement,
    # L6MPU measurements
    "L6MPU_LTE_CHECK": L6MPU_LTE_Check_Measurement,
    "L6MPU_PLC_TEST": L6MPU_PLC_Test_Measurement,
    # SMCV100B measurements
    "SMCV100B_RF": SMCV100B_RF_Output_Measurement,
    # PEAK CAN measurements
    "PEAK_CAN": PEAK_CAN_Message_Measurement,
    # Lowercase variants
    "command": CommandTestMeasurement,
    "wait": WaitMeasurement,
    "relay": RelayMeasurement,
    "chassis_rotation": ChassisRotationMeasurement,
    "other": OtherMeasurement,  # 修改: 使用 OtherMeasurement 執行自定義腳本
    # Case type mappings
    "console": CommandTestMeasurement,
    "comport": CommandTestMeasurement,
    "tcpip": CommandTestMeasurement,
    "URL": SFCMeasurement,
    "webStep1_2": SFCMeasurement,
}


def get_measurement_class(test_command: str) -> Optional[type]:
    """
    Get measurement class by command name.

    Args:
        test_command: Test command string

    Returns:
        Measurement class or None
    """
    # Normalize command names
    command_map = {
        "SFCtest": "SFC_TEST",
        "getSN": "GET_SN",
        "OPjudge": "OP_JUDGE",
        "Other": "OTHER",
        "Final": "FINAL",
        "CommandTest": "COMMAND_TEST",
        "PowerRead": "POWER_READ",
        "PowerSet": "POWER_SET",
        "MeasureSwitchON": "RELAY",      # PDTool4 relay ON mapping
        "MeasureSwitchOFF": "RELAY",     # PDTool4 relay OFF mapping
        "ChassisRotateCW": "CHASSIS_ROTATION",   # PDTool4 clockwise rotation
        "ChassisRotateCCW": "CHASSIS_ROTATION",  # PDTool4 counterclockwise rotation
        # RF_Tool (MT8872A) mappings
        "RF_Tool_LTE_TX": "RF_TOOL_LTE_TX",
        "RF_Tool_LTE_RX": "RF_TOOL_LTE_RX",
        "RFTOOLTETX": "RF_TOOL_LTE_TX",  # Alternative naming
        "RFTOOLTETRX": "RF_TOOL_LTE_RX",  # Alternative naming
        # CMW100 mappings
        "CMW100_BLE": "CMW100_BLE",
        "CMW100_WiFi": "CMW100_WIFI",
        "CMW100WIFI": "CMW100_WIFI",  # Alternative naming
        # L6MPU mappings
        "L6MPU_LTE": "L6MPU_LTE_CHECK",
        "L6MPU_PLC": "L6MPU_PLC_TEST",
        "L6MPULTE": "L6MPU_LTE_CHECK",
        "L6MPUPPLC": "L6MPU_PLC_TEST",
        # SMCV100B mappings
        "SMCV100B": "SMCV100B_RF",
        "SMCV": "SMCV100B_RF",
        # PEAK CAN mappings
        "PEAK": "PEAK_CAN",
        "PCAN": "PEAK_CAN",
        # Console/COM/TCP mappings
        "console": "console",
        "comport": "comport",
        "tcpip": "tcpip",
        "URL": "URL",
        "webStep1_2": "webStep1_2",
        "command": "command",
        "wait": "wait",
        "relay": "relay",
        "chassis_rotation": "chassis_rotation",
        "other": "other",
    }

    # Find in map or use uppercase
    if test_command in command_map:
        registry_key = command_map[test_command]
    elif test_command in MEASUREMENT_REGISTRY:
        registry_key = test_command
    else:
        registry_key = test_command.upper()

    return MEASUREMENT_REGISTRY.get(registry_key)
