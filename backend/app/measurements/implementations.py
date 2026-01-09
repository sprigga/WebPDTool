"""
Example Measurement Implementations
Simplified versions demonstrating the measurement pattern
"""
from decimal import Decimal
from typing import Dict, Any
import asyncio
import random

from app.measurements.base import BaseMeasurement, MeasurementResult, STRING_VALUE_TYPE


class DummyMeasurement(BaseMeasurement):
    """
    Dummy measurement for testing
    Returns random values within limits
    """
    
    async def execute(self) -> MeasurementResult:
        """Execute dummy measurement"""
        try:
            # Simulate measurement delay
            await asyncio.sleep(0.1)
            
            # Generate random value between limits
            if self.lower_limit is not None and self.upper_limit is not None:
                # Generate value within range with 80% pass rate
                if random.random() < 0.8:
                    # Pass case
                    range_size = float(self.upper_limit - self.lower_limit)
                    measured_value = self.lower_limit + Decimal(random.uniform(0.1, 0.9) * range_size)
                else:
                    # Fail case
                    if random.random() < 0.5:
                        measured_value = self.lower_limit - Decimal(abs(random.gauss(1, 0.5)))
                    else:
                        measured_value = self.upper_limit + Decimal(abs(random.gauss(1, 0.5)))
            else:
                # No limits, just return random value
                measured_value = Decimal(random.uniform(0, 100))

            # Validate result
            is_valid, validation_error = self.validate_result(measured_value)
            result_status = "PASS" if is_valid else "FAIL"

            return self.create_result(
                result=result_status,
                measured_value=measured_value,
                error_message=validation_error if not is_valid else None
            )
            
        except Exception as e:
            self.logger.error(f"Error in dummy measurement: {e}")
            return self.create_result(
                result="ERROR",
                error_message=str(e)
            )


class CommandTestMeasurement(BaseMeasurement):
    """
    Command Test Measurement
    Executes external commands/scripts
    對應 PDTool4 的 CommandTest 測試類型
    """

    async def execute(self) -> MeasurementResult:
        """Execute command test measurement"""
        import subprocess
        import os

        try:
            # Extract parameters from test_params
            # 原有程式碼: params = self.test_params
            # 修改: test_engine.py 已經將 command 和 wait_msec 整合到 test_params 中
            #      所以現在可以直接使用 self.test_params
            params = self.test_params

            # 優先使用 parameters["command"]，其次使用 test_plan_item 中的 command
            command = params.get("command", "")

            # 如果 parameters 中沒有，嘗試從 test_plan_item 取得
            if not command:
                command = self.test_plan_item.get("command", "")

            timeout = params.get("timeout", 5000)  # 預設 5 秒

            # 原有程式碼: wait_msec = params.get("wait_msec", 0)
            # 修改: test_engine.py 已經將 wait_msec 整合到 params 中
            #      如果沒有，再嘗試從 test_plan_item 直接讀取
            wait_msec = params.get("wait_msec") or params.get("WaitmSec", 0)
            if not wait_msec:
                wait_msec = self.test_plan_item.get("wait_msec", 0)

            if not command:
                return self.create_result(
                    result="ERROR",
                    error_message="Missing command parameter"
                )

            self.logger.info(f"Executing command: {command}")

            # 等待指定的毫秒數
            if wait_msec and wait_msec > 0:
                await asyncio.sleep(wait_msec / 1000.0)

            # 轉換 timeout 單位 (ms -> s)
            timeout_seconds = timeout / 1000.0 if timeout else 5

            # 執行外部指令
            # 使用 shell=True 以支援路徑和參數
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd="/app"  # 設定工作目錄為容器內的 /app
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
                    error_message=f"Command execution timeout after {timeout}ms"
                )

            # 解碼輸出
            output = stdout.decode().strip()
            error_output = stderr.decode().strip()

            # 檢查執行結果
            if process.returncode != 0:
                error_msg = error_output if error_output else f"Command failed with exit code {process.returncode}"
                self.logger.error(f"Command execution failed: {error_msg}")

                # 根據 PDTool4 邏輯，如果返回錯誤，測試結果應該是 FAIL
                # 但我們需要區分是測試失敗還是執行錯誤
                # 這裡我們將返回碼視為執行錯誤
                return self.create_result(
                    result="ERROR",
                    error_message=error_msg
                )

            # 使用輸出作為測量值
            measured_value = output

            # 驗證結果
            is_valid, validation_error = self.validate_result(measured_value)

            # 根據 value_type 決定如何轉換 measured_value
            if self.value_type is STRING_VALUE_TYPE:
                # 字串類型，直接使用原始值
                final_value = measured_value
            else:
                # 數值類型，轉換為 Decimal
                try:
                    final_value = Decimal(str(measured_value)) if measured_value else None
                except Exception:
                    final_value = measured_value

            if not is_valid:
                return self.create_result(
                    result="FAIL",
                    measured_value=final_value,
                    error_message=validation_error
                )

            return self.create_result(
                result="PASS",
                measured_value=final_value
            )

        except Exception as e:
            self.logger.error(f"Error in command test: {e}", exc_info=True)
            return self.create_result(
                result="ERROR",
                error_message=str(e)
            )


