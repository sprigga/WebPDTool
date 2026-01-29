#!/usr/bin/env python3
"""
測試腳本 - 驗證 PDTool4 重構改進
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.measurements.base import (
    BaseMeasurement,
    MeasurementResult,
    LOWER_LIMIT_TYPE,
    UPPER_LIMIT_TYPE,
    BOTH_LIMIT_TYPE,
    EQUALITY_LIMIT_TYPE,
    PARTIAL_LIMIT_TYPE,
    INEQUALITY_LIMIT_TYPE,
    NONE_LIMIT_TYPE,
    INTEGER_VALUE_TYPE,
    FLOAT_VALUE_TYPE,
    STRING_VALUE_TYPE
)
from decimal import Decimal


class TestMeasurement(BaseMeasurement):
    """測試用的測量類別"""

    async def execute(self) -> MeasurementResult:
        return self.create_result(result="PASS")


def test_validate_result_lower_limit():
    """測試下限檢查"""
    print("✓ 測試下限檢查...")

    test_plan = {
        "item_no": 1,
        "item_name": "Test Voltage",
        "limit_type": "lower",
        "value_type": "float",
        "lower_limit": 3.0,
        "upper_limit": None
    }

    measurement = TestMeasurement(test_plan, {})

    # 測試通過情況
    passed, msg = measurement.validate_result(5.0)
    assert passed, f"應該通過: {msg}"

    # 測試失敗情況
    passed, msg = measurement.validate_result(2.0)
    assert not passed, f"應該失敗: {msg}"

    print("  ✓ 下限檢查通過")


def test_validate_result_upper_limit():
    """測試上限檢查"""
    print("✓ 測試上限檢查...")

    test_plan = {
        "item_no": 2,
        "item_name": "Test Current",
        "limit_type": "upper",
        "value_type": "float",
        "lower_limit": None,
        "upper_limit": 5.0
    }

    measurement = TestMeasurement(test_plan, {})

    # 測試通過情況
    passed, msg = measurement.validate_result(3.0)
    assert passed, f"應該通過: {msg}"

    # 測試失敗情況
    passed, msg = measurement.validate_result(6.0)
    assert not passed, f"應該失敗: {msg}"

    print("  ✓ 上限檢查通過")


def test_validate_result_both_limits():
    """測試雙向限制檢查"""
    print("✓ 測試雙向限制檢查...")

    test_plan = {
        "item_no": 3,
        "item_name": "Test Power",
        "limit_type": "both",
        "value_type": "float",
        "lower_limit": 3.0,
        "upper_limit": 5.0
    }

    measurement = TestMeasurement(test_plan, {})

    # 測試通過情況
    passed, msg = measurement.validate_result(4.0)
    assert passed, f"應該通過: {msg}"

    # 測試下限失敗
    passed, msg = measurement.validate_result(2.0)
    assert not passed, f"應該失敗 (下限): {msg}"

    # 測試上限失敗
    passed, msg = measurement.validate_result(6.0)
    assert not passed, f"應該失敗 (上限): {msg}"

    print("  ✓ 雙向限制檢查通過")


def test_validate_result_equality():
    """測試相等檢查"""
    print("✓ 測試相等檢查...")

    test_plan = {
        "item_no": 4,
        "item_name": "Test Status",
        "limit_type": "equality",
        "value_type": "string",
        "eq_limit": "OK"
    }

    measurement = TestMeasurement(test_plan, {})

    # 測試通過情況
    passed, msg = measurement.validate_result("OK")
    assert passed, f"應該通過: {msg}"

    # 測試失敗情況
    passed, msg = measurement.validate_result("FAIL")
    assert not passed, f"應該失敗: {msg}"

    print("  ✓ 相等檢查通過")


def test_validate_result_partial():
    """測試包含檢查 (runAllTest 專用)"""
    print("✓ 測試包含檢查 (runAllTest)...")

    test_plan = {
        "item_no": 5,
        "item_name": "Test Response",
        "limit_type": "partial",
        "value_type": "string",
        "eq_limit": "Success"
    }

    measurement = TestMeasurement(test_plan, {})

    # 測試通過情況
    passed, msg = measurement.validate_result("Operation Successful")
    assert passed, f"應該通過: {msg}"

    # 測試失敗情況
    passed, msg = measurement.validate_result("Operation Failed")
    assert not passed, f"應該失敗: {msg}"

    print("  ✓ 包含檢查通過")


def test_validate_result_inequality():
    """測試不相等檢查 (runAllTest 專用)"""
    print("✓ 測試不相等檢查 (runAllTest)...")

    test_plan = {
        "item_no": 6,
        "item_name": "Test Value",
        "limit_type": "inequality",
        "value_type": "integer",
        "eq_limit": 0
    }

    measurement = TestMeasurement(test_plan, {})

    # 測試通過情況 (不等於 0)
    passed, msg = measurement.validate_result(5)
    assert passed, f"應該通過: {msg}"

    # 測試失敗情況 (等於 0)
    passed, msg = measurement.validate_result(0)
    assert not passed, f"應該失敗: {msg}"

    print("  ✓ 不相等檢查通過")


def test_validate_result_none():
    """測試無限制檢查"""
    print("✓ 測試無限制檢查...")

    test_plan = {
        "item_no": 7,
        "item_name": "Test No Limit",
        "limit_type": "none",
        "value_type": "string"
    }

    measurement = TestMeasurement(test_plan, {})

    # 所有情況都應該通過
    passed, msg = measurement.validate_result("Anything")
    assert passed, f"應該通過: {msg}"

    passed, msg = measurement.validate_result(None)
    assert passed, f"應該通過 (None): {msg}"

    print("  ✓ 無限制檢查通過")


def test_pdtool4_error_detection():
    """測試 PDTool4 儀器錯誤檢測"""
    print("✓ 測試 PDTool4 儀器錯誤檢測...")

    test_plan = {
        "item_no": 8,
        "item_name": "Test Instrument",
        "limit_type": "both",
        "value_type": "float",
        "lower_limit": 0.0,
        "upper_limit": 10.0
    }

    measurement = TestMeasurement(test_plan, {})

    # 測試 "No instrument found" 錯誤
    passed, msg = measurement.validate_result("No instrument found")
    assert not passed, f"應該偵測到儀器未找到: {msg}"
    assert "No instrument found" in msg

    # 測試 "Error:" 錯誤
    passed, msg = measurement.validate_result("Error: Communication timeout")
    assert not passed, f"應該偵測到儀器錯誤: {msg}"
    assert "Instrument error" in msg

    print("  ✓ 儀器錯誤檢測通過")


def test_value_type_conversion():
    """測試數值類型轉換"""
    print("✓ 測試數值類型轉換...")

    # FLOAT 類型
    test_plan_float = {
        "item_no": 9,
        "item_name": "Test Float",
        "limit_type": "both",
        "value_type": "float",
        "lower_limit": 1.0,
        "upper_limit": 10.0
    }
    measurement_float = TestMeasurement(test_plan_float, {})
    passed, _ = measurement_float.validate_result("5.5")  # 字串輸入
    assert passed, "Float 類型轉換應該成功"

    # INTEGER 類型
    test_plan_int = {
        "item_no": 10,
        "item_name": "Test Integer",
        "limit_type": "both",
        "value_type": "integer",
        "lower_limit": 1,
        "upper_limit": 10
    }
    measurement_int = TestMeasurement(test_plan_int, {})
    passed, _ = measurement_int.validate_result("5")  # 字串輸入
    assert passed, "Integer 類型轉換應該成功"

    print("  ✓ 數值類型轉換通過")


def main():
    """執行所有測試"""
    print("\n" + "="*60)
    print("PDTool4 重構驗證測試")
    print("="*60 + "\n")

    try:
        test_validate_result_lower_limit()
        test_validate_result_upper_limit()
        test_validate_result_both_limits()
        test_validate_result_equality()
        test_validate_result_partial()
        test_validate_result_inequality()
        test_validate_result_none()
        test_pdtool4_error_detection()
        test_value_type_conversion()

        print("\n" + "="*60)
        print("✅ 所有測試通過!")
        print("="*60 + "\n")

        print("重構改進驗證成功:")
        print("  ✓ validate_result() 方法符合 PDTool4 規格")
        print("  ✓ 支援所有 limit_type 類型")
        print("  ✓ 支援所有 value_type 類型")
        print("  ✓ PDTool4 儀器錯誤檢測正常運作")
        print("  ✓ runAllTest 模式錯誤處理正確")
        print("\n建議下一步:")
        print("  1. 測試 measurement_service.py 的 runAllTest 模式")
        print("  2. 整合 frontend 組件")
        print("  3. 執行端到端測試")

    except AssertionError as e:
        print(f"\n❌ 測試失敗: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
