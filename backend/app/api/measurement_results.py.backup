"""
Measurement Result Storage and Retrieval APIs
Based on PDTool4 result management and database integration
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime, date
import json

from app.core.database import get_db
from app.dependencies import get_current_active_user
from app.models.test_result import TestResult as TestResultModel
from app.models.test_session import TestSession as TestSessionModel
from app.models.project import Project as ProjectModel
from app.models.station import Station as StationModel

router = APIRouter()


class MeasurementResultResponse(BaseModel):
    """Response model for measurement result"""
    id: int
    test_session_id: int
    item_no: int
    item_name: str
    result: str
    measured_value: Optional[float] = None
    min_limit: Optional[float] = None
    max_limit: Optional[float] = None
    error_message: Optional[str] = None
    execution_duration_ms: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class TestSessionResponse(BaseModel):
    """Response model for test session with results"""
    id: int
    project_name: str
    station_name: str
    serial_number: str
    operator_id: Optional[str] = None
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    total_tests: int
    passed_tests: int
    failed_tests: int
    error_tests: int
    results: List[MeasurementResultResponse] = []


class ResultSummary(BaseModel):
    """Summary statistics for measurement results"""
    total_sessions: int
    passed_sessions: int
    failed_sessions: int
    pass_rate: float
    total_measurements: int
    avg_execution_time_ms: float
    most_common_failures: List[Dict[str, Any]]


class ResultFilter(BaseModel):
    """Filter parameters for result queries"""
    project_id: Optional[int] = None
    station_id: Optional[int] = None
    serial_number: Optional[str] = None
    operator_id: Optional[str] = None
    result_status: Optional[str] = None  # PASS, FAIL, ERROR
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    test_item_name: Optional[str] = None


@router.get("/sessions", response_model=List[TestSessionResponse])
async def get_test_sessions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    project_id: Optional[int] = Query(None),
    station_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Get test sessions with optional filtering
    
    Provides comprehensive session listing similar to PDTool4's log browsing
    functionality where users can view test history and results.
    """
    try:
        query = db.query(TestSessionModel).join(ProjectModel).join(StationModel)
        
        # Apply filters
        if project_id:
            query = query.filter(TestSessionModel.project_id == project_id)
        
        if station_id:
            query = query.filter(TestSessionModel.station_id == station_id)
        
        if status:
            query = query.filter(TestSessionModel.status == status)
        
        if date_from:
            query = query.filter(TestSessionModel.started_at >= date_from)
        
        if date_to:
            query = query.filter(TestSessionModel.started_at <= date_to)
        
        # Order by most recent first
        sessions = query.order_by(desc(TestSessionModel.started_at))\
                      .offset(skip)\
                      .limit(limit)\
                      .all()
        
        # Build response with session statistics
        response = []
        for session in sessions:
            # Get test results for this session
            results = db.query(TestResultModel)\
                       .filter(TestResultModel.test_session_id == session.id)\
                       .all()
            
            # Calculate statistics
            total_tests = len(results)
            passed_tests = sum(1 for r in results if r.result == "PASS")
            failed_tests = sum(1 for r in results if r.result == "FAIL")
            error_tests = sum(1 for r in results if r.result == "ERROR")
            
            # Convert results to response format
            result_responses = [
                MeasurementResultResponse(
                    id=r.id,
                    test_session_id=r.test_session_id,
                    item_no=r.item_no,
                    item_name=r.item_name,
                    result=r.result,
                    measured_value=r.measured_value,
                    min_limit=r.min_limit,
                    max_limit=r.max_limit,
                    error_message=r.error_message,
                    execution_duration_ms=r.execution_duration_ms,
                    created_at=r.created_at
                )
                for r in results
            ]
            
            response.append(TestSessionResponse(
                id=session.id,
                project_name=session.project.name,
                station_name=session.station.name,
                serial_number=session.serial_number,
                operator_id=session.operator_id,
                status=session.status,
                started_at=session.started_at,
                completed_at=session.completed_at,
                total_tests=total_tests,
                passed_tests=passed_tests,
                failed_tests=failed_tests,
                error_tests=error_tests,
                results=result_responses
            ))
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve test sessions: {str(e)}"
        )


