"""
Measurement Result Management API Endpoints (Modular)

Refactored from measurement_results.py (614 lines) into smaller, focused modules.
This maintains backward compatibility with the original router structure.

Modules:
- sessions.py: Session listing and detail endpoints
- measurements.py: Individual measurement result endpoints
- summary.py: Summary statistics endpoint
- export.py: CSV export endpoint
- cleanup.py: Session cleanup and deletion endpoints
- reports.py: Saved report management endpoints (automatic report storage)
"""

from fastapi import APIRouter

# Import sub-routers from modules
from app.api.results.sessions import router as sessions_router
from app.api.results.measurements import router as measurements_router
from app.api.results.summary import router as summary_router
from app.api.results.export import router as export_router
from app.api.results.cleanup import router as cleanup_router
from app.api.results.reports import router as reports_router

# Create main router
router = APIRouter()

# Include sub-routers
router.include_router(sessions_router)
router.include_router(measurements_router)
router.include_router(summary_router)
router.include_router(export_router)
router.include_router(cleanup_router)
router.include_router(reports_router)

# Export for backward compatibility
__all__ = ["router"]
