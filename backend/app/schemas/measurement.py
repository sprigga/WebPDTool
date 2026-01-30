"""
Measurement Schema Definitions

Pydantic models for measurement request/response validation.
Extracted from api/measurements.py to follow proper layering.
"""
from typing import Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, field_validator


class MeasurementResponse(BaseModel):
    """Response model for measurement results with automatic type conversion"""
    test_point_id: str
    measurement_type: str
    result: str  # PASS, FAIL, ERROR
    measured_value: Optional[str] = None
    error_message: Optional[str] = None
    test_time: datetime
    execution_duration_ms: Optional[int] = None

    @field_validator('measured_value', mode='before')
    @classmethod
    def convert_measured_value_to_string(cls, v):
        """
        Convert measured_value to string representation.

        Handles Decimal, int, float, and other types by converting to string.
        This ensures consistent API responses regardless of internal data types.

        Original implementation was in API layer (measurements.py lines 79-92).
        Moved to schema validator following separation of concerns principle.

        Args:
            v: Value to convert (can be Decimal, int, float, str, or other)

        Returns:
            String representation of the value, or None if input is None
        """
        if v is None:
            return None

        # Handle Decimal type (from database/calculations)
        if isinstance(v, Decimal):
            # Convert Decimal -> float -> str to avoid scientific notation
            return str(float(v))

        # Handle numeric types
        if isinstance(v, (int, float)):
            return str(v)

        # Already a string
        if isinstance(v, str):
            return v

        # Fallback: convert any other type to string
        return str(v)
