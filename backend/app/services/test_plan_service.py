"""
Test Plan Service
基於 PDTool4 test_point_map.py 和 test_point_runAllTest.py 的設計模式
實作測試計畫管理器，提供 TestPointMap 風格的測試計畫操作
"""
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session
from decimal import Decimal
import logging
from datetime import datetime

from app.models.testplan import TestPlan
from app.models.test_session import TestSession as TestSessionModel
from app.models.test_result import TestResult as TestResultModel
from app.core.exceptions import TestPointUniqueIdViolation

logger = logging.getLogger(__name__)


# ============================================================================
# 限制類型 (LimitType) - 對應 PDTool4 test_point_runAllTest.py
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
# 數值類型 (ValueType) - 對應 PDTool4 test_point.py
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
        return int(in_obj, 0)


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
# 異常類型 - 對應 PDTool4
# ============================================================================
class TestPointLimitFailure(Exception):
    """測試點限制失敗異常"""
    pass


class TestPointUpperLimitFailure(TestPointLimitFailure):
    """上限失敗異常"""
    pass


class TestPointLowerLimitFailure(TestPointLimitFailure):
    """下限失敗異常"""
    pass


class TestPointEqualityLimitFailure(TestPointLimitFailure):
    """相等限制失敗異常"""
    pass


class TestPointInequalityLimitFailure(TestPointLimitFailure):
    """不相等限制失敗異常"""
    pass


class TestPointDoubleExecutionError(Exception):
    """雙重執行異常"""
    pass


def is_empty_limit(limit: Optional[Any]) -> bool:
    """
    檢查限制值是否為空
    對應 PDTool4 test_point.py: is_empty_limit()
    """
    return limit is None or len(str(limit)) == 0


