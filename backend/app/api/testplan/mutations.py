"""
Test Plan Mutation Endpoints

POST/PUT/DELETE endpoints for modifying test plans.
Extracted from testplans.py lines 208-543.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List

from app.core.database import get_db
from app.core.api_helpers import get_entity_or_404, PermissionChecker
from app.core.constants import ErrorMessages
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


@router.post("/stations/{station_id}/testplan/upload", response_model=TestPlanUploadResponse)
async def upload_testplan_csv(
    station_id: int,
    file: UploadFile = File(..., description="CSV test plan file"),
    project_id: int = Form(..., description="Project ID this test plan belongs to"),
    test_plan_name: str = Form(None, description="Test plan name"),
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
    # Original code: Manual permission check
    # Refactored: Use PermissionChecker helper
    PermissionChecker.check_admin_or_engineer(current_user, "upload test plans")

    # Original code: Direct query with 404 check
    # Refactored: Use get_entity_or_404 helper
    station = get_entity_or_404(db, Station, station_id)

    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=400,
            detail=ErrorMessages.INVALID_FILE_TYPE
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
            message=ErrorMessages.UPLOAD_SUCCESS,
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
    PermissionChecker.check_admin_or_engineer(current_user, "create test plan items")
    get_entity_or_404(db, Station, testplan.station_id)

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
            status_code=500,
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
            status_code=500,
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
    PermissionChecker.check_admin_or_engineer(current_user, "update test plan items")

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
            status_code=500,
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
    PermissionChecker.check_admin(current_user, "delete test plan items")

    try:
        # 使用 TestPlanService 刪除測試計畫項目
        success = test_plan_service.delete_test_plan(db, testplan_id)
        if not success:
            raise HTTPException(status_code=404, detail="Test plan item not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
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
    PermissionChecker.check_admin(current_user, "delete test plan items")

    try:
        # 使用 TestPlanService 批次刪除測試計畫項目
        deleted_count = test_plan_service.bulk_delete_test_plans(
            db=db,
            test_plan_ids=delete_request.test_plan_ids
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
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
    PermissionChecker.check_admin_or_engineer(current_user, "reorder test plan items")

    try:
        # 使用 TestPlanService 重新排序測試計畫項目
        updated_count = test_plan_service.reorder_test_plans(
            db=db,
            item_orders=reorder_request.item_orders
        )

        return {
            "message": ErrorMessages.REORDER_SUCCESS,
            "updated_count": updated_count
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reorder test plan items: {str(e)}"
        )
