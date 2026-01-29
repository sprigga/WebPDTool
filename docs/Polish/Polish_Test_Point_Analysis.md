# Polish Test Point 模組深入分析

> 分析日期: 2026-01-28
> 版本: PDTool4
> 目錄: `polish/test_point/`

---

## 📋 目錄結構

```
polish/test_point/
├── __init__.py                    # 模組導出（空文件）
├── test_point.py                  # 主要測試點實現 (405行)
├── test_point_map.py              # 測試點映射管理器 (127行)
└── test_point_runAllTest.py       # RunAllTest 模式變體 (340行)
```

---

## 一、模組概覽

**polish/test_point/** 是測試點管理核心模組，提供：

- ✅ 單個測試點定義和執行
- ✅ 多種限制類型檢查
- ✅ 多種數值類型轉換
- ✅ 測試點映射管理
- ✅ RunAllTest 模式支持
- ✅ 測試結果記錄

---

## 二、文件詳細分析

### 2.1 test_point.py - 主要測試點實現

#### 2.1.1 導入與全局配置

```python
RAISE_ON_FAIL = True              # 默認失敗時拋出異常
TEST_ATLAS = 'test_xml.ini'        # 測試配置文件
FILE_NAME = '../../result.txt'     # 結果記錄文件
```

**依賴模組**:
- `configparser` - INI 配置讀取
- `ctypes` - C 類型支持
- `polish.mfg_common.logging_setup` - 日誌記錄
- `subprocess`, `random` - 通用工具

#### 2.1.2 輔助類: Canister

**用途**: 動態屬性字典，允許對象訪問方式操作字典

```python
class Canister(dict):
    def __getattr__(self, name):
        if name in self:
            return self[name]
        else:
            raise AttributeError("No such attribute: %s" % name)

    def __setattr__(self, name, value):
        self[name] = value

    def __delattr__(self, name):
        if name in self:
            del self[name]
        else:
            raise AttributeError("No such attribute: %s" % name)
```

**使用場景**: TestPoint 中的 `self.cfg` 對象，用於存儲配置

#### 2.1.3 限制類型 (LimitType) 系統

##### 限制類型層次結構

```python
class LimitType(object):
    pass

class LOWER_LIMIT_TYPE(LimitType):      # 下限限制
    pass
class UPPER_LIMIT_TYPE(LimitType):      # 上限限制
    pass
class BOTH_LIMIT_TYPE(LimitType):      # 雙邊限制
    pass
class NONE_LIMIT_TYPE(LimitType):       # 無限制
    pass
class EQUALITY_LIMIT_TYPE(LimitType):   # 相等限制
    pass
class PARTIAL_LIMIT_TYPE(LimitType):    # 部分匹配限制（字符串包含）
    pass
class INEQUALITY_LIMIT_TYPE(LimitType): # 不相等限制
    pass
```

##### 限制類型映射表

```python
LIMIT_TYPE_MAP = {
    'lower': LOWER_LIMIT_TYPE,
    'upper': UPPER_LIMIT_TYPE,
    'both': BOTH_LIMIT_TYPE,
    'equality': EQUALITY_LIMIT_TYPE,
    'partial': PARTIAL_LIMIT_TYPE,
    'inequality': INEQUALITY_LIMIT_TYPE,
    'none': NONE_LIMIT_TYPE,
}
```

##### 各限制類型的檢查邏輯

| 類型 | 檢查邏輯 | 失敗條件 | 適用場景 |
|------|----------|----------|----------|
| `NONE_LIMIT_TYPE` | 總是返回 `True` | 無 | 信息記錄，不做檢查 |
| `EQUALITY_LIMIT_TYPE` | `str(value) == equality_limit` | 不相等 | 精確匹配（如狀態碼、字符串） |
| `PARTIAL_LIMIT_TYPE` | `equality_limit in str(value)` | 不包含 | 字符串包含檢查（如錯誤消息） |
| `INEQUALITY_LIMIT_TYPE` | `value != equality_limit` | 相等 | 排除特定值 |
| `LOWER_LIMIT_TYPE` | `float(value) >= lower_limit` | 小於下限 | 最小值檢查（電壓、電流等） |
| `UPPER_LIMIT_TYPE` | `float(value) <= upper_limit` | 大於上限 | 最大值檢查（功耗、溫度等） |
| `BOTH_LIMIT_TYPE` | `lower_limit <= value <= upper_limit` | 超出範圍 | 範圍檢查（頻率、電阻等） |

#### 2.1.4 數值類型 (ValueType) 系統

##### 數值類型層次結構

```python
class ValueType(object):
    cast_call = None  # 轉換函數（子類實現）

class STRING_VALUE_TYPE(ValueType):
    @staticmethod
    def cast_call(in_obj):
        return str(in_obj)

class INTEGER_VALUE_TYPE(ValueType):
    @staticmethod
    def cast_call(in_obj):
        return int(in_obj, 0)  # 自動檢測進制

class FLOAT_VALUE_TYPE(ValueType):
    @staticmethod
    def cast_call(in_obj):
        return float(in_obj)
```

##### 數值類型映射表

```python
VALUE_TYPE_MAP = {
    'string': STRING_VALUE_TYPE,
    'integer': INTEGER_VALUE_TYPE,
    'float': FLOAT_VALUE_TYPE,
}
```

##### 進制自動檢測 (INTEGER_VALUE_TYPE)

```python
def multi_base_int(integer_string):
    return int(integer_string, 0)  # base=0 表示自動檢測
```

**支持的格式**:
- 十進制: `'123'` → 123
- 十六進制: `'0x7B'` → 123
- 八進制: `'0o173'` → 123
- 二進制: `'0b1111011'` → 123

#### 2.1.5 異常類層次結構

```python
class TestPointLimitFailure(Exception):
    pass

class TestPointUpperLimitFailure(TestPointLimitFailure):
    pass

class TestPointLowerLimitFailure(TestPointLimitFailure):
    pass

class TestPointEqualityLimitFailure(TestPointLimitFailure):
    pass

class TestPointInequalityLimitFailure(TestPointLimitFailure):
    pass

class TestPointDoubleExecutionError(Exception):
    pass
```

##### 配置錯誤異常

```python
class TestPointConfigValueTypeError(Exception):
    pass  # 數值類型無效

class TestPointConfigLimitTypeError(Exception):
    pass  # 限制類型無效
```

#### 2.1.6 工具函數

```python
def is_empty_limit(limit):
    """檢查限制值是否為空"""
    return limit is None or len(str(limit)) == 0
```

#### 2.1.7 TestPoint 類（核心類）

##### 構造函數參數

```python
def __init__(
    self,
    name,              # 測試點名稱（用作唯一標識符）
    ItemKey,           # 項目鍵（與 name 相關）
    # unit,            # 單位（在 RunAllTest 版本中使用）
    value_type,        # 數值類型: 'string', 'integer', 'float'
    limit_type,        # 限制類型: 'lower', 'upper', 'both', 'equality', 'partial', 'inequality', 'none'
    equality_limit=None,   # 相等限制值
    lower_limit=None,     # 下限值
    upper_limit=None,      # 上限值
)
```

##### 狀態屬性

```python
self.executed = False    # 是否已執行
self.passed = None       # 是否通過 (True/False)
self.value = None        # 測量值
self.ItemKey = ItemKey   # 項目鍵
self.name = name         # 測試點名稱
self.unique_id = name    # 唯一標識符
self.TestDateTime = ''   # 測試日期時間（可選）
```

##### 初始化流程

```
1. 設置初始狀態（executed=False, passed=None, value=None）
   ↓
2. 設置唯一標識符和項目鍵
   ↓
3. 初始化日誌記錄器
   ↓
4. 創建 Canister 配置對象
   ↓
5. 讀取 test_xml.ini 配置文件
   ↓
6. 解析並驗證 value_type（從 VALUE_TYPE_MAP）
   ↓
7. 解析並驗證 limit_type（從 LIMIT_TYPE_MAP）
   ↓
8. 處理 equality_limit（使用 value_type.cast_call 轉換）
   ↓
9. 處理 lower_limit（轉換為 float）
   ↓
10. 處理 upper_limit（轉換為 float）
```

##### execute() 方法

**簽名**:
```python
def execute(self, value, runAllTest, raiseOnFail=RAISE_ON_FAIL)
```

**參數**:
- `value`: 測量值
- `runAllTest`: "ON" 繼續執行 / 其他停止
- `raiseOnFail`: 失敗時是否拋出異常（默認 True）

**執行流程**:
```
1. 檢查特殊錯誤值
   ├─ "No instrument found" → 設置 passed=False, executed=True, 拋出異常
   └─ "Error: " in value → 設置 passed=False, executed=True, 拋出異常
   ↓
2. 調用 _execute(value, runAllTest, raiseOnFail)
   ↓
3. 更新狀態
   ├─ passed = 結果
   └─ executed = True
   ↓
4. 異常處理
   ├─ TestPointLimitFailure → passed = False, 拋出異常
   └─ 其他異常 → executed = True, 拋出異常
   ↓
5. finally 塊
   ├─ 記錄日誌
   └─ 寫入 result.txt（格式: passed,value）
```

**異常處理**:
```python
try:
    # 檢查特殊錯誤值
    if value == "No instrument found":
        self.value = value
        self.passed = False
        self.executed = True
        raise

    if "Error: " in value:
        self.value = value
        self.passed = False
        self.executed = True
        raise

    # 執行限制檢查
    pass_fail = self._execute(value, runAllTest, raiseOnFail)
    self.passed = pass_fail
    self.executed = True
    return pass_fail

except TestPointLimitFailure:
    self.passed = False
    self.executed = True
    raise

except:
    self.executed = True
    raise

finally:
    # 記錄日誌
    self.logger.info(str(self))
    # 寫入結果文件
    f = open(FILE_NAME, 'a')
    f.write(str(self.passed) + ',' + str(self.value))
    f.close()
```

##### _execute() 方法

**簽名**:
```python
def _execute(self, value, runAllTest, raiseOnFail=RAISE_ON_FAIL)
```

**執行流程**:
```
1. 雙重執行檢查
   └─ 如果已執行或 value 不為 None → 拋出 TestPointDoubleExecutionError
   ↓
2. 設置測量值
   └─ self.value = value
   ↓
3. 根據 limit_type 執行相應檢查
   ├─ NONE_LIMIT_TYPE → 返回 True
   ├─ EQUALITY_LIMIT_TYPE → 精確相等檢查
   │   ├─ runAllTest=="ON" → 失敗時捕獲異常，返回 False
   │   └─ runAllTest!="ON" → 失敗時拋出異常
   ├─ PARTIAL_LIMIT_TYPE → 字符串包含檢查
   │   ├─ runAllTest=="ON" → 失敗時捕獲異常，返回 False
   │   └─ runAllTest!="ON" → 失敗時拋出異常
   ├─ INEQUALITY_LIMIT_TYPE → 不相等檢查
   │   ├─ runAllTest=="ON" → 失敗時捕獲異常，返回 False
   │   └─ runAllTest!="ON" → 失敗時拋出異常
   ├─ LOWER_LIMIT_TYPE → 下限檢查
   │   ├─ runAllTest=="ON" → 失敗時捕獲異常，返回 False
   │   └─ runAllTest!="ON" → 失敗時拋出異常
   ├─ UPPER_LIMIT_TYPE → 上限檢查
   │   ├─ runAllTest=="ON" → 失敗時捕獲異常，返回 False
   │   └─ runAllTest!="ON" → 失敗時拋出異常
   └─ BOTH_LIMIT_TYPE → 雙邊檢查
       └─ 返回 upper_result and lower_result
```

**RunAllTest 模式處理**:

當 `runAllTest == "ON"` 時:
```python
try:
    result = bool(str(value) == self.equality_limit)
    if raiseOnFail and result == False:
        print("Equality_limit : "+str(self.equality_limit))
        raise TestPointEqualityLimitFailure(...)
except TestPointEqualityLimitFailure as e:
    print(str(e))
    return result  # 返回 False，但不拋出異常
```

當 `runAllTest != "ON"` 時:
```python
if raiseOnFail and result == False:
    print("Equality_limit : "+str(self.equality_limit))
    print('%s. Failed equality limit. %r does not equal %r limit.' % (...))
    raise TestPointEqualityLimitFailure  # 拋出異常
```

##### re_execute() 方法

**簽名**:
```python
def re_execute(self, value, raiseOnFail=RAISE_ON_FAIL)
```

**用途**: 重置測試點狀態並重新執行（不支持異常拋出）

**執行流程**:
```
1. 重置狀態
   ├─ executed = False
   ├─ value = None
   └─ 返回 True
   ↓
2. 執行限制檢查（不拋出異常）
   └─ 返回檢查結果
```

**注意**: 與 `execute()` 不同，`re_execute()` 不會拋出異常，也不會寫入 result.txt

##### 字符串表示

```python
def _pretty(self):
    return '{self.unique_id}, EXEC: {self.executed}, VALUE: {self.value}, PASSED: {self.passed}'.format(**locals())

def __str__(self):
    return self._pretty()

def __repr__(self):
    return self._pretty()
```

**輸出示例**:
```
info_vcu_serial_num, EXEC: True, VALUE: 12345, PASSED: True
```

---

### 2.2 test_point_map.py - 測試點映射管理器

#### 2.2.1 導入和配置

```python
import sys
import os
current_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_path))

import test_point
from test_point import *

RAISE_ON_FAIL = True
N_CSV_COLS = 7  # CSV 有效列數
```

#### 2.2.2 異常類

```python
class TestPointUniqueIdViolation(Exception):
    pass  # 測試點 ID 重複
```

#### 2.2.3 TestPointMap 類

**功能**: 測試點註冊、檢索和統計

##### 內部結構

```python
def __init__(self):
    self._map = {}  # {unique_id: TestPoint}
```

##### add_test_point()

```python
def add_test_point(self, test_point):
    unique_id = test_point.unique_id
    if unique_id in self._map:
        raise TestPointUniqueIdViolation('{unique_id} has already been added')
    self._map[unique_id] = test_point
```

**行為**:
- 添加測試點到映射表
- 檢查 ID 重複
- 重複時拋出異常

##### get_test_point()

```python
def get_test_point(self, unique_id):
    return self._map.get(unique_id)  # 不存在時返回 None
```

##### __getitem__()

```python
def __getitem__(self, unique_id):
    if unique_id in self._map:
        return self._map[unique_id]
    else:
        return None
```

**用途**: 字典風格訪問 `test_point_map['info_vcu_serial_num']`

##### get_dict()

```python
def get_dict(self):
    return self._map.copy()
```

**用途**: 獲取所有測試點的副本（避免直接修改內部狀態）

##### all_executed()

```python
def all_executed(self):
    all_executed = all((tp.executed for tp in self._map.values()))
    return all_executed
```

**用途**: 檢查所有測試點是否已執行

##### count_executed()

```python
def count_executed(self):
    n_exec = 0
    for n, tp in enumerate(self._map.values()):
        if tp.executed:
            n_exec += 1
    return n_exec, n+1  # (已執行數量, 總數量)
```

**返回值**: `(已執行數量, 總數量)`

##### count_skipped()

```python
def count_skipped(self):
    c, n = self.count_executed()
    return n - c
```

**用途**: 計算未執行（跳過）的測試點數量

##### all_pass()

```python
def all_pass(self):
    all_pass = all((tp.passed for tp in self._map.values()))
    return all_pass
```

**注意**: 只檢查 `passed` 屬性，不考慮 `executed`

##### all_executed_all_pass()

```python
def all_executed_all_pass(self):
    return self.all_pass() and self.all_executed()
```

**用途**: 綜合檢查是否全部執行並通過

##### get_fail_uid()

```python
def get_fail_uid(self):
    """Return uid of the failing test"""
    uid = None
    for tp in self._map.values():
        if tp.passed == False:
            uid = tp.unique_id
            break
    return uid
```

**用途**: 獲取第一個失敗的測試點 UID

#### 2.2.4 new_test_point_map() 工廠函數

**簽名**:
```python
def new_test_point_map(limits_table)
```

**參數**: `limits_table` - CSV 行列表（來自 csv.reader）

**返回值**: `TestPointMap` 對象

**處理流程**:
```
1. 創建空 TestPointMap
   ↓
2. 遍歷 limits_table 中的每一行
   ↓
3. 跳過空行
   ↓
4. 截取前 N_CSV_COLS 列（7列）
   ↓
5. 跳過 LibreOffice Calc 空行
   └─ row == ['', '', '', '', '', '', '']
   ↓
6. 跳過標題行和註釋行
   ├─ row[0] == 'ID'
   ├─ row[0].startswith(';')
   └─ row[0].startswith('#')
   ↓
7. 創建 TestPoint 對象
   └─ TestPoint(*row)
   ↓
8. 添加到 TestPointMap
   └─ test_point_map.add_test_point(test_point)
   ↓
9. 返回 test_point_map
```

**CSV 行格式**:
```python
[ID, Name, Value_Type, Limit_Type, Equality_Limit, Lower_Limit, Upper_Limit]
```

**示例行**:
```python
['info_vcu_serial_num', 'VCU Serial Number', 'string', 'equality', '12345', '', '']
['voltage', 'Voltage Measurement', 'float', 'both', '', '11.0', '13.0']
```

---

### 2.3 test_point_runAllTest.py - RunAllTest 模式變體

#### 2.3.1 與 test_point.py 的主要區別

| 特性 | test_point.py | test_point_runAllTest.py |
|------|--------------|-------------------------|
| 構造函數參數 | 包含 `ItemKey`，不包含 `unit` | 包含 `unit`，不包含 `ItemKey` |
| 限制類型數量 | 7 種（包含 `PARTIAL_LIMIT_TYPE`） | 6 種（不包含 `PARTIAL_LIMIT_TYPE`） |
| execute() 參數 | `execute(value, runAllTest, raiseOnFail)` | `execute(value, raiseOnFail)` |
| runAllTest 支持 | 完整支持（"ON" 與非 "ON"） | 不支持（無 runAllTest 參數） |
| result.txt 寫入 | `passed,value` | `passed,value\n` (帶換行符) |
| FILE_NAME 路徑 | 動態計算 (`../../result.txt`) | 硬編碼 Windows 路徑 |
| TEST_ATLAS | `test_xml.ini` | `test_atlas.ini` |

#### 2.3.2 構造函數差異

**test_point.py**:
```python
def __init__(
    self,
    name,
    ItemKey,      # ← 包含
    # unit,       # ← 不包含
    value_type,
    limit_type,
    equality_limit=None,
    lower_limit=None,
    upper_limit=None,
):
    self.ItemKey = ItemKey
    self.name = name
    self.unique_id = name
    # self.unit = unit
```

**test_point_runAllTest.py**:
```python
def __init__(
    self,
    name,
    unit,        # ← 包含
    value_type,
    limit_type,
    equality_limit=None,
    lower_limit=None,
    upper_limit=None,
):
    self.name = name
    self.unique_id = name
    self.unit = unit  # ← 包含
    # self.ItemKey = ItemKey  # ← 不包含
```

#### 2.3.3 execute() 方法差異

**test_point.py**:
```python
def execute(self, value, runAllTest, raiseOnFail=RAISE_ON_FAIL):
    try:
        if value == "No instrument found":
            # ... 處理
        if "Error: " in value:
            # ... 處理
        else:
            pass_fail = self._execute(value, runAllTest, raiseOnFail)  # ← 包含 runAllTest
            # ...
```

**test_point_runAllTest.py**:
```python
def execute(self, value, raiseOnFail=RAISE_ON_FAIL):  # ← 不包含 runAllTest
    try:
        pass_fail = self._execute(value, raiseOnFail)  # ← 不包含 runAllTest
        # ...
```

#### 2.3.4 result.txt 寫入差異

**test_point.py**:
```python
f.write(str(self.passed) + ',' + str(self.value))  # ← 無換行符
```

**test_point_runAllTest.py**:
```python
f.write(str(self.passed) + ',' + str(self.value) + '\n')  # ← 帶換行符
```

#### 2.3.5 限制類型差異

**test_point.py** (7 種):
```python
LIMIT_TYPE_MAP = {
    'lower': LOWER_LIMIT_TYPE,
    'upper': UPPER_LIMIT_TYPE,
    'both': BOTH_LIMIT_TYPE,
    'equality': EQUALITY_LIMIT_TYPE,
    'partial': PARTIAL_LIMIT_TYPE,      # ← 包含
    'inequality': INEQUALITY_LIMIT_TYPE,
    'none': NONE_LIMIT_TYPE,
}
```

**test_point_runAllTest.py** (6 種):
```python
LIMIT_TYPE_MAP = {
    'lower': LOWER_LIMIT_TYPE,
    'upper': UPPER_LIMIT_TYPE,
    'both': BOTH_LIMIT_TYPE,
    'equality': EQUALITY_LIMIT_TYPE,
    # 'partial': PARTIAL_LIMIT_TYPE,  # ← 不包含
    'inequality': INEQUALITY_LIMIT_TYPE,
    'none': NONE_LIMIT_TYPE,
}
```

#### 2.3.6 執行邏輯差異

**test_point.py (RunAllTest 模式)**:
```python
if self.limit_type is EQUALITY_LIMIT_TYPE:
    result = bool(str(value) == self.equality_limit)
    if runAllTest == "ON":  # ← 檢查 RunAllTest 模式
        try:
            result = bool(str(value) == self.equality_limit)
            if raiseOnFail and result == False:
                print("Equality_limit : "+str(self.equality_limit))
                raise TestPointEqualityLimitFailure(...)
        except TestPointEqualityLimitFailure as e:
            print(str(e))
            return result  # ← 返回 False，不拋出異常
    else:
        if raiseOnFail and result == False:
            print("Equality_limit : "+str(self.equality_limit))
            print('%s. Failed equality limit. %r does not equal %r limit.' % (...))
            raise TestPointEqualityLimitFailure  # ← 拋出異常
    return result
```

**test_point_runAllTest.py (無 RunAllTest 模式)**:
```python
if self.limit_type is EQUALITY_LIMIT_TYPE:
    try:
        result = bool(str(value) == self.equality_limit)
        if raiseOnFail and result == False:
            print("Equality_limit : "+str(self.equality_limit))
            raise TestPointEqualityLimitFailure(...)
    except TestPointEqualityLimitFailure as e:
        print(str(e))
        return result  # ← 總是捕獲異常，不拋出
    return result
```

#### 2.3.7 使用場景推測

**test_point.py**:
- 用於主測試流程
- 支持完整 RunAllTest 模式
- 與 `test_point_map.py` 配合使用
- 與 `measurement.py` 的 `Measurement` 類集成

**test_point_runAllTest.py**:
- 舊版本或特殊模式
- 不支持 RunAllTest（默認總是繼續執行）
- 硬編碼的 Windows 路徑（可能是遺留代碼）
- 可能用於簡化場景或向後兼容

---

### 2.4 __init__.py - 模組導出

**當前狀態**: 空文件（1行）

**建議導出**:
```python
from test_point import (
    TestPoint,
    Canister,
    LimitType,
    ValueType,
    TestPointLimitFailure,
    TestPointUpperLimitFailure,
    TestPointLowerLimitFailure,
    TestPointEqualityLimitFailure,
    TestPointInequalityLimitFailure,
    TestPointDoubleExecutionError,
    is_empty_limit,
    VALUE_TYPE_MAP,
    LIMIT_TYPE_MAP,
    RAISE_ON_FAIL,
)

from test_point_map import (
    TestPointMap,
    new_test_point_map,
    TestPointUniqueIdViolation,
)

__all__ = [
    'TestPoint',
    'TestPointMap',
    'new_test_point_map',
    'Canister',
    'LimitType',
    'ValueType',
    'TestPointLimitFailure',
    'TestPointUpperLimitFailure',
    'TestPointLowerLimitFailure',
    'TestPointEqualityLimitFailure',
    'TestPointInequalityLimitFailure',
    'TestPointDoubleExecutionError',
    'TestPointUniqueIdViolation',
    'is_empty_limit',
    'VALUE_TYPE_MAP',
    'LIMIT_TYPE_MAP',
    'RAISE_ON_FAIL',
]
```

---

## 三、執行流程分析

### 3.1 完整測試點執行流程

```
┌─────────────────────────────────────────────────────────────┐
│ 1. 創建測試點映射（初始化階段）                             │
├─────────────────────────────────────────────────────────────┤
│ new_test_point_map(limits_csv)                              │
│         ↓                                                   │
│ 讀取 CSV 文件                                               │
│         ↓                                                   │
│ 遍歷每一行                                                 │
│         ↓                                                   │
│ 創建 TestPoint 對象                                         │
│   ├─ 解析 value_type → ValueType 類                         │
│   ├─ 解析 limit_type → LimitType 類                        │
│   ├─ 轉換 equality_limit（使用 ValueType.cast_call）       │
│   ├─ 轉換 lower_limit（float）                             │
│   └─ 轉換 upper_limit（float）                             │
│         ↓                                                   │
│ 添加到 TestPointMap                                         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. 執行測試點（測量階段）                                   │
├─────────────────────────────────────────────────────────────┤
│ test_point.execute(value, runAllTest, raiseOnFail)          │
│         ↓                                                   │
│ 檢查特殊錯誤值                                             │
│   ├─ "No instrument found" → 失敗並拋出異常                 │
│   └─ "Error: " in value → 失敗並拋出異常                    │
│         ↓                                                   │
│ 調用 _execute(value, runAllTest, raiseOnFail)               │
│         ↓                                                   │
│ 檢查是否雙重執行                                            │
│         ↓                                                   │
│ 設置 self.value = value                                     │
│         ↓                                                   │
│ 根據 limit_type 執行限制檢查                                │
│   ├─ NONE_LIMIT_TYPE → 返回 True                           │
│   ├─ EQUALITY_LIMIT_TYPE → 精確相等檢查                     │
│   ├─ PARTIAL_LIMIT_TYPE → 字符串包含檢查                    │
│   ├─ INEQUALITY_LIMIT_TYPE → 不相等檢查                     │
│   ├─ LOWER_LIMIT_TYPE → 下限檢查                            │
│   ├─ UPPER_LIMIT_TYPE → 上限檢查                            │
│   └─ BOTH_LIMIT_TYPE → 雙邊檢查                              │
│         ↓                                                   │
│ RunAllTest 模式判斷                                        │
│   ├─ runAllTest == "ON" → 失敗時捕獲異常，返回 False        │
│   └─ runAllTest != "ON" → 失敗時拋出異常                     │
│         ↓                                                   │
│ 更新狀態                                                     │
│   ├─ self.passed = 結果                                     │
│   └─ self.executed = True                                   │
│         ↓                                                   │
│ finally 塊                                                  │
│   ├─ 記錄日誌                                               │
│   └─ 寫入 result.txt                                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. 測試點映射檢查（結束階段）                               │
├─────────────────────────────────────────────────────────────┤
│ TestPointMap.all_executed_all_pass()                        │
│         ↓                                                   │
│ 檢查所有測試點是否已執行                                    │
│   └─ all(tp.executed for tp in _map.values())              │
│         ↓                                                   │
│ 檢查所有測試點是否通過                                      │
│   └─ all(tp.passed for tp in _map.values())                │
│         ↓                                                   │
│ 返回綜合結果                                                │
│         ↓                                                   │
│ 獲取失敗信息（如果失敗）                                    │
│   └─ TestPointMap.get_fail_uid()                           │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 RunAllTest 模式流程

```
┌─────────────────────────────────────────────────────────────┐
│ RunAllTest = "ON" 模式                                       │
├─────────────────────────────────────────────────────────────┤
│ 測試點 1 執行 → 失敗 → 記錄 → 繼續執行                       │
│ 測試點 2 執行 → 通過 → 記錄 → 繼續執行                       │
│ 測試點 3 執行 → 失敗 → 記錄 → 繼續執行                       │
│ ...                                                         │
│ 所有測試點執行完畢 → 返回結果                               │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ RunAllTest != "ON" 模式                                     │
├─────────────────────────────────────────────────────────────┤
│ 測試點 1 執行 → 失敗 → 拋出異常 → 停止執行                   │
│ 測試點 2 未執行                                             │
│ 測試點 3 未執行                                             │
│ ...                                                         │
│ 捕獲異常 → 返回失敗結果                                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 四、設計模式分析

### 4.1 策略模式 (Strategy Pattern)

**應用**: 限制類型檢查

```python
# 不同的檢查策略
if self.limit_type is EQUALITY_LIMIT_TYPE:
    result = bool(str(value) == self.equality_limit)
elif self.limit_type is LOWER_LIMIT_TYPE:
    result = bool(float(value) >= float(self.lower_limit))
elif self.limit_type is UPPER_LIMIT_TYPE:
    result = bool(float(self.upper_limit) >= float(value))
# ...
```

**優點**:
- 易於添加新的限制類型
- 檢查邏輯解耦

### 4.2 工廠模式 (Factory Pattern)

**應用**: `new_test_point_map()`

```python
def new_test_point_map(limits_table):
    test_point_map = TestPointMap()
    for row in limits_table:
        test_point = TestPoint(*row)
        test_point_map.add_test_point(test_point)
    return test_point_map
```

**優點**:
- 封裝測試點創建邏輯
- 統一初始化流程

### 4.3 容器模式 (Container Pattern)

**應用**: `Canister` 類

```python
self.cfg = Canister()
self.cfg.test_atlas = TEST_ATLAS
```

**優點**:
- 動態屬性訪問
- 代碼簡潔

### 4.4 映射模式 (Map Pattern)

**應用**: `TestPointMap` 類

```python
self._map = {unique_id: TestPoint}

def __getitem__(self, unique_id):
    return self._map.get(unique_id)
```

**優點**:
- 快速查找
- 字典風格訪問

### 4.5 模板方法模式 (Template Method Pattern)

**應用**: `execute()` 和 `_execute()` 分離

```python
def execute(self, value, runAllTest, raiseOnFail):
    try:
        pass_fail = self._execute(value, runAllTest, raiseOnFail)
        self.passed = pass_fail
        self.executed = True
        return pass_fail
    except TestPointLimitFailure:
        self.passed = False
        self.executed = True
        raise
    finally:
        self.logger.info(str(self))
        f = open(FILE_NAME, 'a')
        f.write(str(self.passed) + ',' + str(self.value))
        f.close()
```

**優點**:
- 分離核心邏輯和異常處理
- 代碼復用

---

## 五、代碼重複問題分析

### 5.1 test_point.py vs test_point_runAllTest.py

#### 重複代碼

| 模塊 | 類別 | 行數 | 重複度 |
|------|------|------|--------|
| Canister 類 | 完全重複 | 15 行 | 100% |
| LimitType 類系 | 大部分重複 | 35 行 | 86% |
| ValueType 類系 | 完全重複 | 25 行 | 100% |
| 異常類層次 | 完全重複 | 15 行 | 100% |
| TestPoint.__init__ | 大部分重複 | 45 行 | 80% |
| TestPoint._execute | 部分重複 | 120 行 | 60% |
| TestPoint.re_execute | 大部分重複 | 50 行 | 90% |
| 字符串表示 | 完全重複 | 10 行 | 100% |

**總計重複**: ~315 行（佔總代碼的 ~78%）

#### 差異點

1. **構造函數參數**:
   - `test_point.py`: `(name, ItemKey, value_type, ...)`
   - `test_point_runAllTest.py`: `(name, unit, value_type, ...)`

2. **execute() 參數**:
   - `test_point.py`: `(value, runAllTest, raiseOnFail)`
   - `test_point_runAllTest.py`: `(value, raiseOnFail)`

3. **限制類型**:
   - `test_point.py`: 7 種（包含 `PARTIAL_LIMIT_TYPE`）
   - `test_point_runAllTest.py`: 6 種（不包含 `PARTIAL_LIMIT_TYPE`）

4. **result.txt 寫入**:
   - `test_point.py`: `passed,value` (無換行)
   - `test_point_runAllTest.py**: `passed,value\n` (帶換行)

#### 建議重構方案

```python
# test_point.py（統一版本）
class TestPoint(object):
    def __init__(
        self,
        name,
        ItemKey=None,      # 可選參數
        unit=None,          # 可選參數
        value_type=None,
        limit_type=None,
        equality_limit=None,
        lower_limit=None,
        upper_limit=None,
        runAllTest=False,   # 新增參數
    ):
        self.ItemKey = ItemKey
        self.unit = unit
        self.runAllTest = runAllTest
        # ... 其他初始化

    def execute(self, value, raiseOnFail=RAISE_ON_FAIL):
        runAllTest = self.runAllTest
        # ... 執行邏輯
```

**優點**:
- 消除代碼重複
- 統一維護
- 向後兼容

### 5.2 其他重複

#### test_point.py 和 test_point_map.py 中的重複

- `Canister` 類在兩個文件中都定義
- 應該提取到 `mfg_common/canister.py`

---

## 六、關鍵數據流

### 6.1 測試點初始化數據流

```
CSV 文件 (testPlan/.../...csv)
    ↓
csv.reader()
    ↓
limits_table (list of rows)
    ↓
new_test_point_map(limits_table)
    ↓
TestPointMap._map = {uid: TestPoint}
    ↓
meas_assets.test_point_map
    ↓
Measurement.test_points
```

### 6.2 測試點執行數據流

```
Measurement.measure()
    ↓
test_point.execute(value, runAllTest, raiseOnFail)
    ↓
_execute(value, runAllTest, raiseOnFail)
    ↓
檢查限制
    ↓
更新 TestPoint 狀態
    ├─ executed = True
    ├─ passed = True/False
    └─ value = measured_value
    ↓
寫入 result.txt
    ↓
記錄日誌
```

### 6.3 測試結果數據流

```
TestPoint.passed
    ↓
TestPointMap.all_pass()
    ↓
Measurement.check_test_points()
    ↓
generate_default_report()
    ↓
default_reports/{serial_num}_{date}.csv
```

---

## 七、潛在問題和改進建議

### 7.1 代碼重複

**問題**: `test_point.py` 和 `test_point_runAllTest.py` 有大量重複代碼

**建議**:
- 合併為單個文件
- 使用參數控制行為差異
- 提取公共類到 `mfg_common/`

### 7.2 硬編碼路徑

**問題**:
- `test_point_runAllTest.py` 中的硬編碼 Windows 路徑
- `FILE_NAME` 在多個地方定義

**建議**:
- 使用相對路徑
- 從配置文件讀取
- 統一路徑管理

### 7.3 異常處理不一致

**問題**:
- `execute()` 捕獲所有異常 (`except:`)
- `re_execute()` 不拋出異常
- 某些異常只打印，不拋出

**建議**:
- 統一異常處理策略
- 添加異常日誌
- 區分可恢復和不可恢復異常

### 7.4 日誌記錄不完善

**問題**:
- `logger` 只在 `finally` 塊中記錄
- 缺少調試級別日誌
- 沒有性能日誌

**建議**:
- 添加更多日誌點
- 支持多級日誌
- 添加執行時間記錄

### 7.5 類型提示缺失

**問題**: 所有函數都缺少 Python 類型提示

**建議**:
```python
def __init__(
    self,
    name: str,
    ItemKey: str,
    value_type: str,
    limit_type: str,
    equality_limit: Optional[str] = None,
    lower_limit: Optional[str] = None,
    upper_limit: Optional[str] = None,
) -> None:
    ...

def execute(self, value: str, runAllTest: str, raiseOnFail: bool = True) -> bool:
    ...

def _execute(self, value: str, runAllTest: str, raiseOnFail: bool = True) -> bool:
    ...
```

### 7.6 測試點狀態管理

**問題**:
- `executed`, `passed`, `value` 可以直接修改
- 缺少狀態轉移驗證

**建議**:
- 添加屬性裝飾器
- 驗證狀態轉移有效性
- 添加狀態歷史記錄

### 7.7 CSV 列數硬編碼

**問題**: `N_CSV_COLS = 7` 硬編碼

**建議**:
- 根據實際列數動態處理
- 添加列數驗證
- 支持可變列數

### 7.8 配置文件讀取

**問題**:
- 每個 TestPoint 都讀取 `test_xml.ini`
- 重複讀取浪費資源

**建議**:
- 在 `new_test_point_map()` 中讀取一次
- 傳遞配置對象給 TestPoint
- 使用單例模式

### 7.9 result.txt 寫入

**問題**:
- 每個測試點都打開/關閉文件
- 沒有文件鎖定機制
- 可能存在併發問題

**建議**:
- 使用上下文管理器 (`with`)
- 批量寫入
- 添加文件鎖定

### 7.10 SFC 集成

**問題**:
- SFC 代碼被註釋掉
- 集成邏輯不清晰

**建議**:
- 如果不需要，完全移除
- 如果需要，提取到獨立模組
- 添加開關控制

---

## 八、使用示例

### 8.1 創建測試點映射

```python
from polish.test_point import new_test_point_map
import csv

# 讀取限制表
with open('limits.csv', 'r') as f:
    limits_table = list(csv.reader(f))

# 創建測試點映射
test_point_map = new_test_point_map(limits_table)

# 訪問測試點
tp = test_point_map['info_vcu_serial_num']
print(tp)  # info_vcu_serial_num, EXEC: False, VALUE: None, PASSED: None
```

### 8.2 執行測試點

```python
# 執行測試點（正常模式）
result = tp.execute('12345', 'OFF', True)
print(result)  # True or False
print(tp)  # info_vcu_serial_num, EXEC: True, VALUE: 12345, PASSED: True

# 執行測試點（RunAllTest 模式）
result = tp.execute('invalid', 'ON', True)
print(result)  # False
print(tp)  # info_vcu_serial_num, EXEC: True, VALUE: invalid, PASSED: False

# 重試測試點
result = tp.re_execute('54321', True)
print(result)  # True or False
```

### 8.3 檢查測試點映射狀態

```python
# 檢查是否全部執行
all_executed = test_point_map.all_executed()
print(all_executed)  # True or False

# 檢查是否全部通過
all_pass = test_point_map.all_pass()
print(all_pass)  # True or False

# 綜合檢查
all_ok = test_point_map.all_executed_all_pass()
print(all_ok)  # True or False

# 統計已執行數量
n_exec, n_total = test_point_map.count_executed()
print(f"已執行: {n_exec}/{n_total}")

# 統計跳過數量
n_skipped = test_point_map.count_skipped()
print(f"跳過: {n_skipped}")

# 獲取失敗的測試點 UID
fail_uid = test_point_map.get_fail_uid()
print(f"失敗: {fail_uid}")
```

### 8.4 創建自定義測試點

```python
from polish.test_point import TestPoint, EQUALITY_LIMIT_TYPE, STRING_VALUE_TYPE

# 創建測試點
tp = TestPoint(
    name='my_test_point',
    ItemKey='my_test_point',
    value_type='string',
    limit_type='equality',
    equality_limit='PASS',
)

# 執行測試點
result = tp.execute('PASS', 'OFF', True)
print(result)  # True

# 檢查狀態
print(tp.executed)  # True
print(tp.passed)    # True
print(tp.value)     # 'PASS'
```

### 8.5 RunAllTest 模式示例

```python
from polish.test_point import TestPoint, LOWER_LIMIT_TYPE, FLOAT_VALUE_TYPE

# 創建測試點
tp = TestPoint(
    name='voltage_check',
    ItemKey='voltage_check',
    value_type='float',
    limit_type='lower',
    lower_limit='11.0',
)

# 正常模式（失敗時停止）
try:
    result = tp.execute('10.5', 'OFF', True)
except TestPointLowerLimitFailure as e:
    print(f"測試失敗: {e}")

# RunAllTest 模式（失敗時繼續）
result = tp.execute('10.5', 'ON', True)
print(f"結果: {result}")  # False，但不拋出異常
```

---

## 九、測試場景覆蓋

### 9.1 限制類型測試

| 測試場景 | 限制類型 | 測試值 | 限制值 | 期望結果 |
|----------|----------|--------|--------|----------|
| 相等通過 | EQUALITY_LIMIT_TYPE | "PASS" | "PASS" | True |
| 相等失敗 | EQUALITY_LIMIT_TYPE | "FAIL" | "PASS" | False |
| 部分匹配通過 | PARTIAL_LIMIT_TYPE | "Error: timeout" | "Error:" | True |
| 部分匹配失敗 | PARTIAL_LIMIT_TYPE | "OK" | "Error:" | False |
| 不相等通過 | INEQUALITY_LIMIT_TYPE | "FAIL" | "PASS" | True |
| 不相等失敗 | INEQUALITY_LIMIT_TYPE | "PASS" | "PASS" | False |
| 下限通過 | LOWER_LIMIT_TYPE | 12.0 | 11.0 | True |
| 下限失敗 | LOWER_LIMIT_TYPE | 10.5 | 11.0 | False |
| 上限通過 | UPPER_LIMIT_TYPE | 12.5 | 13.0 | True |
| 上限失敗 | UPPER_LIMIT_TYPE | 13.5 | 13.0 | False |
| 雙邊通過 | BOTH_LIMIT_TYPE | 12.0 | 11.0, 13.0 | True |
| 雙邊下限失敗 | BOTH_LIMIT_TYPE | 10.5 | 11.0, 13.0 | False |
| 雙邊上限失敗 | BOTH_LIMIT_TYPE | 13.5 | 11.0, 13.0 | False |

### 9.2 數值類型測試

| 測試場景 | 數值類型 | 輸入值 | 轉換結果 |
|----------|----------|--------|----------|
| 字符串 | STRING_VALUE_TYPE | 12345 | "12345" |
| 十進制整數 | INTEGER_VALUE_TYPE | "12345" | 12345 |
| 十六進制整數 | INTEGER_VALUE_TYPE | "0x3039" | 12345 |
| 八進制整數 | INTEGER_VALUE_TYPE | "0o30071" | 12345 |
| 二進制整數 | INTEGER_VALUE_TYPE | "0b11000000111001" | 12345 |
| 浮點數 | FLOAT_VALUE_TYPE | "12.34" | 12.34 |

### 9.3 RunAllTest 模式測試

| 測試場景 | RunAllTest | 失敗行為 |
|----------|------------|----------|
| 正常模式失敗 | "OFF" | 拋出異常 |
| RunAllTest 模式失敗 | "ON" | 返回 False，不拋出異常 |
| RunAllTest 模式通過 | "ON" | 返回 True |

### 9.4 錯誤處理測試

| 測試場景 | 輸入值 | 期望行為 |
|----------|--------|----------|
| 無儀器 | "No instrument found" | passed=False, 拋出異常 |
| 錯誤消息 | "Error: timeout" | passed=False, 拋出異常 |
| 雙重執行 | 第二次調用 | 拋出 TestPointDoubleExecutionError |

---

## 十、性能分析

### 10.1 時間複雜度

| 操作 | 時間複雜度 | 說明 |
|------|------------|------|
| `add_test_point()` | O(1) | 字典插入 |
| `get_test_point()` | O(1) | 字典查找 |
| `__getitem__()` | O(1) | 字典查找 |
| `get_dict()` | O(n) | 字典複製 |
| `all_executed()` | O(n) | 遍歷所有測試點 |
| `all_pass()` | O(n) | 遍歷所有測試點 |
| `count_executed()` | O(n) | 遍歷所有測試點 |
| `count_skipped()` | O(n) | 依賴 count_executed() |
| `get_fail_uid()` | O(n) | 遍歷直到找到失敗 |
| `new_test_point_map()` | O(n) | 遍歷 CSV 行 |
| `execute()` | O(1) | 單個測試點執行 |
| `_execute()` | O(1) | 限制檢查 |

### 10.2 空間複雜度

| 結構 | 空間複雜度 | 說明 |
|------|------------|------|
| TestPoint | O(1) | 固定屬性 |
| TestPointMap | O(n) | n 個測試點 |
| new_test_point_map() | O(n) | 創建 n 個 TestPoint |

### 10.3 性能瓶頸

1. **文件 I/O**:
   - `result.txt` 每次執行都打開/關閉
   - 建議批量寫入

2. **日誌記錄**:
   - 每次執行都記錄日誌
   - 建議異步記錄

3. **配置讀取**:
   - 每個 TestPoint 都讀取 `test_xml.ini`
   - 建議讀取一次後共享

---

## 十一、集成點分析

### 11.1 與 measurement.py 集成

```python
from polish import Measurement

class MyMeasurement(Measurement):
    test_point_uids = ('test_1', 'test_2')

    def measure(self):
        # 收集數據
        value1 = collect_data_1()
        value2 = collect_data_2()

        # 執行測試點
        self.test_points.test_1.execute(value1, runAllTest, raiseOnFail)
        self.test_points.test_2.execute(value2, runAllTest, raiseOnFail)
```

### 11.2 與 reports.py 集成

```python
from polish.reports import generate_default_report

# 生成報告
generate_default_report(
    test_point_map=test_point_map,
    uid_serial_num='info_vcu_serial_num',
    test_name='atlas',
    report_name='dflt',
    date_and_time=datetime_str,
)
```

### 11.3 與 oneCSV_atlas_2.py 集成

```python
# 讀取測試計劃 CSV
test_plan_csv = 'testPlan/Other/selfTest/testPlan.csv'

# 創建測試點映射
test_point_map = new_test_point_map(limits_table)

# 執行測試
for measurement in measurements:
    measurement.run()

# 檢查結果
if test_point_map.all_executed_all_pass():
    print("測試通過")
else:
    fail_uid = test_point_map.get_fail_uid()
    print(f"測試失敗: {fail_uid}")
```

---

## 十二、總結

### 12.1 模組優點

✅ **功能完整**: 支持多種限制類型和數值類型
✅ **靈活配置**: 通過 CSV 配置測試點
✅ **RunAllTest 模式**: 支持失敗繼續執行
✅ **狀態管理**: 清晰的執行狀態和結果追蹤
✅ **異常處理**: 完善的異常類層次結構
✅ **映射管理**: 方便的測試點檢索和統計

### 12.2 主要問題

⚠️ **代碼重複**: `test_point.py` 和 `test_point_runAllTest.py` 有大量重複
⚠️ **硬編碼路徑**: 配置文件和結果文件路徑硬編碼
⚠️ **異常處理不一致**: 某些異常捕獲但未正確處理
⚠️ **日誌不完善**: 缺少詳細的日誌記錄
⚠️ **類型提示缺失**: 沒有 Python 類型提示
⚠️ **性能問題**: 重複文件 I/O 和配置讀取

### 12.3 改進優先級

| 優先級 | 改進項 | 影響範圍 |
|--------|--------|----------|
| 高 | 合併重複代碼 | 維護性 |
| 高 | 修復硬編碼路徑 | 可移植性 |
| 中 | 添加類型提示 | 代碼質量 |
| 中 | 優化文件 I/O | 性能 |
| 中 | 完善日誌記錄 | 可調試性 |
| 低 | 統一異常處理 | 穩定性 |

### 12.4 使用建議

1. **新項目**: 使用 `test_point.py`（支持 RunAllTest）
2. **舊項目**: 評估是否需要遷移到統一版本
3. **性能敏感**: 優化文件 I/O 和配置讀取
4. **可維護性**: 合併重複代碼，添加類型提示

---

## 十三、附錄

### 13.1 文件統計

| 文件 | 行數 | 類數量 | 函數數量 |
|------|------|--------|----------|
| test_point.py | 405 | 15 | 4 |
| test_point_map.py | 127 | 2 | 2 |
| test_point_runAllTest.py | 340 | 14 | 4 |
| __init__.py | 1 | 0 | 0 |
| **總計** | **873** | **31** | **10** |

### 13.2 類層次結構

```
object
├── Canister (dict)
├── LimitType
│   ├── LOWER_LIMIT_TYPE
│   ├── UPPER_LIMIT_TYPE
│   ├── BOTH_LIMIT_TYPE
│   ├── NONE_LIMIT_TYPE
│   ├── EQUALITY_LIMIT_TYPE
│   ├── PARTIAL_LIMIT_TYPE
│   └── INEQUALITY_LIMIT_TYPE
├── ValueType
│   ├── STRING_VALUE_TYPE
│   ├── INTEGER_VALUE_TYPE
│   └── FLOAT_VALUE_TYPE
├── TestPoint
└── TestPointMap
```

### 13.3 異常層次結構

```
Exception
├── TestPointLimitFailure
│   ├── TestPointUpperLimitFailure
│   ├── TestPointLowerLimitFailure
│   ├── TestPointEqualityLimitFailure
│   └── TestPointInequalityLimitFailure
├── TestPointDoubleExecutionError
├── TestPointConfigValueTypeError
└── TestPointConfigLimitTypeError
```

### 13.4 配置映射表

**LIMIT_TYPE_MAP**:
```python
{
    'lower': LOWER_LIMIT_TYPE,
    'upper': UPPER_LIMIT_TYPE,
    'both': BOTH_LIMIT_TYPE,
    'equality': EQUALITY_LIMIT_TYPE,
    'partial': PARTIAL_LIMIT_TYPE,  # 僅 test_point.py
    'inequality': INEQUALITY_LIMIT_TYPE,
    'none': NONE_LIMIT_TYPE,
}
```

**VALUE_TYPE_MAP**:
```python
{
    'string': STRING_VALUE_TYPE,
    'integer': INTEGER_VALUE_TYPE,
    'float': FLOAT_VALUE_TYPE,
}
```

### 13.5 全局變量

| 變量 | 默認值 | 用途 |
|------|--------|------|
| `RAISE_ON_FAIL` | `True` | 失敗時是否拋出異常 |
| `TEST_ATLAS` | `'test_xml.ini'` | 測試配置文件 |
| `FILE_NAME` | `'../../result.txt'` | 結果記錄文件 |
| `N_CSV_COLS` | `7` | CSV 有效列數 |

---

**文檔版本**: 1.0
**最後更新**: 2026-01-28
**分析者**: Claude Code
**分析範圍**: polish/test_point/ 模組
