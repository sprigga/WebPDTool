# Polish Mfg Config Readers 模組分析

> 分析日期: 2026-01-28
> 版本: PDTool4
> 目錄: `polish/mfg_config_readers/`

---

## 📋 目錄結構

```
polish/mfg_config_readers/
├── __init__.py                # 模組初始化（空文件）
├── test_config_reader.py      # 測試配置讀取器
├── limits_table_reader.py     # 限制表讀取器（CSV/XML）
└── limits_altasSpec.csv        # 示例限制表
```

---

## 一、核心架構概覽

**mfg_config_readers** 是配置讀取模組，提供：

- ✅ INI 格式測試配置讀取
- ✅ CSV 格式限制表讀取
- ✅ XML 格式限制數據讀取
- ✅ 靈活的數據格式支持

---

## 二、各文件詳細分析

### 2.1 test_config_reader.py - 測試配置讀取器

#### 源代碼分析

```python
from ..mfg_common.config_reader import load_and_read_config

def get_test_config(test_conf_filename):
    return load_and_read_config(test_conf_filename)
```

#### 功能說明

**目的**: 提供測試配置文件的讀取接口

**特點**:
- **代理模式**: 直接調用底層 `load_and_read_config()` 函數
- **簡潔性**: 提供統一的接口，隱藏實現細節
- **依賴**: 依賴 `mfg_common.config_reader` 模組

**參數**:
- `test_conf_filename`: INI 格式的測試配置文件路徑

**返回值**:
- `Canister` 對象，包含解析後的配置

**底層實現** (來自 `mfg_common/config_reader.py`):
```python
def load_and_read_config(filename):
    """加載並解析 INI 文件"""
    config = configparser.ConfigParser()
    config.read(filename)
    return read_config(config)

def read_config(ini):
    """解析 ConfigParser 對象為 Canister"""
    config_canister = Canister()
    for section in ini.sections():
        section_canister = Canister()
        for key, value in ini.items(section):
            # 只允許 [A-Z0-9_] 的鍵名
            sanitized_key = ''.join(c if c.isalnum() or c == '_' else '' for c in key)
            # 自動類型轉換
            section_canister[sanitized_key.lower()] = auto_cast_string(value)
        config_canister[section.lower()] = section_canister
    return config_canister
```

**使用示例**:
```python
from polish.mfg_config_readers import get_test_config

# 讀取測試配置
test_config = get_test_config('test_atlas.ini')

# 訪問配置
timeout = test_config.testspec.timeout
station = test_config.testspec.station
```

**當前使用狀態**:
- ✅ 已導出到 `polish/__init__.py`
- ⚠️ 在 `default_setup` 中被註釋掉（第 5、21 行）
- 💡 可能預留給未來使用

---

### 2.2 limits_table_reader.py - 限制表讀取器

#### 源代碼分析

```python
from __future__ import print_function
import csv
import xml.etree.ElementTree as ET
import io

def get_limits_table(limits_csv_filename):
    """讀取 CSV 格式的限制表"""
    with open(limits_csv_filename) as table_file:
        table_buffer = io.StringIO(table_file.read())
    return csv.reader(table_buffer)

def get_limits_data(xml_file):
    """讀取 XML 格式的限制數據"""
    tree = ET.parse(xml_file)
    root = tree.getroot()

    data = []

    for TestItem in root.findall('TestItems/*'):
        ID = TestItem.tag
        MinElement = TestItem.find("ProgramParams/Lowlimit")
        Min = float(MinElement.text) if MinElement is not None else ""
        Value = ""
        MaxElement = TestItem.find("ProgramParams/Uplimit")
        Max = float(MaxElement.text) if MaxElement is not None else ""

        row_data = [ID, Min, Value, Max]
        data.append(row_data)

    return data
```

#### 2.2.1 get_limits_table() 函數

**功能**: 讀取 CSV 格式的限制表

**參數**:
- `limits_csv_filename`: CSV 文件路徑

**返回值**:
- `csv.reader` 對象（迭代器）

**實現細節**:

1. **文件讀取**:
   ```python
   with open(limits_csv_filename) as table_file:
       table_buffer = io.StringIO(table_file.read())
   ```

2. **為什麼使用 io.StringIO?**
   - 將文件內容讀入內存
   - 支持多次迭代（csv.reader 本身是單次迭代）
   - 創建緩存以便後續處理

