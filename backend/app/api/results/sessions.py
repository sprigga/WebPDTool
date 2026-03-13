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
            test_session_id=r.test_session_id,
            item_no=r.item_no,
            item_name=r.item_name,
            result=r.result,
            measured_value=r.measured_value,
            min_limit=r.min_limit,
            max_limit=r.max_limit,
            error_message=r.error_message,
            execution_duration_ms=r.execution_duration_ms,
            created_at=r.created_at
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
    measured_value: float | None = None
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
    operator_id: str | None = None
    status: str
    started_at: datetime
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
        # Original code: query = db.query(TestSessionModel).join(ProjectModel).join(StationModel)
        # Modified: Use select() with await db.execute() for async
        stmt = select(TestSessionModel).join(ProjectModel).join(StationModel)

        # Apply filters
        if project_id:
            stmt = stmt.where(TestSessionModel.project_id == project_id)

        if station_id:
            stmt = stmt.where(TestSessionModel.station_id == station_id)

        if status:
            stmt = stmt.where(TestSessionModel.status == status)

        if date_from:
            stmt = stmt.where(TestSessionModel.started_at >= date_from)

        if date_to:
            stmt = stmt.where(TestSessionModel.started_at <= date_to)

        # Order by most recent first
        result = await db.execute(
            stmt.order_by(desc(TestSessionModel.started_at))
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
                select(TestResultModel).where(TestResultModel.test_session_id == session.id)
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
                project_name=session.project.name,
                station_name=session.station.name,
                serial_number=session.serial_number,
                operator_id=session.operator_id,
                status=session.status,
                started_at=session.started_at,
                completed_at=session.completed_at,
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
        # Original code: session = db.query(TestSessionModel).join(...).filter(...).first()
        # Modified: Use select() with await
        result = await db.execute(
            select(TestSessionModel)
            .join(ProjectModel)
            .join(StationModel)
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
            .where(TestResultModel.test_session_id == session_id)
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
            project_name=session.project.name,
            station_name=session.station.name,
            serial_number=session.serial_number,
            operator_id=session.operator_id,
            status=session.status,
            started_at=session.started_at,
            completed_at=session.completed_at,
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
