"""
Measurement Result Export Endpoint

CSV export endpoint.
Extracted from measurement_results.py lines 402-478.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
# Original code: from sqlalchemy.orm import Session
# Modified: Use async session for async DB migration (Wave 5)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import csv
import io

# Original code: from app.core.database import get_db
# Modified: Use async DB dependency
from app.core.database import get_async_db
from app.dependencies import get_current_active_user
from app.models.test_result import TestResult as TestResultModel
from app.models.test_session import TestSession as TestSessionModel
from app.models.project import Project as ProjectModel
from app.models.station import Station as StationModel

router = APIRouter()


@router.get("/export/csv/{session_id}")
async def export_session_csv(
    session_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Export session results as CSV

    Similar to PDTool4's CSV export functionality for test results.
    """
    try:
        # Get session and results
        # Original code: session = db.query(TestSessionModel).join(...).filter(...).first()
        # Modified: Use select() with await for async
        result = await db.execute(
            select(TestSessionModel)
            .join(ProjectModel)
            .join(StationModel)
            .where(TestSessionModel.id == session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"Test session {session_id} not found"
            )

        # Original code: results = db.query(TestResultModel).filter(...).order_by(...).all()
        # Modified: Use select() with await
        result = await db.execute(
            select(TestResultModel)
            .where(TestResultModel.test_session_id == session_id)
            .order_by(TestResultModel.item_no)
        )
        results = result.scalars().all()

        # Create CSV content
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            'Item No', 'Item Name', 'Result', 'Measured Value',
            'Min Limit', 'Max Limit', 'Error Message',
            'Execution Time (ms)', 'Test Time'
        ])

        # Write data rows
        for result in results:
            writer.writerow([
                result.item_no,
                result.item_name,
                result.result,
                result.measured_value,
                result.min_limit,
                result.max_limit,
                result.error_message or '',
                result.execution_duration_ms,
                result.created_at.isoformat()
            ])

        output.seek(0)

        # Create filename
        filename = f"{session.project.name}_{session.station.name}_{session.serial_number}_{session.started_at.strftime('%Y%m%d_%H%M%S')}.csv"

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to export CSV: {str(e)}"
        )
