"""Test Plan model"""
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, TIMESTAMP, DECIMAL, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class TestPlan(Base):
    """Test plan item model"""
    __tablename__ = "test_plans"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    station_id = Column(Integer, ForeignKey('stations.id', ondelete='CASCADE'), nullable=False)
    item_no = Column(Integer, nullable=False)
    item_name = Column(String(100), nullable=False)
    test_type = Column(String(50), nullable=False)
    parameters = Column(JSON, nullable=True)
    lower_limit = Column(DECIMAL(15, 6), nullable=True)
    upper_limit = Column(DECIMAL(15, 6), nullable=True)
    unit = Column(String(20), nullable=True)
    enabled = Column(Boolean, default=True)
    sequence_order = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Relationships
    station = relationship("Station")

    def __repr__(self):
        return f"<TestPlan {self.item_name}>"
