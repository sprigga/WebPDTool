"""
Base Measurement Module
Provides abstract base class for all measurement implementations
Integrates PDTool4 TestPoint validation logic
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple, Union
from datetime import datetime, timezone
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# Utility Functions
# ============================================================================
def is_empty_limit(value: Optional[Any]) -> bool:
    """Check if a limit value is empty"""
    return value is None or len(str(value)) == 0


# ============================================================================
# Limit Types
# ============================================================================
class LimitType:
    """Base class for limit types"""
    pass


class LOWER_LIMIT(LimitType):
    """Lower limit constraint"""
    pass


class UPPER_LIMIT(LimitType):
    """Upper limit constraint"""
    pass


class BOTH_LIMIT(LimitType):
    """Both lower and upper limit constraint"""
    pass


class NONE_LIMIT(LimitType):
    """No limit constraint"""
    pass


class EQUALITY_LIMIT(LimitType):
    """Equality constraint"""
    pass


class PARTIAL_LIMIT(LimitType):
    """Partial string match constraint"""
    pass


class INEQUALITY_LIMIT(LimitType):
    """Inequality constraint"""
    pass


# Mapping dictionary for limit types
LIMIT_TYPE_MAP = {
    'lower': LOWER_LIMIT,
    'upper': UPPER_LIMIT,
    'both': BOTH_LIMIT,
    'equality': EQUALITY_LIMIT,
    'partial': PARTIAL_LIMIT,
    'inequality': INEQUALITY_LIMIT,
    'none': NONE_LIMIT,
}


# ============================================================================
# Value Types with casting
# ============================================================================
class ValueType:
    """Base class for value types"""
    @staticmethod
    def cast(value: Any) -> Any:
        return str(value)


class StringType(ValueType):
    @staticmethod
    def cast(value: Any) -> str:
        return str(value)


class IntegerType(ValueType):
    @staticmethod
    def cast(value: Any) -> int:
        if isinstance(value, int):
            return value
        # Handle string representation safely
        try:
            return int(str(value), 0) if isinstance(value, str) else int(value)
        except (ValueError, TypeError):
            return 0


class FloatType(ValueType):
    @staticmethod
    def cast(value: Any) -> float:
        return float(value)


VALUE_TYPE_MAP = {
    'string': StringType,
    'integer': IntegerType,
    'float': FloatType,
}


# ============================================================================
# Measurement Result
# ============================================================================
class MeasurementResult:
    """Stores test measurement result data"""

    def __init__(
        self,
        item_no: Optional[int],
        item_name: Optional[str],
        result: str,
        measured_value: Optional[Union[Decimal, str]] = None,
        lower_limit: Optional[Decimal] = None,
        upper_limit: Optional[Decimal] = None,
        unit: Optional[str] = None,
        error_message: Optional[str] = None,
        execution_duration_ms: Optional[int] = None
    ):
        self.item_no = item_no or 0
        self.item_name = item_name or ""
        self.result = result  # PASS, FAIL, SKIP, ERROR
        self.measured_value = measured_value
        self.lower_limit = lower_limit
        self.upper_limit = upper_limit
        self.unit = unit
        self.error_message = error_message
        self.execution_duration_ms = execution_duration_ms
        self.test_time = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for JSON serialization"""
        # Convert measured_value appropriately based on type
        measured_value = self.measured_value
        if measured_value is not None:
            if isinstance(measured_value, Decimal):
                measured_value = float(measured_value)
            elif not isinstance(measured_value, (str, float, int)):
                measured_value = str(measured_value)

        return {
            "item_no": self.item_no,
            "item_name": self.item_name,
            "result": self.result,
            "measured_value": measured_value,
            "lower_limit": float(self.lower_limit) if self.lower_limit else None,
            "upper_limit": float(self.upper_limit) if self.upper_limit else None,
            "unit": self.unit,
            "error_message": self.error_message,
            "execution_duration_ms": self.execution_duration_ms,
            "test_time": self.test_time.isoformat()
        }


