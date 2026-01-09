"""
Base Measurement Module
Provides abstract base class for all measurement implementations
整合 PDTool4 test_point_runAllTest.py 的 TestPoint 驗證邏輯
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple, Union
from datetime import datetime
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# 輔助函數 - 對應 PDTool4 test_point_runAllTest.py
# ============================================================================
def is_empty_limit(limit: Optional[Any]) -> bool:
    """
    檢查限制值是否為空
    對應 PDTool4 test_point_runAllTest.py: is_empty_limit()
    """
    return limit is None or len(str(limit)) == 0


# ============================================================================
# 限制類型 (LimitType) - 對應 PDTool4
# ============================================================================
class LimitType:
    """限制類型基類"""
    pass


class LOWER_LIMIT_TYPE(LimitType):
    """下限限制類型"""
    pass


class UPPER_LIMIT_TYPE(LimitType):
    """上限限制類型"""
    pass


class BOTH_LIMIT_TYPE(LimitType):
    """雙向限制類型"""
    pass


class NONE_LIMIT_TYPE(LimitType):
    """無限制類型"""
    pass


class EQUALITY_LIMIT_TYPE(LimitType):
    """相等限制類型"""
    pass


class PARTIAL_LIMIT_TYPE(LimitType):
    """部分包含限制類型 (runAllTest 專用)"""
    pass


class INEQUALITY_LIMIT_TYPE(LimitType):
    """不相等限制類型 (runAllTest 專用)"""
    pass


# 限制類型映射表
LIMIT_TYPE_MAP = {
    'lower': LOWER_LIMIT_TYPE,
    'upper': UPPER_LIMIT_TYPE,
    'both': BOTH_LIMIT_TYPE,
    'equality': EQUALITY_LIMIT_TYPE,
    'partial': PARTIAL_LIMIT_TYPE,
    'inequality': INEQUALITY_LIMIT_TYPE,
    'none': NONE_LIMIT_TYPE,
}


# ============================================================================
# 數值類型 (ValueType) - 對應 PDTool4
# ============================================================================
class ValueType:
    """數值類型基類"""
    cast_call = None


class STRING_VALUE_TYPE(ValueType):
    @staticmethod
    def cast_call(in_obj):
        return str(in_obj)


class INTEGER_VALUE_TYPE(ValueType):
    @staticmethod
    def cast_call(in_obj):
        # 如果已經是 int，直接返回
        if isinstance(in_obj, int):
            return in_obj
        # 否則先轉成字串再轉 int
        return int(str(in_obj), 0)


class FLOAT_VALUE_TYPE(ValueType):
    @staticmethod
    def cast_call(in_obj):
        return float(in_obj)


VALUE_TYPE_MAP = {
    'string': STRING_VALUE_TYPE,
    'integer': INTEGER_VALUE_TYPE,
    'float': FLOAT_VALUE_TYPE,
}


# ============================================================================
# 測量結果類別
# ============================================================================
class MeasurementResult:
    """
    測量結果資料結構
    對應 PDTool4 TestPoint 的執行結果
    """

    def __init__(
        self,
        item_no: int,
        item_name: str,
        result: str,
        measured_value: Optional[Union[Decimal, str]] = None,
        lower_limit: Optional[Decimal] = None,
        upper_limit: Optional[Decimal] = None,
        unit: Optional[str] = None,
        error_message: Optional[str] = None,
        execution_duration_ms: Optional[int] = None
    ):
        self.item_no = item_no
        self.item_name = item_name
        self.result = result  # PASS, FAIL, SKIP, ERROR
        self.measured_value = measured_value
        self.lower_limit = lower_limit
        self.upper_limit = upper_limit
        self.unit = unit
        self.error_message = error_message
        self.execution_duration_ms = execution_duration_ms
        self.test_time = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary"""
        # 原有程式碼: measured_value = float(self.measured_value) if self.measured_value else None
        # 修改: 支援字串類型的 measured_value (例如: "Hello World!")
        # 如果是 Decimal 或 float/int，轉換為 float；如果是 str，保持原樣
        measured_value = self.measured_value
        if measured_value is not None:
            from decimal import Decimal
            if isinstance(measured_value, Decimal):
                measured_value = float(measured_value)
            elif not isinstance(measured_value, (str, float, int)):
                measured_value = str(measured_value)

        return {
            "item_no": self.item_no,
            "item_name": self.item_name,
            "result": self.result,
            "measured_value": measured_value,
            "lower_limit": float(self.lower_limit) if self.lower_limit else None,
            "upper_limit": float(self.upper_limit) if self.upper_limit else None,
            "unit": self.unit,
            "error_message": self.error_message,
            "execution_duration_ms": self.execution_duration_ms,
            "test_time": self.test_time.isoformat()
        }