# ============================================================================
# TestPoint 類別 - 對應 PDTool4 TestPoint
# ============================================================================
class TestPoint:
    """
    測試點類別 - 對應 PDTool4 test_point_runAllTest.py 的 TestPoint

    主要差異:
    1. 使用資料庫模型 TestPlan 而非 CSV
    2. 支援 runAllTest 模式 (錯誤繼續執行)
    3. 支援 PARTIAL_LIMIT_TYPE 和 INEQUALITY_LIMIT_TYPE
    """

    def __init__(
        self,
        name: str,                    # 測試點名稱 (unique_id)
        item_key: str,                # 項目鍵值 (runAllTest 專用)
        value_type: str,              # 數值類型
        limit_type: str,              # 限制類型
        equality_limit: Optional[str] = None,
        lower_limit: Optional[float] = None,
        upper_limit: Optional[float] = None,
        unit: Optional[str] = None,   # 單位 (可選)
    ):
        """
        初始化測試點
        對應 PDTool4 test_point_runAllTest.py: TestPoint.__init__()
        """
        self.executed = False
        self.passed = None
        self.value = None
        self.ItemKey = item_key
        self.name = name
        self.unique_id = name
        self.unit = unit
        self.TestDateTime = ''

        # 設置數值類型
        try:
            self.value_type = VALUE_TYPE_MAP[value_type.strip()]
        except KeyError:
            raise ValueError(f'{value_type} not a valid value type, name {name}')

        # 設置限制類型
        try:
            self.limit_type = LIMIT_TYPE_MAP[limit_type.strip()]
        except KeyError:
            raise ValueError(f'{limit_type} not a valid limit type, name {name}')

        # 處理相等限制
        if is_empty_limit(equality_limit):
            self.equality_limit = None
        else:
            self.equality_limit = self.value_type.cast_call(equality_limit)

        # 處理下限
        if is_empty_limit(lower_limit):
            self.lower_limit = None
        else:
            self.lower_limit = float(lower_limit)

        # 處理上限
        if is_empty_limit(upper_limit):
            self.upper_limit = None
        else:
            self.upper_limit = float(upper_limit)

    def execute(self, value: Any, run_all_test: str = "OFF", raise_on_fail: bool = True) -> bool:
        """
        執行測試點驗證
        對應 PDTool4 test_point_runAllTest.py: TestPoint.execute()

        Args:
            value: 測量值
            run_all_test: "ON" 繼續執行, "OFF" 遇到錯誤停止
            raise_on_fail: 失敗時是否拋出異常

        Returns:
            bool: 通過/失敗
        """
        try:
            # 檢查儀器錯誤 (runAllTest 模式專用)
            if value == "No instrument found":
                self.value = value
                self.passed = False
                self.executed = True
                raise Exception("No instrument found")

            if "Error: " in value:
                self.value = value
                self.passed = False
                self.executed = True
                raise Exception(f"Instrument error: {value}")
            else:
                pass_fail = self._execute(value, run_all_test, raise_on_fail)
                self.passed = pass_fail
                self.executed = True
                return pass_fail

        except TestPointLimitFailure:
            self.passed = False
            self.executed = True
            raise
        except Exception:
            self.executed = True
            raise

    def _execute(self, value: Any, run_all_test: str, raise_on_fail: bool) -> bool:
        """
        內部驗證邏輯
        對應 PDTool4 test_point_runAllTest.py: TestPoint._execute()
        """
        # 檢查雙重執行
        if self.value is not None or self.executed == True:
            raise TestPointDoubleExecutionError(f'{self.unique_id} attempted to execute twice')

        if self.value is None:
            self.value = value

        # NONE_LIMIT_TYPE: 直接回傳 True
        if self.limit_type is NONE_LIMIT_TYPE:
            return True

        # EQUALITY_LIMIT_TYPE: 相等判斷
        if self.limit_type is EQUALITY_LIMIT_TYPE:
            result = bool(str(value) == self.equality_limit)
            if run_all_test == "ON":
                try:
                    result = bool(str(value) == self.equality_limit)
                    if raise_on_fail and result == False:
                        logger.warning(f"Equality_limit : {self.equality_limit}")
                        raise TestPointEqualityLimitFailure(
                            f'{self.unique_id}. Failed equality limit. {repr(value)} does not equal {repr(self.equality_limit)} limit.'
                        )
                except TestPointEqualityLimitFailure as e:
                    logger.warning(str(e))
                    return result
            else:
                if raise_on_fail and result == False:
                    logger.warning(f"Equality_limit : {self.equality_limit}")
                    logger.warning(f'{self.unique_id}. Failed equality limit. {repr(value)} does not equal {repr(self.equality_limit)} limit.')
                    raise TestPointEqualityLimitFailure
            return result

        # PARTIAL_LIMIT_TYPE: 包含判斷 (runAllTest 專用)
        if self.limit_type is PARTIAL_LIMIT_TYPE:
            result = str(self.equality_limit) in str(value)
            if run_all_test == "ON":
                try:
                    result = str(self.equality_limit) in str(value)
                    if raise_on_fail and not result:
                        logger.warning(f"Partial_limit : {self.equality_limit}")
                        raise TestPointEqualityLimitFailure(
                            f'{self.unique_id}. Failed partial limit. {repr(value)} does not contain {repr(self.equality_limit)}.'
                        )
                except TestPointEqualityLimitFailure as e:
                    logger.warning(str(e))
                    return result
            else:
                if raise_on_fail and not result:
                    logger.warning(f"Partial_limit : {self.equality_limit}")
                    logger.warning(f'{self.unique_id}. Failed partial limit. {repr(value)} does not contain {repr(self.equality_limit)} limit.')
                    raise TestPointEqualityLimitFailure
            return result

        # INEQUALITY_LIMIT_TYPE: 不相等判斷 (runAllTest 專用)
        if self.limit_type is INEQUALITY_LIMIT_TYPE:
            result = bool(value != self.equality_limit)
            if run_all_test == "ON":
                try:
                    result = bool(value != self.equality_limit)
                    if raise_on_fail and result == False:
                        logger.warning(f"Equality_limit : {self.equality_limit}")
                        raise TestPointInequalityLimitFailure(
                            f'{self.unique_id}. Failed equality limit. {repr(value)} is equal {repr(self.equality_limit)} limit.'
                        )
                except TestPointInequalityLimitFailure as e:
                    logger.warning(str(e))
                    return result
            else:
                if raise_on_fail and result == False:
                    logger.warning(f"Equality_limit : {self.equality_limit}")
                    logger.warning(f'{self.unique_id}. Failed equality limit. {repr(value)} is equal {repr(self.equality_limit)} limit.')
                    raise TestPointInequalityLimitFailure
            return result

        # LOWER_LIMIT_TYPE / BOTH_LIMIT_TYPE: 下限判斷
        if self.limit_type in (LOWER_LIMIT_TYPE, BOTH_LIMIT_TYPE):
            lower_result = bool(float(value) >= float(self.lower_limit))
            if run_all_test == "ON":
                try:
                    lower_result = bool(float(value) >= float(self.lower_limit))
                    if raise_on_fail and lower_result == False:
                        logger.warning(f"Lower_limit : {self.lower_limit}")
                        raise TestPointLowerLimitFailure(
                            f'{self.unique_id}. Failed lower limit. {repr(value)} lower than {repr(self.lower_limit)} limit.'
                        )
                except TestPointLowerLimitFailure as e:
                    logger.warning(str(e))
                    return lower_result
            else:
                if raise_on_fail and lower_result == False:
                    logger.warning(f"Lower_limit : {self.lower_limit}")
                    logger.warning(f'{self.unique_id}. Failed lower limit. {repr(value)} lower than {repr(self.lower_limit)} limit.')
                    raise TestPointLowerLimitFailure
            if self.limit_type is LOWER_LIMIT_TYPE:
                return lower_result

        # UPPER_LIMIT_TYPE / BOTH_LIMIT_TYPE: 上限判斷
        if self.limit_type in (UPPER_LIMIT_TYPE, BOTH_LIMIT_TYPE):
            upper_result = bool(float(self.upper_limit) >= float(value))
            if run_all_test == "ON":
                try:
                    upper_result = bool(float(self.upper_limit) >= float(value))
                    if raise_on_fail and upper_result == False:
                        logger.warning(f"Upper_limit : {self.upper_limit}")
                        raise TestPointUpperLimitFailure(
                            f'{self.unique_id}. Failed upper limit. {repr(value)} higher than {repr(self.upper_limit)} limit.'
                        )
                except TestPointUpperLimitFailure as e:
                    logger.warning(str(e))
                    return upper_result
            else:
                if raise_on_fail and upper_result == False:
                    logger.warning(f"Upper_limit : {self.upper_limit}")
                    logger.warning(f'{self.unique_id}. Failed upper limit. {repr(value)} higher than {repr(self.upper_limit)} limit.')
                    raise TestPointUpperLimitFailure
            if self.limit_type is UPPER_LIMIT_TYPE:
                return upper_result

        # BOTH_LIMIT_TYPE: 返回組合結果
        assert self.limit_type is BOTH_LIMIT_TYPE
        return upper_result and lower_result

    def re_execute(self, value: Any, raise_on_fail: bool = True) -> bool:
        """
        重新執行測試點
        對應 PDTool4 test_point_runAllTest.py: TestPoint.re_execute()
        """
        if self.value is not None or self.executed == True:
            self.executed = False
            self.value = None
            return True

        if self.value is None:
            self.value = value

        if self.limit_type is NONE_LIMIT_TYPE:
            self.executed = False
            self.value = None
            return True
        if self.limit_type is EQUALITY_LIMIT_TYPE:
            result = bool(value == self.equality_limit)
            self.executed = False
            self.value = None
            return result
        if self.limit_type is PARTIAL_LIMIT_TYPE:
            result = str(self.equality_limit) in str(value)
            self.executed = False
            self.value = None
            return result
        if self.limit_type is INEQUALITY_LIMIT_TYPE:
            result = bool(value != self.equality_limit)
            self.executed = False
            self.value = None
            return result
        if self.limit_type in (LOWER_LIMIT_TYPE, BOTH_LIMIT_TYPE):
            lower_result = bool(value >= self.lower_limit)
            if raise_on_fail and lower_result == False:
                self.executed = False
                self.value = None
                return False
            if self.limit_type is LOWER_LIMIT_TYPE:
                self.executed = False
                self.value = None
                return lower_result
        if self.limit_type in (UPPER_LIMIT_TYPE, BOTH_LIMIT_TYPE):
            upper_result = bool(self.upper_limit >= value)
            if raise_on_fail and upper_result == False:
                self.executed = False
                self.value = None
                return False
            if self.limit_type is UPPER_LIMIT_TYPE:
                self.executed = False
                self.value = None
                return upper_result
        if self.limit_type is BOTH_LIMIT_TYPE:
            self.executed = False
            self.value = None
            return upper_result and lower_result

    def _pretty(self) -> str:
        """格式化輸出"""
        return f'{self.unique_id}, EXEC: {self.executed}, VALUE: {self.value}, PASSED: {self.passed}'

    def __str__(self) -> str:
        return self._pretty()

    def __repr__(self) -> str:
        return self._pretty()