# ============================================================================
# Base Measurement Class
# ============================================================================
class BaseMeasurement(ABC):
    """
    Abstract base class for all measurement implementations.
    Integrates PDTool4 TestPoint limit validation logic.
    """

    def __init__(self, test_plan_item: Dict[str, Any], config: Dict[str, Any]):
        """
        Initialize measurement with test plan configuration.

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
        self.item_key = test_plan_item.get("item_key", self.item_name)
        self.lower_limit = test_plan_item.get("lower_limit")
        self.upper_limit = test_plan_item.get("upper_limit")
        self.unit = test_plan_item.get("unit")
        self.test_command = test_plan_item.get("test_type")
        self.test_params = test_plan_item.get("parameters", {})

        # Limit and value types
        self.value_type_str = test_plan_item.get("value_type", "string")
        self.limit_type_str = test_plan_item.get("limit_type", "none")
        self.eq_limit = test_plan_item.get("eq_limit")

        # Set value type with fallback
        self.value_type = VALUE_TYPE_MAP.get(self.value_type_str, StringType)

        # Cast eq_limit if present
        if not is_empty_limit(self.eq_limit):
            self.eq_limit = self.value_type.cast(self.eq_limit)

        # Set limit type with fallback
        self.limit_type = LIMIT_TYPE_MAP.get(self.limit_type_str, NONE_LIMIT)

    @abstractmethod
    async def execute(self) -> MeasurementResult:
        """
        Execute the measurement - must be implemented by subclasses.

        Returns:
            MeasurementResult object containing test results
        """
        pass

    def validate_result(
        self,
        measured_value: Any,
        run_all_test: str = "OFF",
        raise_on_fail: bool = False
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate measured value against specifications.

        Supported limit types:
        - none: No limit, always passes
        - lower: Lower limit check (value >= lower)
        - upper: Upper limit check (value <= upper)
        - both: Both limits check (lower <= value <= upper)
        - equality: Exact match check
        - partial: String contains check
        - inequality: Not equal check

        Special error checks (PDTool4 runAllTest mode):
        - "No instrument found" -> fail
        - "Error:" prefix -> fail

        Args:
            measured_value: The value to validate
            run_all_test: "ON" to continue on error, "OFF" to stop
            raise_on_fail: Whether to raise on validation failure

        Returns:
            Tuple of (passed, error_message)
        """
        try:
            # Check for instrument errors
            if measured_value and isinstance(measured_value, str):
                if measured_value == "No instrument found":
                    self.logger.error("Instrument not found")
                    return False, "No instrument found"
                if "Error: " in measured_value:
                    self.logger.error(f"Instrument error: {measured_value}")
                    return False, f"Instrument error: {measured_value}"

            # Type cast based on value_type
            if not is_empty_limit(measured_value):
                if self.value_type is IntegerType:
                    measured_value = int(str(measured_value), 0)
                elif self.value_type is FloatType:
                    measured_value = float(str(measured_value))
                else:
                    measured_value = str(measured_value)
            else:
                measured_value = None

            # No limit - always passes
            if self.limit_type is NONE_LIMIT:
                return True, None

            # Equality check
            if self.limit_type is EQUALITY_LIMIT:
                result = bool(str(measured_value) == str(self.eq_limit))
                if not result and raise_on_fail:
                    logger.warning(f"Equality limit: {self.eq_limit}")
                    return False, f"Failed equality: {repr(measured_value)} != {repr(self.eq_limit)}"
                return result, None if result else f"Equality failed: {repr(measured_value)} != {repr(self.eq_limit)}"

            # Partial string match check
            if self.limit_type is PARTIAL_LIMIT:
                result = str(self.eq_limit) in str(measured_value)
                if not result and raise_on_fail:
                    logger.warning(f"Partial limit: {self.eq_limit}")
                    if run_all_test == "ON":
                        logger.error(f"TestPointEqualityLimitFailure: {repr(measured_value)} does not contain {repr(self.eq_limit)}")
                    return False, f"Failed partial: {repr(measured_value)} does not contain {repr(self.eq_limit)}"
                return result, None if result else f"Partial failed: '{self.eq_limit}' not in '{measured_value}'"

            # Inequality check
            if self.limit_type is INEQUALITY_LIMIT:
                result = bool(measured_value != self.eq_limit)
                if not result and raise_on_fail:
                    logger.warning(f"Inequality limit: {self.eq_limit}")
                    return False, f"Failed inequality: {repr(measured_value)} == {repr(self.eq_limit)}"
                return result, None if result else f"Inequality failed: {repr(measured_value)} == {repr(self.eq_limit)}"

            # Lower limit check
            lower_result = True
            if self.limit_type in (LOWER_LIMIT, BOTH_LIMIT):
                if measured_value is not None and self.lower_limit is not None:
                    lower_result = bool(float(measured_value) >= float(self.lower_limit))
                    if not lower_result and raise_on_fail:
                        logger.warning(f"Lower limit: {self.lower_limit}")
                        return False, f"Failed lower: {repr(measured_value)} < {repr(self.lower_limit)}"
                    if self.limit_type is LOWER_LIMIT:
                        return lower_result, None if lower_result else f"Lower failed: {measured_value} < {self.lower_limit}"

            # Upper limit check
            upper_result = True
            if self.limit_type in (UPPER_LIMIT, BOTH_LIMIT):
                if measured_value is not None and self.upper_limit is not None:
                    upper_result = bool(float(self.upper_limit) >= float(measured_value))
                    if not upper_result and raise_on_fail:
                        logger.warning(f"Upper limit: {self.upper_limit}")
                        return False, f"Failed upper: {repr(measured_value)} > {repr(self.upper_limit)}"
                    if self.limit_type is UPPER_LIMIT:
                        return upper_result, None if upper_result else f"Upper failed: {measured_value} > {self.upper_limit}"

            # Both limits - combine results
            if self.limit_type is BOTH_LIMIT:
                return upper_result and lower_result, None

            return True, None

        except Exception as e:
            self.logger.error(f"Error validating result: {e}")
            return False, str(e)

    def create_result(
        self,
        result: str,
        measured_value: Optional[Decimal] = None,
        error_message: Optional[str] = None,
        execution_duration_ms: Optional[int] = None
    ) -> MeasurementResult:
        """
        Create a MeasurementResult object.

        Args:
            result: Test result (PASS/FAIL/SKIP/ERROR)
            measured_value: Measured value
            error_message: Error message if failed
            execution_duration_ms: Execution time in milliseconds

        Returns:
            MeasurementResult object
        """
        return MeasurementResult(
            item_no=self.item_no or 0,
            item_name=self.item_name or "",
            result=result,
            measured_value=measured_value,
            lower_limit=self.lower_limit,
            upper_limit=self.upper_limit,
            unit=self.unit,
            error_message=error_message,
            execution_duration_ms=execution_duration_ms
        )

    async def setup(self):
        """Optional setup before measurement"""
        pass

    async def teardown(self):
        """Optional cleanup after measurement"""
        pass
