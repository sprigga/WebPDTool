"""
Pytest-style tests for PDTool4 measurement validation refactoring

Tests validate that the measurement layer correctly implements:
- 7 limit types: lower, upper, both, equality, inequality, partial, none
- 3 value types: string, integer, float
- PDTool4 instrument error detection ("No instrument found", "Error:")
"""
import pytest

from app.measurements.base import (
    BaseMeasurement,
    MeasurementResult,
)


# =============================================================================
# Test Fixture
# =============================================================================

class TestMeasurement(BaseMeasurement):
    """Mock measurement class for testing validation logic"""

    async def execute(self) -> MeasurementResult:
        return self.create_result(result="PASS")


# =============================================================================
# Lower Limit Tests
# =============================================================================

@pytest.mark.measurements
@pytest.mark.unit
class TestLowerLimitValidation:
    """Tests for lower limit validation"""

    @pytest.fixture
    def measurement(self):
        """Create measurement with lower limit configuration"""
        test_plan = {
            "item_no": 1,
            "item_name": "Test Voltage",
            "limit_type": "lower",
            "value_type": "float",
            "lower_limit": 3.0,
            "upper_limit": None
        }
        return TestMeasurement(test_plan, {})

    @pytest.mark.parametrize("value,should_pass", [
        (5.0, True),   # Above lower limit
        (3.0, True),   # Equal to lower limit
        (2.0, False),  # Below lower limit
        (0.0, False),  # Far below lower limit
    ])
    def test_lower_limit_validation(self, measurement, value, should_pass):
        """Test that values above/equal to lower limit pass"""
        passed, msg = measurement.validate_result(value)
        assert passed == should_pass, f"Value {value}: expected {should_pass}, got {passed}. Message: {msg}"

    def test_lower_limit_with_string_input(self, measurement):
        """Should convert string input to float for comparison"""
        passed, _ = measurement.validate_result("5.5")
        assert passed, "String '5.5' should be converted and pass"


# =============================================================================
# Upper Limit Tests
# =============================================================================

@pytest.mark.measurements
@pytest.mark.unit
class TestUpperLimitValidation:
    """Tests for upper limit validation"""

    @pytest.fixture
    def measurement(self):
        """Create measurement with upper limit configuration"""
        test_plan = {
            "item_no": 2,
            "item_name": "Test Current",
            "limit_type": "upper",
            "value_type": "float",
            "lower_limit": None,
            "upper_limit": 5.0
        }
        return TestMeasurement(test_plan, {})

    @pytest.mark.parametrize("value,should_pass", [
        (3.0, True),   # Below upper limit
        (5.0, True),   # Equal to upper limit
        (6.0, False),  # Above upper limit
        (10.0, False), # Far above upper limit
    ])
    def test_upper_limit_validation(self, measurement, value, should_pass):
        """Test that values below/equal to upper limit pass"""
        passed, msg = measurement.validate_result(value)
        assert passed == should_pass, f"Value {value}: expected {should_pass}, got {passed}. Message: {msg}"


# =============================================================================
# Both Limits Tests
# =============================================================================

@pytest.mark.measurements
@pytest.mark.unit
class TestBothLimitsValidation:
    """Tests for both lower and upper limit validation"""

    @pytest.fixture
    def measurement(self):
        """Create measurement with both limits configuration"""
        test_plan = {
            "item_no": 3,
            "item_name": "Test Power",
            "limit_type": "both",
            "value_type": "float",
            "lower_limit": 3.0,
            "upper_limit": 5.0
        }
        return TestMeasurement(test_plan, {})

    @pytest.mark.parametrize("value,should_pass", [
        (4.0, True),   # Within range
        (3.0, True),   # Equal to lower limit
        (5.0, True),   # Equal to upper limit
        (2.0, False),  # Below lower limit
        (6.0, False),  # Above upper limit
    ])
    def test_both_limits_validation(self, measurement, value, should_pass):
        """Test that values within range pass"""
        passed, msg = measurement.validate_result(value)
        assert passed == should_pass, f"Value {value}: expected {should_pass}, got {passed}. Message: {msg}"


# =============================================================================
# Equality Tests
# =============================================================================

