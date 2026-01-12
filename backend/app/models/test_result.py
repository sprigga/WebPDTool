"""Test Result Model"""
from sqlalchemy import Column, Integer, String, TIMESTAMP, BigInteger, Enum, ForeignKey, DECIMAL, Text, func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class ItemResult(str, enum.Enum):
    """Individual test item result enumeration"""
    PASS = "PASS"
    FAIL = "FAIL"
    SKIP = "SKIP"
    ERROR = "ERROR"


class TestResult(Base):
    """Test result model for individual test items"""
    __tablename__ = "test_results"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("test_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    test_plan_id = Column(Integer, ForeignKey("test_plans.id"), nullable=False)

    item_no = Column(Integer, nullable=False)
    item_name = Column(String(100), nullable=False)
    measured_value = Column(String(100), nullable=True)  # String to support both numeric and text values
    lower_limit = Column(DECIMAL(15, 6), nullable=True)
    upper_limit = Column(DECIMAL(15, 6), nullable=True)
    unit = Column(String(20), nullable=True)

    result = Column(Enum(ItemResult), nullable=False, index=True)
    error_message = Column(Text, nullable=True)

    test_time = Column(TIMESTAMP, server_default=func.now(), index=True)
    execution_duration_ms = Column(Integer, nullable=True)

    session = relationship("TestSession", back_populates="test_results")
    test_plan = relationship("TestPlan")

    def __repr__(self):
        return f"<TestResult(id={self.id}, item={self.item_name}, result={self.result})>"
