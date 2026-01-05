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
            'PowerSet': self._execute_power_set,
            'PowerRead': self._execute_power_read,
            'CommandTest': self._execute_command_test,
            'SFCtest': self._execute_sfc_test,
            'getSN': self._execute_get_sn,
            'OPjudge': self._execute_op_judge,
            'Other': self._execute_other,
            'Final': self._execute_final
        }
        
        # Instrument reset mapping (equivalent to PDTool4's used_instruments cleanup)
        self.instrument_reset_map = {
            'DAQ973A': 'DAQ973A_test.py',
            'MODEL2303': '2303_test.py',
            'MODEL2306': '2306_test.py',
            'IT6723C': 'IT6723C.py',
            'PSW3072': 'PSW3072.py',
            '2260B': '2260B.py',
            'APS7050': 'APS7050.py',
            '34970A': '34970A.py',
            'KEITHLEY2015': 'Keithley2015.py',
            'DAQ6510': 'DAQ6510.py',
            'MDO34': 'MDO34.py',
            'MT8872A_INF': 'MT8872A_INF.py'
        }
        
    async def execute_single_measurement(
        self,
        measurement_type: str,
        test_point_id: str, 
        switch_mode: str,
        test_params: Dict[str, Any],
        run_all_test: bool = False,
        user_id: Optional[str] = None
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
            self.logger.info(f"Executing {measurement_type} measurement for {test_point_id}")
            
            # Validate parameters
            validation_result = await self.validate_params(measurement_type, switch_mode, test_params)
            if not validation_result["valid"]:
                return MeasurementResult(
                    item_no=0,
                    item_name=test_point_id,
                    result="ERROR",
                    error_message=f"Invalid parameters: {validation_result['missing_params']}"
                )
            
            # Get measurement executor
            if measurement_type not in self.measurement_dispatch:
                return MeasurementResult(
                    item_no=0,
                    item_name=test_point_id,
                    result="ERROR", 
                    error_message=f"Unknown measurement type: {measurement_type}"
                )
            
            # Execute measurement
            executor = self.measurement_dispatch[measurement_type]
            result = await executor(
                test_point_id=test_point_id,
                switch_mode=switch_mode,
                test_params=test_params,
                run_all_test=run_all_test
            )
            
            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            result.execution_duration_ms = int(execution_time)
            
            self.logger.info(f"Measurement {test_point_id} completed with result: {result.result}")
            return result
            
        except Exception as e:
            self.logger.error(f"Measurement execution failed: {e}")
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            return MeasurementResult(
                item_no=0,
                item_name=test_point_id,
                result="ERROR",
                error_message=str(e),
                execution_duration_ms=int(execution_time)
            )
    
    async def execute_batch_measurements(
        self,
        session_id: int,
        measurements: List[Dict[str, Any]],
        stop_on_fail: bool = True,
        run_all_test: bool = False,
        user_id: Optional[str] = None,
        db: Optional[Session] = None
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
                self.logger.info("PDTool4 runAllTest mode: ENABLED - will continue on errors")

            # Initialize session tracking
            self.active_sessions[session_id] = {
                "status": "RUNNING",
                "current_index": 0,
                "total_count": len(measurements),
                "results": [],
                "test_results": {},  # PDTool4-style result collection
                "errors": [],  # 收集所有錯誤 (runAllTest 模式)
                "run_all_test": run_all_test
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
                    run_all_test=run_all_test or measurement_request.get("run_all_test", False),
                    user_id=user_id
                )

                # Store result
                session_data["results"].append(result)
                session_data["test_results"][measurement_request["test_point_id"]] = result.measured_value

                # PDTool4 runAllTest: 收集錯誤但不停止
                if result.result == "ERROR":
                    error_msg = f"Item {result.item_name}: {result.error_message}"
                    session_data["errors"].append(error_msg)
                    if run_all_test:
                        self.logger.warning(f"[runAllTest] Error at {result.item_name}: {result.error_message} - Continuing...")

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
                        self.logger.warning(f"Stopping batch execution due to failure at {result.item_name}")
                        session_data["status"] = "FAILED"
                        should_stop = True

                if result.result == "ERROR":
                    # runAllTest 模式下，ERROR 不會停止執行
                    if not run_all_test and not stop_on_fail:
                        self.logger.error(f"Stopping batch execution due to error at {result.item_name}")
                        session_data["status"] = "ERROR"
                        should_stop = True

                if should_stop:
                    break

            # Complete session if not stopped
            if session_data["status"] == "RUNNING":
                session_data["status"] = "COMPLETED"
                self.logger.info(f"Batch execution completed successfully")

            # Cleanup instruments (PDTool4 style)
            await self._cleanup_used_instruments(session_data.get("used_instruments", {}))

            # Log summary
            total_errors = len(session_data.get("errors", []))
            if run_all_test and total_errors > 0:
                self.logger.warning(f"[runAllTest] Completed with {total_errors} errors")
                for err in session_data["errors"][:5]:  # 只顯示前 5 個錯誤
                    self.logger.warning(f"  - {err}")

            self.logger.info(f"Batch execution for session {session_id} completed with status: {session_data['status']}")

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
        run_all_test: bool
    ) -> MeasurementResult:
        """
        Execute power setting measurement (based on PowerSetMeasurement.py)
        """
        try:
            if switch_mode in ['DAQ973A', '34970A', 'APS7050', 'DAQ6510']:
                # Validate required parameters
                required_params = ['Instrument', 'Channel', 'Item']
                missing = [p for p in required_params if p not in test_params]
                if missing:
                    return MeasurementResult(
                        item_no=0,
                        item_name=test_point_id,
                        result="ERROR",
                        error_message=f"Missing parameters: {missing}"
                    )

                # Map switch mode to script file
                script_map = {
                    'DAQ973A': 'DAQ973A_test.py',
                    '34970A': '34970A.py',
                    'APS7050': 'APS7050.py',
                    'DAQ6510': 'DAQ6510.py'
                }

                # Execute instrument command via subprocess (PDTool4 style)
                result = await self._execute_instrument_command(
                    script_path=f'./src/lowsheen_lib/{script_map[switch_mode]}',
                    test_point_id=test_point_id,
                    test_params=test_params
                )

                # Process response
                if '1' in result:
                    return MeasurementResult(
                        item_no=0,
                        item_name=test_point_id,
                        result="PASS",
                        measured_value=Decimal('1')
                    )
                else:
                    return MeasurementResult(
                        item_no=0,
                        item_name=test_point_id,
                        result="FAIL",
                        measured_value=Decimal('0')
                    )

            elif switch_mode in ['MODEL2303', 'MODEL2306', '2260B', 'IT6723C', 'PSW3072']:
                # Similar implementation for power supplies
                required_params = ['Instrument', 'SetVolt', 'SetCurr']
                missing = [p for p in required_params if p not in test_params]
                if missing:
                    return MeasurementResult(
                        item_no=0,
                        item_name=test_point_id,
                        result="ERROR",
                        error_message=f"Missing parameters: {missing}"
                    )

                # Map switch mode to script file
                script_map = {
                    'MODEL2303': '2303_test.py',
                    'MODEL2306': '2306_test.py',
                    '2260B': '2260B.py',
                    'IT6723C': 'IT6723C.py',
                    'PSW3072': 'PSW3072.py'
                }

                result = await self._execute_instrument_command(
                    script_path=f'./src/lowsheen_lib/{script_map[switch_mode]}',
                    test_point_id=test_point_id,
                    test_params=test_params
                )

                return MeasurementResult(
                    item_no=0,
                    item_name=test_point_id,
                    result="PASS" if "success" in result.lower() else "FAIL"
                )

            elif switch_mode == 'KEITHLEY2015':
                required_params = ['Instrument', 'Command']
                missing = [p for p in required_params if p not in test_params]
                if missing:
                    return MeasurementResult(
                        item_no=0,
                        item_name=test_point_id,
                        result="ERROR",
                        error_message=f"Missing parameters: {missing}"
                    )

                result = await self._execute_instrument_command(
                    script_path='./src/lowsheen_lib/Keithley2015.py',
                    test_point_id=test_point_id,
                    test_params=test_params
                )

                return MeasurementResult(
                    item_no=0,
                    item_name=test_point_id,
                    result="PASS" if "success" in result.lower() else "FAIL"
                )

            else:
                return MeasurementResult(
                    item_no=0,
                    item_name=test_point_id,
                    result="ERROR",
                    error_message=f"Unsupported switch mode: {switch_mode}"
                )

        except Exception as e:
            return MeasurementResult(
                item_no=0,
                item_name=test_point_id,
                result="ERROR",
                error_message=str(e)
            )
    
    async def _execute_power_read(
        self,
        test_point_id: str,
        switch_mode: str,
        test_params: Dict[str, Any],
        run_all_test: bool
    ) -> MeasurementResult:
        """
        Execute power reading measurement (based on PowerReadMeasurement.py)
        """
        try:
            if switch_mode in ['DAQ973A', '34970A', 'DAQ6510', 'MDO34']:
                required_params = ['Instrument', 'Channel', 'Item']
                # Add 'Type' parameter only for DAQ973A if Item is volt or curr
                if switch_mode == 'DAQ973A' and ('Item' in test_params and (test_params['Item'] == 'volt' or test_params['Item'] == 'curr')):
                    required_params.append('Type')

                missing = [p for p in required_params if p not in test_params]
                if missing:
                    return MeasurementResult(
                        item_no=0,
                        item_name=test_point_id,
                        result="ERROR",
                        error_message=f"Missing parameters: {missing}"
                    )

                # Map switch mode to script file
                script_map = {
                    'DAQ973A': 'DAQ973A_test.py',
                    '34970A': '34970A.py',
                    'DAQ6510': 'DAQ6510.py',
                    'MDO34': 'MDO34.py'
                }

                result = await self._execute_instrument_command(
                    script_path=f'./src/lowsheen_lib/{script_map[switch_mode]}',
                    test_point_id=test_point_id,
                    test_params=test_params
                )

                # Parse numeric result
                try:
                    # Clean up result string
                    cleaned_result = result.replace('\n', '').replace('\r', '').strip()
                    measured_value = Decimal(str(float(cleaned_result)))
                    return MeasurementResult(
                        item_no=0,
                        item_name=test_point_id,
                        result="PASS",  # Will be validated against limits later
                        measured_value=measured_value
                    )
                except (ValueError, TypeError):
                    return MeasurementResult(
                        item_no=0,
                        item_name=test_point_id,
                        result="ERROR",
                        error_message=f"Invalid measurement result: {result}"
                    )

            elif switch_mode in ['APS7050', 'KEITHLEY2015']:
                if switch_mode == 'KEITHLEY2015':
                    required_params = ['Instrument', 'Command']
                else:
                    required_params = ['Instrument', 'Item']  # For APS7050

                missing = [p for p in required_params if p not in test_params]
                if missing:
                    return MeasurementResult(
                        item_no=0,
                        item_name=test_point_id,
                        result="ERROR",
                        error_message=f"Missing parameters: {missing}"
                    )

                # Map switch mode to script file
                script_map = {
                    'APS7050': 'APS7050.py',
                    'KEITHLEY2015': 'Keithley2015.py'
                }

                result = await self._execute_instrument_command(
                    script_path=f'./src/lowsheen_lib/{script_map[switch_mode]}',
                    test_point_id=test_point_id,
                    test_params=test_params
                )

                # Parse numeric result
                try:
                    # Clean up result string
                    cleaned_result = result.replace('\n', '').replace('\r', '').strip()
                    measured_value = Decimal(str(float(cleaned_result)))
                    return MeasurementResult(
                        item_no=0,
                        item_name=test_point_id,
                        result="PASS",  # Will be validated against limits later
                        measured_value=measured_value
                    )
                except (ValueError, TypeError):
                    return MeasurementResult(
                        item_no=0,
                        item_name=test_point_id,
                        result="ERROR",
                        error_message=f"Invalid measurement result: {result}"
                    )

            elif switch_mode == 'MT8870A_INF':
                required_params = ['Instrument', 'Item']
                missing = [p for p in required_params if p not in test_params]
                if missing:
                    return MeasurementResult(
                        item_no=0,
                        item_name=test_point_id,
                        result="ERROR",
                        error_message=f"Missing parameters: {missing}"
                    )

                result = await self._execute_instrument_command(
                    script_path='./src/lowsheen_lib/RF_tool/MT8872A_INF.py',
                    test_point_id=test_point_id,
                    test_params=test_params
                )

                # Parse numeric result
                try:
                    # Clean up result string
                    cleaned_result = result.replace('\n', '').replace('\r', '').strip()
                    measured_value = Decimal(str(float(cleaned_result)))
                    return MeasurementResult(
                        item_no=0,
                        item_name=test_point_id,
                        result="PASS",  # Will be validated against limits later
                        measured_value=measured_value
                    )
                except (ValueError, TypeError):
                    return MeasurementResult(
                        item_no=0,
                        item_name=test_point_id,
                        result="ERROR",
                        error_message=f"Invalid measurement result: {result}"
                    )

            else:
                return MeasurementResult(
                    item_no=0,
                    item_name=test_point_id,
                    result="ERROR",
                    error_message=f"Unsupported switch mode: {switch_mode}"
                )

        except Exception as e:
            return MeasurementResult(
                item_no=0,
                item_name=test_point_id,
                result="ERROR",
                error_message=str(e)
            )
    
    async def _execute_command_test(
        self,
        test_point_id: str,
        switch_mode: str,
        test_params: Dict[str, Any],
        run_all_test: bool
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
            # 定義預設的腳本映射和必要參數
            script_config = {
                'comport': {
                    'script': 'ComPortCommand.py',
                    'required_params': ['Port', 'Baud', 'Command']
                },
                'console': {
                    'script': 'ConSoleCommand.py',
                    'required_params': ['Command']
                },
                'tcpip': {
                    'script': 'TCPIPCommand.py',
                    'required_params': ['Command']
                },
                'PEAK': {
                    'script': 'PEAK_API/PEAK.py',
                    'required_params': ['Command']
                },
                'android_adb': {
                    'script': 'AndroidAdbCommand.py',
                    'required_params': ['Command']
                }
            }

            # 檢查是否為預設的 switch_mode
            if switch_mode in script_config:
                config = script_config[switch_mode]
                script_file = config['script']
                required_params = config['required_params'].copy()

                # 檢查必要參數
                missing = [p for p in required_params if p not in test_params or not test_params[p]]
                if missing:
                    return MeasurementResult(
                        item_no=0,
                        item_name=test_point_id,
                        result="ERROR",
                        error_message=f"Missing required parameters: {missing}"
                    )

                # 添加條件參數到必要參數列表
                if 'keyWord' in test_params:
                    required_params.extend(['keyWord', 'spiltCount', 'splitLength'])
                elif 'EqLimit' in test_params:
                    required_params.append('EqLimit')

                # 執行預設腳本
                result = await self._execute_instrument_command(
                    script_path=f'./src/lowsheen_lib/{script_file}',
                    test_point_id=test_point_id,
                    test_params=test_params
                )

                # 處理輸出結果
                return self._process_command_result(result, test_params, test_point_id)

            # 支援自定義腳本 (從資料庫 command 欄位讀取)
            else:
                # 優先級 1: 使用 test_params 中明確指定的 script_path
                script_path = test_params.get('script_path')

                # 優先級 2: 使用 test_params 中的 command (來自資料庫 test_plans.command)
                if not script_path:
                    script_path = test_params.get('command')

                # 如果都沒有，返回錯誤
                if not script_path:
                    return MeasurementResult(
                        item_no=0,
                        item_name=test_point_id,
                        result="ERROR",
                        error_message=f"No script path specified for CommandTest with switch_mode='{switch_mode}'. "
                                     f"Please provide 'script_path' or 'command' in test_params, "
                                     f"or use a predefined switch_mode: {list(script_config.keys())}"
                    )

                # 檢查腳本檔案是否存在
                import os
                if not os.path.exists(script_path):
                    # 嘗試相對於 backend 目錄的路徑
                    relative_path = os.path.join('/home/ubuntu/WebPDTool/backend', script_path)
                    if os.path.exists(relative_path):
                        script_path = relative_path
                    else:
                        return MeasurementResult(
                            item_no=0,
                            item_name=test_point_id,
                            result="ERROR",
                            error_message=f"Script not found: {script_path}"
                        )

                # 執行自訂腳本
                self.logger.info(f"Executing custom script: {script_path} for {test_point_id}")
                result = await self._execute_instrument_command(
                    script_path=script_path,
                    test_point_id=test_point_id,
                    test_params=test_params
                )

                # 處理輸出結果
                return self._process_command_result(result, test_params, test_point_id)

        except Exception as e:
            self.logger.error(f"CommandTest execution failed: {e}")
            return MeasurementResult(
                item_no=0,
                item_name=test_point_id,
                result="ERROR",
                error_message=str(e)
            )

    def _process_command_result(
        self,
        result: str,
        test_params: Dict[str, Any],
        test_point_id: str
    ) -> MeasurementResult:
        """
        處理 CommandTest 的執行結果 (仿照 PDTool4 CommandTestMeasurement.py)

        支援三種結果處理方式:
        1. keyWord: 關鍵字提取
        2. EqLimit: 等於限制值檢查
        3. default: 基本回應檢查
        """
        try:
            # 模式 1: 關鍵字提取 (keyWord + spiltCount + splitLength)
            if 'keyWord' in test_params and test_params['keyWord']:
                processed_result = self._process_keyword_extraction(result, test_params)
                try:
                    measured_value = Decimal(str(float(processed_result)))
                    return MeasurementResult(
                        item_no=0,
                        item_name=test_point_id,
                        result="PASS",
                        measured_value=measured_value
                    )
                except (ValueError, TypeError):
                    return MeasurementResult(
                        item_no=0,
                        item_name=test_point_id,
                        result="ERROR",
                        error_message=f"Could not parse extracted value: {processed_result}"
                    )

            # 模式 2: 等於限制值檢查 (EqLimit)
            elif 'EqLimit' in test_params and test_params['EqLimit']:
                # 提取包含 EqLimit 的行
                lines = result.replace('\r\n', '\n').split('\n')
                eq_limit_val = test_params['EqLimit']
                found_line = ""

                for line in lines:
                    if eq_limit_val in line:
                        found_line = line.strip()
                        break

                if not found_line:
                    # 尋找錯誤條件
                    for line in lines:
                        if "Failed" in line or "Error" in line:
                            found_line = line.strip()
                            break
                    if not found_line:
                        found_line = f"[{eq_limit_val}] not found in output"

                return MeasurementResult(
                    item_no=0,
                    item_name=test_point_id,
                    result="PASS" if "Failed" not in found_line and "Error" not in found_line else "FAIL",
                    error_message=found_line if ("Failed" in found_line or "Error" in found_line) else None
                )

            # 模式 3: 基本回應檢查 (default)
            else:
                # 清理輸出結果
                cleaned_result = result.replace('\n', '').replace('\r', '').strip()

                # 檢查是否為空輸出
                if not cleaned_result or cleaned_result == "console output is empty":
                    # 如果 LimitType 是 none，則空輸出也算 PASS
                    if test_params.get('LimitType') == 'none':
                        return MeasurementResult(
                            item_no=0,
                            item_name=test_point_id,
                            result="PASS",
                            measured_value=None
                        )
                    return MeasurementResult(
                        item_no=0,
                        item_name=test_point_id,
                        result="FAIL",
                        error_message="Empty output"
                    )

                # 嘗試解析為數值
                try:
                    measured_value = Decimal(str(float(cleaned_result)))
                    return MeasurementResult(
                        item_no=0,
                        item_name=test_point_id,
                        result="PASS",
                        measured_value=measured_value
                    )
                except (ValueError, TypeError):
                    # 無法解析為數值，返回字串作為 PASS
                    return MeasurementResult(
                        item_no=0,
                        item_name=test_point_id,
                        result="PASS",
                        measured_value=None,
                        error_message=f"Output: {cleaned_result}"
                    )

        except Exception as e:
            self.logger.error(f"Failed to process command result: {e}")
            return MeasurementResult(
                item_no=0,
                item_name=test_point_id,
                result="ERROR",
                error_message=f"Result processing failed: {str(e)}"
            )
    
    async def _execute_sfc_test(
        self,
        test_point_id: str,
        switch_mode: str,
        test_params: Dict[str, Any],
        run_all_test: bool
    ) -> MeasurementResult:
        """
        Execute SFC test measurement (based on SFC_GONOGOMeasurement.py)
        """
        try:
            # Placeholder for SFC integration - would need actual SFC service
            if switch_mode in ['webStep1_2', 'URLStep1_2']:
                # Simulate SFC call
                await asyncio.sleep(0.1)  # Simulate network delay
                
                return MeasurementResult(
                    item_no=0,
                    item_name=test_point_id,
                    result="PASS",  # Would be based on actual SFC response
                    measured_value=Decimal('1')
                )
            elif switch_mode == 'skip':
                return MeasurementResult(
                    item_no=0,
                    item_name=test_point_id,
                    result="SKIP"
                )
            else:
                return MeasurementResult(
                    item_no=0,
                    item_name=test_point_id,
                    result="ERROR",
                    error_message=f"Unsupported SFC switch mode: {switch_mode}"
                )
                
        except Exception as e:
            return MeasurementResult(
                item_no=0,
                item_name=test_point_id,
                result="ERROR",
                error_message=str(e)
            )
    
    async def _execute_get_sn(
        self,
        test_point_id: str,
        switch_mode: str,
        test_params: Dict[str, Any],
        run_all_test: bool
    ) -> MeasurementResult:
        """
        Execute serial number acquisition (based on getSNMeasurement.py)
        """
        try:
            # Placeholder implementation - would read from actual source
            if switch_mode in ['SN', 'IMEI', 'MAC']:
                # Simulate reading serial number
                serial_number = test_params.get('serial_number', 'TEST123456')
                
                return MeasurementResult(
                    item_no=0,
                    item_name=test_point_id,
                    result="PASS",
                    measured_value=None  # SN is text, not numeric
                )
            else:
                return MeasurementResult(
                    item_no=0,
                    item_name=test_point_id,
                    result="ERROR",
                    error_message=f"Unsupported SN switch mode: {switch_mode}"
                )
                
        except Exception as e:
            return MeasurementResult(
                item_no=0,
                item_name=test_point_id,
                result="ERROR",
                error_message=str(e)
            )
    
    async def _execute_op_judge(
        self,
        test_point_id: str,
        switch_mode: str,
        test_params: Dict[str, Any],
        run_all_test: bool
    ) -> MeasurementResult:
        """
        Execute operator judgment measurement (based on OPjudgeMeasurement.py)
        """
        try:
            # In real implementation, this would prompt operator
            # For API, we expect the judgment to be passed in test_params
            judgment = test_params.get('operator_judgment', 'PASS')
            
            return MeasurementResult(
                item_no=0,
                item_name=test_point_id,
                result=judgment,
                measured_value=Decimal('1') if judgment == 'PASS' else Decimal('0')
            )
                
        except Exception as e:
            return MeasurementResult(
                item_no=0,
                item_name=test_point_id,
                result="ERROR",
                error_message=str(e)
            )
    
    async def _execute_other(
        self,
        test_point_id: str,
        switch_mode: str,
        test_params: Dict[str, Any],
        run_all_test: bool
    ) -> MeasurementResult:
        """
        Execute other/custom measurements (based on OtherMeasurement.py)

        支援執行自定義 Python 測試腳本，腳本路徑從資料庫 test_plans 表的 command 欄位獲取

        參數說明:
        - switch_mode: 腳本類型或自定義識別符 (例如: 'test123', 'custom_script')
        - test_params['script_path']: 腳本完整路徑 (優先使用，如果提供)
        - test_params['command']: 從資料庫 command 欄位傳入的腳本路徑 (次選)
        - test_params['arg']: 傳遞給腳本的命令行參數 (可選)
        """
        try:
            # 優先級 1: 使用 test_params 中明確指定的 script_path
            script_path = test_params.get('script_path')

            # 優先級 2: 使用 test_params 中的 command (來自資料庫 test_plans.command)
            if not script_path:
                script_path = test_params.get('command')

            # 優先級 3: 如果是 test123，使用預設路徑 (向後相容)
            if not script_path and switch_mode == 'test123':
                script_path = './scripts/test123.py'

            # 如果都沒有，返回錯誤
            if not script_path:
                return MeasurementResult(
                    item_no=0,
                    item_name=test_point_id,
                    result="ERROR",
                    error_message=f"No script path specified. Please provide 'script_path' or 'command' in test_params, or set command in database test_plans table."
                )

            # 原有程式碼: 構建命令行參數
            # 原始腳本邏輯: 如果第一個參數是 '123'，輸出 '456'，否則輸出 '123'
            command = ['python', script_path]

            # 如果有指定參數，則傳入
            if 'arg' in test_params:
                command.append(test_params['arg'])

            # 執行腳本
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=30,
                cwd='/home/ubuntu/WebPDTool/backend'
            )

            if result.returncode != 0:
                return MeasurementResult(
                    item_no=0,
                    item_name=test_point_id,
                    result="ERROR",
                    error_message=f"Script failed: {result.stderr}"
                )

            # 解析輸出
            output = result.stdout.strip()

            # 原有程式碼: 根據輸出決定結果
            # 123.py 邏輯: 參數為 '123' 時輸出 '456'，否則輸出 '123'
            if output == '456':
                return MeasurementResult(
                    item_no=0,
                    item_name=test_point_id,
                    result="PASS",
                    measured_value=Decimal('456')
                )
            elif output == '123':
                return MeasurementResult(
                    item_no=0,
                    item_name=test_point_id,
                    result="PASS",
                    measured_value=Decimal('123')
                )
            # 嘗試解析為數字 (通用處理)
            else:
                try:
                    numeric_value = Decimal(str(float(output)))
                    return MeasurementResult(
                        item_no=0,
                        item_name=test_point_id,
                        result="PASS",
                        measured_value=numeric_value
                    )
                except (ValueError, TypeError):
                    # 如果無法解析為數字，返回原始輸出作為 PASS
                    return MeasurementResult(
                        item_no=0,
                        item_name=test_point_id,
                        result="PASS",
                        error_message=f"Script output: {output}"
                    )

        except subprocess.TimeoutExpired:
            return MeasurementResult(
                item_no=0,
                item_name=test_point_id,
                result="ERROR",
                error_message="Script timeout"
            )
        except FileNotFoundError:
            return MeasurementResult(
                item_no=0,
                item_name=test_point_id,
                result="ERROR",
                error_message=f"Script not found: {script_path}"
            )
        except Exception as e:
            return MeasurementResult(
                item_no=0,
                item_name=test_point_id,
                result="ERROR",
                error_message=str(e)
            )
    
    async def _execute_final(
        self,
        test_point_id: str,
        switch_mode: str,
        test_params: Dict[str, Any],
        run_all_test: bool
    ) -> MeasurementResult:
        """
        Execute final measurement/cleanup (based on FinalMeasurement.py)
        """
        try:
            # Perform any final cleanup or validation
            return MeasurementResult(
                item_no=0,
                item_name=test_point_id,
                result="PASS"
            )
                
        except Exception as e:
            return MeasurementResult(
                item_no=0,
                item_name=test_point_id,
                result="ERROR",
                error_message=str(e)
            )
    
    async def _execute_instrument_command(
        self,
        script_path: str,
        test_point_id: str,
        test_params: Dict[str, Any]
    ) -> str:
        """
        Execute instrument command via subprocess (PDTool4 style)
        """
        try:
            # Convert test_params to string format expected by PDTool4 scripts
            params_str = str(test_params)
            
            # Execute command
            result = subprocess.run(
                ['python', script_path, test_point_id, params_str],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 10:
                raise Exception("No instrument found")
            elif result.returncode != 0:
                raise Exception(f"Command failed with return code {result.returncode}: {result.stderr}")
            
            return result.stdout.strip()
            
        except subprocess.TimeoutExpired:
            raise Exception("Command timeout")
        except FileNotFoundError:
            raise Exception(f"Script not found: {script_path}")
        except Exception as e:
            raise Exception(f"Command execution failed: {str(e)}")
    
    def _process_keyword_extraction(self, response: str, test_params: Dict[str, Any]) -> str:
        """
        Process keyword extraction from response (PDTool4 CommandTest logic)
        """
        import re
        
        keyword = test_params['keyWord']
        split_count = int(test_params['spiltCount'])
        split_length = int(test_params['splitLength'])
        
        # Find keyword and extract following content
        match = re.search(f'{re.escape(keyword)}(.*)', response)
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
                script_path = f'./src/lowsheen_lib/{script_name}'
                test_params = {'Instrument': instrument_location}
                
                await asyncio.create_subprocess_exec(
                    'python', script_path, '--final', str(test_params),
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL
                )
                self.logger.info(f"Reset instrument {instrument_location}")
                
            except Exception as e:
                self.logger.warning(f"Failed to reset instrument {instrument_location}: {e}")
    
    async def validate_params(
        self,
        measurement_type: str,
        switch_mode: str,
        test_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate measurement parameters based on PDTool4 requirements
        """
        validation_rules = {
            'PowerSet': {
                'DAQ973A': ['Instrument', 'Channel', 'Item'],
                'MODEL2303': ['Instrument', 'SetVolt', 'SetCurr'],
                'MODEL2306': ['Instrument', 'Channel', 'SetVolt', 'SetCurr'],
                'IT6723C': ['Instrument', 'SetVolt', 'SetCurr'],
                'PSW3072': ['Instrument', 'SetVolt', 'SetCurr'],
                '2260B': ['Instrument', 'SetVolt', 'SetCurr'],
                'APS7050': ['Instrument', 'Channel', 'SetVolt', 'SetCurr'],
                '34970A': ['Instrument', 'Channel', 'Item'],
                'KEITHLEY2015': ['Instrument', 'Command']
            },
            'PowerRead': {
                'DAQ973A': ['Instrument', 'Channel', 'Item', 'Type'],
                '34970A': ['Instrument', 'Channel', 'Item'],
                '2015': ['Instrument', 'Command'],
                '6510': ['Instrument', 'Item'],
                'APS7050': ['Instrument', 'Item'],
                'MDO34': ['Instrument', 'Channel', 'Item'],
                'MT8870A_INF': ['Instrument', 'Item'],
                'KEITHLEY2015': ['Instrument', 'Command']
            },
            'CommandTest': {
                'comport': ['Port', 'Baud', 'Command'],
                'tcpip': ['Host', 'Port', 'Command'],
                'console': ['Command'],
                'android_adb': ['Command'],
                'PEAK': ['Command'],
                # 自定義腳本模式 - 只要有 command 或 script_path 即可
                'custom': ['command']  # command 欄位可選,如果沒有則使用 script_path
            },
            'SFCtest': {
                'webStep1_2': [],
                'URLStep1_2': [],
                'skip': []
            },
            'getSN': {
                'SN': [],
                'IMEI': [],
                'MAC': []
            },
            'OPjudge': {
                'YorN': [],
                'confirm': []
            },
            # 新增: test123 測試腳本支援
            'Other': {
                'test123': [],  # test123.py 不需要任何必需參數，可選 arg 參數
                'custom': []
            }
        }
        
        if measurement_type not in validation_rules:
            return {
                "valid": False,
                "missing_params": [],
                "invalid_params": [],
                "suggestions": [f"Unknown measurement type: {measurement_type}"]
            }
        
        if switch_mode not in validation_rules[measurement_type]:
            # 对于 CommandTest,未知的 switch_mode 可能是自定義腳本
            if measurement_type == 'CommandTest':
                # 檢查是否有 command 或 script_path
                if 'command' not in test_params and 'script_path' not in test_params:
                    return {
                        "valid": False,
                        "missing_params": ['command or script_path'],
                        "invalid_params": [],
                        "suggestions": [
                            f"Custom switch_mode '{switch_mode}' requires 'command' (script path from database) "
                            f"or 'script_path' in test_params. Use predefined modes: {list(validation_rules[measurement_type].keys())}"
                        ]
                    }
                else:
                    # 自定義腳本模式 - 參數檢查通過
                    return {
                        "valid": True,
                        "missing_params": [],
                        "invalid_params": [],
                        "suggestions": []
                    }
            else:
                return {
                    "valid": False,
                    "missing_params": [],
                    "invalid_params": [],
                    "suggestions": [f"Unknown switch mode '{switch_mode}' for {measurement_type}"]
                }
        
        required_params = validation_rules[measurement_type][switch_mode]
        missing_params = [param for param in required_params if param not in test_params]
        
        # Additional validation for CommandTest with keyword extraction
        if measurement_type == 'CommandTest' and switch_mode in ['comport', 'console', 'tcpip', 'PEAK']:
            if 'keyWord' in test_params:
                additional_required = ['spiltCount', 'splitLength']
                missing_params.extend([param for param in additional_required if param not in test_params])
            elif 'EqLimit' in test_params:
                # EqLimit doesn't require additional parameters beyond itself
                pass
        
        return {
            "valid": len(missing_params) == 0,
            "missing_params": missing_params,
            "invalid_params": [],
            "suggestions": []
        }
    
    async def get_instrument_status(self) -> List[Dict[str, Any]]:
        """
        Get status of all configured instruments
        """
        # Placeholder - would interface with actual instrument manager
        return [
            {
                "id": "daq973a_1",
                "type": "DAQ973A",
                "status": "IDLE",
                "last_used": None
            },
            {
                "id": "model2303_1", 
                "type": "MODEL2303",
                "status": "IDLE",
                "last_used": None
            }
        ]
    
    async def reset_instrument(self, instrument_id: str) -> Dict[str, Any]:
        """
        Reset a specific instrument
        """
        # Find instrument type and call appropriate reset script
        if instrument_id.startswith('daq973a'):
            script_path = './src/lowsheen_lib/DAQ973A_test.py'
        elif instrument_id.startswith('model2303'):
            script_path = './src/lowsheen_lib/2303_test.py'
        else:
            raise Exception(f"Unknown instrument: {instrument_id}")
        
        test_params = {'Instrument': instrument_id}
        await self._execute_instrument_command(
            script_path=script_path,
            test_point_id="reset",
            test_params=test_params
        )
        
        return {"status": "IDLE"}
    
    async def get_session_results(self, session_id: int, db: Session) -> List[Dict[str, Any]]:
        """
        Get measurement results for a session
        """
        if session_id in self.active_sessions:
            session_data = self.active_sessions[session_id]
            return [result.to_dict() for result in session_data["results"]]
        
        # Fallback to database query if session not in memory
        results = db.query(TestResultModel).filter(
            TestResultModel.test_session_id == session_id
        ).all()
        
        return [
            {
                "test_point_id": result.id,
                "result": result.result,
                "measured_value": result.measured_value,
                "test_time": result.created_at.isoformat()
            }
            for result in results
        ]
    
    async def _save_measurement_result(
        self,
        db: Session,
        session_id: int,
        result: MeasurementResult
    ):
        """
        Save measurement result to database
        """
        try:
            db_result = TestResultModel(
                test_session_id=session_id,
                item_no=result.item_no,
                item_name=result.item_name,
                result=result.result,
                measured_value=float(result.measured_value) if result.measured_value else None,
                error_message=result.error_message,
                execution_duration_ms=result.execution_duration_ms
            )
            
            db.add(db_result)
            db.commit()
            
        except Exception as e:
            self.logger.error(f"Failed to save measurement result: {e}")
            db.rollback()


# Global service instance
measurement_service = MeasurementService()