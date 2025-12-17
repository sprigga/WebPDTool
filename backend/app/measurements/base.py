"""
Base Measurement Module
Provides abstract base class for all measurement implementations
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class MeasurementResult:
    """Measurement result data structure"""
    
    def __init__(
        self,
        item_no: int,
        item_name: str,
        result: str,
        measured_value: Optional[Decimal] = None,
        lower_limit: Optional[Decimal] = None,
        upper_limit: Optional[Decimal] = None,
        unit: Optional[str] = None,
        error_message: Optional[str] = None,
        execution_duration_ms: Optional[int] = None
    ):
        self.item_no = item_no
        self.item_name = item_name
        self.result = result  # PASS, FAIL, SKIP, ERROR
        self.measured_value = measured_value
        self.lower_limit = lower_limit
        self.upper_limit = upper_limit
        self.unit = unit
        self.error_message = error_message
        self.execution_duration_ms = execution_duration_ms
        self.test_time = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary"""
        return {
            "item_no": self.item_no,
            "item_name": self.item_name,
            "result": self.result,
            "measured_value": float(self.measured_value) if self.measured_value else None,
            "lower_limit": float(self.lower_limit) if self.lower_limit else None,
            "upper_limit": float(self.upper_limit) if self.upper_limit else None,
            "unit": self.unit,
            "error_message": self.error_message,
            "execution_duration_ms": self.execution_duration_ms,
            "test_time": self.test_time.isoformat()
        }


class BaseMeasurement(ABC):
    """
    Abstract base class for all measurement implementations
    """
    
    def __init__(self, test_plan_item: Dict[str, Any], config: Dict[str, Any]):
        """
        Initialize measurement
        
        Args:
            test_plan_item: Test plan item configuration from database
            config: Global configuration and instrument settings
        """
        self.test_plan_item = test_plan_item
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Extract test plan fields
        self.item_no = test_plan_item.get("item_no")
        self.item_name = test_plan_item.get("item_name")
        self.lower_limit = test_plan_item.get("lower_limit")
        self.upper_limit = test_plan_item.get("upper_limit")
        self.unit = test_plan_item.get("unit")
        self.test_command = test_plan_item.get("test_command")
        self.test_params = test_plan_item.get("test_params", {})
        
    @abstractmethod
    async def execute(self) -> MeasurementResult:
        """
        Execute the measurement
        
        Returns:
            MeasurementResult object containing test results
        """
        pass
    
    def validate_result(self, measured_value: Decimal) -> str:
        """
        Validate measured value against limits
        
        Args:
            measured_value: The measured value to validate
            
        Returns:
            "PASS" or "FAIL"
        """
        try:
            if self.lower_limit is not None and measured_value < self.lower_limit:
                return "FAIL"
            if self.upper_limit is not None and measured_value > self.upper_limit:
                return "FAIL"
            return "PASS"
        except Exception as e:
            self.logger.error(f"Error validating result: {e}")
            return "ERROR"
    
    def create_result(
        self,
        result: str,
        measured_value: Optional[Decimal] = None,
        error_message: Optional[str] = None,
        execution_duration_ms: Optional[int] = None
    ) -> MeasurementResult:
        """
        Create a measurement result object
        
        Args:
            result: Test result (PASS/FAIL/SKIP/ERROR)
            measured_value: Measured value
            error_message: Error message if any
            execution_duration_ms: Execution duration in milliseconds
            
        Returns:
            MeasurementResult object
        """
        return MeasurementResult(
            item_no=self.item_no,
            item_name=self.item_name,
            result=result,
            measured_value=measured_value,
            lower_limit=self.lower_limit,
            upper_limit=self.upper_limit,
            unit=self.unit,
            error_message=error_message,
            execution_duration_ms=execution_duration_ms
        )
    
    async def setup(self):
        """Optional setup before measurement execution"""
        pass
    
    async def teardown(self):
        """Optional cleanup after measurement execution"""
        pass
