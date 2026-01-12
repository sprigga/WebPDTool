"""
Measurement Result Summary Endpoint

Summary statistics endpoint.
Extracted from measurement_results.py lines 320-399.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import date, timedelta, datetime as dt
from pydantic import BaseModel

from app.core.database import get_db
from app.dependencies import get_current_active_user
from app.models.test_result import TestResult as TestResultModel
from app.models.test_session import TestSession as TestSessionModel

router = APIRouter()


class ResultSummary(BaseModel):
    """Summary statistics for measurement results"""
    total_sessions: int
    passed_sessions: int
    failed_sessions: int
    pass_rate: float
    total_measurements: int
    avg_execution_time_ms: float
    most_common_failures: List[Dict[str, Any]]


@router.get("/summary", response_model=ResultSummary)
async def get_result_summary(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    project_id: int | None = Query(None),
    station_id: int | None = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Get summary statistics for measurement results

    Provides overview statistics similar to PDTool4's test summary reports
    that show pass/fail rates and common failure modes.
    """
    try:
        # Base queries
        session_query = db.query(TestSessionModel)
        result_query = db.query(TestResultModel).join(TestSessionModel)

        # Apply date filters
        if date_from:
            session_query = session_query.filter(TestSessionModel.started_at >= date_from)
            result_query = result_query.filter(TestSessionModel.started_at >= date_from)

        if date_to:
            session_query = session_query.filter(TestSessionModel.started_at <= date_to)
            result_query = result_query.filter(TestSessionModel.started_at <= date_to)

        # Apply project/station filters
        if project_id:
            session_query = session_query.filter(TestSessionModel.project_id == project_id)
            result_query = result_query.filter(TestSessionModel.project_id == project_id)

        if station_id:
            session_query = session_query.filter(TestSessionModel.station_id == station_id)
            result_query = result_query.filter(TestSessionModel.station_id == station_id)

        # Calculate session statistics
        all_sessions = session_query.all()
        total_sessions = len(all_sessions)
        passed_sessions = sum(1 for s in all_sessions if s.status == "PASSED")
        failed_sessions = sum(1 for s in all_sessions if s.status == "FAILED")
        pass_rate = (passed_sessions / total_sessions * 100) if total_sessions > 0 else 0

        # Calculate measurement statistics
        all_results = result_query.all()
        total_measurements = len(all_results)

        # Calculate average execution time
        execution_times = [r.execution_duration_ms for r in all_results if r.execution_duration_ms]
        avg_execution_time_ms = sum(execution_times) / len(execution_times) if execution_times else 0

        # Find most common failures
        failed_results = [r for r in all_results if r.result == "FAIL"]
        failure_counts = {}
        for result in failed_results:
            key = result.item_name
            failure_counts[key] = failure_counts.get(key, 0) + 1

        most_common_failures = [
            {"test_item": item, "failure_count": count, "failure_rate": count/total_measurements*100}
            for item, count in sorted(failure_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        ]

        return ResultSummary(
            total_sessions=total_sessions,
            passed_sessions=passed_sessions,
            failed_sessions=failed_sessions,
            pass_rate=round(pass_rate, 2),
            total_measurements=total_measurements,
            avg_execution_time_ms=round(avg_execution_time_ms, 2),
            most_common_failures=most_common_failures
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate result summary: {str(e)}"
        )
