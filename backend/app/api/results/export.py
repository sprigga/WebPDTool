"""
Measurement Result Export Endpoint

CSV export endpoint.
Extracted from measurement_results.py lines 402-478.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import csv
import io

from app.core.database import get_db
from app.dependencies import get_current_active_user
from app.models.test_result import TestResult as TestResultModel
from app.models.test_session import TestSession as TestSessionModel
from app.models.project import Project as ProjectModel
from app.models.station import Station as StationModel

router = APIRouter()


@router.get("/export/csv/{session_id}")
async def export_session_csv(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Export session results as CSV

    Similar to PDTool4's CSV export functionality for test results.
    """
    try:
        # Get session and results
        session = db.query(TestSessionModel)\
                   .join(ProjectModel)\
                   .join(StationModel)\
                   .filter(TestSessionModel.id == session_id)\
                   .first()

        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"Test session {session_id} not found"
            )

        results = db.query(TestResultModel)\
                   .filter(TestResultModel.test_session_id == session_id)\
                   .order_by(TestResultModel.item_no)\
                   .all()

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
