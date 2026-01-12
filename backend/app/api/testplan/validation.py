"""
Test Plan Validation Endpoint

Test point validation endpoint.
Extracted from testplans.py lines 546-621.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.dependencies import get_current_active_user
from app.services.test_plan_service import test_plan_service

router = APIRouter()


@router.post("/testplans/validate-test-point")
async def validate_test_point(
    unique_id: str,
    measured_value: str,
    run_all_test: str = "OFF",
    project_id: int = None,
    station_id: int = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Validate a test point with measured value

    新增端點 - 對應 PDTool4 test_point_runAllTest.py: TestPoint.execute()

    Args:
        unique_id: Test point unique_id (item_name)
        measured_value: Measured value to validate
        run_all_test: "ON" continue on error, "OFF" stop on error
        project_id: Project ID
        station_id: Station ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Validation result
    """
    try:
        # 建立 TestPointMap
        test_plan_map = test_plan_service.new_test_plan_map(
            db=db,
            project_id=project_id,
            station_id=station_id
        )

        # 取得測試點
        test_point = test_plan_map.get_test_point(unique_id)
        if not test_point:
            raise HTTPException(
                status_code=404,
                detail=f"Test point '{unique_id}' not found"
            )

        # 驗證測試點
        passed, error_message = test_plan_service.validate_test_point(
            test_point=test_point,
            measured_value=measured_value,
            run_all_test=run_all_test
        )

        return {
            "unique_id": unique_id,
            "measured_value": measured_value,
            "result": "PASS" if passed else "FAIL",
            "passed": passed,
            "error_message": error_message,
            "test_point": {
                "name": test_point.name,
                "item_key": test_point.ItemKey,
                "executed": test_point.executed,
                "value": test_point.value,
                "limit_type": test_point.limit_type.__class__.__name__,
                "value_type": test_point.value_type.__class__.__name__,
                "lower_limit": test_point.lower_limit,
                "upper_limit": test_point.upper_limit,
                "unit": test_point.unit
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to validate test point: {str(e)}"
        )