3. **返回 csv.reader**:
   ```python
   return csv.reader(table_buffer)
   ```

**CSV 格式要求**:

根據 `test_point_map.py` 中的 `N_CSV_COLS = 7`，CSV 文件應包含至少 7 列：

| 列索引 | 字段名 | 說明 | 示例值 |
|--------|--------|------|--------|
| 0 | ID | 測試點唯一標識符 | Test_one |
| 1 | ItemKey | 項目鍵（單位） | bool |
| 2 | ValueType | 數值類型 | float, integer, string |
| 3 | LimitType | 限制類型 | both, upper, lower, equality, etc. |
| 4 | EqLimit | 相等限制 | 1, "PASS", etc. |
| 5 | LL (Lower Limit) | 下限 | 0.1 |
| 6 | UL (Upper Limit) | 上限 | 100 |

**示例 CSV 文件** (limits_altasSpec.csv):
```csv
ID,Units,ValueType,LimitType,EqLimit,LL,UL,Nominal,Comments,Description
Test_one,bool,float,both,,0.1,0.8,,,
Test_two,bool,float,upper,,,100,,,
Test_three,level,integer,equality,1,,,,,
```

**處理流程** (在 `new_test_point_map` 中):

```python
def new_test_point_map(limits_table):
    test_point_map = TestPointMap()
    for row in limits_table:
        # 1. 跳過空行
        if not row:
            continue

        # 2. 截取前 7 列
        row = row[:N_CSV_COLS]

        # 3. 跳過 LibreOffice Calc 的空行
        if row == ['', '', '', '', '', '', '']:
            continue

        # 4. 跳過標題行或註釋行
        if row[0] == 'ID' or row[0].startswith(';') or row[0].startswith('#'):
            continue

        # 5. 創建 TestPoint 對象
        test_point = TestPoint(*row)
        test_point_map.add_test_point(test_point)

    return test_point_map
```

**TestPoint 構造參數映射**:
```python
TestPoint(
    name=row[0],          # ID
    ItemKey=row[1],       # Units
    value_type=row[2],    # ValueType
    limit_type=row[3],    # LimitType
    equality_limit=row[4],# EqLimit
    lower_limit=row[5],   # LL
    upper_limit=row[6]    # UL
)
```

**數據類型映射**:

| ValueType | Python 類型 | 轉換方法 |
|-----------|-------------|----------|
| string | str | `str(value)` |
| integer | int | `int(value, 0)` (自動檢測進制) |
| float | float | `float(value)` |

| LimitType | 檢查邏輯 |
|-----------|----------|
| lower | `value >= lower_limit` |
| upper | `value <= upper_limit` |
| both | `lower_limit <= value <= upper_limit` |
| equality | `value == equality_limit` |
| partial | `equality_limit in value` |
| inequality | `value != equality_limit` |
| none | 總是返回 True |

#### 2.2.2 get_limits_data() 函數

**功能**: 讀取 XML 格式的限制數據

**參數**:
- `xml_file`: XML 文件路徑

**返回值**:
- `list` 包含 `[ID, Min, Value, Max]` 的列表

**XML 格式要求**:

```xml
<root>
  <TestItems>
    <TestItem1>
      <ProgramParams>
        <Lowlimit>0.1</Lowlimit>
        <Uplimit>0.8</Uplimit>
      </ProgramParams>
    </TestItem1>
    <TestItem2>
      <ProgramParams>
        <Lowlimit>0.5</Lowlimit>
        <Uplimit>1.0</Uplimit>
      </ProgramParams>
    </TestItem2>
  </TestItems>
</root>
```

**實現細節**:

1. **解析 XML**:
   ```python
   tree = ET.parse(xml_file)
   root = tree.getroot()
   ```

2. **遍歷 TestItems**:
   ```python
   for TestItem in root.findall('TestItems/*'):
       ID = TestItem.tag  # 使用標籤名作為 ID
   ```

3. **提取限制值** (帶 None 檢查):
   ```python
   MinElement = TestItem.find("ProgramParams/Lowlimit")
   Min = float(MinElement.text) if MinElement is not None else ""
   MaxElement = TestItem.find("ProgramParams/Uplimit")
   Max = float(MaxElement.text) if MaxElement is not None else ""
   ```

