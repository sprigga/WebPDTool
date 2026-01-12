"""
Test Plan Management API Endpoints
重構版本 - 基於 PDTool4 test_point_map.py 設計模式
整合 TestPlanService 層進行業務邏輯處理
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional

from app.core.database import get_db
from app.dependencies import get_current_active_user
from app.models.testplan import TestPlan
from app.models.station import Station
from app.schemas.testplan import (
    TestPlan as TestPlanSchema,
    TestPlanCreate,
    TestPlanUpdate,
    TestPlanUploadResponse,
    TestPlanBulkDelete,
    TestPlanReorder
)
from app.services.test_plan_service import test_plan_service
from app.utils.csv_parser import TestPlanCSVParser, CSVParseError

router = APIRouter()


@router.get("/stations/{station_id}/testplan", response_model=List[TestPlanSchema])
async def get_station_testplan(
    station_id: int,
    project_id: Optional[int] = None,  # 原有程式碼缺少 Optional 且未設為查詢參數,導致前端無法正確傳遞
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
    # Verify station exists
    station = db.query(Station).filter(Station.id == station_id).first()
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")

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
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get test plan: {str(e)}"
        )


@router.get("/stations/{station_id}/testplan-names", response_model=List[str])
async def get_station_testplan_names(
    station_id: int,
    project_id: Optional[int] = None,  # 原有程式碼缺少 Optional 且未設為查詢參數,導致前端無法正確傳遞
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
    # Verify station exists
    station = db.query(Station).filter(Station.id == station_id).first()
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")

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
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
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
    # Verify station exists
    station = db.query(Station).filter(Station.id == station_id).first()
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")

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
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create TestPointMap: {str(e)}"
        )


@router.post("/stations/{station_id}/testplan/upload", response_model=TestPlanUploadResponse)
async def upload_testplan_csv(
    station_id: int,
    file: UploadFile = File(..., description="CSV test plan file"),
    project_id: int = Form(..., description="Project ID this test plan belongs to"),
    test_plan_name: Optional[str] = Form(None, description="Test plan name"),
    replace_existing: bool = Form(default=True, description="Replace existing test plan"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Upload and parse CSV test plan file

    Args:
        station_id: Station ID to upload test plan for
        file: CSV file upload
        project_id: Project ID this test plan belongs to
        replace_existing: Whether to replace existing test plan (default: True)
        db: Database session
        current_user: Current authenticated user

    Returns:
        Upload result with statistics
    """
    # Check permissions (only admin and engineer can upload)
    user_role = current_user.get("role")
    if user_role not in ["admin", "engineer"]:
        raise HTTPException(
            status_code=403,
            detail="Only administrators and engineers can upload test plans"
        )

    # Verify station exists
    station = db.query(Station).filter(Station.id == station_id).first()
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")

    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only CSV files are supported"
        )

    try:
        # Read file content
        file_content = await file.read()

        # Parse CSV
        test_plan_dicts = TestPlanCSVParser.parse_and_convert(file_content)

        # If replace_existing, delete old test plan
        if replace_existing:
            db.query(TestPlan).filter(
                and_(TestPlan.project_id == project_id, TestPlan.station_id == station_id)
            ).delete()

        # Insert new test plan items
        created_count = 0
        errors = []

        for plan_dict in test_plan_dicts:
            try:
                # 使用 TestPlanService 建立測試計畫項目
                test_plan_data = {
                    **plan_dict,
                    'project_id': project_id,
                    'station_id': station_id,
                    'test_plan_name': test_plan_name
                }
                test_plan_service.create_test_plan(db, test_plan_data)
                created_count += 1
            except Exception as e:
                errors.append(f"Error creating item {plan_dict.get('item_name')}: {str(e)}")

        return TestPlanUploadResponse(
            message="Test plan uploaded successfully",
            project_id=project_id,
            station_id=station_id,
            total_items=len(test_plan_dicts),
            created_items=created_count,
            skipped_items=len(test_plan_dicts) - created_count,
            errors=errors if errors else None
        )

    except CSVParseError as e:
        raise HTTPException(status_code=400, detail=f"CSV parsing error: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error uploading test plan: {str(e)}")


