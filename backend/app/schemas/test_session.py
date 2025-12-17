"""
Test Session Pydantic Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class TestResultEnum(str, Enum):
    """Test result enumeration"""
    PASS = "PASS"
    FAIL = "FAIL"
    ABORT = "ABORT"


class TestSessionCreate(BaseModel):
    """Schema for creating a new test session"""
    serial_number: str = Field(..., min_length=1, max_length=100, description="Product serial number")
    station_id: int = Field(..., gt=0, description="Station ID")


class TestSessionStatus(BaseModel):
    """Schema for test session status updates"""
    session_id: int
    status: str  # "RUNNING", "PAUSED", "COMPLETED", "ABORTED"
    current_item: Optional[int] = None
    total_items: Optional[int] = None
    pass_items: Optional[int] = None
    fail_items: Optional[int] = None
    elapsed_time_seconds: Optional[int] = None

    class Config:
        from_attributes = True


class TestSessionComplete(BaseModel):
    """Schema for completing a test session"""
    final_result: TestResultEnum
    total_items: int
    pass_items: int
    fail_items: int
    test_duration_seconds: int


class TestSession(BaseModel):
    """Schema for test session response"""
    id: int
    serial_number: str
    station_id: int
    user_id: int
    start_time: datetime
    end_time: Optional[datetime] = None
    final_result: Optional[TestResultEnum] = None
    total_items: Optional[int] = None
    pass_items: Optional[int] = None
    fail_items: Optional[int] = None
    test_duration_seconds: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TestSessionDetail(TestSession):
    """Schema for test session with detailed information"""
    # Will include test results in future iterations
    pass
