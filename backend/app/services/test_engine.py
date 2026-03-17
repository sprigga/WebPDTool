"""
Test Execution Engine Service
Core service for orchestrating test execution
"""
from typing import Dict, Any, List, Optional
# Original code: from sqlalchemy.orm import Session
# Modified: Use AsyncSession for async DB migration (Wave 6 - Task 12)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

_TZ_TAIPEI = ZoneInfo("Asia/Taipei")
from decimal import Decimal
import asyncio
import logging
import time

from app.models.test_session import TestSession as TestSessionModel, TestResult as TestResultEnum
from app.models.test_result import TestResult as TestResultModel, ItemResult
from app.models.testplan import TestPlan
from app.models.station import Station
from app.measurements.base import BaseMeasurement, MeasurementResult
from app.measurements.implementations import get_measurement_class
from app.services.instrument_manager import instrument_manager
from app.services.report_service import report_service
from app.services.modbus.modbus_manager import modbus_manager
# Original code: from app.core.database import SessionLocal
# Modified: Use AsyncSessionLocal for async DB migration (Wave 6 - Task 12)
from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class TestExecutionState:
    """Track test execution state"""
    
    def __init__(self, session_id: int):
        self.session_id = session_id
        self.status = "IDLE"  # IDLE, RUNNING, PAUSED, COMPLETED, ABORTED
        self.current_item_index = 0
        self.results: List[MeasurementResult] = []
        self.start_time: Optional[datetime] = None
        self.error: Optional[str] = None
        self.should_stop = False


