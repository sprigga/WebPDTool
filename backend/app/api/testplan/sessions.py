"""
Test Plan Session Results Endpoint

Session-related test result endpoint.
Extracted from testplans.py lines 624-654.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies import get_current_active_user
from app.services.test_plan_service import test_plan_service

router = APIRouter()


@router.get("/sessions/{session_id}/test-results")
async def get_session_test_results(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Get test results for a session

    使用 TestPlanService.get_session_test_results()

    Args:
        session_id: Test session ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        List of test results
    """
    try:
        results = test_plan_service.get_session_test_results(db, session_id)
        return {
            "session_id": session_id,
            "results": results,
            "total_count": len(results)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get session test results: {str(e)}"
        )
