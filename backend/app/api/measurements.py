"""
Measurement API Endpoints
Based on PDTool4 measurement module architecture
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.dependencies import get_current_active_user
from app.services.measurement_service import measurement_service
from app.models.test_session import TestSession as TestSessionModel
from app.schemas.measurement import MeasurementResponse
from app.config.instruments import AVAILABLE_INSTRUMENTS, MEASUREMENT_TEMPLATES

router = APIRouter()


class MeasurementRequest(BaseModel):
    """Request model for measurement execution"""
    measurement_type: str  # PowerSet, PowerRead, CommandTest, SFCtest, etc.
    test_point_id: str
    switch_mode: str  # e.g., 'DAQ973A', 'MODEL2303', 'comport', etc.
    test_params: Dict[str, Any]
    run_all_test: bool = False


class BatchMeasurementRequest(BaseModel):
    """Request model for batch measurement execution"""
    session_id: int
    measurements: List[MeasurementRequest]
    stop_on_fail: bool = True


class InstrumentStatus(BaseModel):
    """Instrument status model"""
    instrument_id: str
    instrument_type: str
    status: str  # IDLE, BUSY, ERROR, OFFLINE
    last_used: Optional[datetime] = None


@router.post("/execute", response_model=MeasurementResponse)
async def execute_measurement(
    request: MeasurementRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Execute a single measurement
    
    Based on PDTool4's measurement dispatch mechanism:
    - PowerSet: For setting power supply voltages/currents
    - PowerRead: For reading voltage/current measurements  
    - CommandTest: For serial/network command testing
    - SFCtest: For SFC integration testing
    """
    try:
        result = await measurement_service.execute_single_measurement(
            measurement_type=request.measurement_type,
            test_point_id=request.test_point_id,
            switch_mode=request.switch_mode,
            test_params=request.test_params,
            run_all_test=request.run_all_test,
            user_id=current_user.get("sub")
        )

        # Original code: Complex type conversion logic in API layer (lines 79-92)
        # Refactored: Type conversion moved to MeasurementResponse field validator
        # See app/schemas/measurement.py:convert_measured_value_to_string
        return MeasurementResponse(
            test_point_id=request.test_point_id,
            measurement_type=request.measurement_type,
            result=result.result,
            measured_value=result.measured_value,  # Validator handles type conversion
            error_message=result.error_message,
            test_time=result.test_time,
            execution_duration_ms=result.execution_duration_ms
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Measurement execution failed: {str(e)}"
        )