4. **構建數據行**:
   ```python
   row_data = [ID, Min, Value, Max]  # Value 始終為空字符串
   data.append(row_data)
   ```

**返回格式差異**:
- CSV 讀取器返回 `csv.reader` (7 列)
- XML 讀取器返回 `list` (4 列: ID, Min, Value, Max)

**使用狀態**:
- ❌ 當前代碼中未被使用
- 💡 預留給未來的 XML 配置支持

---

### 2.3 __init__.py - 模組初始化

#### 源代碼分析

```python

```

**說明**:
- 空文件
- 不導出任何符號
- 模組通過 `polish/__init__.py` 導出

**在 `polish/__init__.py` 中的導出**:
```python
from polish.mfg_config_readers.test_config_reader import get_test_config
from polish.mfg_config_readers.limits_table_reader import get_limits_table
```

---

### 2.4 limits_altasSpec.csv - 示例限制表

#### 內容分析

```csv
ID,Units,ValueType,LimitType,EqLimit,LL,UL,Nominal,Comments,Description
Test_one,bool,float,both,,0.1,0.8,,,
Test_two,bool,float,upper,,,100,,,
Test_three,level,integer,equality,1,,,,,
```

#### 數據解析

| 測試點 | ID | ItemKey | ValueType | LimitType | EqLimit | LL | UL | 說明 |
|--------|-----|---------|-----------|-----------|----------|-----|-----|------|
| Test_one | Test_one | bool | float | both | (空) | 0.1 | 0.8 | 雙邊限制測試 |
| Test_two | Test_two | bool | float | upper | (空) | (空) | 100 | 上限測試 |
| Test_three | Test_three | level | integer | equality | 1 | (空) | (空) | 相等測試 |

#### 生成的 TestPoint 對象

```python
# Test_one
TestPoint(
    name='Test_one',
    ItemKey='bool',
    value_type='float',
    limit_type='both',
    equality_limit='',
    lower_limit='0.1',
    upper_limit='0.8'
)

# Test_two
TestPoint(
    name='Test_two',
    ItemKey='bool',
    value_type='float',
    limit_type='upper',
    equality_limit='',
    lower_limit='',
    upper_limit='100'
)

# Test_three
TestPoint(
    name='Test_three',
    ItemKey='level',
    value_type='integer',
    limit_type='equality',
    equality_limit='1',
    lower_limit='',
    upper_limit=''
)
```

---

## 三、執行流程分析

### 3.1 CSV 限制表讀取流程