@router.post("/testplans", response_model=TestPlanSchema, status_code=status.HTTP_201_CREATED)
async def create_testplan_item(
    testplan: TestPlanCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Create a single test plan item

    使用 TestPlanService.create_test_plan()

    Args:
        testplan: Test plan item data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Created test plan item
    """
    # Check permissions
    user_role = current_user.get("role")
    if user_role not in ["admin", "engineer"]:
        raise HTTPException(
            status_code=403,
            detail="Only administrators and engineers can create test plan items"
        )

    # Verify station exists
    station = db.query(Station).filter(Station.id == testplan.station_id).first()
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")

    try:
        # 使用 TestPlanService 建立測試計畫項目
        test_plan_data = testplan.dict()
        db_testplan = test_plan_service.create_test_plan(
            db=db,
            test_plan_data=test_plan_data,
            user_id=current_user.get("sub")
        )
        return db_testplan
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create test plan item: {str(e)}"
        )


@router.get("/testplans/{testplan_id}", response_model=TestPlanSchema)
async def get_testplan_item(
    testplan_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Get a specific test plan item by ID

    使用 TestPlanService.get_test_plan_by_id()
    """
    try:
        testplan = test_plan_service.get_test_plan_by_id(db, testplan_id)
        if not testplan:
            raise HTTPException(status_code=404, detail="Test plan item not found")
        return testplan
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get test plan item: {str(e)}"
        )


@router.put("/testplans/{testplan_id}", response_model=TestPlanSchema)
async def update_testplan_item(
    testplan_id: int,
    testplan_update: TestPlanUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Update a test plan item

    使用 TestPlanService.update_test_plan()

    Args:
        testplan_id: Test plan item ID
        testplan_update: Updated fields
        db: Database session
        current_user: Current authenticated user

    Returns:
        Updated test plan item
    """
    # Check permissions
    user_role = current_user.get("role")
    if user_role not in ["admin", "engineer"]:
        raise HTTPException(
            status_code=403,
            detail="Only administrators and engineers can update test plan items"
        )

    try:
        # 使用 TestPlanService 更新測試計畫項目
        update_data = testplan_update.dict(exclude_unset=True)
        db_testplan = test_plan_service.update_test_plan(
            db=db,
            test_plan_id=testplan_id,
            update_data=update_data
        )

        if not db_testplan:
            raise HTTPException(status_code=404, detail="Test plan item not found")

        return db_testplan
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update test plan item: {str(e)}"
        )


@router.delete("/testplans/{testplan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_testplan_item(
    testplan_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Delete a test plan item

    使用 TestPlanService.delete_test_plan()

    Args:
        testplan_id: Test plan item ID
        db: Database session
        current_user: Current authenticated user
    """
    # Check permissions (only admin can delete)
    user_role = current_user.get("role")
    if user_role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only administrators can delete test plan items"
        )

    try:
        # 使用 TestPlanService 刪除測試計畫項目
        success = test_plan_service.delete_test_plan(db, testplan_id)
        if not success:
            raise HTTPException(status_code=404, detail="Test plan item not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete test plan item: {str(e)}"
        )


@router.post("/testplans/bulk-delete", status_code=status.HTTP_204_NO_CONTENT)
async def bulk_delete_testplan_items(
    delete_request: TestPlanBulkDelete,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Bulk delete test plan items

    使用 TestPlanService.bulk_delete_test_plans()

    Args:
        delete_request: List of test plan IDs to delete
        db: Database session
        current_user: Current authenticated user
    """
    # Check permissions (only admin can delete)
    user_role = current_user.get("role")
    if user_role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only administrators can delete test plan items"
        )

    try:
        # 使用 TestPlanService 批次刪除測試計畫項目
        deleted_count = test_plan_service.bulk_delete_test_plans(
            db=db,
            test_plan_ids=delete_request.test_plan_ids
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bulk delete test plan items: {str(e)}"
        )


@router.post("/testplans/reorder", response_model=dict)
async def reorder_testplan_items(
    reorder_request: TestPlanReorder,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Reorder test plan items

    使用 TestPlanService.reorder_test_plans()

    Args:
        reorder_request: Mapping of test plan ID to new sequence order
        db: Database session
        current_user: Current authenticated user

    Returns:
        Success message with updated count
    """
    # Check permissions
    user_role = current_user.get("role")
    if user_role not in ["admin", "engineer"]:
        raise HTTPException(
            status_code=403,
            detail="Only administrators and engineers can reorder test plan items"
        )

    try:
        # 使用 TestPlanService 重新排序測試計畫項目
        updated_count = test_plan_service.reorder_test_plans(
            db=db,
            item_orders=reorder_request.item_orders
        )

        return {
            "message": "Test plan items reordered successfully",
            "updated_count": updated_count
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reorder test plan items: {str(e)}"
        )


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
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate test point: {str(e)}"
        )


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
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session test results: {str(e)}"
        )