# ============================================================================
# TestPlanMap 類別 - 對應 PDTool4 TestPointMap
# ============================================================================
class TestPlanMap:
    """
    測試計畫映射管理器 - 對應 PDTool4 test_point_map.py 的 TestPointMap

    主要功能:
    1. 管理多個 TestPoint 物件
    2. 提供類字典風格的存取
    3. 提供執行狀態查詢方法
    """

    def __init__(self):
        """
        初始化測試計畫映射表
        對應 PDTool4 test_point_map.py: TestPointMap.__init__()
        """
        self._map: Dict[str, TestPoint] = {}

    def add_test_point(self, test_point: TestPoint) -> None:
        """
        新增測試點，檢查 unique_id 唯一性
        對應 PDTool4 test_point_map.py: TestPointMap.add_test_point()
        """
        unique_id = test_point.unique_id
        if unique_id in self._map:
            raise TestPointUniqueIdViolation(
                f'{unique_id} has already been added to {self}'
            )
        self._map[unique_id] = test_point

    def get_test_point(self, unique_id: str) -> Optional[TestPoint]:
        """
        取得測試點
        對應 PDTool4 test_point_map.py: TestPointMap.get_test_point()
        """
        return self._map.get(unique_id)

    def __getitem__(self, unique_id: str) -> Optional[TestPoint]:
        """
        支援 dict 風格存取
        對應 PDTool4 test_point_map.py: TestPointMap.__getitem__()
        """
        if unique_id in self._map:
            return self._map[unique_id]
        else:
            return None

    def get_dict(self) -> Dict[str, TestPoint]:
        """
        取得映射表副本
        對應 PDTool4 test_point_map.py: TestPointMap.get_dict()
        """
        return self._map.copy()

    def all_executed(self) -> bool:
        """
        檢查所有測試點是否已執行
        對應 PDTool4 test_point_map.py: TestPointMap.all_executed()
        """
        return all((tp.executed for tp in self._map.values()))

    def count_executed(self) -> Tuple[int, int]:
        """
        計算已執行的測試點數量
        對應 PDTool4 test_point_map.py: TestPointMap.count_executed()

        Returns:
            Tuple[int, int]: (已執行數量, 總數量)
        """
        n_exec = 0
        for n, tp in enumerate(self._map.values()):
            if tp.executed:
                n_exec += 1
        return n_exec, n + 1

    def count_skipped(self) -> int:
        """
        計算跳過的測試點數量
        對應 PDTool4 test_point_map.py: TestPointMap.count_skipped()
        """
        c, n = self.count_executed()
        return n - c

    def all_pass(self) -> bool:
        """
        檢查所有測試點是否通過
        對應 PDTool4 test_point_map.py: TestPointMap.all_pass()
        """
        return all((tp.passed for tp in self._map.values()))

    def all_executed_all_pass(self) -> bool:
        """
        檢查是否全部執行且通過
        對應 PDTool4 test_point_map.py: TestPointMap.all_executed_all_pass()
        """
        return self.all_pass() and self.all_executed()

    def get_fail_uid(self) -> Optional[str]:
        """
        取得失敗的測試點 UID
        對應 PDTool4 test_point_map.py: TestPointMap.get_fail_uid()
        """
        for tp in self._map.values():
            if tp.passed == False:
                return tp.unique_id
        return None

    def __len__(self) -> int:
        """返回測試點總數"""
        return len(self._map)

    def __iter__(self):
        """支援迭代"""
        return iter(self._map.values())

    def keys(self):
        """返回所有 unique_id"""
        return self._map.keys()

    def values(self):
        """返回所有 TestPoint"""
        return self._map.values()

    def items(self):
        """返回所有 (unique_id, TestPoint) 對"""
        return self._map.items()