@router.get("/sessions/{session_id}", response_model=TestSessionResponse)
async def get_test_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Get detailed test session with all measurement results
    
    Equivalent to PDTool4's detailed test log viewing where users can
    examine all test points and their results for a specific session.
    """
    try:
        session = db.query(TestSessionModel)\
                   .join(ProjectModel)\
                   .join(StationModel)\
                   .filter(TestSessionModel.id == session_id)\
                   .first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Test session {session_id} not found"
            )
        
        # Get all measurement results for this session
        results = db.query(TestResultModel)\
                   .filter(TestResultModel.test_session_id == session_id)\
                   .order_by(TestResultModel.item_no)\
                   .all()
        
        # Calculate statistics
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.result == "PASS")
        failed_tests = sum(1 for r in results if r.result == "FAIL") 
        error_tests = sum(1 for r in results if r.result == "ERROR")
        
        # Convert results to response format
        result_responses = [
            MeasurementResultResponse(
                id=r.id,
                test_session_id=r.test_session_id,
                item_no=r.item_no,
                item_name=r.item_name,
                result=r.result,
                measured_value=r.measured_value,
                min_limit=r.min_limit,
                max_limit=r.max_limit,
                error_message=r.error_message,
                execution_duration_ms=r.execution_duration_ms,
                created_at=r.created_at
            )
            for r in results
        ]
        
        return TestSessionResponse(
            id=session.id,
            project_name=session.project.name,
            station_name=session.station.name,
            serial_number=session.serial_number,
            operator_id=session.operator_id,
            status=session.status,
            started_at=session.started_at,
            completed_at=session.completed_at,
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            error_tests=error_tests,
            results=result_responses
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve test session: {str(e)}"
        )


@router.get("/results", response_model=List[MeasurementResultResponse])
async def get_measurement_results(
    skip: int = Query(0, ge=0),
    limit: int = Query(1000, ge=1, le=5000),
    session_id: Optional[int] = Query(None),
    test_item_name: Optional[str] = Query(None),
    result_status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Get measurement results with filtering
    
    Allows detailed analysis of measurement data similar to PDTool4's
    result analysis capabilities.
    """
    try:
        query = db.query(TestResultModel)
        
        # Apply filters
        if session_id:
            query = query.filter(TestResultModel.test_session_id == session_id)
        
        if test_item_name:
            query = query.filter(TestResultModel.item_name.ilike(f"%{test_item_name}%"))
        
        if result_status:
            query = query.filter(TestResultModel.result == result_status)
        
        # Order by creation time
        results = query.order_by(desc(TestResultModel.created_at))\
                      .offset(skip)\
                      .limit(limit)\
                      .all()
        
        return [
            MeasurementResultResponse(
                id=r.id,
                test_session_id=r.test_session_id,
                item_no=r.item_no,
                item_name=r.item_name,
                result=r.result,
                measured_value=r.measured_value,
                min_limit=r.min_limit,
                max_limit=r.max_limit,
                error_message=r.error_message,
                execution_duration_ms=r.execution_duration_ms,
                created_at=r.created_at
            )
            for r in results
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve measurement results: {str(e)}"
        )


@router.get("/summary", response_model=ResultSummary)
async def get_result_summary(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    project_id: Optional[int] = Query(None),
    station_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Get summary statistics for measurement results
    
    Provides overview statistics similar to PDTool4's test summary reports
    that show pass/fail rates and common failure modes.
    """
    try:
        # Base queries
        session_query = db.query(TestSessionModel)
        result_query = db.query(TestResultModel).join(TestSessionModel)
        
        # Apply date filters
        if date_from:
            session_query = session_query.filter(TestSessionModel.started_at >= date_from)
            result_query = result_query.filter(TestSessionModel.started_at >= date_from)
        
        if date_to:
            session_query = session_query.filter(TestSessionModel.started_at <= date_to)
            result_query = result_query.filter(TestSessionModel.started_at <= date_to)
        
        # Apply project/station filters
        if project_id:
            session_query = session_query.filter(TestSessionModel.project_id == project_id)
            result_query = result_query.filter(TestSessionModel.project_id == project_id)
        
        if station_id:
            session_query = session_query.filter(TestSessionModel.station_id == station_id)
            result_query = result_query.filter(TestSessionModel.station_id == station_id)
        
        # Calculate session statistics
        all_sessions = session_query.all()
        total_sessions = len(all_sessions)
        passed_sessions = sum(1 for s in all_sessions if s.status == "PASSED")
        failed_sessions = sum(1 for s in all_sessions if s.status == "FAILED")
        pass_rate = (passed_sessions / total_sessions * 100) if total_sessions > 0 else 0
        
        # Calculate measurement statistics
        all_results = result_query.all()
        total_measurements = len(all_results)
        
        # Calculate average execution time
        execution_times = [r.execution_duration_ms for r in all_results if r.execution_duration_ms]
        avg_execution_time_ms = sum(execution_times) / len(execution_times) if execution_times else 0
        
        # Find most common failures
        failed_results = [r for r in all_results if r.result == "FAIL"]
        failure_counts = {}
        for result in failed_results:
            key = result.item_name
            failure_counts[key] = failure_counts.get(key, 0) + 1
        
        most_common_failures = [
            {"test_item": item, "failure_count": count, "failure_rate": count/total_measurements*100}
            for item, count in sorted(failure_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        ]
        
        return ResultSummary(
            total_sessions=total_sessions,
            passed_sessions=passed_sessions,
            failed_sessions=failed_sessions,
            pass_rate=round(pass_rate, 2),
            total_measurements=total_measurements,
            avg_execution_time_ms=round(avg_execution_time_ms, 2),
            most_common_failures=most_common_failures
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate result summary: {str(e)}"
        )


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
    from fastapi.responses import StreamingResponse
    import csv
    import io
    
    try:
        # Get session and results
        session = db.query(TestSessionModel)\
                   .join(ProjectModel)\
                   .join(StationModel)\
                   .filter(TestSessionModel.id == session_id)\
                   .first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
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
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export CSV: {str(e)}"
        )


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
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Test session {session_id} not found"
            )
        
        # Check user permissions (could be expanded based on requirements)
        user_role = current_user.get("role", "")
        if user_role not in ["admin", "engineer"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to delete test sessions"
            )
        
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
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
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
    from datetime import timedelta
    
    try:
        # Check user permissions
        user_role = current_user.get("role", "")
        if user_role not in ["admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can perform cleanup operations"
            )
        
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
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cleanup operation failed: {str(e)}"
        )