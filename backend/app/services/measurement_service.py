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
            'IT6723C': 'IT6723C.py',
            'PSW3072': 'PSW3072.py',
            '2260B': '2260B.py',
            'APS7050': 'APS7050.py',
            '34970A': '34970A.py',
            '2015': 'Keithley2015.py',
            '6510': 'DAQ6510.py'
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
        user_id: Optional[str] = None,
        db: Optional[Session] = None
    ):
        """
        Execute batch measurements asynchronously
        
        Implements PDTool4's CSV-driven sequential execution with dependency management.
        """
        try:
            self.logger.info(f"Starting batch execution for session {session_id}")
            
            # Initialize session tracking
            self.active_sessions[session_id] = {
                "status": "RUNNING",
                "current_index": 0,
                "total_count": len(measurements),
                "results": [],
                "test_results": {}  # PDTool4-style result collection
            }
            
            session_data = self.active_sessions[session_id]
            
            for index, measurement_request in enumerate(measurements):
                session_data["current_index"] = index
                
                # Check for stop request
                if session_data.get("should_stop", False):
                    session_data["status"] = "STOPPED"
                    break
                
                # Execute measurement
                result = await self.execute_single_measurement(
                    measurement_type=measurement_request["measurement_type"],
                    test_point_id=measurement_request["test_point_id"],
                    switch_mode=measurement_request["switch_mode"],
                    test_params=measurement_request["test_params"],
                    run_all_test=measurement_request.get("run_all_test", False),
                    user_id=user_id
                )
                
                # Store result
                session_data["results"].append(result)
                session_data["test_results"][measurement_request["test_point_id"]] = result.measured_value
                
                # Save to database if provided
                if db:
                    await self._save_measurement_result(db, session_id, result)
                
                # Check if should stop on failure
                if stop_on_fail and result.result == "FAIL":
                    self.logger.warning(f"Stopping batch execution due to failure at {result.item_name}")
                    session_data["status"] = "FAILED"
                    break
            
            # Complete session if not stopped
            if session_data["status"] == "RUNNING":
                session_data["status"] = "COMPLETED"
            
            # Cleanup instruments (PDTool4 style)
            await self._cleanup_used_instruments(session_data.get("used_instruments", {}))
            
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
            if switch_mode == 'DAQ973A':
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
                
                # Execute instrument command via subprocess (PDTool4 style)
                result = await self._execute_instrument_command(
                    script_path='./src/lowsheen_lib/DAQ973A_test.py',
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
            
            elif switch_mode == 'MODEL2303':
                # Similar implementation for MODEL2303
                required_params = ['Instrument', 'Volt', 'Curr']
                missing = [p for p in required_params if p not in test_params]
                if missing:
                    return MeasurementResult(
                        item_no=0,
                        item_name=test_point_id,
                        result="ERROR",
                        error_message=f"Missing parameters: {missing}"
                    )
                
                result = await self._execute_instrument_command(
                    script_path='./src/lowsheen_lib/2303_test.py',
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
            if switch_mode == 'DAQ973A':
                required_params = ['Instrument', 'Channel', 'Item', 'Type']
                missing = [p for p in required_params if p not in test_params]
                if missing:
                    return MeasurementResult(
                        item_no=0,
                        item_name=test_point_id,
                        result="ERROR",
                        error_message=f"Missing parameters: {missing}"
                    )
                
                result = await self._execute_instrument_command(
                    script_path='./src/lowsheen_lib/DAQ973A_test.py',
                    test_point_id=test_point_id,
                    test_params=test_params
                )
                
                # Parse numeric result
                try:
                    measured_value = Decimal(str(float(result.strip())))
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
        """
        try:
            if switch_mode == 'comport':
                required_params = ['Port', 'Baud', 'Command']
                if 'keyWord' in test_params:
                    required_params.extend(['keyWord', 'spiltCount', 'splitLength'])
                
                missing = [p for p in required_params if p not in test_params]
                if missing:
                    return MeasurementResult(
                        item_no=0,
                        item_name=test_point_id,
                        result="ERROR",
                        error_message=f"Missing parameters: {missing}"
                    )
                
                result = await self._execute_instrument_command(
                    script_path='./src/lowsheen_lib/ComPortCommand.py',
                    test_point_id=test_point_id,
                    test_params=test_params
                )
                
                # Process keyword extraction if specified
                if 'keyWord' in test_params:
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
                else:
                    return MeasurementResult(
                        item_no=0,
                        item_name=test_point_id,
                        result="PASS" if result else "FAIL"
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
        """
        try:
            # Placeholder for custom measurements
            return MeasurementResult(
                item_no=0,
                item_name=test_point_id,
                result="PASS",
                measured_value=Decimal('1')
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
                'MODEL2303': ['Instrument', 'Volt', 'Curr'],
                'IT6723C': ['Instrument', 'Channel', 'Volt', 'Curr'],
                'PSW3072': ['Instrument', 'Channel', 'Volt', 'Curr'],
                '2260B': ['Instrument', 'Channel', 'Volt', 'Curr'],
                'APS7050': ['Instrument', 'Channel', 'Volt', 'Curr']
            },
            'PowerRead': {
                'DAQ973A': ['Instrument', 'Channel', 'Item', 'Type'],
                '34970A': ['Instrument', 'Channel', 'Item'],
                '2015': ['Instrument', 'Item'],
                '6510': ['Instrument', 'Item']
            },
            'CommandTest': {
                'comport': ['Port', 'Baud', 'Command'],
                'tcpip': ['Host', 'Port', 'Command'],
                'console': ['Command'],
                'android_adb': ['Command']
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
            return {
                "valid": False,
                "missing_params": [],
                "invalid_params": [],
                "suggestions": [f"Unknown switch mode '{switch_mode}' for {measurement_type}"]
            }
        
        required_params = validation_rules[measurement_type][switch_mode]
        missing_params = [param for param in required_params if param not in test_params]
        
        # Additional validation for CommandTest with keyword extraction
        if measurement_type == 'CommandTest' and 'keyWord' in test_params:
            additional_required = ['spiltCount', 'splitLength']
            missing_params.extend([param for param in additional_required if param not in test_params])
        
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