class TestEngine:
    """
    Test Execution Engine
    Orchestrates test execution, manages test flow, and collects results
    """
    
    def __init__(self):
        self.active_tests: Dict[int, TestExecutionState] = {}
        self.logger = logging.getLogger(self.__class__.__name__)
        self._lock = asyncio.Lock()
    
    # Original code: async def start_test_session(self, session_id: int, serial_number: str, station_id: int, db: Session)
    # Modified: Removed db parameter (Wave 6 - Task 12) - background task creates its own async session
    async def start_test_session(
        self,
        session_id: int,
        serial_number: str,
        station_id: int
    ) -> Dict[str, Any]:
        """
        Start a test session

        Args:
            session_id: Test session ID
            serial_number: Product serial number
            station_id: Station ID

        Returns:
            Dictionary with execution status
        """
        async with self._lock:
            # Check if test already running
            if session_id in self.active_tests:
                raise ValueError(f"Test session {session_id} is already running")

            # Initialize test state
            test_state = TestExecutionState(session_id)
            test_state.status = "RUNNING"
            # 修改(2026-03-16): 改用 Asia/Taipei
            # test_state.start_time = datetime.utcnow()
            test_state.start_time = datetime.now(_TZ_TAIPEI)
            self.active_tests[session_id] = test_state

        # Background task creates its own AsyncSession
        asyncio.create_task(
            self._execute_test_session(session_id, station_id)
        )

        return {
            "session_id": session_id,
            "status": "RUNNING",
            "message": "Test session started successfully"
        }
    
    async def _execute_test_session(
        self,
        session_id: int,
        station_id: int,
    ):
        """
        Execute test session (runs in background)

        Creates its own AsyncSession so it is not bound to the request lifecycle.

        Args:
            session_id: Test session ID
            station_id: Station ID
        """
        # Original code: db: Session = SessionLocal()
        # Modified: Use AsyncSessionLocal for async (Wave 6 - Task 12)
        db: AsyncSession = AsyncSessionLocal()
        test_state = self.active_tests[session_id]

        try:
            # Original code: test_plan_items = db.query(TestPlan).filter(...).order_by(...).all()
            # Modified: Use select() with await for async
            result = await db.execute(
                select(TestPlan)
                .where(TestPlan.station_id == station_id)
                .order_by(TestPlan.sequence_order)
            )
            test_plan_items = result.scalars().all()

            if not test_plan_items:
                raise ValueError(f"No test plan found for station {station_id}")

            self.logger.info(
                f"Starting test session {session_id} with {len(test_plan_items)} items"
            )

            # Original code: station = db.query(Station).filter(...).first()
            # Modified: Use select() with await for async
            result = await db.execute(
                select(Station).where(Station.id == station_id)
            )
            station = result.scalar_one_or_none()
            if not station:
                raise ValueError(f"Station {station_id} not found")
            config = self._load_configuration(station)
            
            # Execute each test item
            for idx, test_plan_item in enumerate(test_plan_items):
                # Check if should stop
                if test_state.should_stop:
                    test_state.status = "ABORTED"
                    self.logger.warning(f"Test session {session_id} aborted by user")
                    break
                
                test_state.current_item_index = idx
                
                # Execute measurement
                result = await self._execute_measurement(
                    session_id,
                    test_plan_item,
                    config,
                    db
                )
                
                # Store result
                test_state.results.append(result)
                
                # Save result to database
                await self._save_test_result(session_id, test_plan_item.id, result, db)
                
                # If critical failure and stop_on_fail is enabled, abort
                if result.result == "FAIL" and config.get("stop_on_fail", False):
                    test_state.status = "ABORTED"
                    self.logger.warning(
                        f"Test session {session_id} aborted due to failure on {result.item_name}"
                    )
                    break
            
            # Calculate final result
            if test_state.status != "ABORTED":
                test_state.status = "COMPLETED"
            
            # Update session in database
            await self._finalize_test_session(session_id, test_state, db)
            
        except Exception as e:
            self.logger.error(f"Error executing test session {session_id}: {e}", exc_info=True)
            test_state.status = "ERROR"
            test_state.error = str(e)
            
            # Try to update session with error
            try:
                await self._finalize_test_session(session_id, test_state, db)
            except Exception as finalize_error:
                self.logger.error(f"Error finalizing failed session: {finalize_error}")

        finally:
            # Close the background-owned async DB session
            # Original code: db.close()
            # Modified: Use await for async session close (Wave 6 - Task 12)
            await db.close()
            # Cleanup active test state
            async with self._lock:
                if session_id in self.active_tests:
                    del self.active_tests[session_id]
    
    # Original code: async def _execute_measurement(self, session_id: int, test_plan_item: TestPlan, config: Dict[str, Any], db: Session)
    # Modified: Change db parameter to AsyncSession (Wave 6 - Task 12)
    async def _execute_measurement(
        self,
        session_id: int,
        test_plan_item: TestPlan,
        config: Dict[str, Any],
        db: AsyncSession
    ) -> MeasurementResult:
        """
        Execute a single measurement

        Args:
            session_id: Test session ID
            test_plan_item: Test plan item to execute
            config: Configuration dictionary
            db: Async database session

        Returns:
            MeasurementResult
        """
        start_time = time.time()

        # 在使用前提取所有屬性，避免 SQLAlchemy session 脫離問題
        # 注意: TestPlan 模型使用 test_type 欄位而非 test_command
        try:
            # 原有程式碼: parameters = test_plan_item.parameters or {}
            # 修改: 構建完整的 parameters 字典,整合 test_plan 的各個欄位
            # 這樣可以確保 CommandTest 和 Other 測量類型能正確讀取所需參數

            # 從資料庫欄位提取參數
            db_parameters = test_plan_item.parameters or {}

            # 構建完整的 parameters 字典,優先級: 資料庫欄位 > JSON parameters
            parameters = {
                **db_parameters,  # 先載入 JSON parameters 中的值
                # 資料庫直接欄位優先級更高 (會覆蓋 JSON 中的同名鍵)
                "command": test_plan_item.command,
                "wait_msec": test_plan_item.wait_msec,
                "timeout": test_plan_item.timeout,
                "use_result": test_plan_item.use_result,
            }

            # 原有程式碼: 使用 case_type 來決定特殊測試類型
            # 修正方案 A: 統一使用 switch_mode 替代 case_type,簡化邏輯
            # switch_mode 現在可以是儀器模式 (DAQ973A) 或特殊測試類型 (wait, relay, console 等)
            switch_mode = test_plan_item.switch_mode or test_plan_item.case_type  # 向後相容 case_type
            test_type = test_plan_item.test_type

            # 決定使用的測試命令 (test_command)
            # 特殊 switch_mode 列表（這些 switch_mode 對應獨立的測量類型或特殊功能）
            special_switch_modes = {'wait', 'relay', 'chassis_rotation', 'console', 'comport', 'tcpip'}

            # 如果 switch_mode 是特殊類型，優先使用 switch_mode 作為測試命令
            # 否則使用 test_type，switch_mode 僅作為儀器選擇或腳本名稱
            if switch_mode and switch_mode.strip() and switch_mode.lower() in special_switch_modes:
                test_command = switch_mode
            else:
                test_command = test_type

            item_dict = {
                "id": test_plan_item.id,
                "item_no": test_plan_item.item_no,
                "item_name": test_plan_item.item_name,
                "item_key": test_plan_item.item_key,
                "lower_limit": test_plan_item.lower_limit,
                "upper_limit": test_plan_item.upper_limit,
                "unit": test_plan_item.unit,
                "test_type": test_type,  # 保留原始 test_type
                "test_command": test_command,  # 實際使用的測試命令 (優先使用 switch_mode)
                "command": test_plan_item.command,  # 原始指令字串
                "switch_mode": switch_mode,  # 修正方案 A: 使用 switch_mode 替代 case_type
                "case_type": test_plan_item.case_type,  # 保留 case_type 以支援向後相容
                "parameters": parameters,  # BaseMeasurement 預期使用 "parameters" 鍵
                "test_params": parameters,  # 同時保留 "test_params" 鍵 (已整合完整參數)
                "value_type": test_plan_item.value_type,
                "limit_type": test_plan_item.limit_type,
                "eq_limit": test_plan_item.eq_limit,
                "timeout": test_plan_item.timeout,
                "use_result": test_plan_item.use_result,
                "wait_msec": test_plan_item.wait_msec
            }
        except Exception as e:
            self.logger.error(f"Error extracting test plan item attributes: {e}")
            execution_time_ms = int((time.time() - start_time) * 1000)
            return MeasurementResult(
                item_no=0,
                item_name="Unknown",
                result="ERROR",
                error_message=f"Failed to extract test plan data: {str(e)}",
                execution_duration_ms=execution_time_ms
            )

        try:
            # Get measurement class based on test command (test_type)
            # 使用 item_dict 中的 test_command
            measurement_class = self._get_measurement_class(item_dict.get("test_command", ""))
            
            if measurement_class is None:
                # No specific measurement implementation, return skip
                self.logger.warning(
                    f"No measurement implementation for command: {item_dict.get('test_command')}"
                )
                return MeasurementResult(
                    item_no=item_dict.get("item_no", 0),
                    item_name=item_dict.get("item_name", "Unknown"),
                    result="SKIP",
                    error_message=f"No implementation for: {item_dict.get('test_command')}"
                )
            
            # Create and execute measurement
            measurement = measurement_class(item_dict, config)
            await measurement.setup()
            result = await measurement.execute()
            await measurement.teardown()
            
            # Calculate execution time
            execution_time_ms = int((time.time() - start_time) * 1000)
            result.execution_duration_ms = execution_time_ms
            
            return result
            
        except Exception as e:
            # 使用 item_dict 而不是 test_plan_item，避免 SQLAlchemy session 脫離問題
            item_name = item_dict.get("item_name", "Unknown")
            item_no = item_dict.get("item_no", 0)

            self.logger.error(
                f"Error executing measurement {item_name}: {e}",
                exc_info=True
            )
            execution_time_ms = int((time.time() - start_time) * 1000)
            return MeasurementResult(
                item_no=item_no,
                item_name=item_name,
                result="ERROR",
                error_message=str(e),
                execution_duration_ms=execution_time_ms
            )
    
    def _get_measurement_class(self, test_command: str) -> Optional[type]:
        """
        Get measurement class based on test command
        
        Args:
            test_command: Test command string
            
        Returns:
            Measurement class or None
        """
        # Use the measurement registry from implementations module
        return get_measurement_class(test_command)
    
    # Original code: async def _save_test_result(self, session_id: int, test_plan_id: int, result: MeasurementResult, db: Session)
    # Modified: Change db parameter to AsyncSession (Wave 6 - Task 12)
    async def _save_test_result(
        self,
        session_id: int,
        test_plan_id: int,
        result: MeasurementResult,
        db: AsyncSession
    ):
        """
        Save test result to database

        Args:
            session_id: Test session ID
            test_plan_id: Test plan item ID
            result: Measurement result
            db: Async database session
        """
        try:
            db_result = TestResultModel(
                session_id=session_id,
                test_plan_id=test_plan_id,
                item_no=result.item_no,
                item_name=result.item_name,
                measured_value=result.measured_value,
                lower_limit=result.lower_limit,
                upper_limit=result.upper_limit,
                unit=result.unit,
                result=ItemResult(result.result),
                error_message=result.error_message,
                execution_duration_ms=result.execution_duration_ms,
                # 修改(2026-03-16): 明確傳入 Asia/Taipei 時間，取代 server_default
                test_time=result.test_time,
            )

            # Original code: db.add(db_result); db.commit()
            # Modified: Use await for async operations (Wave 6 - Task 12)
            db.add(db_result)
            await db.commit()

        except Exception as e:
            self.logger.error(f"Error saving test result: {e}", exc_info=True)
            # Original code: db.rollback()
            # Modified: Use await for async rollback (Wave 6 - Task 12)
            await db.rollback()
    
    # Original code: async def _finalize_test_session(self, session_id: int, test_state: TestExecutionState, db: Session)
    # Modified: Change db parameter to AsyncSession (Wave 6 - Task 12)
    async def _finalize_test_session(
        self,
        session_id: int,
        test_state: TestExecutionState,
        db: AsyncSession
    ):
        """
        Finalize test session and update database

        Args:
            session_id: Test session ID
            test_state: Test execution state
            db: Async database session
        """
        try:
            # Original code: session = db.query(TestSessionModel).filter(...).first()
            # Modified: Use select() with await for async
            result = await db.execute(
                select(TestSessionModel).where(TestSessionModel.id == session_id)
            )
            session = result.scalar_one_or_none()

            if not session:
                self.logger.error(f"Session {session_id} not found in database")
                return

            # Calculate statistics
            total_items = len(test_state.results)
            pass_items = sum(1 for r in test_state.results if r.result == "PASS")
            fail_items = sum(1 for r in test_state.results if r.result == "FAIL")

            # Determine final result
            if test_state.status == "ABORTED":
                final_result = TestResultEnum.ABORT
            elif fail_items > 0:
                final_result = TestResultEnum.FAIL
            else:
                final_result = TestResultEnum.PASS

            # Calculate duration
            # 修改(2026-03-16): 改用 Asia/Taipei，兩端需同為 aware datetime 才能相減
            # duration_seconds = round((datetime.utcnow() - test_state.start_time).total_seconds(), 6)
            _now = datetime.now(_TZ_TAIPEI)
            if test_state.start_time:
                duration_seconds = round((_now - test_state.start_time).total_seconds(), 6)
            else:
                duration_seconds = 0

            # Update session
            # 修改(2026-03-16): 改用 Asia/Taipei
            # session.end_time = datetime.utcnow()
            session.end_time = _now
            session.final_result = final_result
            session.total_items = total_items
            session.pass_items = pass_items
            session.fail_items = fail_items
            session.test_duration_seconds = duration_seconds

            # Original code: db.commit()
            # Modified: Use await for async commit (Wave 6 - Task 12)
            await db.commit()

            self.logger.info(
                f"Test session {session_id} finalized: {final_result} "
                f"({pass_items}/{total_items} passed)"
            )

            # Write result to Modbus device if a listener is active for this station
            await self._write_modbus_result(session.station_id, final_result == TestResultEnum.PASS)

            # Automatically generate and save CSV report
            try:
                # Original code: report_path = report_service.save_session_report(session_id, db)
                # Modified: Use await for async call (Wave 6 - Task 12)
                report_path = await report_service.save_session_report(session_id, db)
                if report_path:
                    self.logger.info(f"Test report saved: {report_path}")
                else:
                    self.logger.warning(f"Failed to save test report for session {session_id}")
            except Exception as report_error:
                # Don't fail the test session if report generation fails
                self.logger.error(f"Error generating test report: {report_error}", exc_info=True)

        except Exception as e:
            self.logger.error(f"Error finalizing test session: {e}", exc_info=True)
            # Original code: db.rollback()
            # Modified: Use await for async rollback (Wave 6 - Task 12)
            await db.rollback()
    
    async def _write_modbus_result(self, station_id: int, passed: bool) -> None:
        """
        Write test result to Modbus device if a listener is active for this station.
        Silently skips if no Modbus listener is running.
        """
        try:
            written = await modbus_manager.write_test_result(station_id, passed)
            if written:
                self.logger.info(f"Wrote Modbus result: {'PASS' if passed else 'FAIL'} for station {station_id}")
        except Exception as e:
            # Do not fail the session if Modbus write fails
            self.logger.error(f"Failed to write Modbus result for station {station_id}: {e}")

    def _load_configuration(self, station: Station) -> Dict[str, Any]:
        """
        Load configuration for test execution
        
        Args:
            station: Station model
            
        Returns:
            Configuration dictionary
        """
        # Load configuration from database, files, etc.
        # For now, return basic config
        config = {
            "station_id": station.id,
            "station_code": station.station_code,
            "stop_on_fail": False,  # Can be loaded from station config
            "instruments": {},  # Instrument configurations
        }
        
        return config
    
    async def stop_test_session(self, session_id: int) -> Dict[str, Any]:
        """
        Stop a running test session
        
        Args:
            session_id: Test session ID to stop
            
        Returns:
            Dictionary with stop status
        """
        async with self._lock:
            if session_id not in self.active_tests:
                raise ValueError(f"Test session {session_id} is not running")
            
            test_state = self.active_tests[session_id]
            test_state.should_stop = True
            
            self.logger.info(f"Stop requested for test session {session_id}")
            
            return {
                "session_id": session_id,
                "status": "STOPPING",
                "message": "Test session stop requested"
            }
    
    def get_test_status(self, session_id: int) -> Optional[Dict[str, Any]]:
        """
        Get current status of a test session
        
        Args:
            session_id: Test session ID
            
        Returns:
            Status dictionary or None if not found
        """
        if session_id not in self.active_tests:
            return None
        
        test_state = self.active_tests[session_id]
        
        return {
            "session_id": session_id,
            "status": test_state.status,
            "current_item_index": test_state.current_item_index,
            "completed_items": len(test_state.results),
            "error": test_state.error
        }


# Global test engine instance
test_engine = TestEngine()
