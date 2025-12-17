"""
CSV Test Plan Parser Utility
Parses test plan CSV files from PDTool4 format
"""
import csv
import io
from typing import List, Dict, Any, Optional
from pathlib import Path
from app.schemas.testplan import TestPlanCSVRow


class CSVParseError(Exception):
    """Custom exception for CSV parsing errors"""
    pass


class TestPlanCSVParser:
    """Parser for test plan CSV files"""

    # Expected CSV header columns
    EXPECTED_HEADERS = [
        'ID', 'ItemKey', 'ValueType', 'LimitType', 'EqLimit', 'LL', 'UL',
        'PassOrFail', 'measureValue', 'ExecuteName', 'case', 'Port', 'Baud',
        'Command', 'InitialCommand', 'Timeout', 'WaitmSec', 'Instrument',
        'Channel', 'Item', 'Type', 'ImagePath', 'content', 'keyWord',
        'spiltCount', 'splitLength'
    ]

    @staticmethod
    def parse_csv_file(file_content: bytes, encoding: str = 'utf-8') -> List[TestPlanCSVRow]:
        """
        Parse CSV file content into TestPlanCSVRow objects

        Args:
            file_content: Raw bytes content of the CSV file
            encoding: File encoding (default: utf-8)

        Returns:
            List of TestPlanCSVRow objects

        Raises:
            CSVParseError: If parsing fails
        """
        try:
            # Decode bytes to string
            text_content = file_content.decode(encoding)

            # Create CSV reader
            csv_reader = csv.DictReader(io.StringIO(text_content))

            # Validate headers
            if not csv_reader.fieldnames:
                raise CSVParseError("CSV file is empty or has no headers")

            # Parse rows
            rows = []
            for line_num, row in enumerate(csv_reader, start=2):  # Start at 2 (header is line 1)
                try:
                    # Create TestPlanCSVRow object
                    csv_row = TestPlanCSVRow(**row)
                    rows.append(csv_row)
                except Exception as e:
                    raise CSVParseError(f"Error parsing line {line_num}: {str(e)}")

            if not rows:
                raise CSVParseError("CSV file contains no test items")

            return rows

        except UnicodeDecodeError as e:
            raise CSVParseError(f"File encoding error: {str(e)}. Try different encoding.")
        except Exception as e:
            if isinstance(e, CSVParseError):
                raise
            raise CSVParseError(f"Unexpected error parsing CSV: {str(e)}")

    @staticmethod
    def csv_row_to_testplan_dict(csv_row: TestPlanCSVRow, sequence_order: int) -> Dict[str, Any]:
        """
        Convert CSV row to test plan dictionary suitable for database insertion

        Args:
            csv_row: Parsed CSV row
            sequence_order: Execution order in the test plan

        Returns:
            Dictionary with test plan fields
        """
        # Parse limits
        lower_limit = None
        upper_limit = None

        if csv_row.LL:
            try:
                lower_limit = float(csv_row.LL)
            except ValueError:
                pass

        if csv_row.UL:
            try:
                upper_limit = float(csv_row.UL)
            except ValueError:
                pass

        # Build parameters JSON from CSV columns
        parameters = {
            'item_key': csv_row.ItemKey,
            'value_type': csv_row.ValueType,
            'limit_type': csv_row.LimitType,
            'eq_limit': csv_row.EqLimit,
            'pass_or_fail': csv_row.PassOrFail,
            'execute_name': csv_row.ExecuteName,
            'case': csv_row.case,
            'port': csv_row.Port,
            'baud': csv_row.Baud,
            'command': csv_row.Command,
            'initial_command': csv_row.InitialCommand,
            'timeout': csv_row.Timeout,
            'wait_msec': csv_row.WaitmSec,
            'instrument': csv_row.Instrument,
            'channel': csv_row.Channel,
            'item': csv_row.Item,
            'type': csv_row.Type,
            'image_path': csv_row.ImagePath,
            'content': csv_row.content,
            'keyword': csv_row.keyWord,
            'split_count': csv_row.spiltCount,
            'split_length': csv_row.splitLength,
        }

        # Remove empty parameters
        parameters = {k: v for k, v in parameters.items() if v}

        return {
            'item_no': sequence_order,
            'item_name': csv_row.ID,
            'test_type': csv_row.ExecuteName or 'Unknown',
            'parameters': parameters,
            'lower_limit': lower_limit,
            'upper_limit': upper_limit,
            'unit': None,  # Not present in original CSV format
            'enabled': True,
            'sequence_order': sequence_order,
        }

    @classmethod
    def parse_and_convert(
        cls,
        file_content: bytes,
        encoding: str = 'utf-8'
    ) -> List[Dict[str, Any]]:
        """
        Parse CSV file and convert to test plan dictionaries

        Args:
            file_content: Raw bytes content of the CSV file
            encoding: File encoding (default: utf-8)

        Returns:
            List of test plan dictionaries ready for database insertion
        """
        csv_rows = cls.parse_csv_file(file_content, encoding)

        test_plans = []
        for idx, csv_row in enumerate(csv_rows, start=1):
            test_plan_dict = cls.csv_row_to_testplan_dict(csv_row, sequence_order=idx)
            test_plans.append(test_plan_dict)

        return test_plans
