# Polish Setup 模組分析

> 分析日期: 2026-01-28
> 版本: PDTool4
> 目錄: `polish/setup/`

---

## 📋 目錄結構

```
polish/setup/
├── __init__.py              # 模組導出（空文件）
└── default_setup.py         # 默認設置實現
```

---

## 一、模組概覽

**setup/** 模組是 Polish 測試框架的環境初始化和清理入口，負責：

- ✅ 初始化項目日誌系統
- ✅ 加載測試限制表（CSV 格式）
- ✅ 創建測試點映射
- ✅ 構建測量資源容器（Canister）
- ✅ 清理測試環境

**設計特點**：
- 採用工廠函數模式
- 集中式環境初始化
- 可擴展的資源容器

---

## 二、文件詳細分析

### 2.1 __init__.py

**狀態**: 空文件（1 行）

**用途**: Python 模組標識符，使 `polish/setup` 成為一個包

**導出**:
```python
# 在 polish/setup/__init__.py 中（目前為空）
# 可導出:
# - default_setup
# - default_teardown
```

---

### 2.2 default_setup.py

**文件大小**: 48 行
**核心功能**: 測試環境設置和清理

#### 2.2.1 導入模組

```python
from ..mfg_common.logging_setup import get_logger
from ..mfg_common.logging_setup import init_project_logger, deinit_project_logger
from ..mfg_config_readers.limits_table_reader import get_limits_table
from ..test_point.test_point_map import new_test_point_map
from ..mfg_common.canister import Canister
import time
```

**註釋掉的導入**（保留以備將來使用）:
```python
# from mfg_config_readers.env_config_reader import get_env_config
# from ..mfg_config_readers.test_config_reader import get_test_config
# from mfg_config_readers.env_config_reader import get_visa_instruments
# from mfg_config_readers.env_config_reader import get_dut_comms
# from mfg_config_readers.env_config_reader import get_flash_programmers
# from mfg_config_readers.env_config_reader import get_tester_ids
# from mfg_config_readers.env_config_reader import get_rec_printer
```

**設計說明**:
- 大部分環境配置讀取器被註釋，簡化當前實現
- 只保留了核心的日誌、限制表和測試點映射功能

---

#### 2.2.2 default_setup() 函數

**簽名**:
```python
def default_setup(limits_csv_filename):
    """初始化測試環境

    Args:
        limits_csv_filename (str): 限制表 CSV 文件路徑

    Returns:
        tuple: (polish_logger, test_point_map, meas_assets)
    """
```

**參數說明**:
| 參數 | 類型 | 說明 |
|------|------|------|
| `limits_csv_filename` | str | 限制表文件路徑（CSV 格式） |

**返回值**:
| 元素 | 類型 | 說明 |
|------|------|------|
| `polish_logger` | Logger | 項目日誌記錄器 |
| `test_point_map` | TestPointMap | 測試點映射容器 |
| `meas_assets` | Canister | 測量資源容器 |

---

#### 2.2.3 default_setup() 執行流程

```
┌─────────────────────────────────────────────────────────────┐
│ 1. 初始化項目日誌                                          │
├─────────────────────────────────────────────────────────────┤
│ polish_logger = init_project_logger()                       │
│     ↓                                                       │
│ - 讀取 SN_file.txt 獲取序列號                               │
│ - 從 test_xml.ini 讀取模型名稱                              │
│ - 創建日誌目錄: {LogPath}/{model_name}/{date}/             │
│ - 日誌文件名: {SN}_{timestamp}.txt                         │
│ - 捕獲 stdout/stderr 到日誌                               │
│ - 記錄 SVN 版本信息                                         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. 加載限制表                                              │
├─────────────────────────────────────────────────────────────┤
│ limits_table = get_limits_table(limits_csv_filename)       │
│     ↓                                                       │
│ - 讀取 CSV 文件                                             │
│ - 使用 csv.reader 解析                                      │
│ - 返回可迭代對象                                            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. 創建測試點映射                                          │
├─────────────────────────────────────────────────────────────┤
│ test_point_map = new_test_point_map(limits_table)          │
│     ↓                                                       │
│ - 遍歷限制表每一行                                          │
│ - 為每行創建 TestPoint 對象                                 │
│ - 將測試點添加到 TestPointMap                               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. 記錄測試點映射內容                                      │
├─────────────────────────────────────────────────────────────┤
│ map_content = str(test_point_map.get_dict())               │
│     ↓                                                       │
│ - 轉換為字符串（當前未使用）                                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. 創建測量資源容器                                        │
├─────────────────────────────────────────────────────────────┤
│ meas_assets = Canister()                                    │
│ meas_assets.test_point_map = test_point_map                │
│     ↓                                                       │
│ - 創建 Canister 動態屬性字典                               │
│ - 添加 test_point_map                                       │
│ - 可選添加: instruments, dut_comms, test_config 等         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. 返回資源                                                │
├─────────────────────────────────────────────────────────────┤
│ return polish_logger, test_point_map, meas_assets          │
└─────────────────────────────────────────────────────────────┘
```

---

#### 2.2.4 default_teardown() 函數

**簽名**:
```python
def default_teardown():
    """清理測試環境，恢復標準輸出"""
```

**執行步驟**:
```python
def default_teardown():
    # 恢復 sys.stdout 和 sys.stderr 到原始狀態
    deinit_project_logger()
```

**清理內容**:
1. 恢復 `sys.stdout` 到原始標準輸出
2. 恢復 `sys.stderr` 到原始標準錯誤輸出
3. 關閉日誌處理器

**依賴**: `deinit_project_logger()` from `mfg_common.logging_setup`

---

## 三、依賴模組分析

### 3.1 mfg_common.logging_setup

**關鍵功能**:

#### init_project_logger(project_name)

**功能**: 初始化項目日誌系統

**執行流程**:
```
1. 讀取 SN_file.txt 獲取序列號
2. 從 test_xml.ini [testspec] 獲取模型路徑
3. 解析模型名稱（路徑的目錄名）
4. 檢測並創建日誌目錄結構:
   {LogPath}/{model_name}/{date}/
5. 創建日誌文件:
   {SN}_{timestamp}.txt
6. 創建 StdStreamsCaptureHandler 捕獲標準輸出
7. 添加文件和控制台處理器
8. 記錄 SVN 版本信息
```

**日誌目錄結構**:
```
{LogPath}/                # 從 test_xml.ini [SfcConfig] LogPath 讀取
  └── {model_name}/       # 從 limits_atlas 路徑提取
      └── {YYYYMMDD}/     # 當前日期
          └── {SN}_{YY-MM-DD_HH_MM_SS}.txt
```

**日誌格式**:
```python
LOG_FORMAT_STRING = '%(asctime)s - %(levelname)s - %(message)s'
VERBOSE_LOG_FORMAT_STRING = '%(asctime)s - %(levelname)s - %(message)s'
```

**StdStreamsCaptureHandler 類**:
- 繼承自 `logging.StreamHandler`
- 攔截 `sys.stdout` 和 `sys.stderr`
- 自動記錄所有 print 輸出到日誌
- 避免日誌記錄時的循環問題

**關鍵方法**:
```python
def stream_capture(self, text):
    """捕獲標準輸出並記錄到日誌"""
    with self.lock:
        if self.is_a_log.is_set():
            self._stdout.write(text)  # 日誌系統輸出，直接寫入
        else:
            if text.strip():
                self.capture_logger.info(text)  # 記錄到日誌

def revert_stdout(self):
    """恢復原始的標準輸出"""
    sys.stdout = self._stdout
    sys.stderr = self._stderr
```

#### get_logger(name, project_name)

**功能**: 獲取命名日誌記錄器

**返回**: `logging.getLogger('{project_name}.{name}')`

---

### 3.2 mfg_config_readers.limits_table_reader

#### get_limits_table(limits_csv_filename)

**功能**: 讀取 CSV 限制表文件

**參數**:
- `limits_csv_filename`: CSV 文件路徑

**返回**: `csv.reader` 對象

**實現**:
```python
def get_limits_table(limits_csv_filename):
    with open(limits_csv_filename) as table_file:
        table_buffer = io.StringIO(table_file.read())
    return csv.reader(table_buffer)
```

**CSV 格式預期**:
```csv
ID, Name, Value_Type, Limit_Type, Equality_Limit, Lower_Limit, Upper_Limit, ...
```

#### get_limits_data(xml_file) （未使用）

**功能**: 從 XML 文件讀取限制數據

**返回**: 列表列表 `[[ID, Min, Value, Max], ...]`

**XML 結構預期**:
```xml
<TestItems>
    <Item1>
        <ProgramParams>
            <Lowlimit>0.0</Lowlimit>
            <Uplimit>10.0</Uplimit>
        </ProgramParams>
    </Item1>
</TestItems>
```

---

### 3.3 test_point.test_point_map

#### new_test_point_map(limits_table)

**功能**: 工廠函數，從限制表創建測試點映射

**參數**:
- `limits_table`: CSV reader 對象

**返回**: `TestPointMap` 對象

**處理邏輯**:
```
1. 遍歷限制表每一行
2. 跳過空行
3. 跳過註釋行（以 ; 或 # 開頭）
4. 跳過標題行（包含 "ID"）
5. 為有效行創建 TestPoint 對象
6. 將測試點添加到 TestPointMap
```

---

### 3.4 mfg_common.canister

#### Canister 類

**功能**: 動態屬性字典，支持點號訪問

**實現**:
```python
class Canister(dict):
    def __getattr__(self, name):
        if name in self:
            return self[name]
        else:
            raise AttributeError(f"No such attribute: {name}")

    def __setattr__(self, name, value):
        self[name] = value

    def __delattr__(self, name):
        if name in self:
            del self[name]
        else:
            raise AttributeError(f"No such attribute: {name}")
```

**使用示例**:
```python
assets = Canister()
assets.test_point_map = test_point_map
assets.instruments = instruments

# 訪問
print(assets.test_point_map)  # 相當於 assets['test_point_map']
```

**優點**:
- 提供類對象的訪問方式
- 保持字典的靈活性
- 便於動態添加資源

---

## 四、配置文件依賴

### 4.1 test_xml.ini

**相關配置節**:

#### [SfcConfig]
```ini
LogPath = C:\LogData  # 日誌存儲路徑
```

#### [testspec]
```ini
limits_atlas = testPlan\BelugaB\A2B_testPlan.csv  # 用於提取模型名稱
```

### 4.2 SN_file.txt

**內容**: 序列號（SN）
**用途**: 用於命名日誌文件

---

## 五、設計模式分析

### 5.1 工廠函數模式（Factory Function）

**應用**: `default_setup()`

```python
# 工廠函數創建所有必要的測試環境資源
polish_logger, test_point_map, meas_assets = default_setup('limits.csv')
```

**優點**:
- 集中式初始化
- 統一錯誤處理
- 簡化客戶代碼

---

### 5.2 容器模式（Container）

**應用**: `Canister`

```python
meas_assets = Canister()
meas_assets.test_point_map = test_point_map
# 動態添加更多資源...
```

**優點**:
- 靈活的資源管理
- 統一的資源傳遞
- 易於擴展

---

### 5.3 依賴注入（Dependency Injection）

**應用**: 將測試點映射注入到測量資源

```python
meas_assets.test_point_map = test_point_map
# 測量對象通過 meas_assets 獲取依賴
```

**優點**:
- 降低耦合
- 易於測試
- 靈活配置

---

### 5.4 裝飾器模式（Decorator）

**應用**: `StdStreamsCaptureHandler` 裝飾標準輸出

```python
sys.stdout = new_stdout  # 裝飾原始 stdout
# 所有 print 輸出自動記錄到日誌
```

**優點**:
- 透明的日誌記錄
- 無需修改現有代碼
- 統一輸出管理

---

## 六、擴展性分析

### 6.1 可選的資源加載

**註釋掉的導入**展示了框架的可擴展性:

```python
# 可選添加的資源:
# - env_config: 環境配置
# - test_config: 測試配置
# - instruments: VISA 儀器
# - dut_comms: DUT 通訊
# - flash_programmers: 編程器
# - tester_ids: 測試器 ID
# - rec_printer: 打印機
```

**擴展方法**:
```python
def default_setup(limits_csv_filename, env_conf_filename=None):
    polish_logger = init_project_logger()
    limits_table = get_limits_table(limits_csv_filename)
    test_point_map = new_test_point_map(limits_table)

    meas_assets = Canister()
    meas_assets.test_point_map = test_point_map

    # 添加可選資源
    if env_conf_filename:
        env_config = get_env_config(env_conf_filename)
        meas_assets.instruments = get_visa_instruments(env_config)
        meas_assets.dut_comms = get_dut_comms(env_config)
        # ...

    return polish_logger, test_point_map, meas_assets
```

---

### 6.2 自定義日誌配置

**可擴展點**:
```python
# 1. 自定義日誌格式
def custom_setup(limits_csv_filename, log_format=None):
    polish_logger = init_project_logger()
    if log_format:
        add_formatter(handler, log_format)
    # ...

# 2. 自定義日誌位置
def custom_setup(limits_csv_filename, log_path=None):
    if log_path:
        # 覆蓋 DEFAULT_LOG_PATH
        # ...

# 3. 添加額外的日誌處理器
def custom_setup(limits_csv_filename, extra_handlers=None):
    polish_logger = init_project_logger()
    if extra_handlers:
        for handler in extra_handlers:
            polish_logger.addHandler(handler)
    # ...
```

---

### 6.3 多環境設置

**支持創建不同的設置函數**:

```python
def production_setup(limits_csv_filename):
    """生產環境設置"""
    polish_logger = init_project_logger()
    limits_table = get_limits_table(limits_csv_filename)
    test_point_map = new_test_point_map(limits_table)

    meas_assets = Canister()
    meas_assets.test_point_map = test_point_map
    meas_assets.instruments = get_visa_instruments(...)
    meas_assets.dut_comms = get_dut_comms(...)

    return polish_logger, test_point_map, meas_assets

def simulation_setup(limits_csv_filename):
    """模擬環境設置（無真實儀器）"""
    polish_logger = init_project_logger()
    limits_table = get_limits_table(limits_csv_filename)
    test_point_map = new_test_point_map(limits_table)

    meas_assets = Canister()
    meas_assets.test_point_map = test_point_map
    # 不加載真實儀器

    return polish_logger, test_point_map, meas_assets
```

---

## 七、使用示例

### 7.1 基本使用

```python
from polish.setup import default_setup, default_teardown
from polish import Measurement, MeasurementList

# 1. 設置測試環境
logger, test_point_map, meas_assets = default_setup('testPlan/limits.csv')

try:
    # 2. 定義測量
    class MyMeasurement(Measurement):
        test_point_uids = ('test_1', 'test_2')

        def measure(self):
            # 使用測試點映射
            value1 = 10.5
            value2 = "PASS"

            # 執行測試點
            self.test_points.test_1.execute(value1, "OFF", True)
            self.test_points.test_2.execute(value2, "OFF", True)

    # 3. 創建並執行測量列表
    measurement_list = MeasurementList()
    measurement_list.add(MyMeasurement(meas_assets))
    measurement_list.run_measurements()

finally:
    # 4. 清理測試環境
    default_teardown()
```

---

### 7.2 訪問資源

```python
def default_setup(limits_csv_filename):
    polish_logger = init_project_logger()
    limits_table = get_limits_table(limits_csv_filename)
    test_point_map = new_test_point_map(limits_table)

    meas_assets = Canister()
    meas_assets.test_point_map = test_point_map

    # 添加自定義資源
    meas_assets.my_custom_resource = "some_value"
    meas_assets.config = {'key': 'value'}

    return polish_logger, test_point_map, meas_assets

# 在測量中使用
class MyMeasurement(Measurement):
    def measure(self):
        # 訪問測試點映射
        test_point_map = self.meas_assets.test_point_map

        # 訪問自定義資源
        custom_resource = self.meas_assets.my_custom_resource
        config = self.meas_assets.config
```

---

### 7.3 使用日誌

```python
def default_setup(limits_csv_filename):
    polish_logger = init_project_logger()

    # 獲取子日誌記錄器
    my_logger = get_logger('my_module')
    my_logger.info('Module initialized')

    # 所有 print 輸出自動記錄到日誌
    print('This will be logged')  # 自動記錄

    return polish_logger, test_point_map, meas_assets
```

---

## 八、潛在改進區域

### 8.1 配置驗證

**問題**: 未驗證限制表文件的格式和內容

**建議**:
```python
def default_setup(limits_csv_filename):
    # 添加文件存在性檢查
    if not os.path.exists(limits_csv_filename):
        raise FileNotFoundError(f"Limits table not found: {limits_csv_filename}")

    # 添加格式驗證
    limits_table = get_limits_table(limits_csv_filename)
    validate_limits_table(limits_table)  # 新增驗證函數

    # ...
```

---

### 8.2 錯誤處理

**問題**: 缺少錯誤處理和恢復機制

**建議**:
```python
def default_setup(limits_csv_filename):
    try:
        polish_logger = init_project_logger()
        limits_table = get_limits_table(limits_csv_filename)
        test_point_map = new_test_point_map(limits_table)
        meas_assets = Canister()
        meas_assets.test_point_map = test_point_map
        return polish_logger, test_point_map, meas_assets
    except Exception as e:
        # 錯誤發生時確保清理資源
        deinit_project_logger()
        raise RuntimeError(f"Setup failed: {e}") from e
```

---

### 8.3 上下文管理器

**問題**: 需要手動調用 `default_teardown()`

**建議**:
```python
from contextlib import contextmanager

@contextmanager
def setup_context(limits_csv_filename):
    """上下文管理器版本的自動設置和清理"""
    polish_logger = test_point_map = meas_assets = None
    try:
        polish_logger, test_point_map, meas_assets = default_setup(limits_csv_filename)
        yield polish_logger, test_point_map, meas_assets
    finally:
        if polish_logger:
            default_teardown()

# 使用
with setup_context('limits.csv') as (logger, test_point_map, meas_assets):
    # 執行測試
    pass
# 自動清理
```

---

### 8.4 日誌目錄創建錯誤處理

**問題**: 如果日誌目錄創建失敗，可能導致程序崩潰

**建議**:
```python
def init_project_logger(project_name=PROJECT_NAME):
    # ...
    if detect_default_log_location():
        try:
            # 創建目錄
            os.makedirs(model_dir, exist_ok=True)
            os.makedirs(date_dir, exist_ok=True)
        except OSError as e:
            # 創建失敗，回退到臨時目錄
            log_dir = tempfile.gettempdir()
            log_file_path = os.path.join(log_dir, log_file_name)
            logging.warning(f"Failed to create log directory, using temp: {log_dir}")
    # ...
```

---

### 8.5 序列號文件處理

**問題**: `SN_file.txt` 讀取失敗時未處理

**建議**:
```python
def init_project_logger(project_name=PROJECT_NAME):
    # ...
    try:
        with open('SN_file.txt', 'r') as f:
            SN = f.read().strip()
    except FileNotFoundError:
        SN = 'UNKNOWN'
        logging.warning("SN_file.txt not found, using 'UNKNOWN'")
    except Exception as e:
        SN = 'ERROR'
        logging.error(f"Failed to read SN_file.txt: {e}")
    # ...
```

---

### 8.6 資源初始化順序

**問題**: 未定義資源的初始化順序和依賴

**建議**:
```python
def default_setup(limits_csv_filename):
    # 定義明確的初始化階段
    stage1_init()  # 日誌、配置
    stage2_init()  # 限制表、測試點
    stage3_init()  # 資源（儀器、通訊等）
    stage4_init()  # 驗證和準備

    return polish_logger, test_point_map, meas_assets
```

---

### 8.7 資源釋放

**問題**: `default_teardown()` 只清理日誌，未清理其他資源

**建議**:
```python
def default_teardown(meas_assets=None):
    # 清理資源
    if meas_assets:
        # 清理儀器連接
        if hasattr(meas_assets, 'instruments'):
            close_instruments(meas_assets.instruments)

        # 清理通訊連接
        if hasattr(meas_assets, 'dut_comms'):
            close_dut_comms(meas_assets.dut_comms)

        # 清理編程器
        if hasattr(meas_assets, 'flash_programmers'):
            close_flash_programmers(meas_assets.flash_programmers)

    # 清理日誌
    deinit_project_logger()
```

---

## 九、關鍵技術點

### 9.1 標準輸出捕獲

**技術**: 重寫 `sys.stdout` 和 `sys.stderr`

**實現**:
```python
class StdStreamsCaptureHandler(logging.StreamHandler):
    def __init__(self, root_logger):
        self._stdout = sys.stdout  # 保存原始 stdout
        sys.stdout = FakeStdStream()  # 替換 stdout
        sys.stdout.write = self.stream_capture  # 重寫 write 方法
```

**注意事項**:
- 必須在日誌輸出時恢復原始 stdout（避免循環）
- 使用線程鎖保護並發訪問
- 確保在 cleanup 時恢復原始 stdout

---

### 9.2 動態屬性字典

**技術**: 繼承 `dict` 並重寫 `__getattr__`, `__setattr__`

**實現**:
```python
class Canister(dict):
    def __getattr__(self, name):
        if name in self:
            return self[name]
        raise AttributeError(f"No such attribute: {name}")
```

**用途**:
- 提供類對象的訪問方式
- 保持字典的靈活性
- 動態添加資源

---

### 9.3 日誌目錄結構

**設計**:
```
{LogPath}/{model_name}/{date}/{SN}_{timestamp}.txt
```

**優點**:
- 按模型分類
- 按日期分組
- 按序列號識別
- 時間戳確保唯一性

**提取模型名**:
```python
model_path = config.get('testspec', 'limits_atlas')
# testPlan\BelugaB\A2B_testPlan.csv
model_name = os.path.basename(os.path.dirname(model_path))
# BelugaB
```

---

### 9.4 SVN 版本獲取

**方法**:
```python
def get_svn_revision():
    try:
        # 優先使用 svn_version.exe
        if os.path.isfile('svn_version.exe'):
            revision = subprocess.check_output(['svn_version.exe'])
        else:
            # 回退到 svn 命令
            output = subprocess.check_output('svn info | find "Revision"', shell=True)
            revision = output.split(":")[1].strip()
        return revision
    except:
        return "cannot get SVN version"
```

**用途**: 版本追溯和問題調試

---

## 十、總結

### 10.1 模組優點

✅ **簡單易用**: 一行代碼完成環境初始化
✅ **集中管理**: 所有初始化邏輯在一個地方
✅ **可擴展**: 易於添加新的資源類型
✅ **日誌集成**: 自動捕獲所有輸出
✅ **靈活容器**: Canister 提供動態資源管理

### 10.2 需要改進

⚠️ **錯誤處理**: 缺少異常處理和恢復機制
⚠️ **資源清理**: teardown 不完整
⚠️ **配置驗證**: 未驗證輸入參數
⚠️ **文檔**: 缺少詳細的 docstrings
⚠️ **測試**: 缺少單元測試

### 10.3 應用場景

- ✅ 製造測試環境初始化
- ✅ 自動化測試框架
- ✅ 質量控制系統
- ✅ 生產線測試

### 10.4 設計哲學

**setup/** 模組體現了以下設計原則：

1. **單一職責**: 只負責環境設置和清理
2. **依賴注入**: 通過 meas_assets 傳遞依賴
3. **開閉原則**: 對擴展開放，對修改封閉
4. **工廠模式**: 集中創建測試環境資源

---

## 十一、關鍵文件索引

| 文件路徑 | 行數 | 核心功能 | 依賴 |
|----------|------|----------|------|
| `polish/setup/__init__.py` | 1 | 模組標識符 | 無 |
| `polish/setup/default_setup.py` | 48 | 設置和清理 | logging_setup, limits_table_reader, test_point_map, canister |
| `polish/mfg_common/logging_setup.py` | 189 | 日誌系統 | logging, threading, configparser, subprocess |
| `polish/mfg_config_readers/limits_table_reader.py` | 38 | 限制表讀取 | csv, xml.etree.ElementTree |
| `polish/test_point/test_point_map.py` | 127 | 測試點映射 | test_point |
| `polish/mfg_common/canister.py` | 33 | 動態屬性字典 | 無 |

---

## 十二、完整執行流程示例

```python
# 示例腳本: run_test.py

from polish.setup import default_setup, default_teardown
from polish import Measurement, MeasurementList

def main():
    # 1. 設置測試環境
    print("Setting up test environment...")
    logger, test_point_map, meas_assets = default_setup(
        'testPlan/Other/limits.csv'
    )
    print("Setup complete!")

    try:
        # 2. 創建測量
        class VoltageMeasurement(Measurement):
            test_point_uids = ('voltage_test',)

            def measure(self):
                # 讀取電壓（模擬）
                voltage = 12.5

                # 執行測試點
                self.test_points.voltage_test.execute(
                    voltage,
                    "OFF",
                    True
                )

        # 3. 執行測試
        print("Running tests...")
        measurement_list = MeasurementList()
        measurement_list.add(VoltageMeasurement(meas_assets))
        measurement_list.run_measurements()

        # 4. 檢查結果
        print("Tests complete!")
        print(f"Executed: {test_point_map.count_executed()}")
        print(f"Passed: {test_point_map.all_pass()}")

        # 5. 生成報告
        from polish.reports import generate_default_report
        generate_default_report(test_point_map)
        print("Report generated!")

    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise

    finally:
        # 6. 清理測試環境
        print("Cleaning up...")
        default_teardown()
        print("Cleanup complete!")

if __name__ == '__main__':
    main()
```

**執行流程**:
```
1. 設置測試環境
   ├─ 初始化日誌（捕獲所有輸出）
   ├─ 讀取限制表
   ├─ 創建測試點映射
   └─ 構建資源容器

2. 創建測量
   ├─ 繼承 Measurement 類
   └─ 定義 test_point_uids

3. 執行測試
   ├─ 添加測量到列表
   ├─ 遍歷執行測量
   └─ 調用 test_point.execute()

4. 檢查結果
   ├─ 統計執行數量
   └─ 檢查通過狀態

5. 生成報告
   ├─ 遍歷測試點
   └─ 生成 CSV 文件

6. 清理環境
   ├─ 恢復標準輸出
   └─ 關閉日誌處理器
```

---

**文檔版本**: 1.0
**最後更新**: 2026-01-28
**分析者**: Claude Code
