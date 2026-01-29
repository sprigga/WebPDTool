# Polish mfg_common/ 模組詳細分析

> 分析日期: 2026-01-28
> 版本: PDTool4
> 目錄: `polish/mfg_common/`

---

## 📋 目錄

1. [目錄結構](#目錄結構)
2. [模組概述](#模組概述)
3. [各檔案詳細分析](#各檔案詳細分析)
4. [核心類別和函數](#核心類別和函數)
5. [設計模式](#設計模式)
6. [執行流程](#執行流程)
7. [使用示例](#使用示例)
8. [潛在改進區域](#潛在改進區域)
9. [技術棧總結](#技術棧總結)
10. [測試和驗證](#測試和驗證)

---

## 目錄結構

```
polish/mfg_common/
├── __init__.py                 # 模組初始化（空文件）
├── canister.py                 # 動態屬性字典類 (33 lines)
├── config_reader.py            # INI 配置讀取器 (80 lines)
├── deps.py                     # 依賴解析器 (74 lines)
├── constants.py                # 常量定義 (6 lines)
├── logging_setup.py            # 日誌設置 (189 lines)
└── path_utils.py               # 路徑工具 (16 lines)
```

**總行數**: 398 行（不含空行和註釋約 250 行）

---

## 模組概述

`mfg_common/` 是 Polish 測試框架的**製造通用工具模組**，提供以下核心功能：

| 功能 | 說明 | 主要檔案 |
|------|------|----------|
| 動態屬性字典 | 允許像對象屬性一樣訪問字典 | `canister.py` |
| 配置管理 | INI 配置文件的讀取和解析 | `config_reader.py` |
| 依賴解析 | 測量間依賴關係的管理 | `deps.py` |
| 日誌系統 | 項目日誌的設置和管理 | `logging_setup.py` |
| 路徑工具 | 路徑創建和驗證 | `path_utils.py` |
| 常量定義 | 全局常量和格式字符串 | `constants.py` |

### 核心特性

✅ **Canister 類**: 動態屬性字典，提供類似對象的訪問方式
✅ **配置讀取**: 自動類型轉換的 INI 解析器
✅ **依賴管理**: 使用 Python MRO 的依賴樹解析
✅ **日誌系統**: 支持文件和控制台的雙輸出日誌
✅ **標準輸出捕獲**: 捕獲並記錄 stdout/stderr 流
✅ **SVN 集成**: 自動獲取 SVN 版本信息

---

## 各檔案詳細分析

### 1. canister.py - 動態屬性字典

**檔案路徑**: `polish/mfg_common/canister.py`
**行數**: 33 行
**依賴**: 無

#### Canister 類

**目的**: 繼承自 `dict`，允許像對象屬性一樣訪問字典鍵

**實現代碼**:
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

**方法說明**:

| 方法 | 功能 | 參數 | 返回值 |
|------|------|------|--------|
| `__getattr__` | 獲取屬性 | `name` (str) | 字典中的值 |
| `__setattr__` | 設置屬性 | `name` (str), `value` (Any) | None |
| `__delattr__` | 刪除屬性 | `name` (str) | None |

**使用示例**:

```python
# 創建 Canister 實例
assets = Canister()

# 設置屬性（字典存儲）
assets.test_point_map = test_point_map
assets.instruments = instrument_list
assets.dut_comms = communication_handler

# 訪問屬性
print(assets.test_point_map)  # 相當於 assets['test_point_map']

# 刪除屬性
del assets.temp_value

# 繼承 dict 的所有功能
for key, value in assets.items():
    print(key, value)
```

**設計模式**:
- **Wrapper 模式**: 封裝 `dict` 提供更高級的接口
- **動態屬性訪問**: 通過魔術方法實現屬性式訪問

**優點**:
✅ 直觀的屬性訪問語法
✅ 保持字典的完整功能
✅ 輕量級實現（無額外依賴）

**限制**:
⚠️ 鍵名必須是合法的 Python 識別符
⚠️ 不能使用 `get()` 方法通過屬性訪問
⚠️ 屬性和字典方法可能衝突（如 `keys()`, `values()`）

---

### 2. config_reader.py - 配置讀取器

**檔案路徑**: `polish/mfg_common/config_reader.py`
**行數**: 80 行
**依賴**:
- `string`, `re` (標準庫)
- `configparser` (標準庫)
- `canister.py` (內部模組)

#### 核心函數

##### auto_cast_string(strValue)

**功能**: 自動將字符串轉換為最合適的類型

**實現**:
```python
def auto_cast_string(strValue):
    try:
        return int(strValue, 0)  # 支持多進制 (0x, 0b, 0)
    except ValueError:
        try:
            return float(strValue)
        except ValueError:
            return strValue  # 保持字符串
```

**轉換邏輯**:
```
字符串 → int (自動檢測進制) → float → 保持字符串
```

**示例**:
```python
auto_cast_string("123")        # 返回 123 (int)
auto_cast_string("0xFF")       # 返回 255 (int, 十六進制)
auto_cast_string("0b1010")     # 返回 10 (int, 二進制)
auto_cast_string("3.14")       # 返回 3.14 (float)
auto_cast_string("OK")         # 返回 "OK" (str)
auto_cast_string("true")       # 返回 "true" (str，不轉換為 bool)
```

**注意**: 不轉換布爾值字符串（"true", "false"）保持原樣

---

##### check_name(name)

**功能**: 驗證 INI 鍵名是否符合命名規則

**驗證規則**:
- 只允許大寫字母、數字、下劃線
- 正則表達式: `^[A-Z0-9_]+$`

**實現**:
```python
ID_FILTER_PATTERN = re.compile('^[A-Z0-9_]+$')

def check_name(name):
    if not re.search(ID_FILTER_PATTERN, name):
        raise IniNameError(name)
    return name
```

**異常**:
- `IniNameError`: 當鍵名不符合規則時拋出

**示例**:
```python
check_name("TEST_CONFIG")      # ✓ 通過
check_name("TEST_CONFIG_01")   # ✓ 通過
check_name("test_config")      # ✗ 拋出 IniNameError (小寫字母)
check_name("TEST-CONFIG")      # ✗ 拋出 IniNameError (連字符)
```

---

##### load_config(filename)

**功能**: 從文件加載 INI 配置

**參數**:
- `filename`: INI 文件路徑

**返回**: `ConfigParser` 實例

**異常**:
- `IniFileNotFound`: 當文件不存在或無法讀取時拋出

**實現**:
```python
def load_config(filename):
    ini = ConfigParser()
    ini.optionxform = str  # 不轉換選項名稱（保持原樣）
    if ini.read(filename):
        return ini
    else:
        raise IniFileNotFound(filename)
```

**特點**:
- `optionxform = str`: 保持鍵名的原始大小寫
- 不默認轉換為小寫

---

##### read_config(ini)

**功能**: 將 `ConfigParser` 對象轉換為嵌套的 Canister 結構

**參數**:
- `ini`: `ConfigParser` 實例

**返回**: `DefaultConfigCanister`（嵌套結構）

**輸出結構**:
```
config (DefaultConfigCanister)
└── section_name_1 (DefaultSectionCanister)
    ├── key_1: value_1 (auto-casted)
    ├── key_2: value_2 (auto-casted)
    └── key_3: value_3 (auto-casted)
└── section_name_2 (DefaultSectionCanister)
    └── ...
```

**實現**:
```python
def read_config(ini):
    config = DefaultConfigCanister()
    for section_name in ini.sections():
        section_name = check_name(section_name)  # 驗證節名
        section_canister = DefaultSectionCanister()
        config[section_name] = section_canister

        for item_name, item_value in ini.items(section_name):
            item_name = check_name(item_name)  # 驗證鍵名
            item_value = auto_cast_string(item_value)  # 自動類型轉換
            section_canister[item_name] = item_value

    return config
```

**示例**:

**輸入 INI** (`config.ini`):
```ini
[TEST_CONFIG]
timeout = 10
retry_count = 3
enable_debug = true
[INSTRUMENTS]
baud_rate = 9600
port = COM1
```

**輸出結構**:
```python
config = read_config(ini)

# 訪問
config.TEST_CONFIG.timeout        # 10 (int)
config.TEST_CONFIG.retry_count    # 3 (int)
config.TEST_CONFIG.enable_debug   # "true" (str)
config.INSTRUMENTS.baud_rate      # 9600 (int)
config.INSTRUMENTS.port           # "COM1" (str)
```

---

##### load_and_read_config(filename)

**功能**: 組合 `load_config` 和 `read_config` 的高級函數

**參數**:
- `filename`: INI 文件路徑

**返回**: `DefaultConfigCanister`（嵌套 Canister）

**實現**:
```python
def load_and_read_config(filename):
    ini = load_config(filename)
    return read_config(ini)
```

**使用示例**:
```python
# 一步加載和解析
config = load_and_read_config('test_xml.ini')

# 訪問配置
timeout = config.TEST_CONFIG.timeout
retry = config.TEST_CONFIG.retry_count
```

---

#### 自定義異常類

| 異常類 | 說明 | 拋出條件 |
|--------|------|----------|
| `IniNameError` | INI 鍵名錯誤 | 鍵名不符合命名規則 |
| `IniFileNotFound` | INI 文件未找到 | 文件不存在或無法讀取 |

---

### 3. deps.py - 依賴解析器

**檔案路徑**: `polish/mfg_common/deps.py`
**行數**: 74 行
**依賴**: 無

#### 設計理念

使用 **Python MRO (Method Resolution Order)** 來構建依賴樹，通過動態創建類實現依賴解析。

#### DepsResolver 類

**功能**: 依賴解析的 Mixin 基類

**關鍵方法**:

##### resolve_deps(cls)

**功能**: 解析類的依賴，創建動態解析類

**實現**:
```python
@classmethod
def resolve_deps(cls):
    # 創建動態依賴解析類
    cls.deps_resolver = type(
        cls.__name__ + '_deps_res',  # 類名: ClassName_deps_res
        tuple([i.deps_resolver for i in cls.deps]),  # 繼承所有依賴的 deps_resolver
        {}  # 無額外屬性
    )
    # 保存對原始類的引用
    cls.deps_resolver.owner = cls
    # 通過 MRO 獲取所有依賴的原始類
    cls.resolved_deps = [
        class_.owner
        for class_ in cls.deps_resolver.mro()
        if class_ not in (object, cls.deps_resolver)
    ]
```

**工作原理**:
1. 創建一個動態類，繼承所有依賴類的 `deps_resolver`
2. 通過 `mro()` 獲取方法解析順序（依賴順序）
3. 提取所有依賴的 `owner`（原始類）

---

##### define_deps(cls)

**功能**: 定義類的依賴關係（子類必須重寫）

**默認實現**:
```python
@classmethod
def define_deps(cls):
    cls.deps = tuple()
    raise NotImplementedError('Subclasses must override define_deps')
```

**子類實現**:
```python
class MeasurementB(DepsResolver):
    @classmethod
    def define_deps(cls):
        cls.deps = (MeasurementA,)  # 依賴 MeasurementA
```

---

#### resolve_deps(ordered_list_of_classes)

**功能**: 解析一系列類的依賴關係

**參數**:
- `ordered_list_of_classes`: 需要解析的類列表

**執行流程**:
```
1. 對每個類調用 define_deps()  # 定義依賴
2. 對每個類調用 resolve_deps()  # 解析依賴
```

**實現**:
```python
def resolve_deps(ordered_list_of_classes):
    for cls in ordered_list_of_classes:
        cls.define_deps()  # 第一輪：定義所有依賴
    for cls in ordered_list_of_classes:
        cls.resolve_deps()  # 第二輪：解析所有依賴
```

---

#### 依賴解析示例

**代碼示例**:
```python
from deps import DepsResolver, resolve_deps

class MeasurementA(DepsResolver):
    test_point_uids = ('test_a',)

    @classmethod
    def define_deps(cls):
        cls.deps = tuple()  # 無依賴

class MeasurementB(DepsResolver):
    test_point_uids = ('test_b',)

    @classmethod
    def define_deps(cls):
        cls.deps = (MeasurementA,)  # 依賴 A

class MeasurementC(DepsResolver):
    test_point_uids = ('test_c',)

    @classmethod
    def define_deps(cls):
        cls.deps = (MeasurementB,)  # 依賴 B (間接依賴 A)

# 解析依賴
resolve_deps([MeasurementA, MeasurementB, MeasurementC])

# 檢查解析結果
print(MeasurementA.resolved_deps)  # []
print(MeasurementB.resolved_deps)  # [<class '__main__.MeasurementA'>]
print(MeasurementC.resolved_deps)  # [<class '__main__.MeasurementB'>, <class '__main__.MeasurementA'>]
```

---

#### MRO 依賴樹圖示

```
原始類層次:

    A       B
     \     /
      \   /
       C
       |
       D

解析後的 deps_resolver 層次:

    A_deps_res     B_deps_res
        \           /
         \         /
          C_deps_res
              |
           D_deps_res

MRO (D_deps_res):
    D_deps_res
    → C_deps_res
    → B_deps_res
    → A_deps_res
    → object
```

---

#### 在 Polish 框架中的使用

**Measurement 基類**:
```python
# polish/measurement/measurement.py
from polish.mfg_common.deps import DepsResolver

class Measurement(DepsResolver):
    def run(self):
        # 獲取依賴的測量結果
        for dep_class in self.resolved_deps:
            # 訪問依賴類的測試結果
            pass
```

**子類定義依賴**:
```python
class PowerMeasurement(Measurement):
    test_point_uids = ('power_test',)

    def measure(self):
        # 執行測量
        pass

class VoltageMeasurement(Measurement):
    test_point_uids = ('voltage_test',)

    @classmethod
    def define_deps(cls):
        cls.deps = (PowerMeasurement,)  # 依賴電源測量

    def measure(self):
        # 使用 PowerMeasurement 的結果
        pass
```

---

#### 優點和限制

**優點**:
✅ 自動處理複雜依賴
✅ 支持多層依賴
✅ 使用標準 MRO 機制
✅ 類層級方法，實例無需調用

**限制**:
⚠️ 依賴關係在類定義時確定
⚠️ 不能運行時修改依賴
⚠️ 循環依賴會導致錯誤
⚠️ 需要提前知道所有測量類

---

### 4. constants.py - 常量定義

**檔案路徑**: `polish/mfg_common/constants.py`
**行數**: 6 行
**依賴**: 無

#### 常量列表

| 常量 | 值 | 用途 |
|------|-----|------|
| `DATE_TIME_FORMAT` | `'%y-%m-%d_%H:%M:%S'` | 日誌文件日期時間格式 |
| `PROJECT_NAME` | `'polish'` | 項目名稱（日誌前綴） |
| `LOG_FORMAT_STRING` | `'%(asctime)s,%(levelname)s %(message)s'` | 基礎日誌格式 |
| `VERBOSE_LOG_FORMAT_STRING` | `'%(asctime)s,%(levelname)s,%(module)s:%(lineno)d:%(funcName)s %(message)s'` | 詳細日誌格式 |
| `DEFAULT_LOG_PATH` | `'logs'` | 默認日誌目錄 |

#### 格式說明

**DATE_TIME_FORMAT**:
```python
'%y-%m-%d_%H:%M:%S'  # 示例: 26-01-28_14:30:45
# %y: 兩位年份
# %m: 月份 (01-12)
# %d: 日期 (01-31)
# %H: 小時 (00-23)
# %M: 分鐘 (00-59)
# %S: 秒 (00-59)
```

**LOG_FORMAT_STRING**:
```python
'%(asctime)s,%(levelname)s %(message)s'
# 示例: 2026-01-28 14:30:45,123,INFO Starting test
# asctime: 時間戳
# levelname: 日誌級別 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
# message: 日誌消息
```

**VERBOSE_LOG_FORMAT_STRING**:
```python
'%(asctime)s,%(levelname)s,%(module)s:%(lineno)d:%(funcName)s %(message)s'
# 示例: 2026-01-28 14:30:45,123,INFO,test_measurement:123:measure Test passed
# module: 模組名稱
# lineno: 行號
# funcName: 函數名稱
```

#### 使用示例

```python
from polish.mfg_common.constants import (
    DATE_TIME_FORMAT,
    PROJECT_NAME,
    LOG_FORMAT_STRING,
    VERBOSE_LOG_FORMAT_STRING,
    DEFAULT_LOG_PATH
)

# 使用常量
log_filename = time.strftime(DATE_TIME_FORMAT) + '.log'
project_logger = logging.getLogger(PROJECT_NAME)
```

---

### 5. logging_setup.py - 日誌設置

**檔案路徑**: `polish/mfg_common/logging_setup.py`
**行數**: 189 行
**依賴**:
- `os`, `io`, `sys` (標準庫)
- `time`, `logging`, `threading` (標準庫)
- `configparser` (標準庫)
- `subprocess` (標準庫)

#### 重定義的常量

```python
DATE_TIME_FORMAT = '%y-%m-%d_%H_%M_%S'  # 與 constants.py 不同！
PROJECT_NAME = 'DAQ973A_test'            # 與 constants.py 不同！
LOG_FORMAT_STRING = '%(asctime)s - %(levelname)s - %(message)s'
VERBOSE_LOG_FORMAT_STRING = '%(asctime)s - %(levelname)s - %(message)s'
```

**注意**: 這些常量與 `constants.py` 定義不同，造成不一致。建議統一使用 `constants.py`。

#### 核心函數

##### get_model_name_from_ini_file(ini_file)

**功能**: 從 INI 文件中獲取型號名稱

**實現**:
```python
def get_model_name_from_ini_file(ini_file):
    config = configparser.ConfigParser()
    config.read(ini_file)
    model_path = config.get('testspec', 'limits_atlas')
    model_name = os.path.basename(os.path.dirname(model_path))
    return model_name
```

**示例**:

INI 文件 (`test_xml.ini`):
```ini
[testspec]
limits_atlas = testPlan\BelugaB\A2B_testPlan.csv
```

調用:
```python
model_name = get_model_name_from_ini_file('test_xml.ini')
# 返回: "BelugaB"
```

---

##### get_logger(name, project_name=PROJECT_NAME)

**功能**: 獲取項目日誌記錄器

**參數**:
- `name`: 日誌記錄器名稱
- `project_name`: 項目名稱（默認為 `PROJECT_NAME`）

**返回**: `logging.Logger` 實例

**實現**:
```python
def get_logger(name, project_name=PROJECT_NAME):
    return logging.getLogger('.'.join((PROJECT_NAME, name)))
```

**示例**:
```python
logger = get_logger('test_measurement')
# logger.name = "DAQ973A_test.test_measurement"
```

---

##### add_formatter(handler, format_string=VERBOSE_LOG_FORMAT_STRING)

**功能**: 為日誌處理器添加格式化器

**參數**:
- `handler`: 日誌處理器（FileHandler, StreamHandler）
- `format_string`: 格式字符串（默認為詳細格式）

**實現**:
```python
def add_formatter(handler, format_string=VERBOSE_LOG_FORMAT_STRING):
    fmtr = logging.Formatter(format_string)
    fmtr.converter = time.localtime  # 使用本地時間
    handler.setFormatter(fmtr)
```

---

##### detect_default_log_location(default_path=DEFAULT_LOG_PATH)

**功能**: 檢測並創建日誌目錄

**參數**:
- `default_path`: 默認日誌路徑

**返回**: `bool` - 目錄是否存在

**實現**:
```python
def detect_default_log_location(default_path=DEFAULT_LOG_PATH):
    abs_path = os.path.abspath(default_path)
    if not os.path.exists(abs_path):
        os.makedirs(abs_path)
    return os.path.exists(os.path.abspath(default_path))
```

---

##### init_project_logger(project_name=PROJECT_NAME)

**功能**: 初始化項目日誌系統

**執行流程**:
```
1. 從 SN_file.txt 讀取序列號
2. 創建項目日誌記錄器
3. 創建 StdStreamsCaptureHandler (捕獲 stdout/stderr)
4. 從 test_xml.ini 獲取型號名稱
5. 創建日誌目錄結構:
   logs/
   └── {model_name}/
       └── {YYYYMMDD}/
           └── {SN}_{timestamp}.txt
6. 添加文件和控制台處理器
7. 獲取 SVN 版本並記錄
8. 返回項目日誌記錄器
```

**日誌目錄結構**:
```
{DEFAULT_LOG_PATH}/                    # 從 test_xml.ini 讀取
└── {model_name}/                      # 型號名稱 (如 "BelugaB")
    └── {YYYYMMDD}/                    # 日期 (如 "20260128")
        └── {SN}_{timestamp}.txt       # 日誌文件 (如 "SN12345_26-01-28_14_30_45.txt")
```

**實現**:
```python
def init_project_logger(project_name=PROJECT_NAME):
    global handler
    f = open('SN_file.txt', 'r')
    SN = f.read()

    project_logger = logging.getLogger(project_name)
    project_logger.setLevel(logging.INFO)

    # 創建標準輸出捕獲處理器
    handler = StdStreamsCaptureHandler(project_logger)

    # 從 INI 獲取型號名稱
    model_name = get_model_name_from_ini_file('test_xml.ini')

    if detect_default_log_location():
        # 創建日誌目錄結構
        model_dir = os.path.join(DEFAULT_LOG_PATH, model_name)
        if not os.path.exists(model_dir):
            os.makedirs(model_dir)

        date_dir = os.path.join(model_dir, time.strftime('%Y%m%d'))
        if not os.path.exists(date_dir):
            os.makedirs(date_dir)

        # 創建日誌文件
        log_file_name = '_'.join((SN, time.strftime(DATE_TIME_FORMAT, time.gmtime()))) + '.txt'
        log_file_path = os.path.join(date_dir, log_file_name)

        # 添加文件處理器
        fileHandler = logging.FileHandler(log_file_path)
        add_formatter(fileHandler, VERBOSE_LOG_FORMAT_STRING)
        add_formatter(handler, LOG_FORMAT_STRING)
        project_logger.addHandler(fileHandler)
    else:
        add_formatter(handler, VERBOSE_LOG_FORMAT_STRING)

    project_logger.addHandler(handler)
    project_logger.info('info')

    # 獲取 SVN 版本
    try:
        svn_revision = get_svn_revision()
    except:
        svn_revision = "cannot get SVN version"
    project_logger.info(f"PDtool SVN Revision: {svn_revision}")

    return project_logger
```

**參數**:
- `project_name`: 項目名稱（默認為 `PROJECT_NAME`）

**返回**: `logging.Logger` 實例

**全局變量**:
- `handler`: 保存 StdStreamsCaptureHandler 實例（用於清理）

---

##### deinit_project_logger()

**功能**: 清理日誌系統

**實現**:
```python
def deinit_project_logger():
    global handler
    handler.revert_stdout()  # 恢復原始 stdout/stderr
    handler.close()
```

---

##### get_svn_revision()

**功能**: 獲取 SVN 倉庫版本號

**實現**:
```python
def get_svn_revision():
    try:
        revision_number = find_svn_exe('svn_version.exe', 'svn info |find "Revision"')
        return revision_number.strip()
    except subprocess.CalledProcessError as e:
        revision_number = "Error"
        return revision_number
```

**異常處理**:
- 捕獲 `CalledProcessError`，返回 "Error"

---

##### find_svn_exe(executable_name, svninfo_cmd)

**功能**: 查找並執行 SVN 命令

**參數**:
- `executable_name`: SVN 可執行文件名稱
- `svninfo_cmd`: SVN 命令字符串

**實現**:
```python
def find_svn_exe(executable_name, svninfo_cmd):
    executable_path = os.path.join(executable_name)

    if os.path.isfile(executable_path):
        # 直接執行可執行文件
        command = [executable_path]
        child_output = subprocess.check_output(command)
    else:
        # 執行 shell 命令
        output = subprocess.check_output(svninfo_cmd, shell=True, universal_newlines=True)
        revision_line = next(line for line in output.splitlines() if "Revision" in line)
        revision_number = revision_line.split(":")[1].strip()
        return revision_number

    # 解碼輸出
    child_output = child_output.decode(encoding="utf-8", errors='ignore')
    return child_output
```

**支持兩種方式**:
1. 直接執行 `svn_version.exe`（如果存在）
2. 執行 shell 命令 `svn info | find "Revision"`

---

#### FakeStdStream 類

**目的**: 模擬標準流（用於捕獲 stdout/stderr）

**實現**:
```python
class FakeStdStream(io.TextIOBase):
    def flush(self):
        pass  # 不執行任何操作
```

**用途**: 替換 `sys.stdout` 和 `sys.stderr`，將所有輸出重定向到日誌。

---

#### StdStreamsCaptureHandler 類

**目的**: 捕獲並記錄標準輸出流（stdout/stderr）

**繼承**: `logging.StreamHandler`

**初始化**:
```python
def __init__(self, root_logger):
    self.lock = threading.RLock()          # 線程鎖
    self.is_a_log = threading.Event()       # 日誌標誌
    self.is_a_log.clear()

    self.capture_logger = root_logger.getChild('stream_capture')
    self._stdout = sys.stdout              # 保存原始 stdout
    self._stderr = sys.stderr              # 保存原始 stderr

    self.new_stdout = FakeStdStream()
    self.new_stderr = FakeStdStream()

    # 重定向寫入方法
    self.new_stdout.write = self.stream_capture
    self.new_stderr.write = self.stream_capture

    # 替換系統流
    sys.stdout = self.new_stdout
    sys.stderr = self.new_stderr

    logging.StreamHandler.__init__(self, self.new_stdout)
```

**屬性**:

| 屬性 | 類型 | 說明 |
|------|------|------|
| `lock` | `threading.RLock` | 線程安全鎖 |
| `is_a_log` | `threading.Event` | 標識是否正在記錄日誌 |
| `capture_logger` | `logging.Logger` | 專用捕獲日誌記錄器 |
| `_stdout` | `file-like` | 保存的原始 stdout |
| `_stderr` | `file-like` | 保存的原始 stderr |
| `new_stdout` | `FakeStdStream` | 替換的 stdout |
| `new_stderr` | `FakeStdStream` | 替換的 stderr |

---

##### rstrip_last_linesep(text)

**功能**: 移除字符串末尾的換行符

**實現**:
```python
def rstrip_last_linesep(self, text):
    return text.rstrip('\r\n')
```

---

##### stream_capture(text)

**功能**: 捕獲並記錄標準輸出流

**參數**:
- `text`: 輸出文本

**邏輯**:
```python
def stream_capture(self, text):
    with self.lock:  # 線程安全
        if self.is_a_log.is_set():
            # 如果正在記錄日誌，寫入原始 stdout
            self._stdout.write(text)
        else:
            # 否則，記錄到日誌
            if text.strip():
                text = self.rstrip_last_linesep(text)
                self.capture_logger.info(text)
```

**特點**:
- 遞歸防止：檢測 `is_a_log` 標誌，避免日誌消息被重新捕獲
- 空字符串過濾：只記錄非空文本
- 線程安全：使用 `RLock` 保護

---

##### emit(record)

**功能**: 發送日誌記錄（重寫 `StreamHandler.emit`）

**參數**:
- `record`: `logging.LogRecord` 實例

**實現**:
```python
def emit(self, record):
    try:
        self.is_a_log.set()  # 設置日誌標誌
        logging.StreamHandler.emit(self, record)
    finally:
        self.is_a_log.clear()  # 清除日誌標誌
```

**用途**: 防止日誌消息被 `stream_capture` 重新捕獲（無限遞歸）。

---

##### revert_stdout()

**功能**: 恢復原始 stdout/stderr

**實現**:
```python
def revert_stdout(self):
    sys.stdout = self._stdout
    sys.stderr = self._stderr
```

---

#### 標準輸出捕獲流程圖

```
正常輸出流程:
    print("Hello") → sys.stdout.write("Hello") → 控制台

捕獲輸出流程:
    print("Hello")
        ↓
    sys.stdout.write("Hello")  (sys.stdout 已被替換為 new_stdout)
        ↓
    handler.stream_capture("Hello")
        ↓
    檢查 is_a_log
        ↓
    ┌─────────────────┐
    │ is_a_log=False? │ → capture_logger.info("Hello") → 日誌文件
    └─────────────────┘
        ↓ is_a_log=True
    _stdout.write("Hello") → 控制台

日誌記錄流程:
    logger.info("Log message")
        ↓
    handler.emit(record)
        ↓
    is_a_log.set()  # 設置標誌
        ↓
    StreamHandler.emit(record)
        ↓
    sys.stdout.write("Log message\n")  # 這次寫入會跳過捕獲
        ↓
    is_a_log.clear()  # 清除標誌
```

---

### 6. path_utils.py - 路徑工具

**檔案路徑**: `polish/mfg_common/path_utils.py`
**行數**: 16 行
**依賴**:
- `os` (標準庫)
- `errno` (標準庫)

#### setup_path(path)

**功能**: 創建目錄（如果不存在），忽略已存在錯誤

**參數**:
- `path`: 目錄路徑

**返回**: 絕對路徑字符串

**異常**:
- `OSError`: 當目錄創建失敗且不是"已存在"錯誤時拋出

**實現**:
```python
def setup_path(path):
    abspath = os.path.abspath(path)
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass  # 忽略已存在的目錄
        else:
            raise  # 重新拋出其他錯誤
    return abspath
```

**錯誤碼**:
- `errno.EEXIST`: 文件/目錄已存在

**示例**:
```python
from polish.mfg_common.path_utils import setup_path

# 第一次：創建目錄
log_dir = setup_path('logs/my_test')
# 返回: "/home/ubuntu/WebPDTool/PDTool4/logs/my_test"

# 第二次：目錄已存在
log_dir = setup_path('logs/my_test')
# 返回: "/home/ubuntu/WebPDTool/PDTool4/logs/my_test" (無錯誤)

# 錯誤情況：權限不足
log_dir = setup_path('/root/my_test')
# 拋出: OSError: [Errno 13] Permission denied
```

**優點**:
✅ 原子操作
✅ 線程安全（依賴 `os.makedirs`）
✅ 防止競爭條件（不使用 `if not os.path.exists: os.makedirs`）

---

## 核心類別和函數

### 類別總覽

| 類別 | 文件 | 父類 | 用途 |
|------|------|------|------|
| `Canister` | `canister.py` | `dict` | 動態屬性字典 |
| `DefaultConfigCanister` | `config_reader.py` | `Canister` | 配置根容器 |
| `DefaultSectionCanister` | `config_reader.py` | `Canister` | 配置節容器 |
| `DepsResolver` | `deps.py` | `object` | 依賴解析 Mixin |
| `FakeStdStream` | `logging_setup.py` | `io.TextIOBase` | 模擬標準流 |
| `StdStreamsCaptureHandler` | `logging_setup.py` | `logging.StreamHandler` | 標準輸出捕獲器 |

### 函數總覽

| 函數 | 文件 | 用途 |
|------|------|------|
| `auto_cast_string` | `config_reader.py` | 自動類型轉換 |
| `check_name` | `config_reader.py` | 驗證 INI 鍵名 |
| `load_config` | `config_reader.py` | 加載 INI 文件 |
| `read_config` | `config_reader.py` | 解析 ConfigParser |
| `load_and_read_config` | `config_reader.py` | 加載並解析 INI |
| `DepsResolver.resolve_deps` | `deps.py` | 解析類依賴 |
| `DepsResolver.define_deps` | `deps.py` | 定義依賴關係 |
| `resolve_deps` | `deps.py` | 解析多個類的依賴 |
| `get_model_name_from_ini_file` | `logging_setup.py` | 從 INI 獲取型號 |
| `get_logger` | `logging_setup.py` | 獲取日誌記錄器 |
| `add_formatter` | `logging_setup.py` | 添加日誌格式 |
| `detect_default_log_location` | `logging_setup.py` | 檢測日誌目錄 |
| `init_project_logger` | `logging_setup.py` | 初始化日誌系統 |
| `deinit_project_logger` | `logging_setup.py` | 清理日誌系統 |
| `get_svn_revision` | `logging_setup.py` | 獲取 SVN 版本 |
| `find_svn_exe` | `logging_setup.py` | 執行 SVN 命令 |
| `setup_path` | `path_utils.py` | 創建目錄 |

---

## 設計模式

### 1. Wrapper 模式 (Wrapper Pattern)

**應用**: `Canister` 類封裝 `dict`

```python
class Canister(dict):
    def __getattr__(self, name):
        if name in self:
            return self[name]
        else:
            raise AttributeError("No such attribute: %s" % name)
```

**特點**:
- 保持原有介面
- 添加新功能（屬性訪問）
- 繼承所有字典方法

---

### 2. Mixin 模式 (Mixin Pattern)

**應用**: `DepsResolver` 作為依賴解析的 Mixin 基類

```python
class DepsResolver(object):
    @classmethod
    def resolve_deps(cls):
        # 依賴解析邏輯
        pass

# 使用
class Measurement(DepsResolver):
    pass
```

**特點**:
- 提供可重用的功能
- 通過多繼承組合功能
- 不影響主類的繼承層次

---

### 3. Template Method 模式

**應用**: `DepsResolver.define_deps()` 定義依賴模板

```python
class DepsResolver(object):
    @classmethod
    def define_deps(cls):
        cls.deps = tuple()
        raise NotImplementedError('Subclasses must override define_deps')

class MyMeasurement(DepsResolver):
    @classmethod
    def define_deps(cls):
        cls.deps = (OtherMeasurement,)  # 子類實現
```

---

### 4. Factory 模式

**應用**: `load_and_read_config()` 創建配置對象

```python
def load_and_read_config(filename):
    ini = load_config(filename)
    return read_config(ini)  # 返回 Canister 實例
```

---

### 5. Adapter 模式

**應用**: `FakeStdStream` 適配標準流介面

```python
class FakeStdStream(io.TextIOBase):
    def flush(self):
        pass  # 最小化實現
```

---

### 6. Proxy 模式

**應用**: `StdStreamsCaptureHandler` 代理 `sys.stdout` 和 `sys.stderr`

```python
class StdStreamsCaptureHandler(logging.StreamHandler):
    def __init__(self, root_logger):
        self._stdout = sys.stdout  # 保存原始引用
        self._stderr = sys.stderr
        sys.stdout = self.new_stdout  # 替換
        sys.stderr = self.new_stderr
```

---

### 7. Singleton 模式

**應用**: 全局項目日誌記錄器

```python
def get_logger(name, project_name=PROJECT_NAME):
    return logging.getLogger('.'.join((PROJECT_NAME, name)))
```

`logging.getLogger()` 確保相同名稱返回同一實例。

---

## 執行流程

### 1. 配置加載流程

```
load_and_read_config('test_xml.ini')
    ↓
load_config('test_xml.ini')
    ↓
ConfigParser.read(filename)
    ↓
read_config(ini)
    ↓
遍歷所有 sections
    ↓
check_name(section_name)  # 驗證節名
    ↓
創建 DefaultSectionCanister
    ↓
遍歷所有 items
    ↓
check_name(item_name)  # 驗證鍵名
    ↓
auto_cast_string(item_value)  # 自動類型轉換
    ↓
返回 DefaultConfigCanister
```

---

### 2. 依賴解析流程

```
resolve_deps([MeasurementA, MeasurementB, MeasurementC])
    ↓
第一輪: define_deps()
    ├─ MeasurementA.define_deps() → deps = ()
    ├─ MeasurementB.define_deps() → deps = (MeasurementA,)
    └─ MeasurementC.define_deps() → deps = (MeasurementB,)
    ↓
第二輪: resolve_deps()
    ├─ MeasurementA.resolve_deps()
    │   └─ deps_resolver = type('MeasurementA_deps_res', (), {})
    │       resolved_deps = []
    ├─ MeasurementB.resolve_deps()
    │   └─ deps_resolver = type('MeasurementB_deps_res', (MeasurementA_deps_res,), {})
    │       resolved_deps = [MeasurementA]
    └─ MeasurementC.resolve_deps()
        └─ deps_resolver = type('MeasurementC_deps_res', (MeasurementB_deps_res,), {})
            resolved_deps = [MeasurementB, MeasurementA]
```

---

### 3. 日誌初始化流程

```
init_project_logger()
    ↓
讀取 SN_file.txt 獲取序列號
    ↓
創建 logging.Logger 實例
    ↓
創建 StdStreamsCaptureHandler (捕獲 stdout/stderr)
    ↓
get_model_name_from_ini_file('test_xml.ini')
    ↓
創建日誌目錄結構
    ├─ {DEFAULT_LOG_PATH}/{model_name}/{YYYYMMDD}/
    └─ 創建日誌文件: {SN}_{timestamp}.txt
    ↓
添加 FileHandler 和 StreamHandler
    ↓
獲取 SVN 版本
    ↓
返回 project_logger
```

---

### 4. 標準輸出捕獲流程

```
初始化階段:
    handler = StdStreamsCaptureHandler(logger)
        ↓
    保存 sys.stdout 和 sys.stderr
        ↓
    創建 FakeStdStream 並替換系統流
        ↓
    sys.stdout → handler.new_stdout
    sys.stderr → handler.new_stderr

運行階段:
    print("Hello")
        ↓
    sys.stdout.write("Hello")  (被替換為 new_stdout.write)
        ↓
    handler.stream_capture("Hello")
        ↓
    檢查 is_a_log 標誌
        ↓
    is_a_log=False? → capture_logger.info("Hello")
    is_a_log=True? → 原始 stdout.write("Hello")

日誌記錄階段:
    logger.info("Log message")
        ↓
    handler.emit(record)
        ↓
    is_a_log.set()  # 設置標誌
        ↓
    StreamHandler.emit(record)
        ↓
    sys.stdout.write("Log message\n")  (這次寫入會跳過捕獲)
        ↓
    is_a_log.clear()  # 清除標誌

清理階段:
    deinit_project_logger()
        ↓
    handler.revert_stdout()
        ↓
    恢復原始 sys.stdout 和 sys.stderr
        ↓
    handler.close()
```

---

## 使用示例

### 1. 使用 Canister 存儲測量資源

```python
from polish.mfg_common.canister import Canister

# 創建 Canister
meas_assets = Canister()

# 添加資源
meas_assets.test_point_map = test_point_map
meas_assets.instruments = instrument_list
meas_assets.dut_comms = communication_handler
meas_assets.config = config_data

# 訪問資源
print(meas_assets.test_point_map)

# 迭代所有資源
for key, value in meas_assets.items():
    print(f"{key}: {value}")
```

---

### 2. 讀取和解析 INI 配置

```python
from polish.mfg_common.config_reader import load_and_read_config

# 加載並解析 INI 文件
config = load_and_read_config('test_xml.ini')

# 訪問配置
timeout = config.TEST_CONFIG.timeout
retry_count = config.TEST_CONFIG.retry_count
enable_debug = config.TEST_CONFIG.enable_debug

# 自動類型轉換
print(type(timeout))        # <class 'int'>
print(type(retry_count))    # <class 'int'>
print(type(enable_debug))   # <class 'str'>
```

**輸入 INI** (`test_xml.ini`):
```ini
[TEST_CONFIG]
timeout = 10
retry_count = 3
enable_debug = true

[INSTRUMENTS]
baud_rate = 9600
port = COM1
```

---

### 3. 定義測量依賴關係

```python
from polish.measurement import Measurement
from polish.mfg_common.deps import resolve_deps

# 測量 A（無依賴）
class PowerMeasurement(Measurement):
    test_point_uids = ('power_test',)

    def measure(self):
        power = self.read_power()
        self.test_points.power_test.execute(power, "OFF", True)

    @classmethod
    def define_deps(cls):
        cls.deps = tuple()

# 測量 B（依賴 A）
class VoltageMeasurement(Measurement):
    test_point_uids = ('voltage_test',)

    def measure(self):
        # 獲取 PowerMeasurement 的結果
        power_measurement = self.resolved_deps[0]
        power_value = power_measurement.test_points.power_test.value

        voltage = self.read_voltage(power_value)
        self.test_points.voltage_test.execute(voltage, "OFF", True)

    @classmethod
    def define_deps(cls):
        cls.deps = (PowerMeasurement,)

# 測量 C（依賴 B）
class CurrentMeasurement(Measurement):
    test_point_uids = ('current_test',)

    def measure(self):
        # 獲取依賴的測量結果
        voltage_measurement = self.resolved_deps[0]
        power_measurement = self.resolved_deps[1]

        voltage = voltage_measurement.test_points.voltage_test.value
        power = power_measurement.test_points.power_test.value

        current = self.calculate_current(voltage, power)
        self.test_points.current_test.execute(current, "OFF", True)

    @classmethod
    def define_deps(cls):
        cls.deps = (VoltageMeasurement,)

# 解析依賴
resolve_deps([PowerMeasurement, VoltageMeasurement, CurrentMeasurement])

# 檢查解析結果
print(CurrentMeasurement.resolved_deps)
# [<class '__main__.VoltageMeasurement'>, <class '__main__.PowerMeasurement'>]
```

---

### 4. 初始化日誌系統

```python
from polish.mfg_common.logging_setup import (
    init_project_logger,
    deinit_project_logger,
    get_logger
)

# 初始化項目日誌
logger = init_project_logger()

# 記錄日誌
logger.info("Starting test")
logger.warning("Warning message")
logger.error("Error message")

# 獲取子日誌記錄器
test_logger = get_logger('test_measurement')
test_logger.info("Test measurement started")

# 輸出會被自動捕獲並記錄
print("This will be captured and logged")

# 清理日誌系統
deinit_project_logger()
```

---

### 5. 創建日誌目錄

```python
from polish.mfg_common.path_utils import setup_path

# 創建日誌目錄
log_dir = setup_path('logs/my_test')

# 創建嵌套目錄
test_dir = setup_path('data/test_results/20260128')

# 檢查返回值
import os
print(os.path.exists(log_dir))  # True
```

---

### 6. 完整測試流程示例

```python
from polish.mfg_common.config_reader import load_and_read_config
from polish.mfg_common.logging_setup import init_project_logger, deinit_project_logger
from polish.mfg_common.deps import resolve_deps
from polish.measurement import Measurement, MeasurementList

# 1. 加載配置
config = load_and_read_config('test_xml.ini')

# 2. 初始化日誌
logger = init_project_logger()
logger.info("Test started")

# 3. 定義測量類
class PowerMeasurement(Measurement):
    test_point_uids = ('power_test',)

    def measure(self):
        power = self.read_power()
        self.test_points.power_test.execute(power, "OFF", True)

    @classmethod
    def define_deps(cls):
        cls.deps = tuple()

class VoltageMeasurement(Measurement):
    test_point_uids = ('voltage_test',)

    def measure(self):
        voltage = self.read_voltage()
        self.test_points.voltage_test.execute(voltage, "OFF", True)

    @classmethod
    def define_deps(cls):
        cls.deps = (PowerMeasurement,)

# 4. 解析依賴
resolve_deps([PowerMeasurement, VoltageMeasurement])

# 5. 創建測量資源
from polish.mfg_common.canister import Canister
meas_assets = Canister()
meas_assets.config = config
meas_assets.logger = logger

# 6. 創建測量列表
measurement_list = MeasurementList()
measurement_list.add(PowerMeasurement(meas_assets))
measurement_list.add(VoltageMeasurement(meas_assets))

# 7. 執行測量
measurement_list.run_measurements()

# 8. 清理日誌
deinit_project_logger()
```

---

## 潛在改進區域

### 1. 常量定義不一致

**問題**: `constants.py` 和 `logging_setup.py` 定義了不同的常量

```python
# constants.py
DATE_TIME_FORMAT = '%y-%m-%d_%H:%M:%S'
PROJECT_NAME = 'polish'

# logging_setup.py
DATE_TIME_FORMAT = '%y-%m-%d_%H_%M_%S'  # 不同！
PROJECT_NAME = 'DAQ973A_test'  # 不同！
```

**影響**:
- 日誌文件名格式不一致
- 日誌記錄器名稱不一致
- 難以維護和調試

**建議**:
```python
# 統一使用 constants.py
from polish.mfg_common.constants import (
    DATE_TIME_FORMAT,
    PROJECT_NAME,
    LOG_FORMAT_STRING,
    VERBOSE_LOG_FORMAT_STRING
)

# 刪除 logging_setup.py 中的重複定義
```

---

### 2. 硬編碼配置

**問題**: 多處使用硬編碼文件名和路徑

```python
# logging_setup.py
f = open('SN_file.txt', 'r')  # 硬編碼
config.read('test_xml.ini')   # 硬編碼
```

**影響**:
- 靈活性低
- 難以在不同環境中使用
- 測試困難

**建議**:
```python
# 通過參數傳遞
def init_project_logger(
    project_name=PROJECT_NAME,
    sn_file='SN_file.txt',
    config_file='test_xml.ini'
):
    with open(sn_file, 'r') as f:
        SN = f.read()

    config = configparser.ConfigParser()
    config.read(config_file)
    # ...
```

---

### 3. 錯誤處理不完善

**問題**: 多處使用裸 `except` 語句

```python
# logging_setup.py
try:
    svn_revision = get_svn_revision()
except:
    svn_revision = "cannot get SVN version"
```

**影響**:
- 掩蓋了真正的錯誤
- 難以調試
- 不符合最佳實踐

**建議**:
```python
try:
    svn_revision = get_svn_revision()
except subprocess.CalledProcessError as e:
    logger.warning(f"Failed to get SVN revision: {e}")
    svn_revision = "cannot get SVN version"
except FileNotFoundError as e:
    logger.warning(f"SVN command not found: {e}")
    svn_revision = "cannot get SVN version"
except Exception as e:
    logger.error(f"Unexpected error getting SVN revision: {e}")
    svn_revision = "cannot get SVN version"
```

---

### 4. 全局變量使用

**問題**: `init_project_logger` 使用全局變量 `handler`

```python
def init_project_logger(project_name=PROJECT_NAME):
    global handler  # 全局變量
    handler = StdStreamsCaptureHandler(project_logger)
    # ...

def deinit_project_logger():
    global handler
    handler.revert_stdout()
```

**影響**:
- 線程不安全
- 難以同時初始化多個日誌系統
- 代碼耦合度高

**建議**:
```python
# 返回 handler 而非使用全局變量
def init_project_logger(project_name=PROJECT_NAME):
    handler = StdStreamsCaptureHandler(project_logger)
    # ...
    return project_logger, handler

def deinit_project_logger(handler):
    handler.revert_stdout()
    handler.close()

# 使用
logger, handler = init_project_logger()
# ...
deinit_project_logger(handler)
```

---

### 5. 缺少類型提示

**問題**: 所有函數和類都沒有類型提示

```python
def auto_cast_string(strValue):  # 缺少類型提示
    # ...

def load_config(filename):  # 缺少類型提示
    # ...
```

**影響**:
- IDE 自動完成不完整
- 類型錯誤無法在編譯時檢測
- 代碼可讀性降低

**建議**:
```python
from typing import Any, Optional, Dict

def auto_cast_string(strValue: str) -> Any:
    try:
        return int(strValue, 0)
    except ValueError:
        try:
            return float(strValue)
        except ValueError:
            return strValue

def load_config(filename: str) -> configparser.ConfigParser:
    ini = configparser.ConfigParser()
    # ...
    return ini

def read_config(ini: configparser.ConfigParser) -> Canister:
    # ...
    return config
```

---

### 6. SVN 依賴

**問題**: `get_svn_revision()` 假設項目使用 SVN

```python
def get_svn_revision():
    # 硬編碼 SVN 邏輯
    revision_number = find_svn_exe('svn_version.exe', 'svn info |find "Revision"')
    return revision_number.strip()
```

**影響**:
- 不支持 Git 等其他版本控制系統
- Windows 特定命令 (`find`)

**建議**:
```python
def get_vcs_revision():
    """獲取版本控制系統版本號（支持 SVN 和 Git）"""
    try:
        # 嘗試 Git
        import subprocess
        output = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], text=True)
        return f"git-{output.strip()}"
    except (FileNotFoundError, subprocess.CalledProcessError):
        pass

    try:
        # 嘗試 SVN
        output = subprocess.check_output(['svn', 'info'], shell=True, universal_newlines=True)
        revision_line = next(line for line in output.splitlines() if "Revision" in line)
        revision_number = revision_line.split(":")[1].strip()
        return f"svn-{revision_number}"
    except (FileNotFoundError, subprocess.CalledProcessError):
        pass

    return "unknown"
```

---

### 7. 日誌目錄結構硬編碼

**問題**: 日誌目錄結構硬編碼在 `init_project_logger` 中

```python
# 日誌目錄結構固定為: {model_name}/{YYYYMMDD}/{SN}_{timestamp}.txt
```

**影響**:
- 靈活性低
- 難以自定義

**建議**:
```python
def init_project_logger(
    project_name=PROJECT_NAME,
    log_structure='model/date/sn',  # 支持自定義
    **kwargs
):
    # log_structure:
    # - 'model/date/sn': {model}/{date}/{sn}_{time}.txt
    # - 'sn': {sn}_{time}.txt
    # - 'date/model': {date}/{model}_{time}.txt
    # ...
```

---

### 8. 缺少配置驗證

**問題**: `load_and_read_config` 不驗證配置文件內容

```python
def load_and_read_config(filename):
    ini = load_config(filename)
    return read_config(ini)  # 無驗證
```

**影響**:
- 無效配置可能導致運行時錯誤
- 缺少默認值
- 錯誤消息不明確

**建議**:
```python
def load_and_read_config(filename, schema=None):
    ini = load_config(filename)
    config = read_config(ini)

    # 驗證配置
    if schema:
        validate_config(config, schema)

    return config

def validate_config(config, schema):
    """驗證配置是否符合架構"""
    for section_name, section_schema in schema.items():
        if section_name not in config:
            raise ConfigError(f"Missing section: {section_name}")

        for key, (required, default) in section_schema.items():
            if required and key not in config[section_name]:
                raise ConfigError(f"Missing required key: {section_name}.{key}")

            if key not in config[section_name]:
                config[section_name][key] = default  # 設置默認值
```

---

### 9. 文檔不完整

**問題**: 大部分函數和類缺少 docstring

```python
def auto_cast_string(strValue):
    try:
        return int(strValue, 0)
    # ...
```

**影響**:
- 代碼可讀性低
- 難以維護
- IDE 支持不完整

**建議**:
```python
def auto_cast_string(strValue):
    """自動將字符串轉換為最合適的類型。

    Args:
        strValue: 要轉換的字符串

    Returns:
        轉換後的值（int, float, 或 str）

    Examples:
        >>> auto_cast_string("123")
        123
        >>> auto_cast_string("3.14")
        3.14
        >>> auto_cast_string("OK")
        'OK'
    """
    try:
        return int(strValue, 0)
    except ValueError:
        try:
            return float(strValue)
        except ValueError:
            return strValue
```

---

### 10. 缺少單元測試

**問題**: 所有模組都沒有單元測試

**影響**:
- 重構風險高
- Bug 難以發現
- 質量無法保證

**建議**:
創建 `tests/polish/mfg_common/` 目錄並添加測試：

```python
# tests/polish/mfg_common/test_canister.py
import pytest
from polish.mfg_common.canister import Canister

def test_canister_setattr():
    c = Canister()
    c.test = 123
    assert c['test'] == 123

def test_canister_getattr():
    c = Canister()
    c['test'] = 123
    assert c.test == 123

def test_canister_delattr():
    c = Canister()
    c.test = 123
    del c.test
    assert 'test' not in c

def test_canister_attribute_error():
    c = Canister()
    with pytest.raises(AttributeError):
        _ = c.nonexistent
```

```python
# tests/polish/mfg_common/test_config_reader.py
import pytest
from polish.mfg_common.config_reader import (
    auto_cast_string,
    load_and_read_config,
    IniNameError
)

def test_auto_cast_string_int():
    assert auto_cast_string("123") == 123

def test_auto_cast_string_float():
    assert auto_cast_string("3.14") == 3.14

def test_auto_cast_string_str():
    assert auto_cast_string("OK") == "OK"

def test_auto_cast_string_hex():
    assert auto_cast_string("0xFF") == 255

def test_auto_cast_string_binary():
    assert auto_cast_string("0b1010") == 10

def test_load_and_read_config():
    config = load_and_read_config('test_config.ini')
    assert hasattr(config, 'TEST_CONFIG')
    assert config.TEST_CONFIG.timeout == 10
```

---

## 技術棧總結

### 標準庫

| 模組 | 用途 | 文件 |
|------|------|------|
| `dict` | 字典基類 | `canister.py` |
| `io.TextIOBase` | 文本流基類 | `logging_setup.py` |
| `re` | 正則表達式 | `config_reader.py` |
| `string` | 字符串操作 | `config_reader.py` |
| `configparser` | INI 配置解析 | `config_reader.py`, `logging_setup.py` |
| `logging` | 日誌系統 | `logging_setup.py` |
| `threading` | 線程安全 | `logging_setup.py` |
| `time` | 時間處理 | `logging_setup.py` |
| `os` | 操作系統接口 | `logging_setup.py`, `path_utils.py` |
| `errno` | 錯誤碼 | `path_utils.py` |
| `sys` | 系統參數 | `logging_setup.py` |
| `subprocess` | 子進程 | `logging_setup.py` |

### 內部模組

| 模組 | 依賴文件 |
|------|----------|
| `canister` | 無 |
| `config_reader` | `canister` |
| `deps` | 無 |
| `constants` | 無 |
| `logging_setup` | 無（但重複定義了 constants.py 的內容） |
| `path_utils` | 無 |

### 依賴關係圖

```
config_reader
    └── canister

deps (獨立)

constants (獨立)

logging_setup (獨立，但應依賴 constants)

path_utils (獨立)
```

---

## 測試和驗證

### 建議的測試結構

```
tests/
└── polish/
    └── mfg_common/
        ├── __init__.py
        ├── test_canister.py
        ├── test_config_reader.py
        ├── test_deps.py
        ├── test_logging_setup.py
        └── test_path_utils.py
```

### 測試覆蓋率目標

| 模組 | 目標覆蓋率 | 優先級 |
|------|-----------|--------|
| `canister.py` | 100% | 高 |
| `config_reader.py` | 90% | 高 |
| `deps.py` | 85% | 中 |
| `logging_setup.py` | 70% | 中 |
| `path_utils.py` | 100% | 高 |

### 關鍵測試場景

#### 1. Canister 測試

```python
def test_canister_dict_methods():
    c = Canister()
    c.test1 = 123
    c.test2 = "abc"

    # 字典方法
    assert len(c) == 2
    assert 'test1' in c
    assert list(c.keys()) == ['test1', 'test2']

def test_canister_attribute_method_conflict():
    c = Canister()
    c.keys = "custom"
    assert c['keys'] == "custom"
    assert c.keys == "custom"  # 屬性訪問優先

def test_canister_with_dict_values():
    c = Canister()
    c.nested = {'a': 1, 'b': 2}
    assert c.nested['a'] == 1
```

---

#### 2. Config Reader 測試

```python
def test_load_config_file_not_found():
    with pytest.raises(IniFileNotFound):
        load_config('nonexistent.ini')

def test_check_name_invalid():
    with pytest.raises(IniNameError):
        check_name('invalid-name')

def test_read_config_auto_cast():
    # 創建臨時 INI 文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
        f.write('[TEST]\nint_val = 123\nfloat_val = 3.14\n')
        f.flush()

        config = load_and_read_config(f.name)
        assert isinstance(config.TEST.int_val, int)
        assert isinstance(config.TEST.float_val, float)

        os.unlink(f.name)
```

---

#### 3. Deps Resolver 測試

```python
def test_resolve_deps_no_deps():
    class A(DepsResolver):
        @classmethod
        def define_deps(cls):
            cls.deps = tuple()

    resolve_deps([A])
    assert A.resolved_deps == []

def test_resolve_deps_simple():
    class A(DepsResolver):
        @classmethod
        def define_deps(cls):
            cls.deps = tuple()

    class B(DepsResolver):
        @classmethod
        def define_deps(cls):
            cls.deps = (A,)

    resolve_deps([A, B])
    assert B.resolved_deps == [A]

def test_resolve_deps_transitive():
    class A(DepsResolver):
        @classmethod
        def define_deps(cls):
            cls.deps = tuple()

    class B(DepsResolver):
        @classmethod
        def define_deps(cls):
            cls.deps = (A,)

    class C(DepsResolver):
        @classmethod
        def define_deps(cls):
            cls.deps = (B,)

    resolve_deps([A, B, C])
    assert set(C.resolved_deps) == {A, B}

def test_resolve_deps_multiple():
    class A(DepsResolver):
        @classmethod
        def define_deps(cls):
            cls.deps = tuple()

    class B(DepsResolver):
        @classmethod
        def define_deps(cls):
            cls.deps = (A,)

    class C(DepsResolver):
        @classmethod
        def define_deps(cls):
            cls.deps = (A, B)

    resolve_deps([A, B, C])
    assert set(C.resolved_deps) == {A, B}
```

---

#### 4. Path Utils 測試

```python
def test_setup_path_create():
    with tempfile.TemporaryDirectory() as tmpdir:
        new_path = os.path.join(tmpdir, 'new_dir')
        result = setup_path(new_path)
        assert os.path.exists(result)
        assert os.path.isdir(result)

def test_setup_path_existing():
    with tempfile.TemporaryDirectory() as tmpdir:
        existing_path = tmpdir
        result = setup_path(existing_path)
        assert result == os.path.abspath(existing_path)

def test_setup_path_permission_error():
    with pytest.raises(OSError):
        setup_path('/root/test_dir')  # 假設無權限
```

---

## 總結

### mfg_common/ 模組核心價值

✅ **Canister 類**: 簡化字典訪問，提供類似對象的語法
✅ **配置管理**: 自動類型轉換的 INI 解析器
✅ **依賴解析**: 使用 Python MRO 的優雅依賴樹管理
✅ **日誌系統**: 支持標準輸出捕獲和結構化日誌
✅ **SVN 集成**: 自動獲取版本信息

### 優點

✅ 模組化設計清晰
✅ 代碼量少（398 行）
✅ 無外部依賴（僅使用標準庫）
✅ 設計模式應用合理
✅ 線程安全的日誌系統

### 需要改進

⚠️ 常量定義不一致（constants.py vs logging_setup.py）
⚠️ 硬編碼配置和路徑
⚠️ 錯誤處理不完善（裸 except）
⚠️ 全局變量使用（handler）
⚠️ 缺少類型提示
⚠️ SVN 特定依賴
⚠️ 缺少配置驗證
⚠️ 文檔不完整
⚠️ 缺少單元測試

### 適用場景

✅ 製造測試框架
✅ 配置驅動的應用
✅ 依賴關係複雜的測試
✅ 需要標準輸出捕獲的日誌系統

---

**文檔版本**: 1.0
**最後更新**: 2026-01-28
**分析者**: Claude Code
**參考文檔**: `docs/Polish_Analysis.md`
