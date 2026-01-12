"""Station model"""
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, TIMESTAMP, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Station(Base):
    """Station model"""
    __tablename__ = "stations"
    __table_args__ = (
        UniqueConstraint('project_id', 'station_code', name='unique_station'),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    station_code = Column(String(50), nullable=False, index=True)
    station_name = Column(String(100), nullable=False)
    project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    test_plan_path = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    project = relationship("Project", back_populates="stations")
    test_sessions = relationship("TestSession", back_populates="station")

    def __repr__(self):
        return f"<Station {self.station_code}>"
