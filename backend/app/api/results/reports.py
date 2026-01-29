"""
Saved Report Management Endpoints

Provides API access to automatically saved test reports.
Complements the automatic report generation in test_engine.py.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from pydantic import BaseModel

from app.core.database import get_db
from app.dependencies import get_current_active_user
from app.services.report_service import report_service

router = APIRouter()


class SavedReportInfo(BaseModel):
    """Information about a saved report file"""
    filename: str
    filepath: str
    project: str
    station: str
    date: str
    size_bytes: int
    modified_at: str


@router.get("/reports/list", response_model=List[SavedReportInfo])
async def list_saved_reports(
    project_name: Optional[str] = Query(None, description="Filter by project name"),
    station_name: Optional[str] = Query(None, description="Filter by station name"),
    date_from: Optional[date] = Query(None, description="Filter from date (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="Filter to date (YYYY-MM-DD)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of reports to return"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    List saved test reports with optional filtering

    Returns information about automatically saved CSV reports.
    Reports are organized by project/station/date in the file system.

    Example:
        GET /api/results/reports/list?project_name=MyProject&station_name=Station1
    """
    try:
        # Convert dates to datetime if provided
        date_from_dt = None
        date_to_dt = None
        if date_from:
            from datetime import datetime
            date_from_dt = datetime.combine(date_from, datetime.min.time())
        if date_to:
            from datetime import datetime
            date_to_dt = datetime.combine(date_to, datetime.max.time())

        # Get report files
        report_files = report_service.list_reports(
            project_name=project_name,
            station_name=station_name,
            date_from=date_from_dt,
            date_to=date_to_dt
        )

        # Limit results
        report_files = report_files[:limit]

        # Build response
        reports_info = []
        for report_path in report_files:
            try:
                # Extract information from path
                # Path structure: reports/{project}/{station}/{YYYYMMDD}/{filename}.csv
                parts = report_path.parts

                if len(parts) >= 4:
                    project = parts[-4]
                    station = parts[-3]
                    date_str = parts[-2]
                else:
                    project = "Unknown"
                    station = "Unknown"
                    date_str = "Unknown"

                # Get file stats
                stat = report_path.stat()

                from datetime import datetime
                modified_at = datetime.fromtimestamp(stat.st_mtime).isoformat()

                reports_info.append(SavedReportInfo(
                    filename=report_path.name,
                    filepath=str(report_path),
                    project=project,
                    station=station,
                    date=date_str,
                    size_bytes=stat.st_size,
                    modified_at=modified_at
                ))
            except Exception as e:
                # Skip files that can't be processed
                continue

        return reports_info

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list reports: {str(e)}"
        )


@router.get("/reports/download/{session_id}")
async def download_saved_report(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Download saved report for a specific test session

    Returns the automatically saved CSV report file.

    Args:
        session_id: Test session ID

    Returns:
        CSV file download
    """
    try:
        # Get report path
        report_path = report_service.get_report_path(session_id, db)

        if not report_path or not report_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Report not found for session {session_id}"
            )

        # Return file for download
        return FileResponse(
            path=str(report_path),
            media_type="text/csv",
            filename=report_path.name,
            headers={
                "Content-Disposition": f"attachment; filename={report_path.name}"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to download report: {str(e)}"
        )


@router.get("/reports/download-by-path")
async def download_report_by_path(
    filepath: str = Query(..., description="Full path to the report file"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Download report by file path

    Useful when you have the exact file path from the list_saved_reports endpoint.

    Args:
        filepath: Full path to the report file

    Returns:
        CSV file download
    """
    try:
        from pathlib import Path

        report_path = Path(filepath)

        # Security check: ensure path is within reports directory
        report_base = report_service.base_report_dir.resolve()
        try:
            report_path = report_path.resolve()
            report_path.relative_to(report_base)
        except ValueError:
            raise HTTPException(
                status_code=403,
                detail="Access denied: Invalid report path"
            )

        if not report_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Report file not found: {filepath}"
            )

        if not report_path.is_file():
            raise HTTPException(
                status_code=400,
                detail="Path is not a file"
            )

        # Return file for download
        return FileResponse(
            path=str(report_path),
            media_type="text/csv",
            filename=report_path.name,
            headers={
                "Content-Disposition": f"attachment; filename={report_path.name}"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to download report: {str(e)}"
        )


@router.delete("/reports/cleanup")
async def cleanup_old_reports(
    days_to_keep: int = Query(90, ge=1, le=3650, description="Number of days to keep reports"),
    project_name: Optional[str] = Query(None, description="Limit cleanup to specific project"),
    station_name: Optional[str] = Query(None, description="Limit cleanup to specific station"),
    dry_run: bool = Query(True, description="Preview without actually deleting"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Cleanup old report files

    Deletes reports older than specified number of days.
    Use dry_run=true to preview what would be deleted.

    Args:
        days_to_keep: Number of days to keep reports (default: 90)
        project_name: Optional project filter
        station_name: Optional station filter
        dry_run: If true, only preview without deleting

    Returns:
        Summary of files to delete or deleted
    """
    try:
        from datetime import datetime, timedelta
        from pathlib import Path

        # Calculate cutoff date
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)

        # Get all reports
        report_files = report_service.list_reports(
            project_name=project_name,
            station_name=station_name
        )

        # Filter by modification date
        old_reports = []
        total_size = 0

        for report_path in report_files:
            try:
                stat = report_path.stat()
                modified_time = datetime.fromtimestamp(stat.st_mtime)

                if modified_time < cutoff_date:
                    old_reports.append({
                        "filepath": str(report_path),
                        "filename": report_path.name,
                        "modified_at": modified_time.isoformat(),
                        "size_bytes": stat.st_size
                    })
                    total_size += stat.st_size
            except Exception:
                continue

        # Delete files if not dry run
        deleted_count = 0
        if not dry_run:
            for report_info in old_reports:
                try:
                    Path(report_info["filepath"]).unlink()
                    deleted_count += 1
                except Exception as e:
                    # Log but continue
                    pass

        return {
            "dry_run": dry_run,
            "cutoff_date": cutoff_date.isoformat(),
            "days_to_keep": days_to_keep,
            "total_old_reports": len(old_reports),
            "deleted_count": deleted_count if not dry_run else 0,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "reports": old_reports[:100]  # Limit preview to 100 files
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cleanup reports: {str(e)}"
        )
