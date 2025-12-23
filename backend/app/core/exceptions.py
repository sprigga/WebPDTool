"""
Custom Exceptions for WebPDTool
對應 PDTool4 test_point_map.py 的異常定義
"""


class TestPointUniqueIdViolation(Exception):
    """測試點唯一 ID 衝突異常"""
    pass


class TestPointValidationError(Exception):
    """測試點驗證失敗異常"""
    pass


class TestPlanNotFoundError(Exception):
    """測試計畫不存在異常"""
    pass


class MeasurementExecutionError(Exception):
    """測量執行失敗異常"""
    pass


class InstrumentConnectionError(Exception):
    """儀器連線失敗異常"""
    pass


class CSVParseError(Exception):
    """CSV 解析失敗異常"""
    pass
