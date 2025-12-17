"""
Pydantic schemas for test plan management
"""
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class TestPlanBase(BaseModel):
    """Base schema for test plan items"""
    item_no: int = Field(..., description="Test item sequence number")
    item_name: str = Field(..., description="Test item name/ID")
    test_type: str = Field(..., description="Test type (e.g., CommandTest, OPjudge, Other)")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="Test parameters in JSON format")
    lower_limit: Optional[float] = Field(default=None, description="Lower limit for numeric tests")
    upper_limit: Optional[float] = Field(default=None, description="Upper limit for numeric tests")
    unit: Optional[str] = Field(default=None, description="Measurement unit")
    enabled: bool = Field(default=True, description="Whether the test item is enabled")
    sequence_order: int = Field(..., description="Execution order in the test plan")


class TestPlanCreate(TestPlanBase):
    """Schema for creating a test plan item"""
    station_id: int = Field(..., description="Station ID this test plan belongs to")


class TestPlanUpdate(BaseModel):
    """Schema for updating a test plan item"""
    item_name: Optional[str] = None
    test_type: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    lower_limit: Optional[float] = None
    upper_limit: Optional[float] = None
    unit: Optional[str] = None
    enabled: Optional[bool] = None
    sequence_order: Optional[int] = None


class TestPlan(TestPlanBase):
    """Schema for test plan item response"""
    id: int
    station_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TestPlanCSVRow(BaseModel):
    """Schema for parsing a single row from CSV test plan"""
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


class TestPlanUploadResponse(BaseModel):
    """Response schema for test plan upload"""
    message: str
    station_id: int
    total_items: int
    created_items: int
    skipped_items: int
    errors: Optional[list[str]] = None


class TestPlanBulkDelete(BaseModel):
    """Schema for bulk deleting test plan items"""
    test_plan_ids: list[int] = Field(..., description="List of test plan IDs to delete")


class TestPlanReorder(BaseModel):
    """Schema for reordering test plan items"""
    item_orders: Dict[int, int] = Field(
        ...,
        description="Mapping of test plan ID to new sequence order"
    )
