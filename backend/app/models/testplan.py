"""Test Plan model"""
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, TIMESTAMP, DECIMAL, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class TestPlan(Base):
    """Test plan item model"""
    __tablename__ = "test_plans"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Project and station
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    station_id = Column(Integer, ForeignKey('stations.id', ondelete='CASCADE'), nullable=False)
    test_plan_name = Column(String(100), nullable=True)

    # Core test fields
    item_no = Column(Integer, nullable=False)
    item_name = Column(String(100), nullable=False)
    test_type = Column(String(50), nullable=False)
    switch_mode = Column(String(50), nullable=True)  # 新增: 儀器模式欄位 (DAQ973A, MODEL2303, comport, etc.)
    parameters = Column(JSON, nullable=True)
    lower_limit = Column(DECIMAL(15, 6), nullable=True)
    upper_limit = Column(DECIMAL(15, 6), nullable=True)
    unit = Column(String(20), nullable=True)
    enabled = Column(Boolean, default=True)
    sequence_order = Column(Integer, nullable=False)

    # CSV import fields
    item_key = Column(String(50), nullable=True)
    value_type = Column(String(50), nullable=True)
    limit_type = Column(String(50), nullable=True)
    eq_limit = Column(String(100), nullable=True)
    pass_or_fail = Column(String(20), nullable=True)
    measure_value = Column(String(100), nullable=True)
    execute_name = Column(String(100), nullable=True)
    case_type = Column(String(50), nullable=True)
    command = Column(String(500), nullable=True)
    timeout = Column(Integer, nullable=True)
    use_result = Column(String(100), nullable=True)
    wait_msec = Column(Integer, nullable=True)

    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    station = relationship("Station")

    def __repr__(self):
        return f"<TestPlan {self.item_name}>"
