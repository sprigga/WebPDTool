"""
Pydantic schemas for Instrument CRUD API.
"""
from datetime import datetime
from typing import Any, Dict, Literal, Optional
from pydantic import BaseModel, Field

# Allowed connection types (mirrors InstrumentAddress.type values)
ConnType = Literal["VISA", "SERIAL", "TCPIP_SOCKET", "GPIB", "LOCAL"]


class InstrumentBase(BaseModel):
    instrument_id: str = Field(..., max_length=64, description="Logical ID, e.g. DAQ973A_1")
    instrument_type: str = Field(..., max_length=64, description="Driver type, e.g. DAQ973A")
    name: str = Field(..., max_length=128)
    conn_type: ConnType
    conn_params: Dict[str, Any] = Field(..., description="Connection parameters JSON")
    enabled: bool = True
    description: Optional[str] = None


class InstrumentCreate(InstrumentBase):
    """Schema for POST /api/instruments"""
    pass


class InstrumentUpdate(BaseModel):
    """Schema for PATCH /api/instruments/{id} — all fields optional"""
    instrument_type: Optional[str] = Field(None, max_length=64)
    name: Optional[str] = Field(None, max_length=128)
    conn_type: Optional[ConnType] = None
    conn_params: Optional[Dict[str, Any]] = None
    enabled: Optional[bool] = None
    description: Optional[str] = None


class InstrumentResponse(InstrumentBase):
    """Schema for API responses"""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
