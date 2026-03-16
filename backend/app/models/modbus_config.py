"""
Modbus Configuration Database Model
Stores per-station Modbus TCP communication settings
"""
from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base


class ModbusConfig(Base):
    """
    Modbus TCP configuration for a station
    One-to-one relationship with stations table
    """
    __tablename__ = "modbus_configs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    station_id = Column(Integer, ForeignKey("stations.id"), unique=True, nullable=False, index=True)

    # Connection settings
    server_host = Column(String(255), nullable=False, default="127.0.0.1")
    server_port = Column(Integer, nullable=False, default=502)
    device_id = Column(Integer, nullable=False, default=1)
    enabled = Column(Boolean, nullable=False, default=False)
    delay_seconds = Column(Float, nullable=False, default=1.0)

    # Read register addresses (hex strings like "0x0013")
    ready_status_address = Column(String(20), nullable=False, default="0x0013")
    ready_status_length = Column(Integer, nullable=False, default=1)
    read_sn_address = Column(String(20), nullable=False, default="0x0064")
    read_sn_length = Column(Integer, nullable=False, default=11)

    # Write register addresses
    test_status_address = Column(String(20), nullable=False, default="0x0014")
    test_status_length = Column(Integer, nullable=False, default=1)
    in_testing_value = Column(String(20), nullable=False, default="0x00")
    test_finished_value = Column(String(20), nullable=False, default="0x01")

    test_result_address = Column(String(20), nullable=False, default="0x0015")
    test_result_length = Column(Integer, nullable=False, default=1)
    test_no_result = Column(String(20), nullable=False, default="0x00")
    test_pass_value = Column(String(20), nullable=False, default="0x01")
    test_fail_value = Column(String(20), nullable=False, default="0x02")

    # Simulation mode
    simulation_mode = Column(Boolean, nullable=False, default=False)

    # Timestamps
    created_at = Column(Integer, nullable=True)  # Unix timestamp
    updated_at = Column(Integer, nullable=True)  # Unix timestamp

    # Relationship
    station = relationship("Station", back_populates="modbus_config")

    def __repr__(self):
        return f"<ModbusConfig(station_id={self.station_id}, host={self.server_host}:{self.server_port})>"
