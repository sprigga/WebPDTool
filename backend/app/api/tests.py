"""
Test Execution API Endpoints
"""
from datetime import datetime
from zoneinfo import ZoneInfo
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
# Original code: from sqlalchemy.orm import Session
# Modified: Use AsyncSession for async DB migration (Wave 6 - Task 13)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, exists
from sqlalchemy import delete as sa_delete
from pydantic import BaseModel

_TZ_TAIPEI = ZoneInfo("Asia/Taipei")

# Original code: from app.core.database import get_db
# Modified: Use async DB dependency
from app.core.database import get_async_db
from app.core.api_helpers import PermissionChecker
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


class BulkDeleteSessionsRequest(BaseModel):
    session_ids: List[int]

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
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Create a new test session

    Args:
        session_data: Test session creation data
        db: Async database session
        current_user: Current authenticated user

    Returns:
        Created test session
    """
    # Original code: station = db.query(Station).filter(...).first()
    # Modified: Use select() with await for async
    result = await db.execute(
        select(Station).where(Station.id == session_data.station_id)
    )
    station = result.scalar_one_or_none()
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")

    # Create test session
    # 修改(2026-03-16): 明確傳入 Asia/Taipei start_time，避免 server_default 依賴 MySQL 時區設定
    # 原有程式碼: 未傳 start_time，改由 server_default=func.now() 填入（若 MySQL session 時區不一致會寫入 UTC）
    db_session = TestSessionModel(
        serial_number=session_data.serial_number,
        station_id=session_data.station_id,
        user_id=current_user.get("id"),
        start_time=datetime.now(_TZ_TAIPEI),
    )

    db.add(db_session)
    await db.commit()
    await db.refresh(db_session)

    return db_session


@router.post("/sessions/{session_id}/start", response_model=dict)
async def start_test_session(
    session_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Start test execution for a session

    Args:
        session_id: Test session ID
        db: Async database session
        current_user: Current authenticated user

    Returns:
        Test execution status
    """
    # Original code: session = db.query(TestSessionModel).filter(...).first()
    # Modified: Use select() with await for async
    result = await db.execute(
        select(TestSessionModel).where(TestSessionModel.id == session_id)
    )
    session = result.scalar_one_or_none()
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
        # Original code: result = await test_engine.start_test_session(..., db=db)
        # Modified: Removed db parameter (Wave 6 - Task 12) - background task creates its own session
        result = await test_engine.start_test_session(
            session_id=session_id,
            serial_number=session.serial_number,
            station_id=session.station_id
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting test: {str(e)}")


@router.post("/sessions/{session_id}/stop", response_model=dict)
async def stop_test_session(
    session_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Stop a running test session

    Args:
        session_id: Test session ID
        db: Async database session
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


@router.get("/sessions/export")
async def export_test_sessions_csv(
    station_id: int = None,
    project_id: int = None,
    serial_number: str = None,
    test_plan_name: str = None,
    final_result: str = None,
    start_date: str = None,
    end_date: str = None,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Export test sessions and their results as CSV

    Uses same filter parameters as GET /sessions.
    Returns a CSV file with session summary rows followed by detail result rows.
    """
    import csv
    import io
    from fastapi.responses import StreamingResponse
    from app.models.station import Station as StationModel
    from app.models.project import Project as ProjectModel

    # Original code: query = db.query(TestSessionModel) with .filter().join() chaining
    # Modified: Use select() with await for async
    stmt = select(TestSessionModel)

    if station_id:
        stmt = stmt.where(TestSessionModel.station_id == station_id)

    if project_id:
        stmt = stmt.join(StationModel, TestSessionModel.station_id == StationModel.id)\
                     .where(StationModel.project_id == project_id)

    if serial_number:
        stmt = stmt.where(
            TestSessionModel.serial_number.like(func.concat('%', serial_number, '%'))
        )

    if final_result:
        stmt = stmt.where(TestSessionModel.final_result == final_result)

    if start_date:
        stmt = stmt.where(TestSessionModel.start_time >= start_date)

    if end_date:
        stmt = stmt.where(TestSessionModel.start_time <= end_date)

    if test_plan_name:
        stmt = stmt.where(
            exists(
                select(TestResultModel.id).where(
                    TestResultModel.session_id == TestSessionModel.id
                ).join(TestPlan, TestResultModel.test_plan_id == TestPlan.id)
                .where(TestPlan.test_plan_name == test_plan_name)
            )
        )

    result = await db.execute(stmt.order_by(desc(TestSessionModel.start_time)))
    sessions = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        'Session ID', '序號', '站別 ID', '測試計劃', '最終結果',
        '開始時間', '結束時間', '測試時長(秒)',
        '總項目', '通過', '失敗',
        '項次', '測試項目', '測量值', '下限', '上限', '單位', '結果', '錯誤訊息', '執行時間(ms)'
    ])

    for session in sessions:
        # Original code: results = db.query(TestResultModel).filter(...).order_by(...).all()
        # Modified: Use select() with await for async
        result = await db.execute(
            select(TestResultModel)
            .where(TestResultModel.session_id == session.id)
            .order_by(TestResultModel.item_no)
        )
        results = result.scalars().all()

        # Get test_plan_name from first result
        plan_name = None
        if results and results[0].test_plan_id:
            first_result = results[0]
            # Original code: plan = db.query(TestPlan).filter(TestPlan.id == ...).first()
            # Modified: Use select() with await for async
            result = await db.execute(
                select(TestPlan).where(TestPlan.id == first_result.test_plan_id)
            )
            plan = result.scalar_one_or_none()
            if plan:
                plan_name = plan.test_plan_name

        if results:
            for i, r in enumerate(results):
                writer.writerow([
                    session.id if i == 0 else '',
                    session.serial_number if i == 0 else '',
                    session.station_id if i == 0 else '',
                    plan_name if i == 0 else '',
                    session.final_result if i == 0 else '',
                    session.start_time.isoformat() if i == 0 and session.start_time else '',
                    session.end_time.isoformat() if i == 0 and session.end_time else '',
                    session.test_duration_seconds if i == 0 else '',
                    session.total_items if i == 0 else '',
                    session.pass_items if i == 0 else '',
                    session.fail_items if i == 0 else '',
                    r.item_no,
                    r.item_name,
                    r.measured_value,
                    r.lower_limit,
                    r.upper_limit,
                    r.unit or '',
                    r.result,
                    r.error_message or '',
                    r.execution_duration_ms or ''
                ])
        else:
            writer.writerow([
                session.id, session.serial_number, session.station_id,
                plan_name, session.final_result,
                session.start_time.isoformat() if session.start_time else '',
                session.end_time.isoformat() if session.end_time else '',
                session.test_duration_seconds,
                session.total_items, session.pass_items, session.fail_items,
                '', '', '', '', '', '', '', '', ''
            ])

    output.seek(0)
    filename = f"test-results-{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    return StreamingResponse(
        iter([output.getvalue().encode('utf-8-sig')]),  # utf-8-sig for Excel BOM
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/sessions/{session_id}", response_model=TestSession)
async def get_test_session(
    session_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Get test session by ID"""
    # Original code: session = db.query(TestSessionModel).filter(...).first()
    # Modified: Use select() with await for async
    result = await db.execute(
        select(TestSessionModel).where(TestSessionModel.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Test session not found")

    return session


@router.get("/sessions/{session_id}/status", response_model=TestSessionStatus)
async def get_test_session_status(
    session_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Get real-time test session status

    Args:
        session_id: Test session ID
        db: Async database session
        current_user: Current authenticated user

    Returns:
        Test session status with progress information
    """
    # Original code: session = db.query(TestSessionModel).filter(...).first()
    # Modified: Use select() with await for async
    result = await db.execute(
        select(TestSessionModel).where(TestSessionModel.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Test session not found")

    # Original code: results = db.query(TestResultModel).filter(...).all()
    # Modified: Use select() with await for async
    result = await db.execute(
        select(TestResultModel).where(TestResultModel.session_id == session_id)
    )
    results = result.scalars().all()
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
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Upload a single test result

    Args:
        session_id: Test session ID
        result_data: Test result data
        db: Async database session
        current_user: Current authenticated user

    Returns:
        Created test result
    """
    # Original code: session = db.query(TestSessionModel).filter(...).first()
    # Modified: Use select() with await for async
    result = await db.execute(
        select(TestSessionModel).where(TestSessionModel.id == session_id)
    )
    session = result.scalar_one_or_none()
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
            execution_duration_ms=result_data.execution_duration_ms,
            wall_time_ms=result_data.wall_time_ms,
            # 修改(2026-03-16): 明確傳入 Asia/Taipei，取代 server_default UTC
            test_time=datetime.now(_TZ_TAIPEI),
        )
        db.add(db_result)
        await db.commit()
        await db.refresh(db_result)

        return db_result
    except Exception as e:
        await db.rollback()
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
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Batch upload multiple test results

    Args:
        session_id: Test session ID
        batch_data: Batch of test results
        db: Async database session
        current_user: Current authenticated user

    Returns:
        Number of results created
    """
    # Original code: session = db.query(TestSessionModel).filter(...).first()
    # Modified: Use select() with await for async
    result = await db.execute(
        select(TestSessionModel).where(TestSessionModel.id == session_id)
    )
    session = result.scalar_one_or_none()
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
                execution_duration_ms=result_data.execution_duration_ms,
                wall_time_ms=result_data.wall_time_ms,
                # 修改(2026-03-16): 明確傳入 Asia/Taipei，取代 server_default UTC
                test_time=datetime.now(_TZ_TAIPEI),
            )
            db.add(db_result)
            created_count += 1

        await db.commit()

        return {
            "message": "Test results created successfully",
            "created_count": created_count
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Batch insert failed, all changes rolled back: {str(e)}"
        )


@router.post("/sessions/{session_id}/complete", response_model=TestSession)
async def complete_test_session(
    session_id: int,
    complete_data: TestSessionComplete,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Complete a test session

    Args:
        session_id: Test session ID
        complete_data: Test completion data
        db: Async database session
        current_user: Current authenticated user

    Returns:
        Updated test session
    """
    # Original code: session = db.query(TestSessionModel).filter(...).first()
    # Modified: Use select() with await for async
    result = await db.execute(
        select(TestSessionModel).where(TestSessionModel.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Test session not found")

    # Check if already completed
    if session.end_time:
        raise HTTPException(
            status_code=400,
            detail="Test session already completed"
        )

    # Update session
    # 修改(2026-03-16): 改用 Asia/Taipei
    # session.end_time = datetime.utcnow()
    session.end_time = datetime.now(_TZ_TAIPEI)
    session.final_result = complete_data.final_result
    session.total_items = complete_data.total_items
    session.pass_items = complete_data.pass_items
    session.fail_items = complete_data.fail_items
    session.test_duration_seconds = complete_data.test_duration_seconds

    await db.commit()
    await db.refresh(session)

    # Original: CSV report was not generated after completion
    # Modified: Auto-generate CSV report to support frontend-driven mode
    # Refer to report generation logic in test_engine.py:_finalize_test_session()
    if REPORT_SERVICE_AVAILABLE and report_service:
        try:
            # Original code: report_path = report_service.save_session_report(session_id, db)
            # Modified: Use await for async call (Wave 6 - Task 13)
            report_path = await report_service.save_session_report(session_id, db)
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
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    ✅ Added: Get real-time logs for a test session

    Retrieves logs from Redis for real-time monitoring during test execution.
    If Redis is not enabled, returns an empty list.

    Args:
        session_id: Test session ID
        limit: Maximum number of log entries to retrieve (default: 100)
        db: Async database session
        current_user: Current authenticated user

    Returns:
        Dictionary with logs list and count
    """
    # Original code: session = db.query(TestSessionModel).filter(...).first()
    # Modified: Use select() with await for async
    result = await db.execute(
        select(TestSessionModel).where(TestSessionModel.id == session_id)
    )
    session = result.scalar_one_or_none()
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
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Get all test results for a session

    Args:
        session_id: Test session ID
        db: Async database session
        current_user: Current authenticated user

    Returns:
        List of test results ordered by item_no
    """
    # Original code: session = db.query(TestSessionModel).filter(...).first()
    # Modified: Use select() with await for async
    result = await db.execute(
        select(TestSessionModel).where(TestSessionModel.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Test session not found")

    # Get results
    # Original code: results = db.query(TestResultModel).filter(...).order_by(...).all()
    # Modified: Use select() with await for async
    result = await db.execute(
        select(TestResultModel)
        .where(TestResultModel.session_id == session_id)
        .order_by(TestResultModel.item_no)
    )
    results = result.scalars().all()

    return results


@router.get("/sessions", response_model=List[TestSession])
async def list_test_sessions(
    station_id: int = None,
    project_id: int = None,
    serial_number: str = None,
    test_plan_name: str = None,
    final_result: str = None,
    start_date: str = None,
    end_date: str = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    List test sessions with optional filtering

    Args:
        station_id: Filter by station ID
        project_id: Filter by project ID (via station join)
        serial_number: Filter by serial number (partial match)
        test_plan_name: Filter by test plan name (via test_results join)
        final_result: Filter by final result (PASS/FAIL/ABORT)
        start_date: Filter sessions starting after this datetime (ISO format)
        end_date: Filter sessions starting before this datetime (ISO format)
        limit: Maximum number of results
        offset: Number of results to skip
        db: Async database session
        current_user: Current authenticated user

    Returns:
        List of test sessions ordered by start_time descending
    """
    from app.models.station import Station as StationModel

    # Original code: query = db.query(TestSessionModel) with .filter().join() chaining
    # Modified: Use select() with await for async
    stmt = select(TestSessionModel)

    if station_id:
        stmt = stmt.where(TestSessionModel.station_id == station_id)

    # Filter by project_id via station join
    if project_id:
        stmt = stmt.join(StationModel, TestSessionModel.station_id == StationModel.id)\
                     .where(StationModel.project_id == project_id)

    # Modified: Use parameterized query to prevent SQL injection risk
    if serial_number:
        stmt = stmt.where(
            TestSessionModel.serial_number.like(func.concat('%', serial_number, '%'))
        )

    if final_result:
        stmt = stmt.where(TestSessionModel.final_result == final_result)

    if start_date:
        stmt = stmt.where(TestSessionModel.start_time >= start_date)

    if end_date:
        stmt = stmt.where(TestSessionModel.start_time <= end_date)

    # Filter by test_plan_name via test_results → test_plans join
    if test_plan_name:
        stmt = stmt.where(
            exists(
                select(TestResultModel.id).where(
                    TestResultModel.session_id == TestSessionModel.id
                ).join(TestPlan, TestResultModel.test_plan_id == TestPlan.id)
                .where(TestPlan.test_plan_name == test_plan_name)
            )
        )

    result = await db.execute(
        stmt.order_by(desc(TestSessionModel.start_time))
        .limit(limit)
        .offset(offset)
    )
    sessions = result.scalars().all()

    # Populate test_plan_name for each session from its first test result's plan
    result_list = []
    for session in sessions:
        # Original code: first_result = db.query(TestResultModel).filter(...).first()
        # Modified: Use select() with await for async
        # FIX: Add .limit(1) since scalar_one_or_none() expects 0 or 1 row,
        # but a session has multiple test results. Using .first() pattern.
        result = await db.execute(
            select(TestResultModel)
            .where(TestResultModel.session_id == session.id)
            .order_by(TestResultModel.id)  # Ensure deterministic ordering
            .limit(1)
        )
        first_result = result.scalar_one_or_none()

        plan_name = None
        if first_result and first_result.test_plan_id:
            # Original code: plan = db.query(TestPlan).filter(TestPlan.id == ...).first()
            # Modified: Use select() with await for async
            result = await db.execute(
                select(TestPlan).where(TestPlan.id == first_result.test_plan_id)
            )
            plan = result.scalar_one_or_none()
            if plan:
                plan_name = plan.test_plan_name
        session_dict = {c.name: getattr(session, c.name) for c in session.__table__.columns}
        session_dict['test_plan_name'] = plan_name
        result_list.append(TestSession(**session_dict))

    return result_list


@router.delete("/sessions")
async def bulk_delete_test_sessions(
    body: BulkDeleteSessionsRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Bulk delete test sessions and all associated test_results (admin only)
    """
    PermissionChecker.check_admin(current_user, "bulk delete test sessions")

    if not body.session_ids:
        raise HTTPException(status_code=400, detail="No session IDs provided")

    try:
        # Confirm at least some sessions exist
        result = await db.execute(
            select(TestSessionModel).where(TestSessionModel.id.in_(body.session_ids))
        )
        found_sessions = result.scalars().all()
        found_ids = [s.id for s in found_sessions]

        if not found_ids:
            raise HTTPException(status_code=404, detail="No matching sessions found")

        # Delete associated test_results first (foreign key)
        await db.execute(
            sa_delete(TestResultModel).where(TestResultModel.session_id.in_(found_ids))
        )

        # Delete sessions
        await db.execute(
            sa_delete(TestSessionModel).where(TestSessionModel.id.in_(found_ids))
        )

        await db.commit()

        return {
            "message": f"Deleted {len(found_ids)} session(s) and associated results",
            "deleted_session_ids": found_ids
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to bulk delete sessions: {str(e)}"
        )
