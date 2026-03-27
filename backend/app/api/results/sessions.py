"""
Measurement Result Session Endpoints

Session listing and detail endpoints.
Extracted from measurement_results.py lines 81-258.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
# Original code: from sqlalchemy.orm import Session
# Modified: Use async session for async DB migration (Wave 5)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from typing import List
from datetime import date, datetime
from pydantic import BaseModel

# Original code: from app.core.database import get_db
# Modified: Use async DB dependency
from app.core.database import get_async_db
from app.core.api_helpers import calculate_test_statistics
from app.core.constants import VALID_SESSION_STATUSES
from app.dependencies import get_current_active_user
from app.models.test_result import TestResult as TestResultModel
from app.models.test_session import TestSession as TestSessionModel
from app.models.project import Project as ProjectModel
from app.models.station import Station as StationModel

router = APIRouter()


def convert_results_to_response(results: List[TestResultModel]) -> List['MeasurementResultResponse']:
    """
    Convert database results to API response format.

    Extracts duplicate conversion logic to improve maintainability.

    Args:
        results: List of TestResult database models

    Returns:
        List of MeasurementResultResponse schemas
    """
    return [
        MeasurementResultResponse(
            id=r.id,
            # Fixed: model field is session_id, not test_session_id
            test_session_id=r.session_id,
            item_no=r.item_no,
            item_name=r.item_name,
            result=r.result,
            measured_value=r.measured_value,
            # Fixed: model fields are lower_limit/upper_limit, not min_limit/max_limit
            min_limit=r.lower_limit,
            max_limit=r.upper_limit,
            error_message=r.error_message,
            execution_duration_ms=r.execution_duration_ms,
            # Fixed: model field is test_time, not created_at
            created_at=r.test_time
        )
        for r in results
    ]


class MeasurementResultResponse(BaseModel):
    """Response model for measurement result"""
    id: int
    test_session_id: int
    item_no: int
    item_name: str
    result: str
    measured_value: str | None = None
    min_limit: float | None = None
    max_limit: float | None = None
    error_message: str | None = None
    execution_duration_ms: int | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class TestSessionResponse(BaseModel):
    """Response model for test session with results"""
    id: int
    project_name: str
    station_name: str
    serial_number: str
    # Fixed: renamed from operator_id to match model (user_id stored, username exposed)
    operator_id: str | None = None
    # Fixed: renamed from status to final_result to match model
    status: str
    # Fixed: renamed from started_at to match model field start_time
    started_at: datetime
    # Fixed: renamed from completed_at to match model field end_time
    completed_at: datetime | None = None
    total_tests: int
    passed_tests: int
    failed_tests: int
    error_tests: int
    results: List[MeasurementResultResponse] = []


@router.get("/sessions", response_model=List[TestSessionResponse])
async def get_test_sessions(
    # Original code: skip parameter (inconsistent with tests.py which uses offset)
    # Modified: Renamed to offset for API consistency - FastAPI convention uses offset
    offset: int = Query(0, ge=0, description="Number of records to skip (pagination)"),
    limit: int = Query(100, ge=1, le=1000),
    # Original code: No validation on query parameters
    # project_id: int | None = Query(None),
    # station_id: int | None = Query(None),
    # status: str | None = Query(None),
    # Refactored: Add validation constraints
    project_id: int | None = Query(None, gt=0, description="Project ID (must be positive)"),
    station_id: int | None = Query(None, gt=0, description="Station ID (must be positive)"),
    status: str | None = Query(
        None,
        pattern=f"^({'|'.join(VALID_SESSION_STATUSES)})$",
        description=f"Session status (valid values: {', '.join(VALID_SESSION_STATUSES)})"
    ),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Get test sessions with optional filtering

    Provides comprehensive session listing similar to PDTool4's log browsing
    functionality where users can view test history and results.
    """
    try:
        # Fixed: join order follows FK chain: TestSession.station_id → Station → Project
        # Use selectinload to eagerly load relationships (required for async SQLAlchemy)
        stmt = (
            select(TestSessionModel)
            .join(StationModel)
            .join(ProjectModel)
            .options(selectinload(TestSessionModel.station).selectinload(StationModel.project))
        )

        # Apply filters
        if project_id:
            # Fixed: TestSession has no project_id; filter via Station.project_id
            stmt = stmt.where(StationModel.project_id == project_id)

        if station_id:
            stmt = stmt.where(TestSessionModel.station_id == station_id)

        if status:
            # Fixed: model field is final_result, not status
            stmt = stmt.where(TestSessionModel.final_result == status)

        if date_from:
            # Fixed: model field is start_time, not started_at
            stmt = stmt.where(TestSessionModel.start_time >= date_from)

        if date_to:
            # Fixed: model field is start_time, not started_at
            stmt = stmt.where(TestSessionModel.start_time <= date_to)

        # Order by most recent first
        result = await db.execute(
            stmt.order_by(desc(TestSessionModel.start_time))
                .offset(offset)
                .limit(limit)
        )
        sessions = result.scalars().all()

        # Build response with session statistics
        response = []
        for session in sessions:
            # Get test results for this session
            # Original code: results = db.query(TestResultModel).filter(...).all()
            # Modified: Use select() with await
            result = await db.execute(
                select(TestResultModel).where(TestResultModel.session_id == session.id)
            )
            results = result.scalars().all()

            # Original code: Duplicated statistics calculation
            # Refactored: Use calculate_test_statistics helper
            stats = calculate_test_statistics(results)

            # Original code: Duplicated result conversion logic
            # Refactored: Use convert_results_to_response helper
            result_responses = convert_results_to_response(results)

            response.append(TestSessionResponse(
                id=session.id,
                # Fixed: project accessed via station relationship; field is project_name
                project_name=session.station.project.project_name,
                # Fixed: field is station_name, not name
                station_name=session.station.station_name,
                serial_number=session.serial_number,
                # Fixed: no operator_id on model; expose user_id as string
                operator_id=str(session.user_id) if session.user_id else None,
                # Fixed: field is final_result, not status
                status=str(session.final_result.value) if session.final_result else "UNKNOWN",
                # Fixed: field is start_time, not started_at
                started_at=session.start_time,
                # Fixed: field is end_time, not completed_at
                completed_at=session.end_time,
                results=result_responses,
                **stats
            ))

        return response

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve test sessions: {str(e)}"
        )


