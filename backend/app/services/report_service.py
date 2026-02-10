"""
Report Service - Automatic Test Report Generation

Provides automatic CSV report generation and storage for production line traceability.
Similar to PDTool4's polish/reports/default_report.py but integrated into WebPDTool.
"""

import csv
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.test_session import TestSession as TestSessionModel
from app.models.test_result import TestResult as TestResultModel
from app.core.constants import TestResult as TestResultConstants

logger = logging.getLogger(__name__)


class ReportService:
    """
    Automatic test report generation and storage service

    Features:
    - Automatic CSV generation on test completion
    - Organized storage by project/station/date
    - Filename format: {serial_number}_{timestamp}.csv
    - WebPDTool enhanced format with error messages and execution times
    """

    def __init__(self, base_report_dir: str = "reports"):
        """
        Initialize report service

        Args:
            base_report_dir: Base directory for storing reports (default: "reports")
        """
        self.base_report_dir = Path(base_report_dir)
        self.logger = logging.getLogger(self.__class__.__name__)

        # Ensure base directory exists
        self.base_report_dir.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"Report service initialized. Base directory: {self.base_report_dir.absolute()}")

    def _get_report_directory(
        self,
        project_name: str,
        station_name: str,
        test_date: datetime
    ) -> Path:
        """
        Get organized report directory path

        Directory structure:
        reports/
        └── {project_name}/
            └── {station_name}/
                └── YYYYMMDD/

        Args:
            project_name: Project name
            station_name: Station name
            test_date: Test date for organizing reports

        Returns:
            Path object for the report directory
        """
        date_str = test_date.strftime("%Y%m%d")
        report_dir = self.base_report_dir / project_name / station_name / date_str

        # 修正: 添加權限錯誤處理，避免因目錄權限問題導致測試失敗
        try:
            report_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError as e:
            # 如果遇到權限錯誤，使用備用目錄
            self.logger.warning(f"Permission denied creating {report_dir}, using fallback directory")
            # 使用臨時目錄或用戶主目錄下的 reports
            fallback_dir = Path.home() / "webpdtool_reports" / project_name / station_name / date_str
            fallback_dir.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Using fallback report directory: {fallback_dir}")
            return fallback_dir

        return report_dir

    def _generate_filename(
        self,
        serial_number: str,
        timestamp: datetime
    ) -> str:
        """
        Generate report filename

        Format: {serial_number}_{YYYYMMDD_HHMMSS}.csv
        Example: SN12345678_20260128_143045.csv

        Args:
            serial_number: Product serial number
            timestamp: Test completion timestamp

        Returns:
            Generated filename
        """
        time_str = timestamp.strftime("%Y%m%d_%H%M%S")
        # Sanitize serial number (replace spaces and special chars with underscore)
        safe_serial = serial_number.replace(" ", "_").replace("/", "_")
        return f"{safe_serial}_{time_str}.csv"

    def save_session_report(
        self,
        session_id: int,
        db: Session
    ) -> Optional[Path]:
        """
        Generate and save test session report to local storage

        This method is automatically called when a test session completes.
        It generates a CSV report with all test results and saves it to
        the organized directory structure.

        Args:
            session_id: Test session ID
            db: Database session

        Returns:
            Path to the saved report file, or None if failed
        """
        try:
            # Fetch session data with related information
            session = db.query(TestSessionModel)\
                       .filter(TestSessionModel.id == session_id)\
                       .first()

            if not session:
                self.logger.error(f"Session {session_id} not found")
                return None

            # Fetch all test results for this session
            results = db.query(TestResultModel)\
                       .filter(TestResultModel.session_id == session_id)\
                       .order_by(TestResultModel.item_no)\
                       .all()

            if not results:
                self.logger.warning(f"No results found for session {session_id}")
                return None

            # Get project and station names
            # 原有程式碼: project_name = session.project.name if session.project else "Unknown_Project"
            # 修改: TestSession 模型沒有直接的 project 關係，需要通過 station.project 訪問
            # 修改: Project 模型使用 project_name 屬性而非 name
            project_name = session.station.project.project_name if session.station and session.station.project else "Unknown_Project"
            station_name = session.station.station_name if session.station else "Unknown_Station"

            # Determine report directory
            report_dir = self._get_report_directory(
                project_name,
                station_name,
                session.start_time  # 原有程式碼: session.started_at，修改: 使用模型中的正確欄位名稱
            )

            # Generate filename
            filename = self._generate_filename(
                session.serial_number,
                session.end_time or session.start_time  # 原有程式碼: session.completed_at or session.started_at
            )

            filepath = report_dir / filename

            # Write CSV report
            self._write_csv_report(filepath, session, results)

            self.logger.info(f"Report saved successfully: {filepath}")
            return filepath

        except Exception as e:
            self.logger.error(f"Failed to save report for session {session_id}: {e}", exc_info=True)
            return None

    def _write_csv_report(
        self,
        filepath: Path,
        session: TestSessionModel,
        results: List[TestResultModel]
    ):
        """
        Write CSV report file with WebPDTool enhanced format

        CSV Format:
        Item No, Item Name, Result, Measured Value, Min Limit, Max Limit,
        Error Message, Execution Time (ms), Test Time

        Args:
            filepath: Output file path
            session: Test session object
            results: List of test result objects
        """
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)

            # Write header
            writer.writerow([
                'Item No',
                'Item Name',
                'Result',
                'Measured Value',
                'Min Limit',
                'Max Limit',
                'Error Message',
                'Execution Time (ms)',
                'Test Time'
            ])

            # Write data rows
            for result in results:
                writer.writerow([
                    result.item_no,
                    result.item_name,
                    result.result.value if hasattr(result.result, 'value') else result.result,
                    result.measured_value or '',
                    result.lower_limit or '',
                    result.upper_limit or '',
                    result.error_message or '',
                    result.execution_duration_ms or '',
                    result.test_time.isoformat() if result.test_time else ''
                ])

    def get_report_path(
        self,
        session_id: int,
        db: Session
    ) -> Optional[Path]:
        """
        Get the path to a saved report for a given session

        Args:
            session_id: Test session ID
            db: Database session

        Returns:
            Path to the report file if it exists, None otherwise
        """
        try:
            session = db.query(TestSessionModel)\
                       .filter(TestSessionModel.id == session_id)\
                       .first()

            if not session:
                return None

            # 原有程式碼: project_name = session.project.name if session.project else "Unknown_Project"
            # 修改: TestSession 模型沒有直接的 project 關係，需要通過 station.project 訪問
            # 修改: Project 模型使用 project_name 屬性而非 name
            project_name = session.station.project.project_name if session.station and session.station.project else "Unknown_Project"
            station_name = session.station.station_name if session.station else "Unknown_Station"

            report_dir = self._get_report_directory(
                project_name,
                station_name,
                session.start_time  # 原有程式碼: session.started_at
            )

            filename = self._generate_filename(
                session.serial_number,
                session.end_time or session.start_time  # 原有程式碼: session.completed_at or session.started_at
            )

            filepath = report_dir / filename

            return filepath if filepath.exists() else None

        except Exception as e:
            self.logger.error(f"Failed to get report path for session {session_id}: {e}")
            return None

    def list_reports(
        self,
        project_name: Optional[str] = None,
        station_name: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> List[Path]:
        """
        List saved report files with optional filtering

        Args:
            project_name: Filter by project name
            station_name: Filter by station name
            date_from: Filter by date range (from)
            date_to: Filter by date range (to)

        Returns:
            List of report file paths
        """
        reports = []

        try:
            # Build search pattern
            if project_name and station_name:
                search_path = self.base_report_dir / project_name / station_name
            elif project_name:
                search_path = self.base_report_dir / project_name
            else:
                search_path = self.base_report_dir

            if not search_path.exists():
                return reports

            # Find all CSV files
            for csv_file in search_path.rglob("*.csv"):
                # Apply date filtering if specified
                if date_from or date_to:
                    # Extract date from parent directory name (YYYYMMDD)
                    date_dir = csv_file.parent.name
                    try:
                        file_date = datetime.strptime(date_dir, "%Y%m%d")
                        if date_from and file_date < date_from:
                            continue
                        if date_to and file_date > date_to:
                            continue
                    except ValueError:
                        # Skip if directory name is not a valid date
                        continue

                reports.append(csv_file)

            # Sort by modification time (newest first)
            reports.sort(key=lambda p: p.stat().st_mtime, reverse=True)

        except Exception as e:
            self.logger.error(f"Failed to list reports: {e}")

        return reports


# Global report service instance
report_service = ReportService()
