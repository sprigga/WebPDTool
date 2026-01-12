"""
Test Plan Query Endpoints

GET endpoints for retrieving test plans, names, and maps.
Extracted from testplans.py lines 29-205.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.api_helpers import get_entity_or_404
from app.dependencies import get_current_active_user
from app.models.station import Station
from app.schemas.testplan import TestPlan as TestPlanSchema
from app.services.test_plan_service import test_plan_service

router = APIRouter()


@router.get("/stations/{station_id}/testplan", response_model=List[TestPlanSchema])
async def get_station_testplan(
    station_id: int,
    project_id: Optional[int] = None,
    enabled_only: bool = True,
    test_plan_name: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Get test plan for a specific station

    整合 TestPlanService.get_test_plans()
    對應 PDTool4 test_point_map.py: TestPointMap 的查詢功能

    Args:
        station_id: Station ID
        project_id: Project ID (查詢參數)
        enabled_only: Return only enabled test items (default: True)
        test_plan_name: Optional test plan name to filter by
        db: Database session
        current_user: Current authenticated user

    Returns:
        List of test plan items ordered by sequence
    """
    # Original code: Direct query with 404 check
    # Refactored: Use get_entity_or_404 helper
    station = get_entity_or_404(db, Station, station_id, "Station not found")

    # 如果未提供 project_id,嘗試從站別獲取預設專案
    if project_id is None and station.project_id:
        project_id = station.project_id

    if project_id is None:
        raise HTTPException(
            status_code=400,
            detail="project_id is required (either as query parameter or configured in station)"
        )

    try:
        # 使用 TestPlanService 取得測試計畫列表
        test_plans = test_plan_service.get_test_plans(
            db=db,
            project_id=project_id,
            station_id=station_id,
            test_plan_name=test_plan_name,
            enabled_only=enabled_only
        )
        return test_plans
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get test plan: {str(e)}"
        )


@router.get("/stations/{station_id}/testplan-names", response_model=List[str])
async def get_station_testplan_names(
    station_id: int,
    project_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Get distinct test plan names for a specific station

    整合 TestPlanService.get_test_plan_names()

    Args:
        station_id: Station ID
        project_id: Project ID (查詢參數)
        db: Database session
        current_user: Current authenticated user

    Returns:
        List of distinct test plan names
    """
    # Original code: Direct query with 404 check
    # Refactored: Use get_entity_or_404 helper
    station = get_entity_or_404(db, Station, station_id, "Station not found")

    # 如果未提供 project_id,嘗試從站別獲取預設專案
    if project_id is None and station.project_id:
        project_id = station.project_id

    if project_id is None:
        raise HTTPException(
            status_code=400,
            detail="project_id is required (either as query parameter or configured in station)"
        )

    try:
        # 使用 TestPlanService 取得測試計畫名稱列表
        test_plan_names = test_plan_service.get_test_plan_names(
            db=db,
            project_id=project_id,
            station_id=station_id
        )
        return test_plan_names
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get test plan names: {str(e)}"
        )


@router.get("/stations/{station_id}/testplan-map")
async def get_station_testplan_map(
    station_id: int,
    project_id: int,
    test_plan_name: Optional[str] = None,
    enabled_only: bool = True,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Get TestPlanMap for a specific station

    新增端點 - 對應 PDTool4 test_point_map.py: new_test_point_map()

    Args:
        station_id: Station ID
        project_id: Project ID
        test_plan_name: Optional test plan name to filter by
        enabled_only: Return only enabled test items (default: True)
        db: Database session
        current_user: Current authenticated user

    Returns:
        TestPlanMap information including execution statistics
    """
    # Original code: Direct query with 404 check
    # Refactored: Use get_entity_or_404 helper
    station = get_entity_or_404(db, Station, station_id, "Station not found")

    try:
        # 使用 TestPlanService 建立 TestPointMap
        test_plan_map = test_plan_service.new_test_plan_map(
            db=db,
            project_id=project_id,
            station_id=station_id,
            test_plan_name=test_plan_name,
            enabled_only=enabled_only
        )

        # 回傳 TestPointMap 資訊
        return {
            "station_id": station_id,
            "project_id": project_id,
            "test_plan_name": test_plan_name,
            "total_test_points": len(test_plan_map),
            "test_points": [
                {
                    "unique_id": tp.unique_id,
                    "name": tp.name,
                    "item_key": tp.ItemKey,
                    "executed": tp.executed,
                    "passed": tp.passed,
                    "value": tp.value,
                    "limit_type": tp.limit_type.__class__.__name__,
                    "value_type": tp.value_type.__class__.__name__,
                    "lower_limit": tp.lower_limit,
                    "upper_limit": tp.upper_limit,
                    "unit": tp.unit
                }
                for tp in test_plan_map.values()
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create TestPointMap: {str(e)}"
        )
