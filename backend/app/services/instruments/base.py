"""
Base Instrument Driver

Abstract base class for all instrument drivers
Provides common interface and utilities
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from decimal import Decimal
import logging

from app.services.instrument_connection import BaseInstrumentConnection


class BaseInstrumentDriver(ABC):
    """
    Abstract base class for instrument drivers

    Each instrument type (DAQ973A, MODEL2303, etc.) should subclass this
    and implement specific measurement/control methods
    """

    def __init__(self, connection: BaseInstrumentConnection):
        """
        Initialize instrument driver

        Args:
            connection: Instrument connection instance
        """
        self.connection = connection
        self.logger = logging.getLogger(f"{self.__class__.__name__}.{connection.config.id}")

    @property
    def instrument_id(self) -> str:
        """Get instrument ID"""
        return self.connection.config.id

    @property
    def instrument_type(self) -> str:
        """Get instrument type"""
        return self.connection.config.type

    @abstractmethod
    async def initialize(self):
        """
        Initialize instrument to known state

        This should be called after connection is established
        """
        pass

    @abstractmethod
    async def reset(self):
        """
        Reset instrument to default state

        This is called during cleanup (equivalent to PDTool4's --final)
        """
        pass

    async def write_command(self, command: str):
        """Write command to instrument"""
        try:
            await self.connection.write(command)
            self.logger.debug(f"Command sent: {command}")
        except Exception as e:
            self.logger.error(f"Failed to write command '{command}': {e}")
            raise

    async def query_command(self, command: str) -> str:
        """Query instrument and return response"""
        try:
            response = await self.connection.query(command)
            self.logger.debug(f"Query: {command} -> {response}")
            return response
        except Exception as e:
            self.logger.error(f"Failed to query '{command}': {e}")
            raise

    async def query_float(self, command: str) -> float:
        """Query instrument and return float value"""
        response = await self.query_command(command)
        try:
            return float(response)
        except ValueError:
            raise ValueError(f"Invalid numeric response: {response}")

    async def query_decimal(self, command: str) -> Decimal:
        """Query instrument and return Decimal value"""
        response = await self.query_command(command)
        try:
            return Decimal(response)
        except Exception:
            raise ValueError(f"Invalid numeric response: {response}")

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self.instrument_id})>"


# ============================================================================
# Common Parameter Validators
# ============================================================================

def validate_required_params(params: Dict[str, Any], required: list[str]) -> None:
    """
    Validate that required parameters are present

    Args:
        params: Parameter dictionary
        required: List of required parameter names

    Raises:
        ValueError: If required parameters are missing
    """
    missing = [p for p in required if p not in params or params[p] is None or params[p] == '']

    if missing:
        raise ValueError(f"Missing required parameters: {', '.join(missing)}")


def get_param(params: Dict[str, Any], *keys: str, default: Any = None) -> Any:
    """
    Get parameter value trying multiple keys (case-insensitive)

    Args:
        params: Parameter dictionary
        *keys: Possible parameter names to try
        default: Default value if not found

    Returns:
        Parameter value or default
    """
    for key in keys:
        # Try exact match
        if key in params and params[key] not in (None, ""):
            return params[key]

        # Try lowercase
        key_lower = key.lower()
        if key_lower in params and params[key_lower] not in (None, ""):
            return params[key_lower]

        # Try uppercase
        key_upper = key.upper()
        if key_upper in params and params[key_upper] not in (None, ""):
            return params[key_upper]

    return default
