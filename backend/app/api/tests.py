"""
Test Execution API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime
import logging

from app.core.database import get_db
from app.dependencies import get_current_active_user
from app.models.test_session import TestSession as TestSessionModel
from app.models.test_result import TestResult as TestResultModel
from app.models.station import Station
from app.models.testplan import TestPlan
from app.schemas.test_session import (
    TestSession,
    TestSessionCreate,
    TestSessionComplete,
    TestSessionStatus,
    TestSessionDetail
)
from app.schemas.test_result import (
    TestResult,
    TestResultCreate,
    TestResultBatch
)
from app.services.test_engine import test_engine
from app.services.instrument_manager import instrument_manager
from app.core.constants import TimeConstants

# Module-level logger
logger = logging.getLogger(__name__)

# Check if report service is available
try:
    from app.services.report_service import report_service
    REPORT_SERVICE_AVAILABLE = True
except ImportError:
    REPORT_SERVICE_AVAILABLE = False
    report_service = None
    logger.warning("Report service not available")

router = APIRouter()


@router.post("/sessions", response_model=TestSession, status_code=status.HTTP_201_CREATED)
async def create_test_session(
    session_data: TestSessionCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Create a new test session

    Args:
        session_data: Test session creation data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Created test session
    """
    # Verify station exists
    station = db.query(Station).filter(Station.id == session_data.station_id).first()
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")

    # Create test session
    db_session = TestSessionModel(
        serial_number=session_data.serial_number,
        station_id=session_data.station_id,
        user_id=current_user.get("id")
    )

    db.add(db_session)
    db.commit()
    db.refresh(db_session)

    return db_session