@pytest.mark.measurements
@pytest.mark.unit
class TestEqualityValidation:
    """Tests for equality limit validation"""

    @pytest.fixture
    def measurement(self):
        """Create measurement with equality configuration"""
        test_plan = {
            "item_no": 4,
            "item_name": "Test Status",
            "limit_type": "equality",
            "value_type": "string",
            "eq_limit": "OK"
        }
        return TestMeasurement(test_plan, {})

    @pytest.mark.parametrize("value,should_pass", [
        ("OK", True),
        ("ok", False),      # Case sensitive
        ("OK ", False),     # Exact match required
        ("FAIL", False),
        ("", False),
    ])
    def test_equality_validation(self, measurement, value, should_pass):
        """Test that only exact matches pass"""
        passed, msg = measurement.validate_result(value)
        assert passed == should_pass, f"Value '{value}': expected {should_pass}, got {passed}"


# =============================================================================
# Partial Tests (runAllTest mode)
# =============================================================================

@pytest.mark.measurements
@pytest.mark.unit
class TestPartialValidation:
    """Tests for partial (substring) validation - used in runAllTest mode"""

    @pytest.fixture
    def measurement(self):
        """Create measurement with partial match configuration"""
        test_plan = {
            "item_no": 5,
            "item_name": "Test Response",
            "limit_type": "partial",
            "value_type": "string",
            "eq_limit": "Success"
        }
        return TestMeasurement(test_plan, {})

    @pytest.mark.parametrize("value,should_pass", [
        ("Operation Successful", True),     # Contains "Success"
        ("Success", True),                   # Exact match
        ("MySuccess Story", True),          # Contains "Success" as part of word
        ("Operation Failed", False),         # Does not contain "Success"
        ("success", False),                  # Case sensitive - lowercase won't match
        ("", False),
    ])
    def test_partial_validation(self, measurement, value, should_pass):
        """Test that substring matches pass"""
        passed, msg = measurement.validate_result(value)
        assert passed == should_pass, f"Value '{value}': expected {should_pass}, got {passed}. Message: {msg}"


# =============================================================================
# Inequality Tests (runAllTest mode)
# =============================================================================

@pytest.mark.measurements
@pytest.mark.unit
class TestInequalityValidation:
    """Tests for inequality validation - used in runAllTest mode"""

    @pytest.fixture
    def measurement(self):
        """Create measurement with inequality configuration"""
        test_plan = {
            "item_no": 6,
            "item_name": "Test Value",
            "limit_type": "inequality",
            "value_type": "integer",
            "eq_limit": 0
        }
        return TestMeasurement(test_plan, {})

    @pytest.mark.parametrize("value,should_pass", [
        (5, True),     # Not equal to 0
        (-1, True),    # Not equal to 0
        (100, True),   # Not equal to 0
        (0, False),    # Equal to 0 - should fail
        ("0", False),  # String "0" should be converted to 0
    ])
    def test_inequality_validation(self, measurement, value, should_pass):
        """Test that values not equal to limit pass"""
        passed, msg = measurement.validate_result(value)
        assert passed == should_pass, f"Value {value}: expected {should_pass}, got {passed}"


# =============================================================================
# None Limit Tests
# =============================================================================

@pytest.mark.measurements
@pytest.mark.unit
class TestNoneLimitValidation:
    """Tests for none limit validation (always passes)"""

    @pytest.fixture
    def measurement(self):
        """Create measurement with no limit configuration"""
        test_plan = {
            "item_no": 7,
            "item_name": "Test No Limit",
            "limit_type": "none",
            "value_type": "string"
        }
        return TestMeasurement(test_plan, {})

    @pytest.mark.parametrize("value", [
        "Anything",
        "FAIL",
        "",
        None,
        123,
        -999,
    ])
    def test_none_limit_always_passes(self, measurement, value):
        """Test that all values pass when limit_type is 'none'"""
        passed, msg = measurement.validate_result(value)
        assert passed, f"Value {value} should always pass. Message: {msg}"


# =============================================================================
# PDTool4 Instrument Error Detection Tests
# =============================================================================

@pytest.mark.measurements
@pytest.mark.unit
class TestInstrumentErrorDetection:
    """Tests for PDTool4 instrument error detection"""

    @pytest.fixture
    def measurement(self):
        """Create measurement with standard configuration"""
        test_plan = {
            "item_no": 8,
            "item_name": "Test Instrument",
            "limit_type": "both",
            "value_type": "float",
            "lower_limit": 0.0,
            "upper_limit": 10.0
        }
        return TestMeasurement(test_plan, {})

    @pytest.mark.parametrize("error_message", [
        "No instrument found",
        "No Instrument Found",  # Case variations
        "NO INSTRUMENT FOUND",
        "Error: Communication timeout",
        "Error: Device not responding",
        "error: something went wrong",  # Lowercase
    ])
    def test_instrument_errors_detected(self, measurement, error_message):
        """Should detect and fail on instrument error messages"""
        passed, msg = measurement.validate_result(error_message)
        assert not passed, f"Error message should fail: {error_message}"
        assert "error" in msg.lower() or "instrument" in msg.lower(), \
            f"Error message should mention instrument/error: {msg}"

    @pytest.mark.parametrize("valid_value", [
        "5.0",
        5.0,
        "5",
        5,
    ])
    def test_valid_values_pass(self, measurement, valid_value):
        """Valid values should pass normally"""
        passed, msg = measurement.validate_result(valid_value)
        assert passed, f"Valid value should pass: {valid_value}"


