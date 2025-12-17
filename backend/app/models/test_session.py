"""
Test Session Model
Represents a test execution session for a product
"""
from sqlalchemy import Column, Integer, String, TIMESTAMP, Enum, ForeignKey, func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class TestResult(str, enum.Enum):
    """Test result enumeration"""
    PASS = "PASS"
    FAIL = "FAIL"
    ABORT = "ABORT"


class TestSession(Base):
    """Test session model"""
    __tablename__ = "test_sessions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    serial_number = Column(String(100), nullable=False, index=True)
    station_id = Column(Integer, ForeignKey("stations.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    start_time = Column(TIMESTAMP, server_default=func.now())
    end_time = Column(TIMESTAMP, nullable=True)

    final_result = Column(Enum(TestResult), nullable=True)
    total_items = Column(Integer, nullable=True)
    pass_items = Column(Integer, nullable=True)
    fail_items = Column(Integer, nullable=True)
    test_duration_seconds = Column(Integer, nullable=True)

    created_at = Column(TIMESTAMP, server_default=func.now())

    # Relationships
    station = relationship("Station", back_populates="test_sessions")
    user = relationship("User")
    test_results = relationship(
        "TestResult",
        back_populates="session",
        cascade="all, delete-orphan"
    )
    sfc_logs = relationship(
        "SFCLog",
        back_populates="session",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<TestSession(id={self.id}, serial={self.serial_number}, result={self.final_result})>"
