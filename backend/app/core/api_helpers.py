"""
API Helper Functions and Utilities

Centralized utilities for common API operations to reduce code duplication.
Original code patterns repeated across multiple files are consolidated here.
"""

from functools import wraps
from typing import List, Dict, Any, Optional, TypeVar, Type
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.test_result import TestResult as TestResultModel

T = TypeVar('T')


# =============================================================================
# Entity Existence Checker
# =============================================================================

def get_entity_or_404(
    db: Session,
    model: Type[T],
    entity_id: int,
    detail: Optional[str] = None
) -> T:
    """
    Get entity by ID or raise 404

    Original pattern (repeated 15+ times across codebase):
    ```python
    station = db.query(Station).filter(Station.id == station_id).first()
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")
    ```

    Usage:
        get_entity_or_404(db, Station, station_id, "Station not found")
    """
    entity = db.query(model).filter(model.id == entity_id).first()
    if not entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail or f"{model.__name__} not found"
        )
    return entity


def get_entity_by_field_or_404(
    db: Session,
    model: Type[T],
    field_name: str,
    field_value: Any,
    detail: Optional[str] = None
) -> T:
    """
    Get entity by field value or raise 404

    Usage:
        get_entity_by_field_or_404(db, User, "username", username, "User not found")
    """
    filter_kwargs = {field_name: field_value}
    entity = db.query(model).filter_by(**filter_kwargs).first()
    if not entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail or f"{model.__name__} with {field_name}='{field_value}' not found"
        )
    return entity


# =============================================================================
# Permission Checker
# =============================================================================

class PermissionChecker:
    """
    Centralized permission checking to reduce duplicated role checks

    Original pattern (repeated 15+ times):
    ```python
    user_role = current_user.get("role")
    if user_role not in ["admin", "engineer"]:
        raise HTTPException(status_code=403, detail="Only administrators and engineers can...")
    ```

    Usage:
        PermissionChecker.check_admin_or_engineer(current_user, "create stations")
    """

    ADMIN = "admin"
    ENGINEER = "engineer"
    USER = "user"

    @staticmethod
    def check_role(current_user: dict, allowed_roles: List[str], action: str = "perform this action"):
        """
        Check if user has required role

        Args:
            current_user: Current authenticated user dict
            allowed_roles: List of roles that can perform the action
            action: Description of the action for error message
        """
        user_role = current_user.get("role")
        if user_role not in allowed_roles:
            role_names = ", ".join(allowed_roles)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Only {role_names} can {action}"
            )

    @staticmethod
    def check_admin(current_user: dict, action: str = "perform this action"):
        """Check if user is admin"""
        PermissionChecker.check_role(current_user, [PermissionChecker.ADMIN], action)

    @staticmethod
    def check_engineer(current_user: dict, action: str = "perform this action"):
        """Check if user is engineer"""
        PermissionChecker.check_role(current_user, [PermissionChecker.ENGINEER], action)

    @staticmethod
    def check_admin_or_engineer(current_user: dict, action: str = "perform this action"):
        """Check if user is admin or engineer"""
        PermissionChecker.check_role(
            current_user,
            [PermissionChecker.ADMIN, PermissionChecker.ENGINEER],
            action
        )


# =============================================================================
# API Error Handler Decorator
# =============================================================================

def handle_api_errors(func):
    """
    Decorator for standardized API error handling

    Original pattern (repeated throughout):
    ```python
    try:
        # ... code ...
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ...: {str(e)}"
        )
    ```

    Usage:
        @router.get("/items")
        @handle_api_errors
        async def get_items(...):
            # ... code ...
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except HTTPException:
            raise
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            func_name = func.__name__
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to {func_name}: {str(e)}"
            )
    return wrapper


# =============================================================================
# Statistics Calculator
# =============================================================================

def calculate_test_statistics(results: List[TestResultModel]) -> Dict[str, int]:
    """
    Calculate pass/fail/error statistics from test results

    Original duplicated code in measurement_results.py lines 133-136 and 213-216:
    ```python
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r.result == "PASS")
    failed_tests = sum(1 for r in results if r.result == "FAIL")
    error_tests = sum(1 for r in results if r.result == "ERROR")
    ```

    Args:
        results: List of TestResultModel objects

    Returns:
        Dictionary with total_tests, passed_tests, failed_tests, error_tests
    """
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r.result == "PASS")
    failed_tests = sum(1 for r in results if r.result == "FAIL")
    error_tests = sum(1 for r in results if r.result == "ERROR")

    return {
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "failed_tests": failed_tests,
        "error_tests": error_tests
    }


# =============================================================================
# Response Builders
# =============================================================================

def build_success_response(message: str, **kwargs) -> Dict[str, Any]:
    """Build a standardized success response"""
    response = {"message": message}
    response.update(kwargs)
    return response


def build_error_response(detail: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR) -> HTTPException:
    """Build a standardized error response"""
    return HTTPException(status_code=status_code, detail=detail)