class PowerReadMeasurement(BaseMeasurement):
    """
    Power Read Measurement
    Reads voltage/current from power instruments
    (Simplified version - to be expanded based on PDTool4 implementation)
    """
    
    async def execute(self) -> MeasurementResult:
        """Execute power read measurement"""
        try:
            # Extract parameters
            params = self.test_params
            instrument = params.get("Instrument")
            channel = params.get("Channel")
            item = params.get("Item")  # volt or curr
            
            if not all([instrument, channel, item]):
                return self.create_result(
                    result="ERROR",
                    error_message="Missing required parameters: Instrument, Channel, Item"
                )
            
            self.logger.info(
                f"Reading {item} from {instrument} channel {channel}"
            )
            
            # Simulate instrument read
            await asyncio.sleep(0.3)
            
            # Generate simulated value based on limits
            if self.lower_limit and self.upper_limit:
                # Generate value near center of range
                center = (self.lower_limit + self.upper_limit) / 2
                variance = (self.upper_limit - self.lower_limit) / 10
                measured_value = center + Decimal(random.gauss(0, float(variance)))
            else:
                measured_value = Decimal(random.uniform(0, 100))

            is_valid, validation_error = self.validate_result(measured_value)
            result_status = "PASS" if is_valid else "FAIL"

            return self.create_result(
                result=result_status,
                measured_value=measured_value,
                error_message=validation_error if not is_valid else None
            )
            
        except Exception as e:
            self.logger.error(f"Error in power read: {e}")
            return self.create_result(
                result="ERROR",
                error_message=str(e)
            )


class PowerSetMeasurement(BaseMeasurement):
    """
    Power Set Measurement
    Sets voltage/current on power supplies
    (Simplified version - to be expanded based on PDTool4 implementation)
    """

    async def execute(self) -> MeasurementResult:
        """Execute power set measurement"""
        try:
            # Extract parameters
            params = self.test_params
            instrument = params.get("Instrument")
            voltage = params.get("Voltage") or params.get("SetVolt")
            current = params.get("Current") or params.get("SetCurr")

            if not instrument:
                return self.create_result(
                    result="ERROR",
                    error_message="Missing required parameter: Instrument"
                )

            self.logger.info(
                f"Setting power on {instrument}: V={voltage}, I={current}"
            )

            # Simulate power set
            await asyncio.sleep(0.2)

            # Power set typically doesn't return a measured value but indicates success
            return self.create_result(
                result="PASS",
                measured_value=Decimal("1.0")  # Success indicator
            )

        except Exception as e:
            self.logger.error(f"Error in power set: {e}")
            return self.create_result(
                result="ERROR",
                error_message=str(e)
            )


class SFCMeasurement(BaseMeasurement):
    """
    SFC (Shop Floor Control) Test Measurement
    Integrates with manufacturing execution systems
    (Simplified version - to be expanded based on PDTool4 implementation)
    """

    async def execute(self) -> MeasurementResult:
        """Execute SFC test measurement"""
        try:
            # Extract parameters
            params = self.test_params
            sfc_mode = params.get("Mode", "webStep1_2")  # Default mode

            self.logger.info(f"Executing SFC test with mode: {sfc_mode}")

            # Simulate SFC communication delay
            await asyncio.sleep(0.5)

            # In real implementation, this would call the SFC system
            # For now, simulate a successful response
            result_status = "PASS"

            return self.create_result(
                result=result_status,
                measured_value=Decimal("1.0")  # Success indicator
            )

        except Exception as e:
            self.logger.error(f"Error in SFC test: {e}")
            return self.create_result(
                result="ERROR",
                error_message=str(e)
            )


class GetSNMeasurement(BaseMeasurement):
    """
    Get Serial Number Measurement
    Acquires device serial numbers via various methods
    (Simplified version - to be expanded based on PDTool4 implementation)
    """

    async def execute(self) -> MeasurementResult:
        """Execute serial number acquisition measurement"""
        try:
            # Extract parameters
            params = self.test_params
            sn_type = params.get("Type", "SN")  # SN, IMEI, MAC, etc.

            self.logger.info(f"Acquiring {sn_type} from device")

            # Simulate serial number read delay
            await asyncio.sleep(0.1)

            # In real implementation, this would read from actual source
            # For now, return a placeholder
            sn_value = params.get("SerialNumber", f"SN{random.randint(100000, 999999)}")

            return self.create_result(
                result="PASS",
                measured_value=Decimal("1.0")  # Success indicator
            )

        except Exception as e:
            self.logger.error(f"Error in serial number acquisition: {e}")
            return self.create_result(
                result="ERROR",
                error_message=str(e)
            )