@router.post("/batch-execute")
async def execute_batch_measurements(
    request: BatchMeasurementRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Execute batch measurements asynchronously
    
    Mimics PDTool4's CSV-driven test execution where multiple measurements
    are executed sequentially with dependency management.
    """
    try:
        # Validate session exists
        session = db.query(TestSessionModel).filter(
            TestSessionModel.id == request.session_id
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Test session not found"
            )
        
        # Start batch execution in background
        background_tasks.add_task(
            measurement_service.execute_batch_measurements,
            session_id=request.session_id,
            measurements=request.measurements,
            stop_on_fail=request.stop_on_fail,
            user_id=current_user.get("sub"),
            db=db
        )
        
        return {
            "message": "Batch measurement execution started",
            "session_id": request.session_id,
            "measurement_count": len(request.measurements)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start batch measurements: {str(e)}"
        )


@router.get("/types")
async def get_measurement_types():
    """
    Get available measurement types
    
    Returns the measurement types supported by the system,
    based on PDTool4's measurement module implementations.
    """
    return {
        "measurement_types": [
            {
                "name": "PowerSet",
                "description": "Power supply voltage/current setting",
                "supported_switches": ["DAQ973A", "MODEL2303", "IT6723C", "PSW3072", "2260B", "APS7050"]
            },
            {
                "name": "PowerRead", 
                "description": "Voltage/current measurement reading",
                "supported_switches": ["DAQ973A", "34970A", "2015", "6510"]
            },
            {
                "name": "CommandTest",
                "description": "Serial/network command execution",
                "supported_switches": ["comport", "tcpip", "console", "android_adb"]
            },
            {
                "name": "SFCtest",
                "description": "SFC integration testing",
                "supported_switches": ["webStep1_2", "URLStep1_2", "skip"]
            },
            {
                "name": "getSN",
                "description": "Serial number acquisition",
                "supported_switches": ["SN", "IMEI", "MAC"]
            },
            {
                "name": "OPjudge",
                "description": "Operator judgment/confirmation",
                "supported_switches": ["YorN", "confirm"]
            },
            {
                "name": "Other",
                "description": "Custom measurement implementations",
                "supported_switches": ["custom"]
            }
        ]
    }


@router.get("/instruments", response_model=List[InstrumentStatus])
async def get_instrument_status():
    """
    Get current status of all instruments
    
    Returns the status of all configured instruments,
    similar to PDTool4's instrument resource management.
    """
    try:
        instruments = await measurement_service.get_instrument_status()
        return [
            InstrumentStatus(
                instrument_id=inst["id"],
                instrument_type=inst["type"],
                status=inst["status"],
                last_used=inst.get("last_used")
            )
            for inst in instruments
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get instrument status: {str(e)}"
        )


@router.post("/instruments/{instrument_id}/reset")
async def reset_instrument(
    instrument_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Reset a specific instrument
    
    Equivalent to PDTool4's instrument finalization/reset functionality
    that is called after test completion.
    """
    try:
        result = await measurement_service.reset_instrument(instrument_id)
        return {
            "message": f"Instrument {instrument_id} reset successfully",
            "status": result.get("status", "IDLE")
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset instrument {instrument_id}: {str(e)}"
        )


@router.get("/session/{session_id}/results")
async def get_session_measurement_results(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Get measurement results for a specific session
    
    Returns detailed measurement results similar to PDTool4's
    test result collection and reporting.
    """
    try:
        results = await measurement_service.get_session_results(session_id, db)
        return {
            "session_id": session_id,
            "results": results
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session results: {str(e)}"
        )


@router.post("/validate-params")
async def validate_measurement_params(
    measurement_type: str,
    switch_mode: str,
    test_params: Dict[str, Any]
):
    """
    Validate measurement parameters

    Based on PDTool4's parameter validation logic where each measurement
    type has required and optional parameters.
    """
    try:
        validation_result = await measurement_service.validate_params(
            measurement_type=measurement_type,
            switch_mode=switch_mode,
            test_params=test_params
        )

        return {
            "valid": validation_result["valid"],
            "missing_params": validation_result.get("missing_params", []),
            "invalid_params": validation_result.get("invalid_params", []),
            "suggestions": validation_result.get("suggestions", [])
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Parameter validation failed: {str(e)}"
        )


@router.get("/instruments/available")
async def get_available_instruments():
    """
    Get list of all available instruments based on PDTool4 configuration

    Returns instruments that can be used for measurements, similar to
    PDTool4's instrument discovery and configuration system.

    Original code: 30+ lines of hardcoded instrument dictionaries
    Modified: Loaded from app.config.instruments module for easier maintenance
    """
    try:
        return AVAILABLE_INSTRUMENTS
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get available instruments: {str(e)}"
        )


@router.get("/measurement-templates")
async def get_measurement_templates():
    """
    Get measurement templates based on PDTool4's measurement module patterns

    Returns standardized templates for different measurement types,
    making it easier to configure test parameters.

    Original code: 87+ lines of hardcoded template dictionaries
    Modified: Loaded from app.config.instruments module for easier maintenance
    """
    try:
        return MEASUREMENT_TEMPLATES
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get measurement templates: {str(e)}"
        )


@router.post("/execute-with-dependencies")
async def execute_measurement_with_dependencies(
    request: MeasurementRequest,
    dependencies: List[str] = [],
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Execute measurement with dependencies resolution

    Based on PDTool4's measurement dependency system where measurements
    can depend on results of previous measurements.
    """
    try:
        # Validate dependencies exist
        if dependencies:
            for dep_id in dependencies:
                # In a real implementation, this would check if the dependency result exists
                # and might wait for it if it's still executing
                pass

        # Execute the measurement
        result = await execute_measurement(request, db, current_user)

        return {
            "result": result,
            "dependencies": dependencies,
            "message": f"Measurement executed with {len(dependencies)} dependencies"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Measurement with dependencies failed: {str(e)}"
        )