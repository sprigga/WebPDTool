"""
Report Configuration

Centralized configuration for automatic report generation.
"""

from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional


class ReportSettings(BaseSettings):
    """Report generation settings"""

    # Base directory for storing reports
    REPORT_BASE_DIR: str = "reports"

    # Whether to enable automatic report generation
    REPORT_AUTO_SAVE: bool = True

    # Date format for report directory organization
    REPORT_DATE_FORMAT: str = "%Y%m%d"

    # Timestamp format for report filenames
    REPORT_TIMESTAMP_FORMAT: str = "%Y%m%d_%H%M%S"

    # Maximum age of reports to keep (days)
    # 0 means never auto-delete
    REPORT_MAX_AGE_DAYS: int = 0

    # CSV encoding
    REPORT_CSV_ENCODING: str = "utf-8"

    class Config:
        env_file = ".env"
        env_prefix = ""
        case_sensitive = True


# Global settings instance
report_settings = ReportSettings()


def get_report_directory() -> Path:
    """
    Get the absolute path to the report directory

    Returns:
        Path object for the report directory
    """
    report_path = Path(report_settings.REPORT_BASE_DIR)

    # If relative path, make it relative to backend directory
    if not report_path.is_absolute():
        backend_dir = Path(__file__).parent.parent.parent
        report_path = backend_dir / report_path

    # Create directory if it doesn't exist
    report_path.mkdir(parents=True, exist_ok=True)

    return report_path
