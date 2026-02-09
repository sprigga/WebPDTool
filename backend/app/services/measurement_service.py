"""
Measurement Service
Core service implementing PDTool4 measurement execution logic

ARCHITECTURE UPDATE (2026-02-06):
- Refactored from dual-path (legacy subprocess + modern async) to single-path architecture
- All measurement execution now delegates to implementations.py classes
- Removed 1401 lines of duplicate legacy code (66.6% reduction: 2103 → 702 lines)
- execute_single_measurement() now uses get_measurement_class() exclusively
- Legacy subprocess helper (_execute_instrument_command) retained for backward compatibility only
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
from app.config.instruments import validate_params as validate_params_config

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

        # Legacy: Instrument reset mapping (equivalent to PDTool4's used_instruments cleanup)
        # TODO: This can be removed once all instruments use modern async drivers with proper cleanup
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
        Execute a single measurement using modern implementation classes.

        This method now delegates ALL measurements to implementations.py classes,
        eliminating the legacy subprocess-based execution paths.

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

            # Get measurement class from implementations.py
            measurement_class = get_measurement_class(measurement_type)

            if not measurement_class:
                return MeasurementResult(
                    item_no=0,
                    item_name=test_point_id,
                    result="ERROR",
                    error_message=f"Unknown measurement type: {measurement_type}",
                )

            # Create measurement instance
            # Note: Implementations expect test_plan_item dict with combined params
            # FIXED: Include item_no and item_name in test_plan_item dict per BaseMeasurement.__init__ signature
            test_plan_item = {
                **test_params,
                "switch_mode": switch_mode,
                "measurement_type": measurement_type,
                "item_no": 0,
                "item_name": test_point_id,
            }

            measurement = measurement_class(
                test_plan_item=test_plan_item,
                config={},  # Empty config dict for compatibility
            )

            # Execute measurement
            result = await measurement.execute()

            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            result.execution_duration_ms = int(execution_time)

            measured_value_str = str(result.measured_value) if result.measured_value is not None else "None"
            self.logger.info(
                f"Measurement {test_point_id} completed with result: {result.result}, measured_value: {measured_value_str}"
            )
            return result

        except Exception as e:
            self.logger.error(f"Measurement execution failed: {e}", exc_info=True)
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

    # =========================================================================
    # Legacy Subprocess Helper (Private - for backward compatibility only)
    # =========================================================================
    # NOTE: This method is kept as a private fallback for measurements that
    # haven't been fully migrated to async drivers yet. All measurement
    # execution should go through implementations.py classes instead.
    #
    # TODO: Remove this once all instruments have proper async drivers
    # =========================================================================

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

        原有程式碼: 100+ 行硬編碼的驗證規則字典
        修改: 優先使用 app.config.instruments.validate_params() 進行驗證
        保留: 舊版驗證邏輯作為後備 (支援尚未遷移到 MEASUREMENT_TEMPLATES 的測試類型)
        """
        # 嘗試使用配置文件的驗證邏輯
        config_validation = validate_params_config(measurement_type, switch_mode, test_params)

        # 如果配置文件中找到對應的模板，直接返回驗證結果
        # 檢查是否為「不支援的組合」錯誤
        is_unsupported = (
            config_validation.get("suggestions") and
            len(config_validation["suggestions"]) > 0 and
            config_validation["suggestions"][0].startswith("Unsupported combination")
        )

        # 如果驗證通過，或者是有效的失敗（有模板但參數不完整），直接返回配置驗證結果
        if config_validation["valid"] or (not is_unsupported and not config_validation["valid"]):
            return config_validation

        # 如果是「不支援的組合」，回退到舊版驗證邏輯
        # 這允許尚未遷移到 MEASUREMENT_TEMPLATES 的測試類型仍然可以驗證

        # 後備: 使用舊版硬編碼驗證規則 (支援尚未遷移的測試類型)
        # TODO: 將以下所有規則遷移到 MEASUREMENT_TEMPLATES 後可移除此段
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
            "OPjudge": {
                "YorN": ["TestParams"],  # Requires TestParams list with ImagePath and content
                "confirm": ["TestParams"],  # Requires TestParams list with ImagePath and content
            },
            # 新增: wait 測量類型支援
            "wait": {"wait": []},  # wait switch_mode 不需要任何參數
            "Wait": {"wait": []},  # 支援大寫 Wait
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
            # 修正: 對於 "Other" 測量類型,未知的 switch_mode 也視為有效的自定義腳本
            # 這樣可以支援 test123.py, 123_1.py, 123_2.py 等自定義測試腳本
            # 不需要在 validation_rules 中預先定義每個腳本名稱
            elif measurement_type in ["Other", "wait", "Wait"]:
                # Other 和 wait 類型允許任意 switch_mode (自定義腳本名稱)
                # 不需要任何必需參數
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

        # 返回後備驗證結果
        # 注意: 此結果僅在配置文件沒有對應模板時使用
        return {
            "valid": len(missing_params) == 0,
            "missing_params": missing_params,
            "invalid_params": [],
            "suggestions": [] if len(missing_params) == 0 else [
                f"Legacy validation used. Consider migrating '{measurement_type}/{switch_mode}' to MEASUREMENT_TEMPLATES"
            ],
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
