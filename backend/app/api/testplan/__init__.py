"""
Test Plan Management API Endpoints (Modular)

Refactored from testplans.py (655 lines) into smaller, focused modules.
This maintains backward compatibility with the original router structure.

Modules:
- queries.py: GET endpoints for retrieving test plans
- mutations.py: POST/PUT/DELETE endpoints for modifying test plans
- validation.py: Test point validation endpoint
- sessions.py: Session-related test result endpoints
"""

from fastapi import APIRouter

# Import sub-routers from modules
from app.api.testplan.queries import router as queries_router
from app.api.testplan.mutations import router as mutations_router
from app.api.testplan.validation import router as validation_router
from app.api.testplan.sessions import router as sessions_router

# Create main router
router = APIRouter()

# Include sub-routers
router.include_router(queries_router)
router.include_router(mutations_router)
router.include_router(validation_router)
router.include_router(sessions_router)

# Export for backward compatibility
__all__ = ["router"]
