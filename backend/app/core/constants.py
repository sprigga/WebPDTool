"""
Application-wide Constants

Centralized constants to replace magic strings scattered throughout the codebase.
This improves maintainability and reduces typos.
"""

from typing import List


# =============================================================================
# User Roles
# =============================================================================

class UserRole:
    """User role constants"""
    ADMIN = "admin"
    ENGINEER = "engineer"
    USER = "user"


ALL_ROLES: List[str] = [UserRole.ADMIN, UserRole.ENGINEER, UserRole.USER]
WRITE_ROLES: List[str] = [UserRole.ADMIN, UserRole.ENGINEER]


# =============================================================================
# Test Result Statuses
# =============================================================================

class TestResult:
    """Test result status constants"""
    PASS = "PASS"
    FAIL = "FAIL"
    ERROR = "ERROR"
    SKIP = "SKIP"


# =============================================================================
# Test Session Statuses
# =============================================================================

class SessionStatus:
    """Test session status constants"""
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    STOPPED = "STOPPED"
    FAILED = "FAILED"
    ERROR = "ERROR"
    PASSED = "PASSED"


# Valid session statuses for query parameter validation
VALID_SESSION_STATUSES: List[str] = [
    SessionStatus.RUNNING,
    SessionStatus.COMPLETED,
    SessionStatus.STOPPED,
    SessionStatus.FAILED,
    SessionStatus.ERROR,
    SessionStatus.PASSED
]


# =============================================================================
# Run All Test Mode (PDTool4)
# =============================================================================

class RunAllTest:
    """Run all test mode constants from PDTool4"""
    ON = "ON"
    OFF = "OFF"


# =============================================================================
# Measurement Types
# =============================================================================

class MeasurementType:
    """Measurement type constants"""
    POWER_SET = "PowerSet"
    POWER_READ = "PowerRead"
    COMMAND_TEST = "CommandTest"
    COMMAND = "command"  # Alias for CommandTest
    SFC_TEST = "SFCtest"
    URL = "URL"  # SFC web mode
    GET_SN = "getSN"
    OP_JUDGE = "OPjudge"
    WAIT = "wait"
    WAIT_UPPER = "Wait"  # Uppercase variant
    OTHER = "Other"
    FINAL = "Final"


# =============================================================================
# Switch Modes (Instruments)
# =============================================================================

class SwitchMode:
    """Switch mode / instrument type constants"""

    # Data Acquisition
    DAQ973A = "DAQ973A"
    DAQ6510 = "DAQ6510"
    MODEL2303 = "MODEL2303"
    MODEL2306 = "MODEL2306"
    APS7050 = "APS7050"
    IT6723C = "IT6723C"
    PSW3072 = "PSW3072"
    KEITHLEY2015 = "KEITHLEY2015"
    MDO34 = "MDO34"
    MT8872A_INF = "MT8872A_INF"
    RF_MT8872A_INF = "RF_tool/MT8872A_INF"

    # Communication types
    COMPORT = "comport"
    CONSOLE = "console"
    TCPIP = "tcpip"
    ANDROID_ADB = "android_adb"
    PEAK = "PEAK"

    # Special modes
    SKIP = "skip"
    WAIT_FIX_5SEC = "WAIT_FIX_5sec"


# =============================================================================
# Limit Types
# =============================================================================

class LimitType:
    """Limit type constants for test validation"""
    NONE = "none"
    PARTIAL = "partial"
    EQUALITY = "equality"
    INEQUALITY = "inequality"


# =============================================================================
# Value Types
# =============================================================================

class ValueType:
    """Value type constants"""
    STRING = "string"
    NUMERIC = "numeric"


# =============================================================================
# Error Messages
# =============================================================================

class ErrorMessages:
    """Standardized error messages"""
    STATION_NOT_FOUND = "Station not found"
    PROJECT_NOT_FOUND = "Project not found"
    SESSION_NOT_FOUND = "Test session {id} not found"
    INSUFFICIENT_PERMISSIONS = "Insufficient permissions to perform this action"
    ONLY_ADMIN = "Only administrators can perform this action"
    ONLY_ADMIN_ENGINEER = "Only administrators and engineers can perform this action"
    INVALID_FILE_TYPE = "Invalid file type. Only CSV files are supported"


# =============================================================================
# API Response Messages
# =============================================================================

class ResponseMessages:
    """Standardized success messages"""
    UPLOAD_SUCCESS = "Test plan uploaded successfully"
    REORDER_SUCCESS = "Test plan items reordered successfully"
    DELETE_SUCCESS = " deleted successfully"


# =============================================================================
# HTTP Status Codes (for reference)
# =============================================================================

class HttpStatus:
    """HTTP status code constants"""
    OK = 200
    CREATED = 201
    NO_CONTENT = 204
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    INTERNAL_SERVER_ERROR = 500


# =============================================================================
# Time Conversion Constants
# =============================================================================

class TimeConstants:
    """Time conversion constants"""
    MS_PER_SECOND = 1000  # Milliseconds per second
    DEFAULT_DECIMAL_PLACES = 3  # Default decimal places for time conversion
