"""
SFC Log Model
Represents SFC communication logs for test sessions
"""
from sqlalchemy import Column, Integer, String, TIMESTAMP, Text, ForeignKey, func
from sqlalchemy.orm import relationship
from app.core.database import Base


class SFCLog(Base):
    """SFC communication log model"""
    __tablename__ = "sfc_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    test_session_id = Column(Integer, ForeignKey("test_sessions.id"), nullable=False)
    
    timestamp = Column(TIMESTAMP, server_default=func.now())
    command = Column(String(255), nullable=True)
    response = Column(Text, nullable=True)
    status = Column(String(50), nullable=True)
    
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Relationships
    session = relationship("TestSession", back_populates="sfc_logs")
