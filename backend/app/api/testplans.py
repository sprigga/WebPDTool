"""
Test Plan Management API Endpoints
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
from app.utils.csv_parser import TestPlanCSVParser, CSVParseError

router = APIRouter()


@router.get("/stations/{station_id}/testplan", response_model=List[TestPlanSchema])
async def get_station_testplan(
    station_id: int,
    enabled_only: bool = True,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Get test plan for a specific station

    Args:
        station_id: Station ID
        enabled_only: Return only enabled test items (default: True)
        db: Database session
        current_user: Current authenticated user

    Returns:
        List of test plan items ordered by sequence
    """
    # Verify station exists
    station = db.query(Station).filter(Station.id == station_id).first()
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")

    # Build query
    query = db.query(TestPlan).filter(TestPlan.station_id == station_id)

    if enabled_only:
        query = query.filter(TestPlan.enabled == True)

    # Order by sequence
    test_plans = query.order_by(TestPlan.sequence_order).all()

    return test_plans


@router.post("/stations/{station_id}/testplan/upload", response_model=TestPlanUploadResponse)
async def upload_testplan_csv(
    station_id: int,
    file: UploadFile = File(..., description="CSV test plan file"),
    replace_existing: bool = Form(default=True, description="Replace existing test plan"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Upload and parse CSV test plan file

    Args:
        station_id: Station ID to upload test plan for
        file: CSV file upload
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
            db.query(TestPlan).filter(TestPlan.station_id == station_id).delete()

        # Insert new test plan items
        created_count = 0
        errors = []

        for plan_dict in test_plan_dicts:
            try:
                test_plan = TestPlan(
                    station_id=station_id,
                    **plan_dict
                )
                db.add(test_plan)
                created_count += 1
            except Exception as e:
                errors.append(f"Error creating item {plan_dict.get('item_name')}: {str(e)}")

        # Commit changes
        db.commit()

        return TestPlanUploadResponse(
            message="Test plan uploaded successfully",
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

    # Create test plan item
    db_testplan = TestPlan(**testplan.dict())
    db.add(db_testplan)
    db.commit()
    db.refresh(db_testplan)

    return db_testplan


@router.get("/testplans/{testplan_id}", response_model=TestPlanSchema)
async def get_testplan_item(
    testplan_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Get a specific test plan item by ID"""
    testplan = db.query(TestPlan).filter(TestPlan.id == testplan_id).first()
    if not testplan:
        raise HTTPException(status_code=404, detail="Test plan item not found")

    return testplan


@router.put("/testplans/{testplan_id}", response_model=TestPlanSchema)
async def update_testplan_item(
    testplan_id: int,
    testplan_update: TestPlanUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Update a test plan item

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

    # Get existing test plan item
    db_testplan = db.query(TestPlan).filter(TestPlan.id == testplan_id).first()
    if not db_testplan:
        raise HTTPException(status_code=404, detail="Test plan item not found")

    # Update fields
    update_data = testplan_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_testplan, field, value)

    db.commit()
    db.refresh(db_testplan)

    return db_testplan


@router.delete("/testplans/{testplan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_testplan_item(
    testplan_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Delete a test plan item

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

    # Get existing test plan item
    db_testplan = db.query(TestPlan).filter(TestPlan.id == testplan_id).first()
    if not db_testplan:
        raise HTTPException(status_code=404, detail="Test plan item not found")

    db.delete(db_testplan)
    db.commit()

    return None


@router.post("/testplans/bulk-delete", status_code=status.HTTP_204_NO_CONTENT)
async def bulk_delete_testplan_items(
    delete_request: TestPlanBulkDelete,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Bulk delete test plan items

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

    # Delete items
    deleted_count = db.query(TestPlan).filter(
        TestPlan.id.in_(delete_request.test_plan_ids)
    ).delete(synchronize_session=False)

    db.commit()

    return None


@router.post("/testplans/reorder", response_model=dict)
async def reorder_testplan_items(
    reorder_request: TestPlanReorder,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Reorder test plan items

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

    # Update sequence orders
    updated_count = 0
    for testplan_id, new_order in reorder_request.item_orders.items():
        testplan = db.query(TestPlan).filter(TestPlan.id == testplan_id).first()
        if testplan:
            testplan.sequence_order = new_order
            updated_count += 1

    db.commit()

    return {
        "message": "Test plan items reordered successfully",
        "updated_count": updated_count
    }
