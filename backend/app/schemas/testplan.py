"""Test Plan schemas"""
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


# ============================================================================
# Test Plan Schemas
# ============================================================================
class TestPlanBase(BaseModel):
    """Base test plan schema"""
    # Core fields
    item_no: int = Field(..., description="Test item sequence number")
    item_name: str = Field(..., description="Test item name")
    test_type: str = Field(..., description="Test type")
    switch_mode: Optional[str] = Field(default=None, description="Instrument/switch mode (DAQ973A, MODEL2303, comport, etc.)")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="Test parameters JSON")
    lower_limit: Optional[float] = Field(default=None, description="Lower limit")
    upper_limit: Optional[float] = Field(default=None, description="Upper limit")
    unit: Optional[str] = Field(default=None, description="Measurement unit")
    enabled: bool = Field(default=True, description="Is test enabled")
    sequence_order: int = Field(..., description="Execution order")
    test_plan_name: Optional[str] = Field(default=None, description="Test plan name")

    # CSV import fields
    item_key: Optional[str] = Field(default=None)
    value_type: Optional[str] = Field(default=None)
    limit_type: Optional[str] = Field(default=None)
    eq_limit: Optional[str] = Field(default=None)
    pass_or_fail: Optional[str] = Field(default=None)
    measure_value: Optional[str] = Field(default=None)
    execute_name: Optional[str] = Field(default=None)
    case_type: Optional[str] = Field(default=None)
    command: Optional[str] = Field(default=None)
    timeout: Optional[int] = Field(default=None)
    use_result: Optional[str] = Field(default=None)
    wait_msec: Optional[int] = Field(default=None)


class TestPlanCreate(TestPlanBase):
    """Test plan creation"""
    project_id: int
    station_id: int


class TestPlanUpdate(BaseModel):
    """Test plan update"""
    item_name: Optional[str] = None
    test_type: Optional[str] = None
    switch_mode: Optional[str] = None  # 新增: 儀器模式欄位
    parameters: Optional[Dict[str, Any]] = None
    lower_limit: Optional[float] = None
    upper_limit: Optional[float] = None
    unit: Optional[str] = None
    enabled: Optional[bool] = None
    sequence_order: Optional[int] = None
    test_plan_name: Optional[str] = None
    item_key: Optional[str] = None
    value_type: Optional[str] = None
    limit_type: Optional[str] = None
    eq_limit: Optional[str] = None
    pass_or_fail: Optional[str] = None
    measure_value: Optional[str] = None
    execute_name: Optional[str] = None
    case_type: Optional[str] = None
    command: Optional[str] = None
    timeout: Optional[int] = None
    use_result: Optional[str] = None
    wait_msec: Optional[int] = None


class TestPlan(TestPlanBase):
    """Test plan response"""
    id: int
    project_id: int
    station_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# CSV Row Schema
# ============================================================================
class TestPlanCSVRow(BaseModel):
    """Single CSV row for test plan import"""
    ID: str = Field(..., alias="ID")
    ItemKey: str = Field(default="", alias="ItemKey")
    ValueType: str = Field(default="string", alias="ValueType")
    LimitType: str = Field(default="none", alias="LimitType")
    EqLimit: str = Field(default="", alias="EqLimit")
    LL: str = Field(default="", alias="LL")
    UL: str = Field(default="", alias="UL")
    PassOrFail: str = Field(default="", alias="PassOrFail")
    measureValue: str = Field(default="", alias="measureValue")
    ExecuteName: str = Field(default="", alias="ExecuteName")
    case: str = Field(default="", alias="case")
    Port: str = Field(default="", alias="Port")
    Baud: str = Field(default="", alias="Baud")
    Command: str = Field(default="", alias="Command")
    InitialCommand: str = Field(default="", alias="InitialCommand")
    Timeout: str = Field(default="", alias="Timeout")
    UseResult: str = Field(default="", alias="UseResult")
    WaitmSec: str = Field(default="", alias="WaitmSec")
    Instrument: str = Field(default="", alias="Instrument")
    Channel: str = Field(default="", alias="Channel")
    Item: str = Field(default="", alias="Item")
    Type: str = Field(default="", alias="Type")
    ImagePath: str = Field(default="", alias="ImagePath")
    content: str = Field(default="", alias="content")
    keyWord: str = Field(default="", alias="keyWord")
    spiltCount: str = Field(default="", alias="spiltCount")
    splitLength: str = Field(default="", alias="splitLength")

    class Config:
        populate_by_name = True


# ============================================================================
# Bulk Operations
# ============================================================================
class TestPlanUploadResponse(BaseModel):
    """Test plan upload response"""
    message: str
    project_id: int
    station_id: int
    total_items: int
    created_items: int
    skipped_items: int
    errors: Optional[list[str]] = None


class TestPlanBulkDelete(BaseModel):
    """Bulk delete test plans"""
    test_plan_ids: list[int] = Field(..., description="IDs to delete")


class TestPlanReorder(BaseModel):
    """Reorder test plan items"""
    item_orders: Dict[int, int] = Field(..., description="ID -> new order")