# ============================================================================
# 測量基類 - 整合 TestPoint 驗證邏輯
# ============================================================================
class BaseMeasurement(ABC):
    """
    抽象測量基類，所有測量實作都應繼承此類
    整合 PDTool4 TestPoint 的 limit_type 驗證邏輯
    """

    def __init__(self, test_plan_item: Dict[str, Any], config: Dict[str, Any]):
        """
        初始化測量
        對應 PDTool4 TestPoint.__init__()

        Args:
            test_plan_item: 測試計畫項目配置 (來自資料庫)
            config: 全域配置和儀器設定
        """
        self.test_plan_item = test_plan_item
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)

        # 提取測試計畫欄位
        self.item_no = test_plan_item.get("item_no")
        self.item_name = test_plan_item.get("item_name")
        self.item_key = test_plan_item.get("item_key", self.item_name)
        self.lower_limit = test_plan_item.get("lower_limit")
        self.upper_limit = test_plan_item.get("upper_limit")
        self.unit = test_plan_item.get("unit")
        self.test_command = test_plan_item.get("test_type")  # test_type 對應 test_command
        self.test_params = test_plan_item.get("parameters", {})

        # 新增: 支援 limit_type 和 value_type
        self.value_type_str = test_plan_item.get("value_type", "string")
        self.limit_type_str = test_plan_item.get("limit_type", "none")
        self.eq_limit = test_plan_item.get("eq_limit")

        # 設置數值類型
        try:
            self.value_type = VALUE_TYPE_MAP.get(self.value_type_str, STRING_VALUE_TYPE)
        except KeyError:
            self.value_type = STRING_VALUE_TYPE
            self.logger.warning(f"Unknown value_type '{self.value_type_str}', using STRING")

        # 處理 eq_limit (相等限制)
        if not is_empty_limit(self.eq_limit):
            self.eq_limit = self.value_type.cast_call(self.eq_limit)

        # 設置限制類型
        try:
            self.limit_type = LIMIT_TYPE_MAP.get(self.limit_type_str, NONE_LIMIT_TYPE)
        except KeyError:
            self.limit_type = NONE_LIMIT_TYPE
            self.logger.warning(f"Unknown limit_type '{self.limit_type_str}', using NONE")

    @abstractmethod
    async def execute(self) -> MeasurementResult:
        """
        執行測量 - 子類必須實作

        Returns:
            MeasurementResult 物件包含測試結果
        """
        pass

    def validate_result(
        self,
        measured_value: Any,
        run_all_test: str = "OFF",
        raise_on_fail: bool = False
    ) -> Tuple[bool, Optional[str]]:
        """
        驗證測量值是否符合規格
        對應 PDTool4 test_point_runAllTest.py: TestPoint._execute()

        支援的 limit_type:
        - none: 無限制，直接通過
        - lower: 下限檢查
        - upper: 上限檢查
        - both: 雙向限制檢查
        - equality: 相等檢查
        - partial: 包含檢查 (字串包含)
        - inequality: 不相等檢查

        特殊錯誤檢查 (PDTool4 runAllTest 模式):
        - "No instrument found" -> 失敗
        - "Error:" 開頭 -> 失敗

        Args:
            measured_value: 測量值
            run_all_test: "ON" 繼續執行, "OFF" 遇到錯誤停止
            raise_on_fail: 失敗時是否拋出異常

        Returns:
            Tuple[bool, Optional[str]]: (通過/失敗, 錯誤訊息)
        """
        try:
            # PDTool4 runAllTest: 檢查儀器錯誤
            if measured_value and isinstance(measured_value, str):
                if measured_value == "No instrument found":
                    self.logger.error("Instrument not found")
                    return False, "No instrument found"
                if "Error: " in measured_value:
                    self.logger.error(f"Instrument error: {measured_value}")
                    return False, f"Instrument error: {measured_value}"

            # 檢查測量值類型轉換
            if not is_empty_limit(measured_value):
                # 根據 value_type 轉換
                if self.value_type is INTEGER_VALUE_TYPE:
                    measured_value = int(str(measured_value), 0)
                elif self.value_type is FLOAT_VALUE_TYPE:
                    measured_value = float(str(measured_value))
                else:
                    measured_value = str(measured_value)
            else:
                measured_value = None

            # NONE_LIMIT_TYPE: 無限制，直接通過
            if self.limit_type is NONE_LIMIT_TYPE:
                return True, None

            # EQUALITY_LIMIT_TYPE: 相等判斷
            if self.limit_type is EQUALITY_LIMIT_TYPE:
                result = bool(str(measured_value) == str(self.eq_limit))
                if not result and raise_on_fail:
                    logger.warning(f"Equality_limit : {self.eq_limit}")
                    return False, f"Failed equality limit: {repr(measured_value)} does not equal {repr(self.eq_limit)}"
                return result, None if result else f"Equality check failed: {repr(measured_value)} != {repr(self.eq_limit)}"

            # PARTIAL_LIMIT_TYPE: 包含判斷 (runAllTest 專用)
            if self.limit_type is PARTIAL_LIMIT_TYPE:
                result = str(self.eq_limit) in str(measured_value)
                if not result and raise_on_fail:
                    logger.warning(f"Partial_limit : {self.eq_limit}")
                    if run_all_test == "ON":
                        # runAllTest 模式: 記錄錯誤但不中斷
                        logger.error(f"TestPointEqualityLimitFailure: {repr(measured_value)} does not contain {repr(self.eq_limit)}")
                    return False, f"Failed partial limit: {repr(measured_value)} does not contain {repr(self.eq_limit)}"
                return result, None if result else f"Partial check failed: '{self.eq_limit}' not in '{measured_value}'"

            # INEQUALITY_LIMIT_TYPE: 不相等判斷 (runAllTest 專用)
            if self.limit_type is INEQUALITY_LIMIT_TYPE:
                result = bool(measured_value != self.eq_limit)
                if not result and raise_on_fail:
                    logger.warning(f"Inequality_limit : {self.eq_limit}")
                    return False, f"Failed inequality limit: {repr(measured_value)} equals {repr(self.eq_limit)}"
                return result, None if result else f"Inequality check failed: {repr(measured_value)} == {repr(self.eq_limit)}"

            # LOWER_LIMIT_TYPE / BOTH_LIMIT_TYPE: 下限判斷
            if self.limit_type in (LOWER_LIMIT_TYPE, BOTH_LIMIT_TYPE):
                lower_result = bool(float(measured_value) >= float(self.lower_limit))
                if not lower_result and raise_on_fail:
                    logger.warning(f"Lower_limit : {self.lower_limit}")
                    return False, f"Failed lower limit: {repr(measured_value)} < {repr(self.lower_limit)}"
                if self.limit_type is LOWER_LIMIT_TYPE:
                    return lower_result, None if lower_result else f"Lower limit failed: {measured_value} < {self.lower_limit}"

            # UPPER_LIMIT_TYPE / BOTH_LIMIT_TYPE: 上限判斷
            if self.limit_type in (UPPER_LIMIT_TYPE, BOTH_LIMIT_TYPE):
                upper_result = bool(float(self.upper_limit) >= float(measured_value))
                if not upper_result and raise_on_fail:
                    logger.warning(f"Upper_limit : {self.upper_limit}")
                    return False, f"Failed upper limit: {repr(measured_value)} > {repr(self.upper_limit)}"
                if self.limit_type is UPPER_LIMIT_TYPE:
                    return upper_result, None if upper_result else f"Upper limit failed: {measured_value} > {self.upper_limit}"

            # BOTH_LIMIT_TYPE: 返回組合結果
            if self.limit_type is BOTH_LIMIT_TYPE:
                return upper_result and lower_result, None

            return True, None

        except Exception as e:
            self.logger.error(f"Error validating result: {e}")
            return False, str(e)

    def create_result(
        self,
        result: str,
        measured_value: Optional[Decimal] = None,
        error_message: Optional[str] = None,
        execution_duration_ms: Optional[int] = None
    ) -> MeasurementResult:
        """
        建立測量結果物件

        Args:
            result: 測試結果 (PASS/FAIL/SKIP/ERROR)
            measured_value: 測量值
            error_message: 錯誤訊息
            execution_duration_ms: 執行時間 (毫秒)

        Returns:
            MeasurementResult 物件
        """
        return MeasurementResult(
            item_no=self.item_no,
            item_name=self.item_name,
            result=result,
            measured_value=measured_value,
            lower_limit=self.lower_limit,
            upper_limit=self.upper_limit,
            unit=self.unit,
            error_message=error_message,
            execution_duration_ms=execution_duration_ms
        )

    async def setup(self):
        """測量前設定 (可選)"""
        pass

    async def teardown(self):
        """測量後清理 (可選)"""
        pass