@router.get("/sessions/{session_id}", response_model=TestSessionResponse)
async def get_test_session(
    session_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Get detailed test session with all measurement results

    Equivalent to PDTool4's detailed test log viewing where users can
    examine all test points and their results for a specific session.
    """
    try:
        # Fixed: join order follows FK chain + eager load relationships for async
        result = await db.execute(
            select(TestSessionModel)
            .join(StationModel)
            .join(ProjectModel)
            .options(selectinload(TestSessionModel.station).selectinload(StationModel.project))
            .where(TestSessionModel.id == session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"Test session {session_id} not found"
            )

        # Get all measurement results for this session
        # Original code: results = db.query(TestResultModel).filter(...).order_by(...).all()
        # Modified: Use select() with await
        result = await db.execute(
            select(TestResultModel)
            .where(TestResultModel.session_id == session_id)
            .order_by(TestResultModel.item_no)
        )
        results = result.scalars().all()

        # Original code: Duplicated statistics calculation
        # Refactored: Use calculate_test_statistics helper
        stats = calculate_test_statistics(results)

        # Original code: Duplicated result conversion logic
        # Refactored: Use convert_results_to_response helper
        result_responses = convert_results_to_response(results)

        return TestSessionResponse(
            id=session.id,
            # Fixed: project accessed via station relationship; field is project_name
            project_name=session.station.project.project_name,
            # Fixed: field is station_name, not name
            station_name=session.station.station_name,
            serial_number=session.serial_number,
            # Fixed: no operator_id on model; expose user_id as string
            operator_id=str(session.user_id) if session.user_id else None,
            # Fixed: field is final_result, not status
            status=str(session.final_result.value) if session.final_result else "UNKNOWN",
            # Fixed: field is start_time, not started_at
            started_at=session.start_time,
            # Fixed: field is end_time, not completed_at
            completed_at=session.end_time,
            results=result_responses,
            **stats
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve test session: {str(e)}"
        )
