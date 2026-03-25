"""
Modbus Configuration Pydantic Schemas
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional


class ModbusConfigBase(BaseModel):
    """Base Modbus configuration fields"""
    server_host: str = Field(default="127.0.0.1", description="Modbus TCP server host")
    server_port: int = Field(default=502, ge=1, le=65535, description="Modbus TCP server port")
    device_id: int = Field(default=1, ge=1, le=255, description="Modbus device ID (slave address)")
    enabled: bool = Field(default=False, description="Whether Modbus listener is enabled")
    delay_seconds: float = Field(default=1.0, ge=0.1, le=60.0, description="Polling delay in seconds")

    # Register addresses (hex string format)
    ready_status_address: str = Field(default="0x0013", description="Ready status register address")
    ready_status_length: int = Field(default=1, ge=1, le=125, description="Ready status register count")
    read_sn_address: str = Field(default="0x0064", description="Serial number read address")
    read_sn_length: int = Field(default=11, ge=1, le=125, description="Serial number register count")

    test_status_address: str = Field(default="0x0014", description="Test status register address")
    test_status_length: int = Field(default=1, ge=1, le=125, description="Test status register count")
    in_testing_value: str = Field(default="0x00", description="Value to write when testing")
    test_finished_value: str = Field(default="0x01", description="Value to write when finished")

    test_result_address: str = Field(default="0x0015", description="Test result register address")
    test_result_length: int = Field(default=1, ge=1, le=125, description="Test result register count")
    test_no_result: str = Field(default="0x00", description="Value for no result")
    test_pass_value: str = Field(default="0x01", description="Value for PASS")
    test_fail_value: str = Field(default="0x02", description="Value for FAIL")

    simulation_mode: bool = Field(default=False, description="Simulation mode (no real Modbus)")

    @field_validator(
        'ready_status_address', 'read_sn_address', 'test_status_address',
        'test_result_address', 'in_testing_value', 'test_finished_value',
        'test_no_result', 'test_pass_value', 'test_fail_value'
    )
    @classmethod
    def validate_hex_string(cls, v: str) -> str:
        """Validate hex string format. Accepts 0x-prefixed hex or plain decimal strings."""
        if v.startswith('0x') or v.startswith('0X'):
            try:
                int(v, 16)
            except ValueError:
                raise ValueError(f'Invalid hex string: {v}')
        else:
            # Accept plain decimal strings stored by legacy data (e.g. "400001")
            if not v.isdigit():
                raise ValueError('Hex address must start with 0x or 0X, or be a plain decimal number')
        return v


class ModbusConfigCreate(ModbusConfigBase):
    """Schema for creating Modbus configuration"""
    station_id: int = Field(..., description="Station ID")


class ModbusConfigUpdate(BaseModel):
    """Schema for updating Modbus configuration (all fields optional)"""
    server_host: Optional[str] = None
    server_port: Optional[int] = Field(None, ge=1, le=65535)
    device_id: Optional[int] = Field(None, ge=1, le=255)
    enabled: Optional[bool] = None
    delay_seconds: Optional[float] = Field(None, ge=0.1, le=60.0)

    ready_status_address: Optional[str] = None
    ready_status_length: Optional[int] = Field(None, ge=1, le=125)
    read_sn_address: Optional[str] = None
    read_sn_length: Optional[int] = Field(None, ge=1, le=125)

    test_status_address: Optional[str] = None
    test_status_length: Optional[int] = Field(None, ge=1, le=125)
    in_testing_value: Optional[str] = None
    test_finished_value: Optional[str] = None

    test_result_address: Optional[str] = None
    test_result_length: Optional[int] = Field(None, ge=1, le=125)
    test_no_result: Optional[str] = None
    test_pass_value: Optional[str] = None
    test_fail_value: Optional[str] = None

    simulation_mode: Optional[bool] = None


class ModbusConfigResponse(ModbusConfigBase):
    """Schema for Modbus configuration response"""
    id: int
    station_id: int

    model_config = {"from_attributes": True}


class ModbusStatusResponse(BaseModel):
    """Schema for Modbus listener status"""
    station_id: int
    running: bool
    connected: bool
    last_sn: Optional[str] = None
    error_message: Optional[str] = None
    cycle_count: int = 0
    uptime_seconds: Optional[float] = None
