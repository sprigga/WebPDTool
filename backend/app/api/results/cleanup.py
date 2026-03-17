"""
Measurement Result Cleanup Endpoints

Session cleanup and deletion endpoints.
Extracted from measurement_results.py lines 481-614.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
# Original code: from sqlalchemy.orm import Session
# Modified: Use async session for async DB migration (Wave 5)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete as sa_delete
from datetime import datetime, timedelta

# Original code: from app.core.database import get_db
# Modified: Use async DB dependency
from app.core.database import get_async_db
from app.core.api_helpers import PermissionChecker
from app.dependencies import get_current_active_user
from app.models.test_result import TestResult as TestResultModel
from app.models.test_session import TestSession as TestSessionModel

router = APIRouter()


@router.delete("/sessions/{session_id}")
async def delete_test_session(
    session_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Delete test session and all associated results

    Provides cleanup functionality similar to PDTool4's log management.
    Only allows deletion if user has appropriate permissions.
    """
    try:
        # Check if session exists
        # Original code: session = db.query(TestSessionModel).filter(...).first()
        # Modified: Use select() with await for async
        result = await db.execute(
            select(TestSessionModel).where(TestSessionModel.id == session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"Test session {session_id} not found"
            )

        # Original code: Manual permission check
        # Refactored: Use PermissionChecker helper
        PermissionChecker.check_admin_or_engineer(current_user, "delete test sessions")

        # Delete associated results first (cascade)
        # Original code: db.query(TestResultModel).filter(...).delete(synchronize_session=False)
        # Modified: Use sa_delete() with await for async
        await db.execute(
            sa_delete(TestResultModel).where(TestResultModel.session_id == session_id)
        )

        # Delete session
        await db.delete(session)
        await db.commit()

        return {
            "message": f"Test session {session_id} and associated results deleted successfully",
            "deleted_session_id": session_id
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete test session: {str(e)}"
        )



@router.post("/cleanup")
async def cleanup_old_results(
    days_to_keep: int = Query(30, ge=1, le=365),
    dry_run: bool = Query(True),
    db: AsyncSession = Depends(get_async_db),
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
        # Original code: old_sessions = db.query(TestSessionModel).filter(...).all()
        # Modified: Use select() with await for async
        result = await db.execute(
            select(TestSessionModel).where(TestSessionModel.start_time < cutoff_date)
        )
        old_sessions = result.scalars().all()

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
                        "start_time": s.start_time.isoformat() if s.start_time else None
                    }
                    for s in old_sessions
                ]
            }
        else:
            # Actually delete the sessions and results
            # 修改(簡化): 使用 bulk .in_() 取代 N×1 迴圈，避免每個 session 發出兩次 DB round-trip
            old_ids = [s.id for s in old_sessions]
            if old_ids:
                # Delete results first (referential integrity)
                # Original code: per-session loop with await db.execute(sa_delete(...)) + await db.delete()
                await db.execute(
                    sa_delete(TestResultModel).where(TestResultModel.session_id.in_(old_ids))
                )
                await db.execute(
                    sa_delete(TestSessionModel).where(TestSessionModel.id.in_(old_ids))
                )

            await db.commit()

            return {
                "dry_run": False,
                "deleted_sessions": len(old_ids),
                "cutoff_date": cutoff_date.isoformat()
            }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Cleanup operation failed: {str(e)}"
        )