# ============================================================================
# TestPlanService 類別 - 整合資料庫與 TestPointMap
# ============================================================================
class TestPlanService:
    """
    測試計畫服務 - 整合資料庫 ORM 和 TestPointMap

    主要功能:
    1. 從資料庫載入測試計畫並建立 TestPointMap
    2. 提供測試計畫的 CRUD 操作
    3. 支援 runAllTest 模式
    4. 提供測試結果收集和驗證
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def new_test_plan_map(
        self,
        db: Session,
        project_id: int,
        station_id: int,
        test_plan_name: Optional[str] = None,
        enabled_only: bool = True
    ) -> TestPlanMap:
        """
        從資料庫建立 TestPointMap
        對應 PDTool4 test_point_map.py: new_test_point_map()

        Args:
            db: 資料庫會話
            project_id: 專案 ID
            station_id: 工站 ID
            test_plan_name: 測試計畫名稱 (可選)
            enabled_only: 是否只載入已啟用的測試項目

        Returns:
            TestPlanMap: 測試計畫映射表
        """
        test_plan_map = TestPlanMap()

        # 查詢測試計畫
        query = db.query(TestPlan).filter(
            TestPlan.project_id == project_id,
            TestPlan.station_id == station_id
        )

        if test_plan_name:
            query = query.filter(TestPlan.test_plan_name == test_plan_name)

        if enabled_only:
            query = query.filter(TestPlan.enabled == True)

        # 按順序排序
        test_plans = query.order_by(TestPlan.sequence_order).all()

        # 建立 TestPoint 物件並加入映射表
        for plan in test_plans:
            # 處理空值
            value_type = plan.value_type or 'string'
            limit_type = plan.limit_type or 'none'

            # 建立 TestPoint
            test_point = TestPoint(
                name=plan.item_name,
                item_key=plan.item_key or plan.item_name,
                value_type=value_type,
                limit_type=limit_type,
                equality_limit=plan.eq_limit,
                lower_limit=float(plan.lower_limit) if plan.lower_limit else None,
                upper_limit=float(plan.upper_limit) if plan.upper_limit else None,
                unit=plan.unit
            )
            test_plan_map.add_test_point(test_point)

        self.logger.info(f"Created TestPlanMap with {len(test_plan_map)} test points")
        return test_plan_map

    def get_test_plan_by_id(
        self,
        db: Session,
        test_plan_id: int
    ) -> Optional[TestPlan]:
        """
        根據 ID 取得測試計畫項目
        對應 PDTool4 test_point_map.py: TestPointMap.get_test_point()
        """
        return db.query(TestPlan).filter(TestPlan.id == test_plan_id).first()

    def get_test_plans(
        self,
        db: Session,
        project_id: int,
        station_id: int,
        test_plan_name: Optional[str] = None,
        enabled_only: bool = True
    ) -> List[TestPlan]:
        """
        取得測試計畫列表
        對應 PDTool4 的多測試點查詢
        """
        query = db.query(TestPlan).filter(
            TestPlan.project_id == project_id,
            TestPlan.station_id == station_id
        )

        if test_plan_name:
            query = query.filter(TestPlan.test_plan_name == test_plan_name)

        if enabled_only:
            query = query.filter(TestPlan.enabled == True)

        return query.order_by(TestPlan.sequence_order).all()

    def create_test_plan(
        self,
        db: Session,
        test_plan_data: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> TestPlan:
        """
        建立測試計畫項目
        """
        try:
            # 檢查唯一性
            existing = db.query(TestPlan).filter(
                TestPlan.project_id == test_plan_data['project_id'],
                TestPlan.station_id == test_plan_data['station_id'],
                TestPlan.item_no == test_plan_data['item_no']
            ).first()

            if existing:
                raise ValueError(f"Test plan item with item_no={test_plan_data['item_no']} already exists")

            # 建立測試計畫
            test_plan = TestPlan(**test_plan_data)
            db.add(test_plan)
            db.commit()
            db.refresh(test_plan)

            self.logger.info(f"Created test plan: {test_plan.item_name}")
            return test_plan

        except Exception as e:
            db.rollback()
            self.logger.error(f"Failed to create test plan: {e}")
            raise

    def update_test_plan(
        self,
        db: Session,
        test_plan_id: int,
        update_data: Dict[str, Any]
    ) -> Optional[TestPlan]:
        """
        更新測試計畫項目
        """
        try:
            test_plan = self.get_test_plan_by_id(db, test_plan_id)
            if not test_plan:
                return None

            for field, value in update_data.items():
                setattr(test_plan, field, value)

            db.commit()
            db.refresh(test_plan)

            self.logger.info(f"Updated test plan: {test_plan.item_name}")
            return test_plan

        except Exception as e:
            db.rollback()
            self.logger.error(f"Failed to update test plan: {e}")
            raise

    def delete_test_plan(
        self,
        db: Session,
        test_plan_id: int
    ) -> bool:
        """
        刪除測試計畫項目
        """
        try:
            test_plan = self.get_test_plan_by_id(db, test_plan_id)
            if not test_plan:
                return False

            db.delete(test_plan)
            db.commit()

            self.logger.info(f"Deleted test plan: {test_plan.item_name}")
            return True

        except Exception as e:
            db.rollback()
            self.logger.error(f"Failed to delete test plan: {e}")
            raise

    def bulk_delete_test_plans(
        self,
        db: Session,
        test_plan_ids: List[int]
    ) -> int:
        """
        批次刪除測試計畫項目
        """
        try:
            deleted_count = db.query(TestPlan).filter(
                TestPlan.id.in_(test_plan_ids)
            ).delete(synchronize_session=False)

            db.commit()
            self.logger.info(f"Bulk deleted {deleted_count} test plan items")
            return deleted_count

        except Exception as e:
            db.rollback()
            self.logger.error(f"Failed to bulk delete test plans: {e}")
            raise

    def reorder_test_plans(
        self,
        db: Session,
        item_orders: Dict[int, int]
    ) -> int:
        """
        重新排序測試計畫項目
        """
        try:
            updated_count = 0
            for testplan_id, new_order in item_orders.items():
                testplan = db.query(TestPlan).filter(TestPlan.id == testplan_id).first()
                if testplan:
                    testplan.sequence_order = new_order
                    updated_count += 1

            db.commit()
            self.logger.info(f"Reordered {updated_count} test plan items")
            return updated_count

        except Exception as e:
            db.rollback()
            self.logger.error(f"Failed to reorder test plans: {e}")
            raise

    def get_test_plan_names(
        self,
        db: Session,
        project_id: int,
        station_id: int
    ) -> List[str]:
        """
        取得測試計畫名稱列表
        """
        test_plan_names = db.query(TestPlan.test_plan_name)\
            .filter(TestPlan.project_id == project_id)\
            .filter(TestPlan.station_id == station_id)\
            .filter(TestPlan.test_plan_name.isnot(None))\
            .filter(TestPlan.test_plan_name != '')\
            .distinct()\
            .all()

        return [name[0] for name in test_plan_names]

    def validate_test_point(
        self,
        test_point: TestPoint,
        measured_value: Any,
        run_all_test: str = "OFF"
    ) -> Tuple[bool, Optional[str]]:
        """
        驗證測試點
        對應 PDTool4 test_point_runAllTest.py: TestPoint.execute()

        Args:
            test_point: 測試點物件
            measured_value: 測量值
            run_all_test: "ON" 繼續執行, "OFF" 遇到錯誤停止

        Returns:
            Tuple[bool, Optional[str]]: (通過/失敗, 錯誤訊息)
        """
        try:
            result = test_point.execute(measured_value, run_all_test, raise_on_fail=False)
            return result, None
        except TestPointLimitFailure as e:
            return False, str(e)
        except Exception as e:
            return False, str(e)

    def get_session_test_results(
        self,
        db: Session,
        session_id: int
    ) -> List[Dict[str, Any]]:
        """
        取得測試會話的測試結果
        """
        results = db.query(TestResultModel).filter(
            TestResultModel.session_id == session_id
        ).all()

        return [
            {
                "id": result.id,
                "item_no": result.item_no,
                "item_name": result.item_name,
                "result": result.result,
                "measured_value": result.measured_value,
                "lower_limit": result.lower_limit,
                "upper_limit": result.upper_limit,
                "unit": result.unit,
                "error_message": result.error_message,
                "test_time": result.test_time.isoformat() if result.test_time else None,
                "execution_duration_ms": result.execution_duration_ms
            }
            for result in results
        ]


# ============================================================================
# 全局服務實例
# ============================================================================
test_plan_service = TestPlanService()
