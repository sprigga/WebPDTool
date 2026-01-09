"""
Measurement Service
Core service implementing PDTool4 measurement execution logic
"""

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import asyncio
import logging
import subprocess
import json
from decimal import Decimal

from app.measurements.base import BaseMeasurement, MeasurementResult
from app.measurements.implementations import get_measurement_class
from app.models.test_session import TestSession as TestSessionModel
from app.models.test_result import TestResult as TestResultModel
from app.services.instrument_manager import instrument_manager

logger = logging.getLogger(__name__)


class MeasurementService:
    """
    Service for executing measurements based on PDTool4 architecture

    This service implements the core measurement dispatch and execution logic
    similar to PDTool4's oneCSV_atlas_2.py functionality.
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.active_sessions: Dict[int, Dict] = {}

        # PDTool4-style measurement dispatch table
        self.measurement_dispatch = {
            "PowerSet": self._execute_power_set,
            "PowerRead": self._execute_power_read,
            "CommandTest": self._execute_command_test,
            # 新增: 支援 case_type='command' (測量類型直接使用 command)
            "command": self._execute_command_test,
            "SFCtest": self._execute_sfc_test,
            # 新增: 支援 case_type='URL' (SFC web 模式)
            "URL": self._execute_sfc_test,
            "webStep1_2": self._execute_sfc_test,
            # 新增: 直接支援 case_type 作為 measurement_type (comport, console, tcpip 等)
            # 這些都映射到 CommandTest 執行器
            "comport": self._execute_command_test,
            "console": self._execute_command_test,
            "tcpip": self._execute_command_test,
            "android_adb": self._execute_command_test,
            "PEAK": self._execute_command_test,
            "getSN": self._execute_get_sn,
            "OPjudge": self._execute_op_judge,
            "wait": self._execute_wait,  # 新增: wait 測量類型支援
            "Wait": self._execute_wait,  # 支援大寫
            "Other": self._execute_other,
            "Final": self._execute_final,
        }

        # Instrument reset mapping (equivalent to PDTool4's used_instruments cleanup)
        self.instrument_reset_map = {
            "DAQ973A": "DAQ973A_test.py",
            "MODEL2303": "2303_test.py",
            "MODEL2306": "2306_test.py",
            "IT6723C": "IT6723C.py",
            "PSW3072": "PSW3072.py",
            "2260B": "2260B.py",
            "APS7050": "APS7050.py",
            "34970A": "34970A.py",
            "KEITHLEY2015": "Keithley2015.py",
            "DAQ6510": "DAQ6510.py",
            "MDO34": "MDO34.py",
            "MT8872A_INF": "MT8872A_INF.py",
        }

    async def execute_single_measurement(
        self,
        measurement_type: str,
        test_point_id: str,
        switch_mode: str,
        test_params: Dict[str, Any],
        run_all_test: bool = False,
        user_id: Optional[str] = None,
    ) -> MeasurementResult:
        """
        Execute a single measurement

        Args:
            measurement_type: Type of measurement (PowerSet, PowerRead, etc.)
            test_point_id: Test point identifier
            switch_mode: Switch/instrument mode (DAQ973A, MODEL2303, etc.)
            test_params: Test parameters dictionary
            run_all_test: Whether to continue on failure
            user_id: User executing the test

        Returns:
            MeasurementResult object
        """
        start_time = datetime.utcnow()

        try:
            self.logger.info(
                f"Executing {measurement_type} measurement for {test_point_id}"
            )

            # Validate parameters
            validation_result = await self.validate_params(
                measurement_type, switch_mode, test_params
            )
            if not validation_result["valid"]:
                return MeasurementResult(
                    item_no=0,
                    item_name=test_point_id,
                    result="ERROR",
                    error_message=f"Invalid parameters: {validation_result['missing_params']}",
                )

            # Get measurement executor
            if measurement_type not in self.measurement_dispatch:
                return MeasurementResult(
                    item_no=0,
                    item_name=test_point_id,
                    result="ERROR",
                    error_message=f"Unknown measurement type: {measurement_type}",
                )

            # Execute measurement
            executor = self.measurement_dispatch[measurement_type]

            # 原有程式碼: 呼叫 executor,不傳遞 measurement_type
            # 修改: 對於 _execute_command_test,需要傳遞 measurement_type 參數
            #      以判斷是否使用預設腳本還是直接執行 command
            import inspect
            sig = inspect.signature(executor)
            kwargs = {
                "test_point_id": test_point_id,
                "switch_mode": switch_mode,
                "test_params": test_params,
                "run_all_test": run_all_test,
            }

            # 如果 executor 接受 measurement_type 參數,則傳入
            if "measurement_type" in sig.parameters:
                kwargs["measurement_type"] = measurement_type

            result = await executor(**kwargs)

            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            result.execution_duration_ms = int(execution_time)

            # 原有程式碼: 只記錄 result 狀態,沒有記錄 measured_value
            # 修改: 同時記錄 result 狀態和 measured_value,方便調試和追蹤
            measured_value_str = str(result.measured_value) if result.measured_value is not None else "None"
            self.logger.info(
                f"Measurement {test_point_id} completed with result: {result.result}, measured_value: {measured_value_str}"
            )
            return result

        except Exception as e:
            self.logger.error(f"Measurement execution failed: {e}")
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            return MeasurementResult(
                item_no=0,
                item_name=test_point_id,
                result="ERROR",
                error_message=str(e),
                execution_duration_ms=int(execution_time),
            )

    async def execute_batch_measurements(
        self,
        session_id: int,
        measurements: List[Dict[str, Any]],
        stop_on_fail: bool = True,
        run_all_test: bool = False,
        user_id: Optional[str] = None,
        db: Optional[Session] = None,
    ):
        """
        Execute batch measurements asynchronously

        Implements PDTool4's CSV-driven sequential execution with dependency management.

        Args:
            session_id: 測試會話 ID
            measurements: 測量請求列表
            stop_on_fail: 失敗時是否停止 (True=停止, False=繼續)
            run_all_test: PDTool4 runAllTest 模式 (遇到錯誤繼續執行)
            user_id: 使用者 ID
            db: 資料庫 session
        """
        try:
            self.logger.info(f"Starting batch execution for session {session_id}")
            if run_all_test:
                self.logger.info(
                    "PDTool4 runAllTest mode: ENABLED - will continue on errors"
                )

            # Initialize session tracking
            self.active_sessions[session_id] = {
                "status": "RUNNING",
                "current_index": 0,
                "total_count": len(measurements),
                "results": [],
                "test_results": {},  # PDTool4-style result collection
                "errors": [],  # 收集所有錯誤 (runAllTest 模式)
                "run_all_test": run_all_test,
            }

            session_data = self.active_sessions[session_id]

            for index, measurement_request in enumerate(measurements):
                session_data["current_index"] = index

                # Check for stop request
                if session_data.get("should_stop", False):
                    session_data["status"] = "STOPPED"
                    break

                # 執行測量 - 傳遞 run_all_test 參數
                result = await self.execute_single_measurement(
                    measurement_type=measurement_request["measurement_type"],
                    test_point_id=measurement_request["test_point_id"],
                    switch_mode=measurement_request["switch_mode"],
                    test_params=measurement_request["test_params"],
                    run_all_test=run_all_test
                    or measurement_request.get("run_all_test", False),
                    user_id=user_id,
                )

                # Store result
                session_data["results"].append(result)
                session_data["test_results"][
                    measurement_request["test_point_id"]
                ] = result.measured_value

                # PDTool4 runAllTest: 收集錯誤但不停止
                if result.result == "ERROR":
                    error_msg = f"Item {result.item_name}: {result.error_message}"
                    session_data["errors"].append(error_msg)
                    if run_all_test:
                        self.logger.warning(
                            f"[runAllTest] Error at {result.item_name}: {result.error_message} - Continuing..."
                        )

                # Save to database if provided
                if db:
                    await self._save_measurement_result(db, session_id, result)

                # 判斷是否停止:
                # - 如果啟用 runAllTest，遇到 FAIL 或 ERROR 都繼續
                # - 如果 stop_on_fail=True 且未啟用 runAllTest，遇到 FAIL 停止
                # - ERROR 總是會被記錄，但在 runAllTest 模式下不停止
                should_stop = False

                if result.result == "FAIL":
                    if stop_on_fail and not run_all_test:
                        self.logger.warning(
                            f"Stopping batch execution due to failure at {result.item_name}"
                        )
                        session_data["status"] = "FAILED"
                        should_stop = True

                if result.result == "ERROR":
                    # runAllTest 模式下，ERROR 不會停止執行
                    if not run_all_test and not stop_on_fail:
                        self.logger.error(
                            f"Stopping batch execution due to error at {result.item_name}"
                        )
                        session_data["status"] = "ERROR"
                        should_stop = True

                if should_stop:
                    break

            # Complete session if not stopped
            if session_data["status"] == "RUNNING":
                session_data["status"] = "COMPLETED"
                self.logger.info(f"Batch execution completed successfully")

            # Cleanup instruments (PDTool4 style)
            await self._cleanup_used_instruments(
                session_data.get("used_instruments", {})
            )

            # Log summary
            total_errors = len(session_data.get("errors", []))
            if run_all_test and total_errors > 0:
                self.logger.warning(
                    f"[runAllTest] Completed with {total_errors} errors"
                )
                for err in session_data["errors"][:5]:  # 只顯示前 5 個錯誤
                    self.logger.warning(f"  - {err}")

            self.logger.info(
                f"Batch execution for session {session_id} completed with status: {session_data['status']}"
            )

        except Exception as e:
            self.logger.error(f"Batch execution failed for session {session_id}: {e}")
            if session_id in self.active_sessions:
                self.active_sessions[session_id]["status"] = "ERROR"
                self.active_sessions[session_id]["error"] = str(e)

    async def _execute_power_set(
        self,
        test_point_id: str,
        switch_mode: str,
        test_params: Dict[str, Any],
        run_all_test: bool,
    ) -> MeasurementResult:
        """
        Execute power setting measurement (based on PowerSetMeasurement.py)
        """
        try:
            if switch_mode in ["DAQ973A", "34970A", "APS7050", "DAQ6510"]:
                # Validate required parameters
                required_params = ["Instrument", "Channel", "Item"]
                missing = [p for p in required_params if p not in test_params]
                if missing:
                    return MeasurementResult(
                        item_no=0,
                        item_name=test_point_id,
                        result="ERROR",
                        error_message=f"Missing parameters: {missing}",
                    )

                # Map switch mode to script file
                script_map = {
                    "DAQ973A": "DAQ973A_test.py",
                    "34970A": "34970A.py",
                    "APS7050": "APS7050.py",
                    "DAQ6510": "DAQ6510.py",
                }

                # Execute instrument command via subprocess (PDTool4 style)
                result = await self._execute_instrument_command(
                    script_path=f"./src/lowsheen_lib/{script_map[switch_mode]}",
                    test_point_id=test_point_id,
                    test_params=test_params,
                )

                # Process response
                if "1" in result:
                    return MeasurementResult(
                        item_no=0,
                        item_name=test_point_id,
                        result="PASS",
                        measured_value=Decimal("1"),
                    )
                else:
                    return MeasurementResult(
                        item_no=0,
                        item_name=test_point_id,
                        result="FAIL",
                        measured_value=Decimal("0"),
                    )

            elif switch_mode in [
                "MODEL2303",
                "MODEL2306",
                "2260B",
                "IT6723C",
                "PSW3072",
            ]:
                # Similar implementation for power supplies
                required_params = ["Instrument", "SetVolt", "SetCurr"]
                missing = [p for p in required_params if p not in test_params]
                if missing:
                    return MeasurementResult(
                        item_no=0,
                        item_name=test_point_id,
                        result="ERROR",
                        error_message=f"Missing parameters: {missing}",
                    )

                # Map switch mode to script file
                script_map = {
                    "MODEL2303": "2303_test.py",
                    "MODEL2306": "2306_test.py",
                    "2260B": "2260B.py",
                    "IT6723C": "IT6723C.py",
                    "PSW3072": "PSW3072.py",
                }

                result = await self._execute_instrument_command(
                    script_path=f"./src/lowsheen_lib/{script_map[switch_mode]}",
                    test_point_id=test_point_id,
                    test_params=test_params,
                )

                return MeasurementResult(
                    item_no=0,
                    item_name=test_point_id,
                    result="PASS" if "success" in result.lower() else "FAIL",
                )

            elif switch_mode == "KEITHLEY2015":
                required_params = ["Instrument", "Command"]
                missing = [p for p in required_params if p not in test_params]
                if missing:
                    return MeasurementResult(
                        item_no=0,
                        item_name=test_point_id,
                        result="ERROR",
                        error_message=f"Missing parameters: {missing}",
                    )

                result = await self._execute_instrument_command(
                    script_path="./src/lowsheen_lib/Keithley2015.py",
                    test_point_id=test_point_id,
                    test_params=test_params,
                )

                return MeasurementResult(
                    item_no=0,
                    item_name=test_point_id,
                    result="PASS" if "success" in result.lower() else "FAIL",
                )

            else:
                return MeasurementResult(
                    item_no=0,
                    item_name=test_point_id,
                    result="ERROR",
                    error_message=f"Unsupported switch mode: {switch_mode}",
                )

        except Exception as e:
            return MeasurementResult(
                item_no=0, item_name=test_point_id, result="ERROR", error_message=str(e)
            )

    async def _execute_power_read(
        self,
        test_point_id: str,
        switch_mode: str,
        test_params: Dict[str, Any],
        run_all_test: bool,
    ) -> MeasurementResult:
        """
        Execute power reading measurement (based on PowerReadMeasurement.py)
        """
        try:
            if switch_mode in ["DAQ973A", "34970A", "DAQ6510", "MDO34"]:
                required_params = ["Instrument", "Channel", "Item"]
                # Add 'Type' parameter only for DAQ973A if Item is volt or curr
                if switch_mode == "DAQ973A" and (
                    "Item" in test_params
                    and (test_params["Item"] == "volt" or test_params["Item"] == "curr")
                ):
                    required_params.append("Type")

                missing = [p for p in required_params if p not in test_params]
                if missing:
                    return MeasurementResult(
                        item_no=0,
                        item_name=test_point_id,
                        result="ERROR",
                        error_message=f"Missing parameters: {missing}",
                    )

                # Map switch mode to script file
                script_map = {
                    "DAQ973A": "DAQ973A_test.py",
                    "34970A": "34970A.py",
                    "DAQ6510": "DAQ6510.py",
                    "MDO34": "MDO34.py",
                }

                result = await self._execute_instrument_command(
                    script_path=f"./src/lowsheen_lib/{script_map[switch_mode]}",
                    test_point_id=test_point_id,
                    test_params=test_params,
                )

                # Parse numeric result
                try:
                    # Clean up result string
                    cleaned_result = result.replace("\n", "").replace("\r", "").strip()
                    measured_value = Decimal(str(float(cleaned_result)))
                    return MeasurementResult(
                        item_no=0,
                        item_name=test_point_id,
                        result="PASS",  # Will be validated against limits later
                        measured_value=measured_value,
                    )
                except (ValueError, TypeError):
                    return MeasurementResult(
                        item_no=0,
                        item_name=test_point_id,
                        result="ERROR",
                        error_message=f"Invalid measurement result: {result}",
                    )

            elif switch_mode in ["APS7050", "KEITHLEY2015"]:
                if switch_mode == "KEITHLEY2015":
                    required_params = ["Instrument", "Command"]
                else:
                    required_params = ["Instrument", "Item"]  # For APS7050

                missing = [p for p in required_params if p not in test_params]
                if missing:
                    return MeasurementResult(
                        item_no=0,
                        item_name=test_point_id,
                        result="ERROR",
                        error_message=f"Missing parameters: {missing}",
                    )

                # Map switch mode to script file
                script_map = {
                    "APS7050": "APS7050.py",
                    "KEITHLEY2015": "Keithley2015.py",
                }

                result = await self._execute_instrument_command(
                    script_path=f"./src/lowsheen_lib/{script_map[switch_mode]}",
                    test_point_id=test_point_id,
                    test_params=test_params,
                )

                # Parse numeric result
                try:
                    # Clean up result string
                    cleaned_result = result.replace("\n", "").replace("\r", "").strip()
                    measured_value = Decimal(str(float(cleaned_result)))
                    return MeasurementResult(
                        item_no=0,
                        item_name=test_point_id,
                        result="PASS",  # Will be validated against limits later
                        measured_value=measured_value,
                    )
                except (ValueError, TypeError):
                    return MeasurementResult(
                        item_no=0,
                        item_name=test_point_id,
                        result="ERROR",
                        error_message=f"Invalid measurement result: {result}",
                    )

            elif switch_mode == "MT8870A_INF":
                required_params = ["Instrument", "Item"]
                missing = [p for p in required_params if p not in test_params]
                if missing:
                    return MeasurementResult(
                        item_no=0,
                        item_name=test_point_id,
                        result="ERROR",
                        error_message=f"Missing parameters: {missing}",
                    )

                result = await self._execute_instrument_command(
                    script_path="./src/lowsheen_lib/RF_tool/MT8872A_INF.py",
                    test_point_id=test_point_id,
                    test_params=test_params,
                )

                # Parse numeric result
                try:
                    # Clean up result string
                    cleaned_result = result.replace("\n", "").replace("\r", "").strip()
                    measured_value = Decimal(str(float(cleaned_result)))
                    return MeasurementResult(
                        item_no=0,
                        item_name=test_point_id,
                        result="PASS",  # Will be validated against limits later
                        measured_value=measured_value,
                    )
                except (ValueError, TypeError):
                    return MeasurementResult(
                        item_no=0,
                        item_name=test_point_id,
                        result="ERROR",
                        error_message=f"Invalid measurement result: {result}",
                    )

            else:
                return MeasurementResult(
                    item_no=0,
                    item_name=test_point_id,
                    result="ERROR",
                    error_message=f"Unsupported switch mode: {switch_mode}",
                )

        except Exception as e:
            return MeasurementResult(
                item_no=0, item_name=test_point_id, result="ERROR", error_message=str(e)
            )

    async def _execute_command_test(
        self,
        test_point_id: str,
        switch_mode: str,
        test_params: Dict[str, Any],
        run_all_test: bool,
        measurement_type: str = "CommandTest",  # 新增: 用於判斷是否使用預設腳本
    ) -> MeasurementResult:
        """
        Execute command test measurement (based on CommandTestMeasurement.py)

        支援多種通信方式: comport, console, tcpip, PEAK, android_adb
        可從資料庫 test_plans 表的 command 欄位讀取自訂腳本路徑

        參數說明:
        - switch_mode: 通信類型 (comport, console, tcpip, PEAK, android_adb, 或自定義腳本名稱)
        - test_params['Command']: 通信命令或腳本參數
        - test_params['command']: 從資料庫 command 欄位傳入的自訂腳本路徑 (當 switch_mode 不在預設列表時使用)
        - test_params['keyWord']: 關鍵字提取參數 (可選)
        - test_params['spiltCount']: 分割計數 (可選,配合 keyWord 使用)
        - test_params['splitLength']: 分割長度 (可選,配合 keyWord 使用)
        - test_params['EqLimit']: 等於限制值檢查 (可選)
        """
        try:
            import os

            # 定義預設的腳本映射和必要參數
            script_config = {
                "comport": {
                    "script": "ComPortCommand.py",
                    "required_params": ["Port", "Baud", "Command"],
                },
                "console": {
                    "script": "ConSoleCommand.py",
                    "required_params": ["Command"],
                },
                "tcpip": {"script": "TCPIPCommand.py", "required_params": ["Command"]},
                "PEAK": {"script": "PEAK_API/PEAK.py", "required_params": ["Command"]},
                "android_adb": {
                    "script": "AndroidAdbCommand.py",
                    "required_params": ["Command"],
                },
            }

            # 原有程式碼: 檢查是否為預設的 switch_mode
            # 修改: 當 measurement_type == switch_mode 時(例如都是 'console'),
            #      應該視為「直接執行 command」模式,而不是執行預設腳本
            #      只有當 switch_mode 是獨立的通信模式時,才使用預設腳本
            use_default_script = (
                switch_mode in script_config and
                # 如果 measurement_type 不是 CommandTest/command,則使用預設腳本
                # 例如: measurement_type='CommandTest', switch_mode='comport' -> 使用 ComPortCommand.py
                # 但: measurement_type='console', switch_mode='console' -> 直接執行 command
                (measurement_type in ["CommandTest", "command"] or measurement_type != switch_mode)
            )

            if use_default_script:
                config = script_config[switch_mode]
                script_file = config["script"]
                required_params = config["required_params"].copy()

                # 原有程式碼: 檢查必要參數 (要求大寫的 Command)
                # 修改: 支援 case-insensitive 參數查找,因為前端傳遞的是小寫 command
                missing = []
                for p in required_params:
                    # 優先使用原參數名,然後嘗試小寫版本
                    param_value = test_params.get(p)
                    if not param_value:
                        param_value = test_params.get(p.lower())

                    if not param_value:
                        missing.append(p)

                if missing:
                    return MeasurementResult(
                        item_no=0,
                        item_name=test_point_id,
                        result="ERROR",
                        error_message=f"Missing required parameters: {missing}",
                    )

                # 添加條件參數到必要參數列表
                if "keyWord" in test_params or "keyword" in test_params:
                    required_params.extend(["keyWord", "spiltCount", "splitLength"])
                elif "EqLimit" in test_params or "eq_limit" in test_params:
                    required_params.append("EqLimit")

                # 原有程式碼: 沒有實現 WaitmSec 等待功能
                # 修改: 在執行腳本前，如果有 WaitmSec 參數，先等待指定的毫秒數
                # 支援 case-insensitive 參數讀取
                wait_msec = test_params.get("WaitmSec") or test_params.get("wait_msec")
                if wait_msec and isinstance(wait_msec, (int, float)):
                    wait_seconds = wait_msec / 1000
                    self.logger.info(
                        f"Waiting {wait_msec}ms ({wait_seconds}s) before executing {test_point_id}"
                    )
                    await asyncio.sleep(wait_seconds)

                # 執行預設腳本 (使用 PDTool4 instrument library)
                # 原有程式碼: 傳遞 test_params (包含大寫的 Command)
                # 修改: 構建 params_for_execution,確保參數名稱符合腳本期望 (大寫 Command)
                params_for_execution = test_params.copy()
                if "command" in test_params and "Command" not in test_params:
                    params_for_execution["Command"] = test_params["command"]

                result = await self._execute_instrument_command(
                    script_path=f"./src/lowsheen_lib/{script_file}",
                    test_point_id=test_point_id,
                    test_params=params_for_execution,
                )

                # 處理輸出結果
                return self._process_command_result(result, test_params, test_point_id)

            # 支援自定義腳本 (從資料庫 command 欄位讀取)
            else:
                # 優先級 1: 使用 test_params 中明確指定的 command (來自資料庫 test_plans.command)
                # 這是完整命令字符串,例如: 'python ./scripts/test123.py'
                command = test_params.get("command")

                # 優先級 2: 使用 test_params 中明確指定的 script_path (向後相容)
                if not command:
                    script_path = test_params.get("script_path")
                    if script_path:
                        # 如果是相對路徑,則相對於 backend 目錄
                        if not os.path.isabs(script_path):
                            current_file = os.path.abspath(__file__)
                            backend_dir = os.path.dirname(
                                os.path.dirname(os.path.dirname(current_file))
                            )
                            script_path = os.path.join(backend_dir, script_path)

                        # 檢查腳本檔案是否存在
                        if not os.path.exists(script_path):
                            return MeasurementResult(
                                item_no=0,
                                item_name=test_point_id,
                                result="ERROR",
                                error_message=f"Script not found: {script_path}",
                            )

                        # 構建命令: python3 + script_path
                        command = f"python3 {script_path}"

                # 如果都沒有，返回錯誤
                if not command:
                    return MeasurementResult(
                        item_no=0,
                        item_name=test_point_id,
                        result="ERROR",
                        error_message=f"No command specified for CommandTest with switch_mode='{switch_mode}'. "
                        f"Please provide 'command' or 'script_path' in test_params, "
                        f"or use a predefined switch_mode: {list(script_config.keys())}",
                    )

                # 原有程式碼: 沒有實現 WaitmSec 等待功能
                # 修改: 在執行腳本前，如果有 WaitmSec 參數，先等待指定的毫秒數
                wait_msec = test_params.get("WaitmSec") or test_params.get("wait_msec")
                if wait_msec and isinstance(wait_msec, (int, float)):
                    wait_seconds = wait_msec / 1000
                    self.logger.info(
                        f"Waiting {wait_msec}ms ({wait_seconds}s) before executing {test_point_id}"
                    )
                    await asyncio.sleep(wait_seconds)

                # 修改: 使用直接命令執行 (類似 CommandTestMeasurement implementations.py)
                # 原有程式碼: 使用 _execute_instrument_command，期望 PDTool4 格式的腳本
                # 修改: 使用 asyncio.create_subprocess_shell 直接執行 shell 命令
                timeout_ms = (
                    test_params.get("Timeout") or test_params.get("timeout") or 30000
                )
                timeout_seconds = (
                    timeout_ms / 1000 if isinstance(timeout_ms, (int, float)) else 30
                )

                # 執行命令
                self.logger.info(f"Executing command: {command}")
                process = await asyncio.create_subprocess_shell(
                    command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd="/app",  # 容器環境工作目錄
                )

                try:
                    stdout, stderr = await asyncio.wait_for(
                        process.communicate(), timeout=timeout_seconds
                    )
                except asyncio.TimeoutError:
                    process.kill()
                    await process.wait()
                    return MeasurementResult(
                        item_no=0,
                        item_name=test_point_id,
                        result="ERROR",
                        error_message=f"Command execution timeout after {timeout_ms}ms",
                    )

                # 解碼輸出
                output = stdout.decode().strip()
                error_output = stderr.decode().strip()

                # 檢查執行結果
                if process.returncode != 0:
                    error_msg = (
                        error_output
                        if error_output
                        else f"Command failed with exit code {process.returncode}"
                    )
                    self.logger.error(f"Command execution failed: {error_msg}")
                    return MeasurementResult(
                        item_no=0,
                        item_name=test_point_id,
                        result="ERROR",
                        error_message=error_msg,
                    )

                # 處理輸出結果
                return self._process_command_result(output, test_params, test_point_id)

        except Exception as e:
            self.logger.error(f"CommandTest execution failed: {e}")
            return MeasurementResult(
                item_no=0, item_name=test_point_id, result="ERROR", error_message=str(e)
            )

    def _get_param_case_insensitive(
        self, test_params: Dict[str, Any], *possible_keys: str
    ) -> Any:
        """
        Get parameter value from test_params with case-insensitive key lookup

        Args:
            test_params: Test parameters dictionary
            *possible_keys: Possible key variations to try (in priority order)

        Returns:
            First non-None value found, or None if all keys are missing
        """
        for key in possible_keys:
            if key in test_params:
                return test_params[key]
        return None

    def _process_command_result(
        self, result: str, test_params: Dict[str, Any], test_point_id: str
    ) -> MeasurementResult:
        """
        處理 CommandTest 的執行結果 (仿照 PDTool4 CommandTestMeasurement.py)

        支援三種結果處理方式:
        1. keyWord: 關鍵字提取
        2. EqLimit: 等於限制值檢查
        3. default: 基本回應檢查

        修改: 使用 case-insensitive 參數查找，支援 CSV 欄位不同大小寫的情況
        例如: 'LimitType' (CSV) -> 'limit_type' (backend expects)
        """
        try:
            # 模式 1: 關鍵字提取 (keyWord + spiltCount + splitLength)
            # 使用 case-insensitive 查找
            keyword = self._get_param_case_insensitive(
                test_params, "keyWord", "keyword", "KEYWORD"
            )
            split_count = self._get_param_case_insensitive(
                test_params, "spiltCount", "split_count"
            )
            split_length = self._get_param_case_insensitive(
                test_params, "splitLength", "split_length"
            )

            if keyword:
                processed_result = self._process_keyword_extraction(result, test_params)
                try:
                    measured_value = Decimal(str(float(processed_result)))
                    return MeasurementResult(
                        item_no=0,
                        item_name=test_point_id,
                        result="PASS",
                        measured_value=measured_value,
                    )
                except (ValueError, TypeError):
                    return MeasurementResult(
                        item_no=0,
                        item_name=test_point_id,
                        result="ERROR",
                        error_message=f"Could not parse extracted value: {processed_result}",
                    )

            # 原有程式碼: 模式 2 - 等於限制值檢查 (EqLimit)
            # 問題: 這個模式沒有返回 measured_value,導致前端無法顯示測量值
            # 修改: 移除這個模式,因為模式 3 (limit_type 驗證) 已經完整處理所有情況
            #       包括 partial, equality, inequality 等限制類型
            # 模式 2 保留註解供參考,但不再執行,讓程式進入模式 3 處理
            #
            # eq_limit_check = self._get_param_case_insensitive(
            #     test_params, "EqLimit", "eq_limit"
            # )
            # if eq_limit_check and eq_limit_check != "":
            #     ... (舊的 EqLimit 檢查邏輯,已移除)
            #
            # 現在直接進入模式 3,使用 limit_type 進行完整的驗證和返回 measured_value

            # 模式 3: 基本回應檢查 (default)
            # 清理輸出結果
            cleaned_result = result.replace("\n", "").replace("\r", "").strip()

            # 檢查是否為空輸出
            if not cleaned_result or cleaned_result == "console output is empty":
                # 使用 case-insensitive 查找 limit_type
                limit_type = self._get_param_case_insensitive(
                    test_params, "limit_type", "LimitType"
                )
                if limit_type == "none":
                    return MeasurementResult(
                        item_no=0,
                        item_name=test_point_id,
                        result="PASS",
                        measured_value=None,
                    )
                return MeasurementResult(
                    item_no=0,
                    item_name=test_point_id,
                    result="FAIL",
                    error_message="Empty output",
                )

            # 原有程式碼: 根據 value_type 決定如何處理測量值
            # 修改: 新增 limit_type 驗證邏輯 (支援 partial, equality, inequality)
            # 使用 case-insensitive 查找
            value_type = (
                self._get_param_case_insensitive(
                    test_params, "value_type", "ValueType"
                )
                or "string"
            )
            limit_type = (
                self._get_param_case_insensitive(
                    test_params, "limit_type", "LimitType"
                )
                or "none"
            )
            eq_limit = self._get_param_case_insensitive(
                test_params, "eq_limit", "EqLimit"
            )

            # 決定 measured_value 的類型和值
            if value_type == "string":
                measured_value = cleaned_result  # 字串類型，直接使用原始值
            else:
                # 數值類型，嘗試轉換為 Decimal
                try:
                    measured_value = Decimal(str(float(cleaned_result)))
                except (ValueError, TypeError):
                    # 無法解析為數字，使用字串
                    measured_value = cleaned_result

            # 根據 limit_type 進行驗證
            if limit_type == "partial" and eq_limit:
                # PARTIAL_LIMIT_TYPE: 檢查 eq_limit 是否包含在 measured_value 中
                # 對應資料庫: arduino (eq_limit="456"), 123_1 (eq_limit="123")
                is_valid = str(eq_limit) in str(measured_value)
                if is_valid:
                    return MeasurementResult(
                        item_no=0,
                        item_name=test_point_id,
                        result="PASS",
                        measured_value=measured_value,
                    )
                else:
                    return MeasurementResult(
                        item_no=0,
                        item_name=test_point_id,
                        result="FAIL",
                        measured_value=measured_value,
                        error_message=f"Partial check failed: '{eq_limit}' not found in output",
                    )

            elif limit_type == "equality" and eq_limit:
                # EQUALITY_LIMIT_TYPE: 檢查 measured_value 是否等於 eq_limit
                is_valid = str(measured_value) == str(eq_limit)
                if is_valid:
                    return MeasurementResult(
                        item_no=0,
                        item_name=test_point_id,
                        result="PASS",
                        measured_value=measured_value,
                    )
                else:
                    return MeasurementResult(
                        item_no=0,
                        item_name=test_point_id,
                        result="FAIL",
                        measured_value=measured_value,
                        error_message=f"Equality check failed: expected '{eq_limit}', got '{measured_value}'",
                    )

            elif limit_type == "inequality" and eq_limit:
                # INEQUALITY_LIMIT_TYPE: 檢查 measured_value 是否不等於 eq_limit
                is_valid = str(measured_value) != str(eq_limit)
                if is_valid:
                    return MeasurementResult(
                        item_no=0,
                        item_name=test_point_id,
                        result="PASS",
                        measured_value=measured_value,
                    )
                else:
                    return MeasurementResult(
                        item_no=0,
                        item_name=test_point_id,
                        result="FAIL",
                        measured_value=measured_value,
                        error_message=f"Inequality check failed: value should not equal '{eq_limit}'",
                    )

            else:
                # NONE_LIMIT_TYPE 或其他: 直接返回 PASS
                return MeasurementResult(
                    item_no=0,
                    item_name=test_point_id,
                    result="PASS",
                    measured_value=measured_value,
                )

        except Exception as e:
            self.logger.error(f"Failed to process command result: {e}")
            return MeasurementResult(
                item_no=0,
                item_name=test_point_id,
                result="ERROR",
                error_message=f"Result processing failed: {str(e)}",
            )

    async def _execute_sfc_test(
        self,
        test_point_id: str,
        switch_mode: str,
        test_params: Dict[str, Any],
        run_all_test: bool,
    ) -> MeasurementResult:
        """
        Execute SFC test measurement (based on SFC_GONOGOMeasurement.py)
        """
        try:
            # Placeholder for SFC integration - would need actual SFC service
            if switch_mode in ["webStep1_2", "URLStep1_2"]:
                # Simulate SFC call
                await asyncio.sleep(0.1)  # Simulate network delay

                return MeasurementResult(
                    item_no=0,
                    item_name=test_point_id,
                    result="PASS",  # Would be based on actual SFC response
                    measured_value=Decimal("1"),
                )
            elif switch_mode == "skip":
                return MeasurementResult(
                    item_no=0, item_name=test_point_id, result="SKIP"
                )
            # 原有程式碼: 新增 WAIT_FIX_5sec 支援,等待 5 秒後返回 PASS
            elif switch_mode == "WAIT_FIX_5sec":
                self.logger.info(
                    f"Executing WAIT_FIX_5sec for {test_point_id} - waiting 5 seconds"
                )
                await asyncio.sleep(5)  # 等待 5 秒

                return MeasurementResult(
                    item_no=0,
                    item_name=test_point_id,
                    result="PASS",
                    measured_value=Decimal("1"),
                )
            else:
                return MeasurementResult(
                    item_no=0,
                    item_name=test_point_id,
                    result="ERROR",
                    error_message=f"Unsupported SFC switch mode: {switch_mode}",
                )

        except Exception as e:
            return MeasurementResult(
                item_no=0, item_name=test_point_id, result="ERROR", error_message=str(e)
            )

    async def _execute_get_sn(
        self,
        test_point_id: str,
        switch_mode: str,
        test_params: Dict[str, Any],
        run_all_test: bool,
    ) -> MeasurementResult:
        """
        Execute serial number acquisition (based on getSNMeasurement.py)
        """
        try:
            # Placeholder implementation - would read from actual source
            if switch_mode in ["SN", "IMEI", "MAC"]:
                # Simulate reading serial number
                serial_number = test_params.get("serial_number", "TEST123456")

                return MeasurementResult(
                    item_no=0,
                    item_name=test_point_id,
                    result="PASS",
                    measured_value=None,  # SN is text, not numeric
                )
            else:
                return MeasurementResult(
                    item_no=0,
                    item_name=test_point_id,
                    result="ERROR",
                    error_message=f"Unsupported SN switch mode: {switch_mode}",
                )

        except Exception as e:
            return MeasurementResult(
                item_no=0, item_name=test_point_id, result="ERROR", error_message=str(e)
            )

    async def _execute_wait(
        self,
        test_point_id: str,
        switch_mode: str,
        test_params: Dict[str, Any],
        run_all_test: bool,
    ) -> MeasurementResult:
        """
        Execute wait measurement (based on WaitMeasurement)

        等待指定時間後返回 PASS

        參數說明:
        - wait_msec: 等待時間（毫秒），從 test_params 中讀取
        - WaitmSec: 等待時間（毫秒），向後相容
        """
        try:
            # 從 test_params 讀取 wait_msec
            wait_msec = test_params.get("wait_msec") or test_params.get("WaitmSec") or 0

            if not isinstance(wait_msec, (int, float)) or wait_msec <= 0:
                return MeasurementResult(
                    item_no=0,
                    item_name=test_point_id,
                    result="ERROR",
                    error_message=f"wait mode requires wait_msec parameter (milliseconds). Got: {wait_msec}",
                )

            wait_seconds = wait_msec / 1000
            self.logger.info(
                f"Executing wait for {test_point_id} - waiting {wait_msec}ms ({wait_seconds}s)"
            )

            # 等待指定的秒數
            await asyncio.sleep(wait_seconds)

            return MeasurementResult(
                item_no=0,
                item_name=test_point_id,
                result="PASS",
                measured_value=Decimal("1"),
            )

        except Exception as e:
            return MeasurementResult(
                item_no=0, item_name=test_point_id, result="ERROR", error_message=str(e)
            )

    async def _execute_op_judge(
        self,
        test_point_id: str,
        switch_mode: str,
        test_params: Dict[str, Any],
        run_all_test: bool,
    ) -> MeasurementResult:
        """
        Execute operator judgment measurement (based on OPjudgeMeasurement.py)
        """
        try:
            # In real implementation, this would prompt operator
            # For API, we expect the judgment to be passed in test_params
            judgment = test_params.get("operator_judgment", "PASS")

            return MeasurementResult(
                item_no=0,
                item_name=test_point_id,
                result=judgment,
                measured_value=Decimal("1") if judgment == "PASS" else Decimal("0"),
            )

        except Exception as e:
            return MeasurementResult(
                item_no=0, item_name=test_point_id, result="ERROR", error_message=str(e)
            )

    async def _execute_other(
        self,
        test_point_id: str,
        switch_mode: str,
        test_params: Dict[str, Any],
        run_all_test: bool,
    ) -> MeasurementResult:
        """
        Execute other/custom measurements (based on OtherMeasurement.py)

        支援執行自定義命令,命令從資料庫 test_plans 表的 command 欄位獲取
        可以執行各種類型的命令,不限於 Python (例如: python, bash, node, etc.)

        參數說明:
        - switch_mode: 腳本類型或自定義識別符 (例如: 'test123', 'custom_script', 'WAIT_FIX_5sec')
        - test_params['script_path']: 腳本完整路徑 (僅路徑,不包含命令,向後相容)
        - test_params['command']: 完整命令字符串 (例如: 'python ./scripts/test123.py')
        - test_params['arg']: 傳遞給腳本的命令行參數 (可選,僅在使用 script_path 時有效)

        Command 欄位支援格式:
        1. 完整命令: 'python ./scripts/test123.py arg1 arg2'
        2. 僅路徑: './scripts/test123.py' (將自動使用 python3 執行)
        3. 其他命令: 'bash ./scripts/test.sh', 'node ./app.js', etc.
        """
        try:
            import os
            import shlex

            # 原有程式碼: 新增 WAIT_FIX_5sec 支援,等待 5 秒後返回 PASS
            if switch_mode == "WAIT_FIX_5sec":
                self.logger.info(
                    f"Executing WAIT_FIX_5sec for {test_point_id} - waiting 5 seconds"
                )
                await asyncio.sleep(5)  # 等待 5 秒

                return MeasurementResult(
                    item_no=0,
                    item_name=test_point_id,
                    result="PASS",
                    measured_value=Decimal("1"),
                )

            # 修改: 新增 wait 支援,根據 WaitmSec 參數等待指定毫秒數後返回 PASS
            if switch_mode == "wait":
                # 從 test_params 讀取 WaitmSec (單位: ms)，轉換為秒
                wait_msec = (
                    test_params.get("WaitmSec") or test_params.get("wait_msec") or 0
                )
                if isinstance(wait_msec, (int, float)) and wait_msec > 0:
                    wait_seconds = wait_msec / 1000
                    self.logger.info(
                        f"Executing wait for {test_point_id} - waiting {wait_msec}ms ({wait_seconds}s)"
                    )
                    await asyncio.sleep(wait_seconds)

                    return MeasurementResult(
                        item_no=0,
                        item_name=test_point_id,
                        result="PASS",
                        measured_value=Decimal("1"),
                    )
                else:
                    return MeasurementResult(
                        item_no=0,
                        item_name=test_point_id,
                        result="ERROR",
                        error_message=f"wait mode requires WaitmSec parameter (milliseconds). Got: {wait_msec}",
                    )

            # 優先級 1: 使用 test_params 中的 command (來自資料庫 test_plans.command)
            # 這是完整命令字符串,例如: 'python ./scripts/test123.py'
            raw_command = test_params.get("command")

            # 優先級 2: 使用 test_params 中明確指定的 script_path (向後相容)
            if not raw_command:
                script_path = test_params.get("script_path")

                # 優先級 3: 如果是 test123，使用預設路徑 (向後相容)
                if not script_path and switch_mode == "test123":
                    script_path = "scripts/test123.py"

                # 如果只有 script_path,構建為完整命令
                if script_path:
                    # 如果是相對路徑,則相對於 backend 目錄
                    if not os.path.isabs(script_path):
                        current_file = os.path.abspath(__file__)
                        backend_dir = os.path.dirname(
                            os.path.dirname(os.path.dirname(current_file))
                        )
                        script_path = os.path.join(backend_dir, script_path)

                    # 檢查腳本檔案是否存在
                    if not os.path.exists(script_path):
                        return MeasurementResult(
                            item_no=0,
                            item_name=test_point_id,
                            result="ERROR",
                            error_message=f"Script not found: {script_path}",
                        )

                    # 構建命令: python3 + script_path + arg
                    raw_command = f"python3 {script_path}"
                    if "arg" in test_params:
                        raw_command += f' {test_params["arg"]}'

            # 如果都沒有，返回錯誤
            if not raw_command:
                return MeasurementResult(
                    item_no=0,
                    item_name=test_point_id,
                    result="ERROR",
                    error_message=f"No command specified. Please provide 'command' or 'script_path' in test_params, or set command in database test_plans table.",
                )

            # 解析完整命令字符串為命令列表
            # 使用 shlex.split 正確處理帶引號的參數
            try:
                command_parts = shlex.split(raw_command)
            except ValueError as e:
                return MeasurementResult(
                    item_no=0,
                    item_name=test_point_id,
                    result="ERROR",
                    error_message=f"Invalid command format: {raw_command}. Error: {str(e)}",
                )

            # 獲取執行檔案路徑 (命令的第一部分)
            executable = command_parts[0]

            # 如果執行檔案是相對路徑,解析為絕對路徑
            if not os.path.isabs(executable) and "/" in executable:
                current_file = os.path.abspath(__file__)
                backend_dir = os.path.dirname(
                    os.path.dirname(os.path.dirname(current_file))
                )
                executable_abs = os.path.join(backend_dir, executable)
                if os.path.exists(executable_abs):
                    command_parts[0] = executable_abs

            # 構建最終命令列表
            command = command_parts

            # 原有程式碼: 沒有實現 WaitmSec 等待功能
            # 修改: 在執行腳本前，如果有 WaitmSec 參數，先等待指定的毫秒數
            wait_msec = test_params.get("WaitmSec") or test_params.get("wait_msec")
            if wait_msec and isinstance(wait_msec, (int, float)):
                wait_seconds = wait_msec / 1000
                self.logger.info(
                    f"Waiting {wait_msec}ms ({wait_seconds}s) before executing {test_point_id}"
                )
                await asyncio.sleep(wait_seconds)

            # 原有程式碼: 使用固定 30 秒超時
            # 修改: 從 test_params 讀取 Timeout (單位: ms)，轉換為秒
            # 優先級: test_params['Timeout'] > test_params['timeout'] > 預設 30 秒
            timeout_ms = (
                test_params.get("Timeout") or test_params.get("timeout") or 30000
            )
            timeout_seconds = (
                timeout_ms / 1000 if isinstance(timeout_ms, (int, float)) else 30
            )

            # 執行命令
            # 注意: 在容器環境中,工作目錄是 /app (對應專案的 backend 目錄)
            # 原有程式碼: 使用硬編碼路徑 '/home/ubuntu/WebPDTool/backend',這在容器中會失敗
            # 修正: 使用當前檔案的目錄來動態獲取 backend 目錄路徑
            self.logger.info(f"Executing command: {' '.join(command)}")

            # 動態獲取 backend 目錄路徑 (支援本地和容器環境)
            current_file = os.path.abspath(__file__)
            backend_cwd = os.path.dirname(
                os.path.dirname(os.path.dirname(current_file))
            )

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                cwd=backend_cwd,
            )

            if result.returncode != 0:
                return MeasurementResult(
                    item_no=0,
                    item_name=test_point_id,
                    result="ERROR",
                    error_message=f"Command failed with return code {result.returncode}. stderr: {result.stderr}",
                )

            # 解析輸出
            output = result.stdout.strip()

            # 原有程式碼: 根據輸出決定結果
            # 123.py 邏輯: 參數為 '123' 時輸出 '456'，否則輸出 '123'
            if output == "456":
                return MeasurementResult(
                    item_no=0,
                    item_name=test_point_id,
                    result="PASS",
                    measured_value=Decimal("456"),
                )
            elif output == "123":
                return MeasurementResult(
                    item_no=0,
                    item_name=test_point_id,
                    result="PASS",
                    measured_value=Decimal("123"),
                )
            # 嘗試解析為數字 (通用處理)
            else:
                try:
                    numeric_value = Decimal(str(float(output)))
                    return MeasurementResult(
                        item_no=0,
                        item_name=test_point_id,
                        result="PASS",
                        measured_value=numeric_value,
                    )
                except (ValueError, TypeError):
                    # 如果無法解析為數字，返回原始輸出作為 PASS
                    return MeasurementResult(
                        item_no=0,
                        item_name=test_point_id,
                        result="PASS",
                        error_message=f"Command output: {output}",
                    )

        except subprocess.TimeoutExpired:
            return MeasurementResult(
                item_no=0,
                item_name=test_point_id,
                result="ERROR",
                error_message="Command execution timeout",
            )
        except FileNotFoundError as e:
            return MeasurementResult(
                item_no=0,
                item_name=test_point_id,
                result="ERROR",
                error_message=f"Command or file not found: {str(e)}",
            )
        except Exception as e:
            return MeasurementResult(
                item_no=0, item_name=test_point_id, result="ERROR", error_message=str(e)
            )

    async def _execute_final(
        self,
        test_point_id: str,
        switch_mode: str,
        test_params: Dict[str, Any],
        run_all_test: bool,
    ) -> MeasurementResult:
        """
        Execute final measurement/cleanup (based on FinalMeasurement.py)
        """
        try:
            # Perform any final cleanup or validation
            return MeasurementResult(item_no=0, item_name=test_point_id, result="PASS")

        except Exception as e:
            return MeasurementResult(
                item_no=0, item_name=test_point_id, result="ERROR", error_message=str(e)
            )

    async def _execute_instrument_command(
        self, script_path: str, test_point_id: str, test_params: Dict[str, Any]
    ) -> str:
        """
        Execute instrument command via subprocess (PDTool4 style)
        """
        try:
            # Convert test_params to string format expected by PDTool4 scripts
            params_str = str(test_params)

            # 原有程式碼: 使用 python3 而非 python，確保在不同環境中都能執行
            # 原有程式碼: timeout=30 (固定值)
            # 修改: 從 test_params 讀取 Timeout (單位: ms)，轉換為秒
            timeout_ms = (
                test_params.get("Timeout") or test_params.get("timeout") or 30000
            )
            timeout_seconds = (
                timeout_ms / 1000 if isinstance(timeout_ms, (int, float)) else 30
            )

            # Execute command
            result = subprocess.run(
                ["python3", script_path, test_point_id, params_str],
                capture_output=True,
                text=True,
                timeout=timeout_seconds,  # 原有程式碼: timeout=30 (固定值)
            )

            if result.returncode == 10:
                raise Exception("No instrument found")
            elif result.returncode != 0:
                raise Exception(
                    f"Command failed with return code {result.returncode}: {result.stderr}"
                )

            return result.stdout.strip()

        except subprocess.TimeoutExpired:
            raise Exception("Command timeout")
        except FileNotFoundError:
            raise Exception(f"Script not found: {script_path}")
        except Exception as e:
            raise Exception(f"Command execution failed: {str(e)}")

    def _process_keyword_extraction(
        self, response: str, test_params: Dict[str, Any]
    ) -> str:
        """
        Process keyword extraction from response (PDTool4 CommandTest logic)

        修改: 使用 case-insensitive 參數查找
        """
        import re

        # 使用 case-insensitive 查找參數
        keyword = self._get_param_case_insensitive(
            test_params, "keyWord", "keyword", "KEYWORD"
        )
        spilt_count = self._get_param_case_insensitive(
            test_params, "spiltCount", "split_count"
        )
        split_length = self._get_param_case_insensitive(
            test_params, "splitLength", "split_length"
        )

        if not keyword:
            raise ValueError("keyWord parameter is required for keyword extraction")

        split_count = int(spilt_count) if spilt_count else 1
        split_length = int(split_length) if split_length else 10

        # Find keyword and extract following content
        match = re.search(f"{re.escape(keyword)}(.*)", response)
        if match:
            content = match.group(1)
            start_pos = split_count - 1  # Convert to 0-based index
            end_pos = start_pos + split_length
            if start_pos >= 0 and end_pos <= len(content):
                return content[start_pos:end_pos]

        raise ValueError(f"Could not extract value using keyword '{keyword}'")

    async def _cleanup_used_instruments(self, used_instruments: Dict[str, str]):
        """
        Cleanup instruments after test completion (PDTool4 style)
        """
        for instrument_location, script_name in used_instruments.items():
            try:
                script_path = f"./src/lowsheen_lib/{script_name}"
                test_params = {"Instrument": instrument_location}

                # 原有程式碼: 使用 python3 而非 python，確保在不同環境中都能執行
                await asyncio.create_subprocess_exec(
                    "python3",
                    script_path,
                    "--final",
                    str(test_params),
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                self.logger.info(f"Reset instrument {instrument_location}")

            except Exception as e:
                self.logger.warning(
                    f"Failed to reset instrument {instrument_location}: {e}"
                )

    async def validate_params(
        self, measurement_type: str, switch_mode: str, test_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate measurement parameters based on PDTool4 requirements
        """
        validation_rules = {
            "PowerSet": {
                "DAQ973A": ["Instrument", "Channel", "Item"],
                "MODEL2303": ["Instrument", "SetVolt", "SetCurr"],
                "MODEL2306": ["Instrument", "Channel", "SetVolt", "SetCurr"],
                "IT6723C": ["Instrument", "SetVolt", "SetCurr"],
                "PSW3072": ["Instrument", "SetVolt", "SetCurr"],
                "2260B": ["Instrument", "SetVolt", "SetCurr"],
                "APS7050": ["Instrument", "Channel", "SetVolt", "SetCurr"],
                "34970A": ["Instrument", "Channel", "Item"],
                "KEITHLEY2015": ["Instrument", "Command"],
            },
            "PowerRead": {
                "DAQ973A": ["Instrument", "Channel", "Item", "Type"],
                "34970A": ["Instrument", "Channel", "Item"],
                "2015": ["Instrument", "Command"],
                "6510": ["Instrument", "Item"],
                "APS7050": ["Instrument", "Item"],
                "MDO34": ["Instrument", "Channel", "Item"],
                "MT8870A_INF": ["Instrument", "Item"],
                "KEITHLEY2015": ["Instrument", "Command"],
            },
            "CommandTest": {
                "comport": ["Port", "Baud", "Command"],
                "tcpip": ["Host", "Port", "Command"],
                "console": ["Command"],
                "android_adb": ["Command"],
                "PEAK": ["Command"],
                # 自定義腳本模式 - 只要有 command 或 script_path 即可
                "custom": ["command"],  # command 欄位可選,如果沒有則使用 script_path
            },
            # 新增: 支援 measurement_type='command' (對應 case_type='command')
            "command": {
                "comport": ["Port", "Baud", "Command"],
                "console": ["Command"],
                "tcpip": ["Host", "Port", "Command"],
                "android_adb": ["Command"],
                "PEAK": ["Command"],
                "custom": ["command"],
            },
            # 新增: 直接支援 case_type 作為 measurement_type
            # 這些都使用與 CommandTest 相同的驗證規則
            "comport": {
                "comport": ["Port", "Baud", "Command"],
                "custom": ["command"],
            },
            "console": {
                "console": ["Command"],
                "custom": ["command"],
            },
            "tcpip": {
                "tcpip": ["Host", "Port", "Command"],
                "custom": ["command"],
            },
            "android_adb": {
                "android_adb": ["Command"],
                "custom": ["command"],
            },
            "PEAK": {
                "PEAK": ["Command"],
                "custom": ["command"],
            },
            "SFCtest": {
                "webStep1_2": [],
                "URLStep1_2": [],
                "skip": [],
                "WAIT_FIX_5sec": [],  # 原有程式碼: 新增 WAIT_FIX_5sec 支援,不需要任何參數
            },
            "getSN": {"SN": [], "IMEI": [], "MAC": []},
            "OPjudge": {"YorN": [], "confirm": []},
            # 新增: wait 測量類型支援
            "wait": {"wait": []},  # wait switch_mode 不需要任何參數
            # 新增: test123 測試腳本支援
            "Other": {
                "test123": [],  # test123.py 不需要任何必需參數，可選 arg 參數
                "custom": [],
                "WAIT_FIX_5sec": [],  # 原有程式碼: 新增 WAIT_FIX_5sec 支援,不需要任何參數
                "wait": [],  # 修改: 新增 wait 支援,用於 WAIT_DUT_restart_20 等待測試,不需要任何參數
            },
        }

        if measurement_type not in validation_rules:
            return {
                "valid": False,
                "missing_params": [],
                "invalid_params": [],
                "suggestions": [f"Unknown measurement type: {measurement_type}"],
            }

        if switch_mode not in validation_rules[measurement_type]:
            # 对于 CommandTest, command, comport, console 等,未知的 switch_mode 可能是自定義腳本
            if measurement_type in ["CommandTest", "command", "comport", "console", "tcpip", "android_adb", "PEAK"]:
                # 原有程式碼: 檢查是否有 command 或 script_path (僅檢查大寫)
                # 修改: 支援 case-insensitive 參數查找
                def has_parameter(param_name):
                    """Check if parameter exists (case-insensitive)"""
                    if param_name in test_params:
                        return True
                    if param_name.lower() in test_params:
                        return True
                    if param_name[0].upper() + param_name[1:] in test_params:
                        return True
                    return False

                if not has_parameter("command") and not has_parameter("script_path"):
                    return {
                        "valid": False,
                        "missing_params": ["command or script_path"],
                        "invalid_params": [],
                        "suggestions": [
                            f"Custom switch_mode '{switch_mode}' requires 'command' (script path from database) "
                            f"or 'script_path' in test_params. Use predefined modes: {list(validation_rules[measurement_type].keys())}"
                        ],
                    }
                else:
                    # 自定義腳本模式 - 參數檢查通過
                    return {
                        "valid": True,
                        "missing_params": [],
                        "invalid_params": [],
                        "suggestions": [],
                    }
            else:
                return {
                    "valid": False,
                    "missing_params": [],
                    "invalid_params": [],
                    "suggestions": [
                        f"Unknown switch mode '{switch_mode}' for {measurement_type}"
                    ],
                }

        required_params = validation_rules[measurement_type][switch_mode]

        # 原有程式碼: 對於 CommandTest 的 comport 和 console 模式，強制要求預設參數
        # 修改: 如果提供了 command 或 script_path 參數（自定義腳本），則跳過預設參數檢查
        # 這樣可以支援使用自定義腳本的 comport 和 console 測試項目
        # 同時支援 case-insensitive 參數查找 (command vs Command)

        def has_parameter(param_name):
            """Check if parameter exists (case-insensitive)"""
            if param_name in test_params:
                return True
            # 嘗試小寫版本
            if param_name.lower() in test_params:
                return True
            # 嘗試大寫版本
            if param_name[0].upper() + param_name[1:] in test_params:
                return True
            return False

        # 擴展支援的測量類型 (包括 case_type 直接作為 measurement_type 的情況)
        command_test_types = ["CommandTest", "command", "comport", "console", "tcpip", "android_adb", "PEAK"]

        if measurement_type in command_test_types and switch_mode in ["comport", "console", "tcpip", "android_adb", "PEAK"]:
            if has_parameter("command") or has_parameter("script_path"):
                # 自定義腳本模式 - 不檢查預設參數
                missing_params = []
            else:
                # 預設模式 - 檢查必要參數
                missing_params = [
                    param for param in required_params if not has_parameter(param)
                ]
        else:
            # 其他模式保持原有邏輯,但使用 case-insensitive 檢查
            missing_params = [
                param for param in required_params if not has_parameter(param)
            ]

        # Additional validation for CommandTest with keyword extraction
        if measurement_type in command_test_types and switch_mode in [
            "comport",
            "console",
            "tcpip",
            "PEAK",
        ]:
            if has_parameter("keyWord"):
                additional_required = ["spiltCount", "splitLength"]
                missing_params.extend(
                    [param for param in additional_required if not has_parameter(param)]
                )
            elif has_parameter("EqLimit"):
                # EqLimit doesn't require additional parameters beyond itself
                pass

        return {
            "valid": len(missing_params) == 0,
            "missing_params": missing_params,
            "invalid_params": [],
            "suggestions": [],
        }

    async def get_instrument_status(self) -> List[Dict[str, Any]]:
        """
        Get status of all configured instruments
        """
        # Placeholder - would interface with actual instrument manager
        return [
            {"id": "daq973a_1", "type": "DAQ973A", "status": "IDLE", "last_used": None},
            {
                "id": "model2303_1",
                "type": "MODEL2303",
                "status": "IDLE",
                "last_used": None,
            },
        ]

    async def reset_instrument(self, instrument_id: str) -> Dict[str, Any]:
        """
        Reset a specific instrument
        """
        # Find instrument type and call appropriate reset script
        if instrument_id.startswith("daq973a"):
            script_path = "./src/lowsheen_lib/DAQ973A_test.py"
        elif instrument_id.startswith("model2303"):
            script_path = "./src/lowsheen_lib/2303_test.py"
        else:
            raise Exception(f"Unknown instrument: {instrument_id}")

        test_params = {"Instrument": instrument_id}
        await self._execute_instrument_command(
            script_path=script_path, test_point_id="reset", test_params=test_params
        )

        return {"status": "IDLE"}

    async def get_session_results(
        self, session_id: int, db: Session
    ) -> List[Dict[str, Any]]:
        """
        Get measurement results for a session
        """
        if session_id in self.active_sessions:
            session_data = self.active_sessions[session_id]
            return [result.to_dict() for result in session_data["results"]]

        # Fallback to database query if session not in memory
        results = (
            db.query(TestResultModel)
            .filter(TestResultModel.test_session_id == session_id)
            .all()
        )

        return [
            {
                "test_point_id": result.id,
                "result": result.result,
                "measured_value": result.measured_value,
                "test_time": result.created_at.isoformat(),
            }
            for result in results
        ]

    async def _save_measurement_result(
        self, db: Session, session_id: int, result: MeasurementResult
    ):
        """
        Save measurement result to database
        """
        try:
            # 原有程式碼: measured_value=float(result.measured_value) if result.measured_value else None
            # 修改: 支援字串類型的 measured_value (例如: "Hello World!")
            # 將 measured_value 轉換為字串存儲到資料庫
            measured_value = result.measured_value
            if measured_value is not None:
                from decimal import Decimal

                if isinstance(measured_value, Decimal):
                    measured_value = str(float(measured_value))
                elif not isinstance(measured_value, str):
                    measured_value = str(measured_value)
                # 如果已經是字串，保持原樣

            db_result = TestResultModel(
                test_session_id=session_id,
                item_no=result.item_no,
                item_name=result.item_name,
                result=result.result,
                measured_value=measured_value,
                error_message=result.error_message,
                execution_duration_ms=result.execution_duration_ms,
            )

            db.add(db_result)
            db.commit()

        except Exception as e:
            self.logger.error(f"Failed to save measurement result: {e}")
            db.rollback()


# Global service instance
measurement_service = MeasurementService()
measurement_service = MeasurementService()
