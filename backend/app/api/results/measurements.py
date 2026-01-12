"""
Measurement Result Query Endpoints

Individual measurement result endpoints.
Extracted from measurement_results.py lines 261-317.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.dependencies import get_current_active_user
from app.models.test_result import TestResult as TestResultModel

router = APIRouter()


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


@router.get("/results", response_model=List[MeasurementResultResponse])
async def get_measurement_results(
    skip: int = Query(0, ge=0),
    limit: int = Query(1000, ge=1, le=5000),
    session_id: int | None = Query(None),
    test_item_name: str | None = Query(None),
    result_status: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Get measurement results with filtering

    Allows detailed analysis of measurement data similar to PDTool4's
    result analysis capabilities.
    """
    try:
        query = db.query(TestResultModel)

        # Apply filters
        if session_id:
            query = query.filter(TestResultModel.test_session_id == session_id)

        if test_item_name:
            query = query.filter(TestResultModel.item_name.ilike(f"%{test_item_name}%"))

        if result_status:
            query = query.filter(TestResultModel.result == result_status)

        # Order by creation time
        results = query.order_by(desc(TestResultModel.created_at))\
                      .offset(skip)\
                      .limit(limit)\
                      .all()

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

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve measurement results: {str(e)}"
        )