# =============================================================================
# Value Type Conversion Tests
# =============================================================================

@pytest.mark.measurements
@pytest.mark.unit
class TestValueTypeConversion:
    """Tests for automatic value type conversion"""

    def test_float_type_conversion_from_string(self):
        """Should convert string input to float for float value_type"""
        test_plan = {
            "item_no": 9,
            "item_name": "Test Float",
            "limit_type": "both",
            "value_type": "float",
            "lower_limit": 1.0,
            "upper_limit": 10.0
        }
        measurement = TestMeasurement(test_plan, {})
        passed, _ = measurement.validate_result("5.5")
        assert passed, "String '5.5' should be converted to float 5.5 and pass"

    def test_integer_type_conversion_from_string(self):
        """Should convert string input to integer for integer value_type"""
        test_plan = {
            "item_no": 10,
            "item_name": "Test Integer",
            "limit_type": "both",
            "value_type": "integer",
            "lower_limit": 1,
            "upper_limit": 10
        }
        measurement = TestMeasurement(test_plan, {})
        passed, _ = measurement.validate_result("5")
        assert passed, "String '5' should be converted to integer 5 and pass"

    @pytest.mark.parametrize("float_string,expected", [
        ("5.5", True),
        ("5.0", True),
        ("0.5", True),
        ("-5.5", True),
    ])
    def test_float_conversion_edge_cases(self, float_string, expected):
        """Test various float string conversions"""
        test_plan = {
            "limit_type": "none",
            "value_type": "float",
        }
        measurement = TestMeasurement(test_plan, {})
        passed, _ = measurement.validate_result(float_string)
        assert passed == expected, f"Float conversion of '{float_string}' failed"


# =============================================================================
# Comprehensive Validation Test Suite
# =============================================================================

@pytest.mark.measurements
@pytest.mark.integration
class TestAllLimitTypes:
    """Comprehensive test suite for all limit types"""

    @pytest.mark.parametrize("limit_type,lower,upper,eq_limit,test_value,should_pass", [
        # Lower limit tests
        ("lower", 3.0, None, None, 5.0, True),
        ("lower", 3.0, None, None, 2.0, False),

        # Upper limit tests
        ("upper", None, 5.0, None, 3.0, True),
        ("upper", None, 5.0, None, 6.0, False),

        # Both limits tests
        ("both", 3.0, 5.0, None, 4.0, True),
        ("both", 3.0, 5.0, None, 2.0, False),
        ("both", 3.0, 5.0, None, 6.0, False),

        # Equality tests
        ("equality", None, None, "OK", "OK", True),
        ("equality", None, None, "OK", "FAIL", False),

        # Inequality tests
        ("inequality", None, None, 0, 5, True),
        ("inequality", None, None, 0, 0, False),

        # Partial tests
        ("partial", None, None, "Success", "Operation Successful", True),
        ("partial", None, None, "Success", "Operation Failed", False),

        # None tests
        ("none", None, None, None, "anything", True),
        ("none", None, None, None, None, True),
    ])
    def test_all_limit_types_comprehensive(
        self, limit_type, lower, upper, eq_limit, test_value, should_pass
    ):
        """Test all limit types with various configurations"""
        test_plan = {
            "item_no": 1,
            "item_name": f"Test {limit_type}",
            "limit_type": limit_type,
            "value_type": "float" if limit_type in ["lower", "upper", "both"] else "string",
            "lower_limit": lower,
            "upper_limit": upper,
            "eq_limit": eq_limit,
        }
        measurement = TestMeasurement(test_plan, {})
        passed, msg = measurement.validate_result(test_value)
        assert passed == should_pass, \
            f"Limit type {limit_type} with value {test_value}: expected {should_pass}, got {passed}. Msg: {msg}"


if __name__ == "__main__":
    # Allow running this file directly
    pytest.main([__file__, "-v"])
