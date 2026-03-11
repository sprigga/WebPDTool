"""Instrument model - DB-backed instrument configuration"""
from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, JSON
from sqlalchemy.sql import func
from app.core.database import Base


class Instrument(Base):
    """Instrument connection configuration model"""
    __tablename__ = "instruments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    instrument_id = Column(String(64), unique=True, nullable=False, index=True,
                           comment="Logical ID, e.g. DAQ973A_1")
    instrument_type = Column(String(64), nullable=False, index=True,
                             comment="Driver type, e.g. DAQ973A")
    name = Column(String(128), nullable=False)
    conn_type = Column(String(32), nullable=False,
                       comment="VISA | SERIAL | TCPIP_SOCKET | GPIB | LOCAL")
    conn_params = Column(JSON, nullable=False,
                         comment="Connection parameters (address, port, baudrate...)")
    enabled = Column(Boolean, nullable=False, default=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(),
                        onupdate=func.now())

    def __repr__(self):
        return f"<Instrument {self.instrument_id} ({self.instrument_type})>"