class OPJudgeMeasurement(BaseMeasurement):
    """
    Operator Judgment Measurement
    Awaits operator confirmation for subjective tests
    (Simplified version - to be expanded based on PDTool4 implementation)
    """

    async def execute(self) -> MeasurementResult:
        """Execute operator judgment measurement"""
        try:
            # Extract parameters
            params = self.test_params
            judgment_type = params.get("Type", "YorN")  # YorN, confirm, etc.

            self.logger.info(f"Awaiting operator judgment: {judgment_type}")

            # In real implementation, this would prompt the operator
            # For now, simulate based on test parameters
            expected_result = params.get("Expected", "PASS")
            actual_result = params.get("Result", expected_result)

            return self.create_result(
                result=actual_result,
                measured_value=Decimal("1.0") if actual_result == "PASS" else Decimal("0.0")
            )

        except Exception as e:
            self.logger.error(f"Error in operator judgment: {e}")
            return self.create_result(
                result="ERROR",
                error_message=str(e)
            )


class WaitMeasurement(BaseMeasurement):
    """
    Wait Measurement
    等待指定時間後返回 PASS
    對應 PDTool4 的 WAIT 功能

    參數說明:
    - wait_msec: 等待時間（毫秒），從 test_plans.wait_msec 欄位讀取
    - WaitmSec: 等待時間（毫秒），從 parameters JSON 中讀取（向後相容）
    """

    async def execute(self) -> MeasurementResult:
        """Execute wait measurement"""
        try:
            # 原有程式碼: 優先從 test_plan_item 讀取 wait_msec（來自 test_plans.wait_msec 欄位）
            #         其次從 test_params 讀取 WaitmSec（來自 parameters JSON）
            # 修改: test_engine.py 已經將 wait_msec 整合到 test_params 中
            #      所以現在直接從 test_params 讀取即可 (優先級已由 test_engine 處理)
            #      test_engine 的優先級: test_plans.wait_msec > parameters JSON
            wait_msec = (
                self.test_params.get("wait_msec") or
                self.test_params.get("WaitmSec") or
                0
            )

            # 如果仍然沒有值,嘗試從 test_plan_item 直接讀取 (向後相容)
            if not wait_msec:
                wait_msec = self.test_plan_item.get("wait_msec", 0)

            if not isinstance(wait_msec, (int, float)) or wait_msec <= 0:
                return self.create_result(
                    result="ERROR",
                    error_message=f"wait mode requires wait_msec parameter (milliseconds). Got: {wait_msec}"
                )

            wait_seconds = wait_msec / 1000
            self.logger.info(f"Executing wait for {self.item_name} - waiting {wait_msec}ms ({wait_seconds}s)")

            # 等待指定的秒數
            await asyncio.sleep(wait_seconds)

            return self.create_result(
                result="PASS",
                measured_value=Decimal("1.0")
            )

        except Exception as e:
            self.logger.error(f"Error in wait measurement: {e}")
            return self.create_result(
                result="ERROR",
                error_message=str(e)
            )


# Measurement type registry
MEASUREMENT_REGISTRY = {
    "DUMMY": DummyMeasurement,
    "COMMAND_TEST": CommandTestMeasurement,
    "POWER_READ": PowerReadMeasurement,
    "POWER_SET": PowerSetMeasurement,
    "SFC_TEST": SFCMeasurement,
    "GET_SN": GetSNMeasurement,
    "OP_JUDGE": OPJudgeMeasurement,
    "WAIT": WaitMeasurement,
    "OTHER": DummyMeasurement,
    "FINAL": DummyMeasurement,
    # 新增: 直接支援小寫的 test_type 值
    "command": CommandTestMeasurement,
    "wait": WaitMeasurement,
    "other": DummyMeasurement,
    # 新增: 支援 case_type 的測量類型
    "console": CommandTestMeasurement,  # console 類型使用 CommandTest
    "comport": CommandTestMeasurement,  # comport 類型使用 CommandTest
    "tcpip": CommandTestMeasurement,   # tcpip 類型使用 CommandTest
    "URL": SFCMeasurement,             # URL 類型使用 SFC (webStep1_2)
    "webStep1_2": SFCMeasurement,      # SFC webStep1_2 模式
}


def get_measurement_class(test_command: str):
    """
    Get measurement class by command name

    Args:
        test_command: Test command string

    Returns:
        Measurement class or None
    """
    # Convert PDTool4-style names to registry keys
    command_map = {
        "SFCtest": "SFC_TEST",
        "getSN": "GET_SN",
        "OPjudge": "OP_JUDGE",
        "Other": "OTHER",
        "Final": "FINAL",
        "CommandTest": "COMMAND_TEST",
        "PowerRead": "POWER_READ",
        "PowerSet": "POWER_SET",
        # 新增: 小寫 test_type 的映射
        "command": "command",
        "wait": "wait",
        "other": "other",
        # 新增: case_type 的映射
        "console": "console",
        "comport": "comport",
        "tcpip": "tcpip",
        "URL": "URL",
        "webStep1_2": "webStep1_2",
    }

    # 優先使用 command_map，如果沒有則嘗試直接查找或轉大寫
    if test_command in command_map:
        registry_key = command_map[test_command]
    elif test_command in MEASUREMENT_REGISTRY:
        registry_key = test_command
    else:
        registry_key = test_command.upper()

    return MEASUREMENT_REGISTRY.get(registry_key)
