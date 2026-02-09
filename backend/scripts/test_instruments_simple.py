#!/usr/bin/env python3
"""
簡化版 instruments.py 重構驗證測試

不依賴其他模組，直接測試配置函數
"""

import sys
import os

# 直接導入必要的配置常數和函數
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 避免導入整個 app 包，直接讀取文件並執行
import importlib.util

spec = importlib.util.spec_from_file_location(
    "instruments",
    os.path.join(os.path.dirname(__file__), '../app/config/instruments.py')
)
instruments_module = importlib.util.module_from_spec(spec)

try:
    spec.loader.exec_module(instruments_module)
except Exception as e:
    print(f"✗ 無法載入 instruments.py: {e}")
    print("  這可能是因為模組依賴問題，但配置本身應該是獨立的")
    print("  建議: 將 instruments.py 改為純配置文件，不依賴其他模組")
    sys.exit(1)


def test_get_measurement_types():
    """測試動態生成測試類型清單"""
    print("=" * 80)
    print("測試 1: get_measurement_types() - 動態生成測試類型")
    print("=" * 80)

    types = instruments_module.get_measurement_types()

    print(f"✓ 成功生成 {len(types)} 個測試類型\n")

    for test_type in types:
        print(f"測試類型: {test_type['name']}")
        print(f"  描述: {test_type['description']}")
        print(f"  分類: {test_type['category']}")
        print(f"  支援儀器: {', '.join(test_type['supported_switches'])}")
        print()

    # 驗證是否包含基本測試類型
    type_names = [t['name'] for t in types]
    assert 'PowerSet' in type_names, "缺少 PowerSet 測試類型"
    assert 'PowerRead' in type_names, "缺少 PowerRead 測試類型"
    assert 'CommandTest' in type_names, "缺少 CommandTest 測試類型"

    print("✓ 所有基本測試類型都存在\n")
    return True


def test_get_template():
    """測試模板查詢功能"""
    print("=" * 80)
    print("測試 2: get_template() - 模板查詢")
    print("=" * 80)

    # 測試存在的模板
    template = instruments_module.get_template("PowerSet", "DAQ973A")
    assert template is not None, "應該找到 PowerSet/DAQ973A 模板"
    assert "required" in template, "模板應包含 required 欄位"
    assert "optional" in template, "模板應包含 optional 欄位"
    assert "example" in template, "模板應包含 example 欄位"

    print("✓ PowerSet/DAQ973A 模板查詢成功")
    print(f"  必填參數: {template['required']}")
    print(f"  可選參數: {template['optional']}")
    print(f"  範例: {template['example']}\n")

    # 測試不存在的模板
    template = instruments_module.get_template("PowerSet", "INVALID_INSTRUMENT")
    assert template is None, "不應找到不存在的模板"
    print("✓ 不存在的模板正確返回 None\n")
    return True


def test_validate_params():
    """測試參數驗證邏輯"""
    print("=" * 80)
    print("測試 3: validate_params() - 參數驗證")
    print("=" * 80)

    # 測試 1: 完整參數 - 應該通過
    result = instruments_module.validate_params(
        "PowerSet",
        "DAQ973A",
        {
            "Instrument": "daq973a_1",
            "Channel": "101",
            "Item": "volt",
            "Volt": "5.0"
        }
    )

    print("測試 3.1: 完整參數驗證")
    print(f"  驗證結果: {'✓ PASS' if result['valid'] else '✗ FAIL'}")
    print(f"  缺少參數: {result['missing_params']}")
    print(f"  無效參數: {result['invalid_params']}")
    print(f"  建議: {result['suggestions']}\n")

    assert result['valid'], "完整參數應該通過驗證"

    # 測試 2: 缺少必填參數 - 應該失敗
    result = instruments_module.validate_params(
        "PowerSet",
        "DAQ973A",
        {
            "Instrument": "daq973a_1"
            # 缺少 Channel 和 Item
        }
    )

    print("測試 3.2: 缺少必填參數")
    print(f"  驗證結果: {'✓ PASS' if result['valid'] else '✗ FAIL (預期)'}")
    print(f"  缺少參數: {result['missing_params']}")
    print(f"  建議: {result['suggestions']}\n")

    assert not result['valid'], "缺少必填參數應該失敗"
    assert 'Channel' in result['missing_params'], "應該標示缺少 Channel"
    assert 'Item' in result['missing_params'], "應該標示缺少 Item"

    print("✓ 參數驗證邏輯正確\n")
    return True


def main():
    """執行所有測試"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "instruments.py 重構驗證測試" + " " * 30 + "║")
    print("╚" + "=" * 78 + "╝")
    print("\n")

    try:
        test_get_measurement_types()
        test_get_template()
        test_validate_params()

        print("=" * 80)
        print("✓ ✓ ✓  所有測試通過！重構成功！  ✓ ✓ ✓")
        print("=" * 80)
        print("\n重構總結:")
        print("1. ✓ get_measurement_types() 可動態生成測試類型清單")
        print("2. ✓ validate_params() 可驗證參數並提供建議")
        print("3. ✓ get_template() 可查詢參數模板")
        print("\n改進效果:")
        print("- /types API 從 40+ 行硬編碼減少到 1 行函數調用")
        print("- 參數驗證可提供詳細的錯誤訊息和建議")
        print("- 配置統一管理，避免不一致")
        print()

        return 0

    except AssertionError as e:
        print(f"\n✗ 測試失敗: {e}\n")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n✗ 執行錯誤: {e}\n")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
