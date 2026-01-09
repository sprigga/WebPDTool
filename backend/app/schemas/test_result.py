"""
Test Result Pydantic Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, Union
from datetime import datetime
from decimal import Decimal
from enum import Enum


class ItemResultEnum(str, Enum):
    """Individual test item result enumeration"""
    PASS = "PASS"
    FAIL = "FAIL"
    SKIP = "SKIP"
    ERROR = "ERROR"


class TestResultCreate(BaseModel):
    """Schema for creating a test result"""
    session_id: int = Field(..., description="Test session ID")
    test_plan_id: int = Field(..., description="Test plan item ID")
    item_no: int = Field(..., description="Test item number")
    item_name: str = Field(..., max_length=100, description="Test item name")
    measured_value: Optional[Union[Decimal, str]] = Field(None, description="Measured value")
    lower_limit: Optional[Decimal] = Field(None, description="Lower limit")
    upper_limit: Optional[Decimal] = Field(None, description="Upper limit")
    unit: Optional[str] = Field(None, max_length=20, description="Unit")
    result: ItemResultEnum = Field(..., description="Test result")
    error_message: Optional[str] = Field(None, description="Error message if test failed")
    execution_duration_ms: Optional[int] = Field(None, description="Execution duration in milliseconds")


class TestResult(TestResultCreate):
    """Schema for test result response"""
    id: int
    test_time: datetime

    class Config:
        from_attributes = True


class TestResultBatch(BaseModel):
    """Schema for batch uploading test results"""
    session_id: int
    results: list[TestResultCreate]