@router.post("/sessions/{session_id}/start", response_model=dict)
async def start_test_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Start test execution for a session

    Args:
        session_id: Test session ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Test execution status
    """
    # Verify session exists
    session = db.query(TestSessionModel).filter(TestSessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Test session not found")

    # Check if session already completed
    if session.end_time:
        raise HTTPException(
            status_code=400,
            detail="Test session already completed"
        )

    # Start test execution
    try:
        result = await test_engine.start_test_session(
            session_id=session_id,
            serial_number=session.serial_number,
            station_id=session.station_id,
            db=db
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting test: {str(e)}")


@router.post("/sessions/{session_id}/stop", response_model=dict)
async def stop_test_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Stop a running test session

    Args:
        session_id: Test session ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Stop status
    """
    try:
        result = await test_engine.stop_test_session(session_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error stopping test: {str(e)}")


@router.get("/sessions/{session_id}", response_model=TestSession)
async def get_test_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Get test session by ID"""
    session = db.query(TestSessionModel).filter(TestSessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Test session not found")

    return session


@router.get("/sessions/{session_id}/status", response_model=TestSessionStatus)
async def get_test_session_status(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Get real-time test session status

    Args:
        session_id: Test session ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Test session status with progress information
    """
    session = db.query(TestSessionModel).filter(TestSessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Test session not found")

    # Get result counts
    results = db.query(TestResultModel).filter(TestResultModel.session_id == session_id).all()
    total_items = len(results)
    pass_items = sum(1 for r in results if r.result == "PASS")
    fail_items = sum(1 for r in results if r.result == "FAIL")

    # Calculate elapsed time by summing all test items' execution_duration_ms
    # (Previous implementation used wall-clock time - see git history for details)
    elapsed_time = None
    if results:
        # Sum execution time (ms) of all test items and convert to seconds
        total_duration_ms = sum(int(r.execution_duration_ms or 0) for r in results)
        if total_duration_ms > 0:
            elapsed_time = round(
                total_duration_ms / TimeConstants.MS_PER_SECOND,
                TimeConstants.DEFAULT_DECIMAL_PLACES
            )

    # Determine status
    if session.end_time:
        test_status = "COMPLETED" if session.final_result != "ABORT" else "ABORTED"
    else:
        test_status = "RUNNING"

    return TestSessionStatus(
        session_id=session.id,
        status=test_status,
        current_item=total_items,
        total_items=session.total_items,
        pass_items=pass_items,
        fail_items=fail_items,
        elapsed_time_seconds=elapsed_time
    )


@router.post("/sessions/{session_id}/results", response_model=TestResult, status_code=status.HTTP_201_CREATED)
async def create_test_result(
    session_id: int,
    result_data: TestResultCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Upload a single test result

    Args:
        session_id: Test session ID
        result_data: Test result data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Created test result
    """
    # Verify session exists
    session = db.query(TestSessionModel).filter(TestSessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Test session not found")

    # Ensure session_id matches
    if result_data.session_id != session_id:
        raise HTTPException(
            status_code=400,
            detail="session_id in URL and body must match"
        )

    # Original: db_result = TestResultModel(**result_data.dict())
    # Modified: Explicit field mapping to avoid bypassing Pydantic validation
    # 修正: 添加錯誤處理和日誌，幫助診斷 500 錯誤
    try:
        # 修正: 確保 measured_value 正確處理空字串和 NULL
        # 空字串轉換為 NULL，避免資料庫類型錯誤
        measured_value_str = None
        if result_data.measured_value is not None:
            value_str = str(result_data.measured_value).strip()
            # 空字串或 "None" 視為 NULL
            if value_str and value_str.lower() != 'none':
                measured_value_str = value_str

        # Create test result with explicit field mapping
        db_result = TestResultModel(
            session_id=result_data.session_id,
            test_plan_id=result_data.test_plan_id,
            item_no=result_data.item_no,
            item_name=result_data.item_name,
            measured_value=measured_value_str,
            lower_limit=result_data.lower_limit,
            upper_limit=result_data.upper_limit,
            unit=result_data.unit,
            result=result_data.result,
            error_message=result_data.error_message,
            execution_duration_ms=result_data.execution_duration_ms
        )
        db.add(db_result)
        db.commit()
        db.refresh(db_result)

        return db_result
    except Exception as e:
        db.rollback()
        # 記錄詳細錯誤訊息
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to create test result: {e}")
        logger.error(f"Result data: session_id={result_data.session_id}, test_plan_id={result_data.test_plan_id}, "
                    f"item_no={result_data.item_no}, measured_value={result_data.measured_value}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create test result: {str(e)}"
        )


@router.post("/sessions/{session_id}/results/batch", response_model=dict)
async def create_test_results_batch(
    session_id: int,
    batch_data: TestResultBatch,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Batch upload multiple test results

    Args:
        session_id: Test session ID
        batch_data: Batch of test results
        db: Database session
        current_user: Current authenticated user

    Returns:
        Number of results created
    """
    # Verify session exists
    session = db.query(TestSessionModel).filter(TestSessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Test session not found")

    # Ensure session_id matches
    if batch_data.session_id != session_id:
        raise HTTPException(
            status_code=400,
            detail="session_id in URL and body must match"
        )

    # Original: Batch insert lacked transaction safety handling
    # Modified: Add try-except and rollback mechanism
    try:
        # Original: db_result = TestResultModel(**result_data.dict())
        # Modified: Explicit field mapping to avoid bypassing Pydantic validation
        # Create test results with explicit field mapping
        created_count = 0
        for result_data in batch_data.results:
            db_result = TestResultModel(
                session_id=result_data.session_id,
                test_plan_id=result_data.test_plan_id,
                item_no=result_data.item_no,
                item_name=result_data.item_name,
                measured_value=result_data.measured_value,
                lower_limit=result_data.lower_limit,
                upper_limit=result_data.upper_limit,
                unit=result_data.unit,
                result=result_data.result,
                error_message=result_data.error_message,
                execution_duration_ms=result_data.execution_duration_ms
            )
            db.add(db_result)
            created_count += 1

        db.commit()

        return {
            "message": "Test results created successfully",
            "created_count": created_count
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Batch insert failed, all changes rolled back: {str(e)}"
        )


@router.post("/sessions/{session_id}/complete", response_model=TestSession)
async def complete_test_session(
    session_id: int,
    complete_data: TestSessionComplete,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Complete a test session

    Args:
        session_id: Test session ID
        complete_data: Test completion data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Updated test session
    """
    # Get test session
    session = db.query(TestSessionModel).filter(TestSessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Test session not found")

    # Check if already completed
    if session.end_time:
        raise HTTPException(
            status_code=400,
            detail="Test session already completed"
        )

    # Update session
    session.end_time = datetime.utcnow()
    session.final_result = complete_data.final_result
    session.total_items = complete_data.total_items
    session.pass_items = complete_data.pass_items
    session.fail_items = complete_data.fail_items
    session.test_duration_seconds = complete_data.test_duration_seconds

    db.commit()
    db.refresh(session)

    # Original: CSV report was not generated after completion
    # Modified: Auto-generate CSV report to support frontend-driven mode
    # Refer to report generation logic in test_engine.py:_finalize_test_session()
    if REPORT_SERVICE_AVAILABLE and report_service:
        try:
            report_path = report_service.save_session_report(session_id, db)
            if report_path:
                logger.info(f"CSV report generated for session {session_id}: {report_path}")
        except Exception as report_error:
            # Report generation failure does not affect session completion, only log the error
            logger.error(f"Failed to generate CSV report for session {session_id}: {report_error}")

    return session


@router.get("/instruments/status", response_model=dict)
async def get_instruments_status(
    current_user: dict = Depends(get_current_active_user)
):
    """
    Get status of all instruments

    Args:
        current_user: Current authenticated user

    Returns:
        Instrument status information
    """
    try:
        status = instrument_manager.get_status()
        return status
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting instrument status: {str(e)}"
        )


@router.post("/instruments/{instrument_id}/reset", response_model=dict)
async def reset_instrument(
    instrument_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Reset a specific instrument

    Args:
        instrument_id: Instrument ID to reset
        current_user: Current authenticated user

    Returns:
        Reset status
    """
    try:
        await instrument_manager.reset_instrument(instrument_id)
        return {
            "instrument_id": instrument_id,
            "status": "reset_completed",
            "message": f"Instrument {instrument_id} has been reset"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error resetting instrument: {str(e)}"
        )
    # Original: return session  # ← This line was unreachable (removed)
    # Modified: Remove unreachable dead code to avoid confusion and potential bugs


@router.get("/sessions/{session_id}/logs", response_model=dict)
async def get_session_logs(
    session_id: int,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    ✅ Added: Get real-time logs for a test session

    Retrieves logs from Redis for real-time monitoring during test execution.
    If Redis is not enabled, returns an empty list.

    Args:
        session_id: Test session ID
        limit: Maximum number of log entries to retrieve (default: 100)
        db: Database session
        current_user: Current authenticated user

    Returns:
        Dictionary with logs list and count
    """
    # Verify session exists
    session = db.query(TestSessionModel).filter(TestSessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Test session not found")

    # Import logging_manager (lazy import to avoid circular dependencies)
    from app.core.logging_v2 import logging_manager

    try:
        # Get logs from Redis
        logs = await logging_manager.get_session_logs(session_id, limit)
        return {
            "session_id": session_id,
            "logs": logs,
            "count": len(logs),
            "source": "redis" if logs else "file"
        }
    except Exception as e:
        # If Redis is not available, return empty list
        return {
            "session_id": session_id,
            "logs": [],
            "count": 0,
            "source": "none",
            "message": f"Log streaming not available: {str(e)}"
        }


@router.get("/sessions/{session_id}/results", response_model=List[TestResult])
async def get_session_results(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Get all test results for a session

    Args:
        session_id: Test session ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        List of test results ordered by item_no
    """
    # Verify session exists
    session = db.query(TestSessionModel).filter(TestSessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Test session not found")

    # Get results
    results = db.query(TestResultModel).filter(
        TestResultModel.session_id == session_id
    ).order_by(TestResultModel.item_no).all()

    return results


@router.get("/sessions", response_model=List[TestSession])
async def list_test_sessions(
    station_id: int = None,
    serial_number: str = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    List test sessions with optional filtering

    Args:
        station_id: Filter by station ID
        serial_number: Filter by serial number (partial match)
        limit: Maximum number of results
        offset: Number of results to skip
        db: Database session
        current_user: Current authenticated user

    Returns:
        List of test sessions ordered by start_time descending
    """
    query = db.query(TestSessionModel)

    if station_id:
        query = query.filter(TestSessionModel.station_id == station_id)

    # Original: query = query.filter(TestSessionModel.serial_number.like(f"%{serial_number}%"))
    # Modified: Use parameterized query to prevent SQL injection risk
    if serial_number:
        # SQLAlchemy handles parameterization automatically, but using concat is more explicit and safe
        from sqlalchemy import func
        query = query.filter(
            TestSessionModel.serial_number.like(func.concat('%', serial_number, '%'))
        )

    sessions = query.order_by(
        desc(TestSessionModel.start_time)
    ).limit(limit).offset(offset).all()

    return sessions