```
┌─────────────────────────────────────────────────────────────┐
│ 1. 文件讀取 (get_limits_table)                              │
├─────────────────────────────────────────────────────────────┤
│   打開 CSV 文件                                              │
│         ↓                                                   │
│   讀取文件內容到 StringIO                                    │
│         ↓                                                   │
│   創建 csv.reader 對象                                      │
│         ↓                                                   │
│   返回 csv.reader (迭代器)                                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. 數據解析 (new_test_point_map)                            │
├─────────────────────────────────────────────────────────────┤
│   遍歷 csv.reader 的每一行                                   │
│         ↓                                                   │
│   跳過空行                                                  │
│         ↓                                                   │
│   截取前 7 列 (N_CSV_COLS)                                  │
│         ↓                                                   │
│   跳過 LibreOffice 空行                                     │
│         ↓                                                   │
│   跳過標題行和註釋行                                         │
│         ↓                                                   │
│   創建 TestPoint(*row)                                      │
│         ↓                                                   │
│   添加到 TestPointMap                                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. TestPoint 初始化                                         │
├─────────────────────────────────────────────────────────────┤
│   解析參數:                                                 │
│   ├─ name (ID)                                             │
│   ├─ ItemKey                                               │
│   ├─ value_type → ValueType 類                             │
│   ├─ limit_type → LimitType 類                             │
│   ├─ equality_limit                                        │
│   ├─ lower_limit                                           │
│   └─ upper_limit                                           │
│         ↓                                                   │
│   初始化狀態:                                               │
│   ├─ executed = False                                      │
│   ├─ passed = None                                         │
│   └─ value = None                                          │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 XML 限制表讀取流程

```
┌─────────────────────────────────────────────────────────────┐
│ 1. 文件解析 (get_limits_data)                               │
├─────────────────────────────────────────────────────────────┤
│   解析 XML 文件                                             │
│         ↓                                                   │
│   獲取根元素                                                │
│         ↓                                                   │
│   遍歷 TestItems/* (所有子元素)                             │
│         ↓                                                   │
│   提取 ID (標籤名)                                          │
│         ↓                                                   │
│   提取 Lowlimit (ProgramParams/Lowlimit)                    │
│   提取 Uplimit (ProgramParams/Uplimit)                      │
│         ↓                                                   │
│   轉換為 float 或空字符串                                    │
│         ↓                                                   │
│   構建 [ID, Min, Value, Max]                               │
│         ↓                                                   │
│   返回 list                                                │
└─────────────────────────────────────────────────────────────┘
```

---

## 四、關鍵設計模式

### 4.1 代理模式 (Proxy)

**應用**: `test_config_reader.py`

```python
def get_test_config(test_conf_filename):
    return load_and_read_config(test_conf_filename)
```

**目的**:
- 簡化接口
- 隱藏實現細節
- 統一訪問點

### 4.2 適配器模式 (Adapter)

**應用**: `get_limits_data()` (XML → 統一格式)

**目的**:
- 將 XML 格式適配為內部使用的列表格式
- 支持多種配置格式

### 4.3 迭代器模式 (Iterator)

**應用**: `csv.reader` 返回值

**優點**:
- 延遲加載
- 內存效率高
- 支持流式處理

### 4.4 工廠模式 (Factory)

**應用**: `new_test_point_map()`

**目的**:
- 從配置文件批量創建 TestPoint 對象
- 封裝對象創建邏輯

---

## 五、技術棧

### 文件格式
- **INI**: ConfigParser (測試配置)
- **CSV**: csv 模組 (限制表)
- **XML**: xml.etree.ElementTree (限制數據)

### 數據結構
- **io.StringIO**: 內存文件緩沖
- **csv.reader**: CSV 行迭代器
- **list**: 數據行列表

### 依賴模組
- `polish.mfg_common.config_reader`: 配置讀取基礎
- `polish.test_point.test_point`: TestPoint 定義
- `polish.test_point.test_point_map`: TestPointMap 定義

---

## 六、擴展點

### 6.1 新增配置格式

在 `limits_table_reader.py` 添加新函數:

```python
def get_limits_json(json_file):
    """讀取 JSON 格式的限制表"""
    import json
    with open(json_file, 'r') as f:
        data = json.load(f)

    result = []
    for item in data:
        row = [
            item['ID'],
            item['ItemKey'],
            item['ValueType'],
            item['LimitType'],
            item.get('EqLimit', ''),
            item.get('LL', ''),
            item.get('UL', '')
        ]
        result.append(row)

    return result
```

### 6.2 新增配置字段

修改 `N_CSV_COLS` 常量:
```python
# test_point_map.py
N_CSV_COLS = 10  # 增加到 10 列
```

更新 TestPoint 構造函數:
```python
def __init__(
    self,
    name,
    ItemKey,
    value_type,
    limit_type,
    equality_limit=None,
    lower_limit=None,
    upper_limit=None,
    nominal=None,      # 新增
    comments=None,     # 新增
    description=None   # 新增
):
    self.nominal = nominal
    self.comments = comments
    self.description = description
```

### 6.3 增強錯誤處理

```python
def get_limits_table(limits_csv_filename):
    """讀取 CSV 格式的限制表（增強版）"""
    try:
        with open(limits_csv_filename, encoding='utf-8') as table_file:
            table_buffer = io.StringIO(table_file.read())
        return csv.reader(table_buffer)
    except FileNotFoundError:
        raise ConfigError(f"限制表文件不存在: {limits_csv_filename}")
    except UnicodeDecodeError:
        raise ConfigError(f"限制表文件編碼錯誤: {limits_csv_filename}")
    except Exception as e:
        raise ConfigError(f"讀取限制表失敗: {str(e)}")
```

### 6.4 配置驗證

```python
def validate_limits_table(limits_table):
    """驗證限制表的完整性"""
    required_columns = 7
    errors = []

    for i, row in enumerate(limits_table, 1):
        if len(row) < required_columns:
            errors.append(f"第 {i} 行: 列數不足（需要 {required_columns} 列）")
            continue

        id, item_key, value_type, limit_type = row[:4]

        if not id:
            errors.append(f"第 {i} 行: ID 不能為空")

        if value_type not in VALUE_TYPE_MAP:
            errors.append(f"第 {i} 行: 無效的 ValueType '{value_type}'")

        if limit_type not in LIMIT_TYPE_MAP:
            errors.append(f"第 {i} 行: 無效的 LimitType '{limit_type}'")

    return errors
```

---

## 七、潛在改進區域

### 7.1 代碼重構

**問題**: `test_config_reader.py` 過於簡單

**建議**: 考慮是否需要保留此文件，直接使用 `load_and_read_config`

**選項**:
1. 保留代理，提供更好的抽象
2. 移除代理，直接使用底層函數
3. 增強功能，添加測試配置驗證

### 7.2 CSV 處理優化

**問題**: 使用 StringIO 可能不必要

**建議**:
```python
def get_limits_table(limits_csv_filename):
    """優化版本：直接返回 csv.reader"""
    with open(limits_csv_filename) as table_file:
        reader = csv.reader(table_file)
        # 如果需要多次迭代，轉換為列表
        # return list(reader)
        return reader
```

**優點**:
- 減少內存使用
- 更簡潔
- 避免不必要的複制

### 7.3 XML 讀取器改進

**問題**: `get_limits_data()` 未被使用

**建議**:
1. 與 CSV 讀取器統一接口
2. 返回相同格式的數據 (7 列)
3. 添加使用文檔和測試

```python
def get_limits_data(xml_file):
    """讀取 XML 格式的限制數據（統一格式）"""
    tree = ET.parse(xml_file)
    root = tree.getroot()

    data = []

    for TestItem in root.findall('TestItems/*'):
        ID = TestItem.tag
        MinElement = TestItem.find("ProgramParams/Lowlimit")
        Min = MinElement.text if MinElement is not None else ""
        MaxElement = TestItem.find("ProgramParams/Uplimit")
        Max = MaxElement.text if MaxElement is not None else ""

        # 統一為 7 列格式
        row_data = [ID, "", "float", "both", "", Min, Max]
        data.append(row_data)

    return data
```

### 7.4 錯誤處理增強

**問題**: 缺少異常處理

**建議**:
- 添加文件不存在錯誤處理
- 添加格式錯誤處理
- 提供詳細的錯誤消息

```python
class ConfigError(Exception):
    pass

def get_limits_table(limits_csv_filename):
    try:
        with open(limits_csv_filename, encoding='utf-8') as table_file:
            return csv.reader(table_file)
    except FileNotFoundError:
        raise ConfigError(f"限制表文件不存在: {limits_csv_filename}")
    except csv.Error as e:
        raise ConfigError(f"CSV 解析錯誤: {str(e)}")
```

### 7.5 文檔改進

**問題**: 缺少 docstrings 和使用示例

**建議**:
```python
def get_limits_table(limits_csv_filename):
    """
    讀取 CSV 格式的限制表

    Args:
        limits_csv_filename (str): CSV 文件路徑

    Returns:
        csv.reader: CSV 行迭代器

    Raises:
        ConfigError: 文件不存在或格式錯誤

    Example:
        >>> limits_table = get_limits_table('limits.csv')
        >>> test_point_map = new_test_point_map(limits_table)
    """
    # 實現
```

### 7.6 類型提示

**問題**: 缺少類型提示

**建議**:
```python
from typing import Iterator, List, Any
import csv

def get_limits_table(limits_csv_filename: str) -> csv.reader:
    """讀取 CSV 格式的限制表"""
    pass

def get_limits_data(xml_file: str) -> List[List[Any]]:
    """讀取 XML 格式的限制數據"""
    pass
```

### 7.7 配置緩存

**問題**: 重複讀取相同配置文件

**建議**:
```python
from functools import lru_cache

@lru_cache(maxsize=32)
def get_limits_table(limits_csv_filename: str) -> csv.reader:
    """讀取 CSV 格式的限制表（帶緩存）"""
    with open(limits_csv_filename) as table_file:
        return list(csv.reader(table_file))
```

### 7.8 單元測試

**問題**: 缺少測試

**建議**:
```python
import pytest
import tempfile
import os

def test_get_limits_table():
    """測試 CSV 讀取"""
    content = """ID,Units,ValueType,LimitType,EqLimit,LL,UL
Test_one,bool,float,both,,0.1,0.8"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(content)
        temp_file = f.name

    try:
        reader = get_limits_table(temp_file)
        rows = list(reader)
        assert len(rows) == 2
        assert rows[1][0] == 'Test_one'
    finally:
        os.unlink(temp_file)
```

---

## 八、關鍵文件索引

| 文件路徑 | 行數 | 核心功能 | 依賴 |
|----------|------|----------|------|
| `polish/mfg_config_readers/__init__.py` | 1 | 模組初始化 | 無 |
| `polish/mfg_config_readers/test_config_reader.py` | 5 | 測試配置讀取 | mfg_common.config_reader |
| `polish/mfg_config_readers/limits_table_reader.py` | 38 | 限制表讀取 (CSV/XML) | csv, xml.etree.ElementTree |
| `polish/mfg_config_readers/limits_altasSpec.csv` | 5 | 示例限制表 | 無 |

---

## 九、使用示例

### 9.1 CSV 限制表使用

```python
from polish import default_setup, default_teardown
from polish import Measurement, MeasurementList

# 1. 設置（讀取限制表）
logger, test_point_map, meas_assets = default_setup('limits.csv')

# 2. 創建測量
class MyMeasurement(Measurement):
    test_point_uids = ('Test_one', 'Test_two')

    def measure(self):
        # 測試 Test_one (0.1 <= value <= 0.8)
        value1 = 0.5
        self.test_points.Test_one.execute(value1, "OFF", True)

        # 測試 Test_two (value <= 100)
        value2 = 50.0
        self.test_points.Test_two.execute(value2, "OFF", True)

# 3. 執行
measurement_list = MeasurementList()
measurement_list.add(MyMeasurement(meas_assets))
measurement_list.run_measurements()

# 4. 清理
default_teardown()
```

### 9.2 直接使用讀取器

```python
from polish.mfg_config_readers import get_limits_table
from polish.test_point.test_point_map import new_test_point_map

# 讀取限制表
limits_table = get_limits_table('limits.csv')

# 創建測試點映射
test_point_map = new_test_point_map(limits_table)

# 訪問測試點
test_point = test_point_map.get_test_point('Test_one')
print(f"Test Point: {test_point.name}")
print(f"Lower Limit: {test_point.lower_limit}")
print(f"Upper Limit: {test_point.upper_limit}")
```

### 9.3 測試配置使用

```python
from polish.mfg_config_readers import get_test_config

# 讀取測試配置
test_config = get_test_config('test_atlas.ini')

# 訪問配置
section = test_config.testspec
timeout = section.timeout
station = section.station
mode = section.mode
```

### 9.4 XML 限制表使用（未激活）

```python
from polish.mfg_config_readers import get_limits_data

# 讀取 XML 限制數據
limits_data = get_limits_data('limits.xml')

# 數據格式: [[ID, Min, Value, Max], ...]
for row in limits_data:
    id, min_val, value, max_val = row
    print(f"ID: {id}, Range: [{min_val}, {max_val}]")
```

---

## 十、總結

**mfg_config_readers** 是配置讀取模組，具有以下特點：

### 優點
✅ 支持多種配置格式 (INI, CSV, XML)
✅ 簡潔的接口設計
✅ 靈活的擴展性
✅ 與 TestPoint 系統良好集成

### 需要改進
⚠️ 缺少異常處理
⚠️ 缺少單元測試
⚠️ 文檔不完善
⚠️ XML 讀取器未使用
⚠️ 潛在的性能優化空間

### 適用場景
- ✅ 測試計劃配置
- ✅ 測試限制定義
- ✅ 測試參數管理
- ✅ 測試點映射創建

### 核心流程
```
配置文件 → 讀取器 → 解析 → TestPoint → TestPointMap → 測量執行
```

---

## 十一、未來發展方向

### 11.1 配置格式統一

- 統一 CSV 和 XML 的返回格式
- 提供配置轉換工具
- 支持更多配置格式 (JSON, YAML)

### 11.2 配置驗證

- 添加架構驗證
- 數據類型檢查
- 依賴關係驗證

### 11.3 性能優化

- 配置緩存機制
- 延遲加載
- 並行處理

### 11.4 開發體驗

- 配置生成工具
- 配置編輯器
- 語法高亮和驗證

---

**文檔版本**: 1.0
**最後更新**: 2026-01-28
**分析者**: Claude Code
