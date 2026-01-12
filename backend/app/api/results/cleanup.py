"""
Measurement Result Cleanup Endpoints

Session cleanup and deletion endpoints.
Extracted from measurement_results.py lines 481-614.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.api_helpers import PermissionChecker
from app.dependencies import get_current_active_user
from app.models.test_result import TestResult as TestResultModel
from app.models.test_session import TestSession as TestSessionModel

router = APIRouter()


@router.delete("/sessions/{session_id}")
async def delete_test_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Delete test session and all associated results

    Provides cleanup functionality similar to PDTool4's log management.
    Only allows deletion if user has appropriate permissions.
    """
    try:
        # Check if session exists
        session = db.query(TestSessionModel)\
                   .filter(TestSessionModel.id == session_id)\
                   .first()

        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"Test session {session_id} not found"
            )

        # Original code: Manual permission check
        # Refactored: Use PermissionChecker helper
        PermissionChecker.check_admin_or_engineer(current_user, "delete test sessions")

        # Delete associated results first (cascade)
        db.query(TestResultModel)\
          .filter(TestResultModel.test_session_id == session_id)\
          .delete(synchronize_session=False)

        # Delete session
        db.delete(session)
        db.commit()

        return {
            "message": f"Test session {session_id} and associated results deleted successfully",
            "deleted_session_id": session_id
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete test session: {str(e)}"
        )


@router.post("/cleanup")
async def cleanup_old_results(
    days_to_keep: int = Query(30, ge=1, le=365),
    dry_run: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Cleanup old test results

    Similar to PDTool4's log cleanup functionality that manages disk space
    by removing old test results.
    """
    try:
        # Original code: Manual permission check
        # Refactored: Use PermissionChecker helper
        PermissionChecker.check_admin(current_user, "perform cleanup operations")

        # Calculate cutoff date
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

        # Find sessions to be deleted
        old_sessions = db.query(TestSessionModel)\
                        .filter(TestSessionModel.started_at < cutoff_date)\
                        .all()

        if dry_run:
            # Just return what would be deleted
            return {
                "dry_run": True,
                "sessions_to_delete": len(old_sessions),
                "cutoff_date": cutoff_date.isoformat(),
                "sessions": [
                    {
                        "id": s.id,
                        "project": s.project.name,
                        "station": s.station.name,
                        "serial_number": s.serial_number,
                        "started_at": s.started_at.isoformat()
                    }
                    for s in old_sessions
                ]
            }
        else:
            # Actually delete the sessions and results
            deleted_count = 0
            for session in old_sessions:
                # Delete results first
                db.query(TestResultModel)\
                  .filter(TestResultModel.test_session_id == session.id)\
                  .delete(synchronize_session=False)

                # Delete session
                db.delete(session)
                deleted_count += 1

            db.commit()

            return {
                "dry_run": False,
                "deleted_sessions": deleted_count,
                "cutoff_date": cutoff_date.isoformat()
            }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Cleanup operation failed: {str(e)}"
        )
