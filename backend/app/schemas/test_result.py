"""Test Result schemas"""
from pydantic import BaseModel, Field
from typing import Optional, Union
from datetime import datetime
from decimal import Decimal
from enum import Enum


class ItemResultEnum(str, Enum):
    """Individual test item result"""
    PASS = "PASS"
    FAIL = "FAIL"
    SKIP = "SKIP"
    ERROR = "ERROR"


class TestResultCreate(BaseModel):
    """Create test result"""
    session_id: int
    test_plan_id: int
    item_no: int
    item_name: str
    measured_value: Optional[Union[Decimal, str]] = None
    lower_limit: Optional[Decimal] = None
    upper_limit: Optional[Decimal] = None
    unit: Optional[str] = None
    result: ItemResultEnum
    error_message: Optional[str] = None
    execution_duration_ms: Optional[int] = None


class TestResult(TestResultCreate):
    """Test result response"""
    id: int
    test_time: datetime

    class Config:
        from_attributes = True


class TestResultBatch(BaseModel):
    """Batch upload test results"""
    session_id: int
    results: list[TestResultCreate]
