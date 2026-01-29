# Polish 目錄模組架構分析

> 分析日期: 2026-01-27
> 版本: PDTool4
> 目錄: `polish/`

---

## 📋 目錄結構

```
polish/
├── measurement/              # 測量執行核心
│   ├── __init__.py
│   └── measurement.py
├── test_point/              # 測試點管理
│   ├── __init__.py
│   ├── test_point.py
│   ├── test_point_map.py
│   └── test_point_runAllTest.py
├── mfg_common/             # 製造通用工具
│   ├── __init__.py
│   ├── canister.py
│   ├── config_reader.py
│   ├── deps.py
│   ├── constants.py
│   ├── logging_setup.py
│   └── path_utils.py
├── mfg_config_readers/     # 配置讀取
│   ├── __init__.py
│   ├── test_config_reader.py
│   ├── limits_table_reader.py
│   └── limits_altasSpec.csv
├── reports/               # 報告生成
│   ├── __init__.py
│   ├── default_report.py
│   ├── print_receipt.py
│   └── thermal_printer.py
├── setup/                 # 測試環境設置
│   ├── __init__.py
│   └── default_setup.py
├── dut_comms/             # DUT 通訊
│   ├── __init__.py
│   ├── ls_comms/          # LS 系列設備通訊
│   ├── ltl_chassis_fixt_comms/  # 底盤治具通訊
│   ├── vcu_ether_comms/  # VCU 以太網通訊
│   ├── semigloss_remote/  # 遠程控制
│   └── mkstruct.py
├── library/               # 庫模組
│   └── __init__.py
├── __init__.py            # 模組導出
└── util_funcs.py          # 通用工具函數
```

---

## 一、核心架構概覽

**polish** 是一個完整的製造測試框架，提供：

- ✅ 測試點定義和管理
- ✅ 測量執行和協調
- ✅ 限制檢查（多種類型）
- ✅ 依賴解析
- ✅ 報告生成
- ✅ 設備通訊
- ✅ 配置管理

---

## 二、各模組詳細分析

### 2.1 measurement/ - 測量執行模組

#### 核心文件: `measurement.py`

#### 類層次結構

```
DepsResolver (依賴解析器)
    ↓
Measurement (測量基類)
    ↓
MeasurementList (測量列表管理器)

Job (獨立任務)
    ↓
(繼承自 Measurement)
```

#### Measurement 類

**目的**: 每個測量操作的抽象基類

**關鍵屬性**:
```python
test_point_uids = tuple()  # 測試點 UID 列表（子類必須定義）
```

**關鍵方法**:

| 方法 | 說明 | 子類實現 |
|------|------|----------|
| `__init__(meas_assets)` | 初始化測試點 | ❌ |
| `setup()` | 測量前設置 | ✅ 可選 |
| `measure()` | 執行測量 | ✅ **必須** |
| `teardown()` | 測量後清理 | ✅ 可選 |
| `check_test_points()` | 檢查所有測試點已執行 | ❌ |
| `run()` | 執行完整測量流程 | ❌ |

**執行流程**:
```python
def run(self):
    tick = time.time()
    try:
        self.setup()         # 測量前設置
        self.measure()       # 執行測量（子類實現）
        self.check_test_points()  # 檢查所有測試點
    finally:
        self.teardown()      # 測量後清理
        # 記錄執行時間
        # 寫入 result.txt
```

#### MeasurementList 類

**功能**: 管理和執行多個測量

**方法**:
```python
add(measurements)        # 添加一個或多個測量
run_measurements()       # 執行所有測量
```

**執行邏輯**:
```
1. get_ordered_measurments() - 排序並解析依賴
2. 依次執行每個 Measurement
3. 每個測量調用 run()
```

#### Job 類

**功能**: 執行獨立任務（無測試點）

**方法**:
```python
job()   # 任務執行（子類實現）
run()   # 執行並計時
```

---

### 2.2 test_point/ - 測試點管理模組

#### 核心文件

| 文件 | 功能 |
|------|------|
| `test_point.py` | 單個測試點實現 |
| `test_point_map.py` | 測試點映射管理器 |
| `test_point_runAllTest.py` | RunAllTest 模式變體 |

#### TestPoint 類

**構造參數**:
```python
def __init__(
    self,
    name,              # 測試點名稱
    ItemKey,           # 項目鍵
    value_type,        # 數值類型
    limit_type,        # 限制類型
    equality_limit=None,    # 相等限制
    lower_limit=None,      # 下限
    upper_limit=None       # 上限
)
```

**狀態屬性**:
```python
executed = False     # 是否已執行
passed = None        # 是否通過 (True/False)
value = None         # 測量值
```

#### 限制類型 (LimitType)

| 類型 | 說明 | 檢查邏輯 |
|------|------|----------|
| `NONE_LIMIT_TYPE` | 無限制 | 總是返回 True |
| `EQUALITY_LIMIT_TYPE` | 相等 | `value == equality_limit` |
| `PARTIAL_LIMIT_TYPE` | 部分匹配 | `equality_limit in value` |
| `INEQUALITY_LIMIT_TYPE` | 不相等 | `value != equality_limit` |
| `LOWER_LIMIT_TYPE` | 下限 | `value >= lower_limit` |
| `UPPER_LIMIT_TYPE` | 上限 | `value <= upper_limit` |
| `BOTH_LIMIT_TYPE` | 雙邊限制 | `lower_limit <= value <= upper_limit` |

#### 數值類型 (ValueType)

| 類型 | 轉換方法 |
|------|----------|
| `STRING_VALUE_TYPE` | `str(value)` |
| `INTEGER_VALUE_TYPE` | `int(value, 0)` (自動檢測進制) |
| `FLOAT_VALUE_TYPE` | `float(value)` |

#### 核心方法

##### execute(value, runAllTest, raiseOnFail)

**功能**: 執行測試點並檢查限制

**參數**:
- `value`: 測量值
- `runAllTest`: "ON" 繼續執行 / 其他停止
- `raiseOnFail`: 失敗時是否拋出異常

**異常**:
- `TestPointEqualityLimitFailure`: 相等限制失敗
- `TestPointInequalityLimitFailure`: 不相等限制失敗
- `TestPointLowerLimitFailure`: 下限失敗
- `TestPointUpperLimitFailure`: 上限失敗
- `TestPointDoubleExecutionError`: 重複執行

**特殊處理**:
```python
# 錯誤消息處理
if value == "No instrument found":
    self.passed = False
    self.executed = True
    raise

if "Error: " in value:
    self.passed = False
    self.executed = True
    raise
```

##### re_execute(value, raiseOnFail)

**功能**: 重置並重新執行測試點

**用途**: 測試重試場景

#### TestPointMap 類

**功能**: 測試點註冊、檢索和統計

**方法**:
```python
add_test_point(test_point)        # 添加測試點
get_test_point(unique_id)          # 獲取測試點
__getitem__(unique_id)             # 字典風格訪問
get_dict()                        # 獲取所有測試點字典
all_executed()                    # 檢查是否全部執行
all_pass()                        # 檢查是否全部通過
all_executed_all_pass()           # 檢查是否全部執行並通過
count_executed()                  # 統計已執行數量
count_skipped()                   # 統計跳過數量
get_fail_uid()                    # 獲取失敗的測試點 UID
```

#### new_test_point_map(limits_table)

**工廠函數**: 從限制表創建測試點映射

**輸入格式** (CSV 行):
```
ID, Name, Value_Type, Limit_Type, Equality_Limit, Lower_Limit, Upper_Limit
```

**處理邏輯**:
```
1. 跳過空行
2. 跳過註釋行 (; 或 #)
3. 跳過標題行 (ID)
4. 每行創建一個 TestPoint
5. 添加到 TestPointMap
```

---

### 2.3 mfg_common/ - 製造通用工具模組

#### 文件列表

| 文件 | 功能 |
|------|------|
| `canister.py` | 動態屬性字典 |
| `config_reader.py` | INI 配置讀取器 |
| `deps.py` | 依賴解析器 |
| `constants.py` | 常量定義 |
| `logging_setup.py` | 日誌設置 |
| `path_utils.py` | 路徑工具 |

#### Canister 類

**目的**: 允許像對象屬性一樣訪問字典鍵

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
assets.dut_comms = dut_comms

# 訪問
print(assets.test_point_map)  # 相當於 assets['test_point_map']
```

#### deps.py - 依賴解析器

**設計**: 使用 Python MRO (Method Resolution Order)

**DepsResolver 類**:
```python
class DepsResolver:
    @classmethod
    def resolve_deps(cls):
        # 創建動態依賴解析類
        cls.deps_resolver = type(
            cls.__name__ + '_deps_res',
            tuple([i.deps_resolver for i in cls.deps]),
            {}
        )
        cls.deps_resolver.owner = cls
        cls.resolved_deps = [
            class_.owner for class_ in cls.deps_resolver.mro()
            if class_ not in (object, cls.deps_resolver)
        ]
```

**依賴定義**:
```python
class MyMeasurement(Measurement):
    @classmethod
    def define_deps(cls):
        cls.deps = (OtherMeasurement,)  # 依賴列表
```

**使用**:
```python
# 解析所有測量的依賴
resolve_deps([MeasurementA, MeasurementB, MeasurementC])
```

#### config_reader.py

**功能**: INI 配置文件讀取和解析

**核心函數**:

| 函數 | 說明 |
|------|------|
| `load_config(filename)` | 加載 INI 文件 |
| `read_config(ini)` | 解析配置為 Canister |
| `load_and_read_config(filename)` | 加載並解析（組合） |
| `auto_cast_string(strValue)` | 自動類型轉換 |

**名稱過濾**: 只允許 `[A-Z0-9_]` 的鍵名

**示例 INI**:
```ini
[TestConfig]
timeout = 10
retry_count = 3
enable_debug = true
```

**輸出**:
```python
config.test_config.timeout = 10
config.test_config.retry_count = 3
config.test_config.enable_debug = "true"
```

#### constants.py

```python
DATE_TIME_FORMAT = '%y-%m-%d_%H:%M:%S'
PROJECT_NAME = 'polish'
LOG_FORMAT_STRING = '%(asctime)s,%(levelname)s %(message)s'
VERBOSE_LOG_FORMAT_STRING = '%(asctime)s,%(levelname)s,%(module)s:%(lineno)d:%(funcName)s %(message)s'
DEFAULT_LOG_PATH = 'logs'
```

---

### 2.4 mfg_config_readers/ - 配置讀取模組

#### 文件

| 文件 | 功能 |
|------|------|
| `test_config_reader.py` | 測試配置讀取 |
| `limits_table_reader.py` | 限制表讀取 (CSV/XML) |
| `limits_altasSpec.csv` | 示例限制表 |

#### test_config_reader.py

```python
def get_test_config(test_conf_filename):
    return load_and_read_config(test_conf_filename)
```

#### limits_table_reader.py

**CSV 讀取**:
```python
def get_limits_table(limits_csv_filename):
    with open(limits_csv_filename) as table_file:
        table_buffer = io.StringIO(table_file.read())
    return csv.reader(table_buffer)
```

**XML 讀取**:
```python
def get_limits_data(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    data = []
    for TestItem in root.findall('TestItems/*'):
        ID = TestItem.tag
        Min = float(TestItem.find("ProgramParams/Lowlimit").text)
        Max = float(TestItem.find("ProgramParams/Uplimit").text)
        Value = ""
        row_data = [ID, Min, Value, Max]
        data.append(row_data)

    return data
```

---

### 2.5 reports/ - 報告生成模組

#### 文件

| 文件 | 功能 |
|------|------|
| `default_report.py` | 默認 CSV 報告生成 |
| `print_receipt.py` | 收據打印格式化 |
| `thermal_printer.py` | 熱敏打印機支持 |

#### default_report.py

**generate_default_report()** 函數

**參數**:
- `test_point_map`: 測試點映射
- `uid_serial_num`: 序列號測試點 UID
- `test_name`: 測試名稱 (默認 'atlas')
- `report_name`: 報告名稱 (默認 'dflt')
- `date_and_time`: 日期時間
- `leader_path`: 報告目錄 (默認 'default_reports')
- `filename_template`: 文件名模板

**文件名格式**:
```
{serial_num}_{date_and_time}.csv
```

**CSV 格式**:
```
ItemKey, ID, LL, UL, TestValue, TestDateTime, Result
```

**結果編碼**:
- `P`: 通過
- `F`: 失敗
- ` ` (空格): 未執行

#### print_receipt.py

**Receipt 類**

**模板**:
```
----------
FItem:{fail_name},
FInfo:{fail_info},
FailVal:{fail_val},
Ulimit:{ulimit}, Llimit:{llimit}, Elimit:{elimit}
```

**橫幅**:
```
PASS:
 ---------------
     P A S S
 ---------------

FAIL:
 ***************
 **  F A I L  **
 ***************
```

**方法**:
```python
print_summary(test_point_map)  # 打印測試摘要
```

**信息提取**:
- 序列號 (`info_vcu_serial_num`)
- 日期時間 (`info_date_time`)
- 執行統計 (`count_executed()`)
- 失敗信息 (`get_fail_uid()`)

---

### 2.6 setup/ - 測試環境設置模組

#### default_setup.py

**default_setup(limits_csv_filename)**

**流程**:
```
1. init_project_logger()
   ↓
2. get_limits_table(limits_csv_filename)
   ↓
3. new_test_point_map(limits_table)
   ↓
4. 創建 meas_assets (Canister)
   - test_point_map
   - (其他資源可選)
   ↓
5. 返回 (polish_logger, test_point_map, meas_assets)
```

**default_teardown()**
```
deinit_project_logger()
```

---

### 2.7 dut_comms/ - DUT 通訊模組

#### 子目錄結構

```
dut_comms/
├── ls_comms/                 # LS 系列設備通訊
│   ├── __init__.py
│   ├── ls_mod.py            # 串口通訊模組
│   └── ls_msgs.py           # 消息定義
├── ltl_chassis_fixt_comms/   # 底盤治具通訊
│   ├── __init__.py
│   ├── chassis_msgs.py      # Protocol Buffers 消息
│   ├── chassis_transport.py  # 傳輸層
│   ├── button_launch.py     # 按鈕啟動
│   └── generate_c_include.py # C 頭文件生成
├── vcu_ether_comms/          # VCU 以太網通訊
│   ├── __init__.py
│   ├── vcu_common.py        # 通用定義
│   ├── vcu_cmds.py          # 命令定義
│   ├── vcu_ether_link.py    # 以太網鏈接
│   ├── vcu_motor_command_timestamp.py
│   ├── vcu_req_replay.py
│   ├── header.py
│   ├── proto/               # Protocol Buffers 消息
│   │   ├── __init__.py
│   │   ├── common_pb2.py
│   │   ├── system_control_msgs_pb2.py
│   │   └── ... (40+ 消息文件)
│   └── build_vcu_proto_msgs.sh
├── semigloss_remote/          # 遠程控制
│   └── __init__.py
└── mkstruct.py               # 結構生成工具
```

#### ls_comms/ls_mod.py

**SafetyInterface 類**

**參數**:
```python
port_name = '/dev/ttyUSB0'  # 或 COM 端口
baud_rate = 9600
```

**消息格式**:
```
Header:
  Sync: 0xCA 0xFE
  Length: 2 bytes
  CRC: 4 bytes
  Message Format: 2 bytes
  Reserved: 2 bytes
  Command: 1 byte
  Response Indicator: 1 byte
  Sensor: 1 byte
  Params: variable
```

**CRC 計算**:
```python
def get_crc(frame_header_str, complete_serialized_body_str):
    trimmed_header_str = frame_header_str[8:]  # 跳過 sync, length, crc
    header_crc_part = zlib.crc32(trimmed_header_str) & 0xFFFFFFFF
    crc = zlib.crc32(complete_serialized_body_str, header_crc_part) & 0xFFFFFFFF
    return crc
```

**支持的命令**:
- 懸崖傳感器讀取 (`cliff1` ~ `cliff5`)
- 編碼器讀取 (`enc1`, `enc2`)

#### ltl_chassis_fixt_comms/chassis_msgs.py

**同步字**: `0xA5FF00CC`

**消息類**:

| 消息類 | 消息類型 | 功能 |
|--------|----------|------|
| `TransportHeader` | -10 | 傳輸頭 |
| `TransportFooter` | -9 | 傳輸尾 |
| `ActuateCliffSensorDoor` | 0x10 | 懸崖傳感器門控制 |
| `ActuateCliffSensorDoorStatus` | 0x11 | 狀態響應 |
| `ReadEncoderCount` | 0x12 | 讀取編碼器計數 |
| `EncoderCount` | 0x13 | 編碼器計數響應 |
| `WaitForTurntable` | 0x14 | 等待轉盤 |
| `RotateTurntable` | 0x16 | 旋轉轉盤 |
| `GetTurntableAngle` | 0x1A | 獲取轉盤角度 |
| `TurntableAngleRsp` | 0x1B | 角度響應 |

**枚舉類**:
```python
class close_open_enum(Enum):
    CLOSE = 0
    OPEN = 1

class left_right_enum(Enum):
    LEFT = 0
    RIGHT = 1

class status_enum(Enum):
    SUCCESS = 0
    GENERAL_FAILURE = 1
    TIMEOUT_EXPIRED = 2

class operation_enum(Enum):
    ROTATE_TO_OPTO_SWITCH = 0
    ROTATE_LEFT = 1
    ROTATE_RIGHT = 2
```

**序列化/反序列化**:
```python
def serialize(msg_inst):
    return struct.pack(msg_packing_format_map[type(msg_inst)], *get_values(msg_inst))

def deserialize(msg_class, msg_blob):
    msg = msg_class()
    values = struct.unpack(msg_packing_format_map[msg_class], msg_blob)
    for name, value in zip(msg_class.fields, values):
        setattr(msg, name, value)
    return msg
```

#### vcu_ether_comms/

**Protocol Buffers 消息** (40+ 文件):

| 分類 | 消息文件 |
|------|----------|
| 通用 | `common_pb2.py` |
| 系統控制 | `system_control_msgs_pb2.py` |
| 電池 | `battery_msgs_pb2.py` |
| 牽引電機 | `traction_motor_msgs_pb2.py` |
| 故障代碼 | `fault_codes_pb2.py` |
| IMU 數據 | `imu_data_msgs_pb2.py` |
| GPIO | `gpio_test_msgs_pb2.py`, `gpio_init_v2_pb2.py` |
| 日誌 | `log_msgs_pb2.py` |
| 版本信息 | `version_info_pb2.py` |
| ... | ... |

**vcu_cmds.py**: VCU 命令定義和執行
**vcu_ether_link.py**: 以太網鏈接管理
**vcu_common.py**: 通用定義
**vcu_req_replay.py**: 請求重放工具

---

### 2.8 util_funcs.py - 通用工具函數

#### 函數列表

```python
def sleep_until_timestamp(tick):
    """睡眠到指定時間戳"""

def make_list(thing):
    """將對象轉換為列表"""

def cast_ros_int(ros_int):
    """將 ROS int 轉換為 Python int"""
```

---

## 三、執行流程分析

### 完整測試流程

```
┌─────────────────────────────────────────────────────────────┐
│ 1. 設置階段 (default_setup)                                │
├─────────────────────────────────────────────────────────────┤
│   init_project_logger()                                     │
│         ↓                                                   │
│   get_limits_table(limits_csv_filename)                     │
│         ↓                                                   │
│   new_test_point_map(limits_table)                          │
│         ↓                                                   │
│   創建 meas_assets (Canister)                              │
│         │                                                   │
│         ├─ test_point_map                                    │
│         ├─ instruments (可選)                                │
│         ├─ dut_comms (可選)                                  │
│         └─ ...                                              │
│         ↓                                                   │
│   返回 (logger, test_point_map, meas_assets)                │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. 測量執行階段                                             │
├─────────────────────────────────────────────────────────────┤
│   MeasurementList.run_measurements()                        │
│         ↓                                                   │
│   get_ordered_measurments()  # 排序和依賴解析               │
│         ↓                                                   │
│   對每個 Measurement:                                        │
│     ├─ run()                                                │
│     │   ├─ setup()                                          │
│     │   ├─ measure()  # 子類實現，收集數據                  │
│     │   │   ↓                                               │
│     │   │   test_point.execute(value, runAllTest)           │
│     │   │   ├─ 檢查限制                                     │
│     │   │   ├─ 更新 executed, passed, value                 │
│     │   │   └─ 寫入 result.txt                             │
│     │   └─ teardown()                                       │
│     └─ 檢查測試點是否全部執行                                │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. 報告生成階段                                             │
├─────────────────────────────────────────────────────────────┤
│   generate_default_report(test_point_map)                     │
│         ↓                                                   │
│   遍歷所有測試點                                             │
│         ↓                                                   │
│   生成 CSV 文件                                              │
│   文件名: {serial_num}_{date_and_time}.csv                 │
│   路徑: default_reports/                                    │
│         ↓                                                   │
│   Receipt.print_summary(test_point_map)                      │
│         ↓                                                   │
│   打印測試摘要 (控制台/打印機)                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 四、關鍵設計模式

### 4.1 模板方法模式 (Template Method)

**應用**: `Measurement.run()`

```python
class Measurement:
    def run(self):
        try:
            self.setup()      # 鉤子方法
            self.measure()    # 抽象方法（子類實現）
            self.check_test_points()
        finally:
            self.teardown()   # 鉤子方法
```

### 4.2 策略模式 (Strategy)

**應用**: 不同的 `LimitType` 和 `ValueType`

```python
# 限制檢查策略
if self.limit_type is EQUALITY_LIMIT_TYPE:
    return str(value) == self.equality_limit
elif self.limit_type is LOWER_LIMIT_TYPE:
    return float(value) >= float(self.lower_limit)
elif ...
```

### 4.3 容器模式 (Container)

**應用**: `Canister` 動態屬性字典

```python
assets = Canister()
assets.test_point_map = test_point_map  # 動態添加屬性
```

### 4.4 依賴注入 (Dependency Injection)

**應用**: `meas_assets` 傳遞到測量對象

```python
def __init__(self, meas_assets):
    self.test_point_map = meas_assets.test_point_map
    self.instruments = meas_assets.instruments
    self.dut_comms = meas_assets.dut_comms
```

### 4.5 工廠模式 (Factory)

**應用**: `new_test_point_map()`

```python
def new_test_point_map(limits_table):
    test_point_map = TestPointMap()
    for row in limits_table:
        test_point = TestPoint(*row)
        test_point_map.add_test_point(test_point)
    return test_point_map
```

### 4.6 迭代器模式 (Iterator)

**應用**: `MeasurementList` 和 `TestPointMap`

```python
for test_point in test_point_map.get_dict().values():
    # 處理測試點
```

---

## 五、技術棧

### 序列化
- **Protocol Buffers**: vcu_ether_comms 消息定義
- **struct**: 二進制數據打包/解包

### 通訊
- **Serial (pyserial)**: 串口通訊 (ls_comms)
- **Ethernet**: 以太網通訊 (vcu_ether_comms)

### 配置
- **INI**: ConfigParser
- **CSV**: csv 模組
- **XML**: xml.etree.ElementTree

### 日誌
- **Python logging**: 標準日誌庫

### 校驗
- **CRC**: zlib.crc32

### 異常處理
- 自定義異常類層次結構

---

## 六、擴展點

### 6.1 新增測量類型

```python
from polish import Measurement

class MyMeasurement(Measurement):
    test_point_uids = ('my_test_point_1', 'my_test_point_2')

    def measure(self):
        # 收集數據
        value1 = self.collect_data_1()
        value2 = self.collect_data_2()

        # 執行測試點
        self.test_points.my_test_point_1.execute(value1, runAllTest, raiseOnFail)
        self.test_points.my_test_point_2.execute(value2, runAllTest, raiseOnFail)
```

### 6.2 新增通訊協議

在 `dut_comms/` 下創建新子目錄:

```
dut_comms/
└── my_protocol/
    ├── __init__.py
    ├── my_protocol_mod.py
    └── my_protocol_msgs.py
```

### 6.3 新增報告格式

在 `reports/` 下添加生成器:

```python
def generate_custom_report(test_point_map, ...):
    # 自定義報告邏輯
    pass
```

### 6.4 新增配置格式

在 `mfg_config_readers/` 添加讀取器:

```python
def get_custom_config(filename):
    # 自定義配置讀取邏輯
    pass
```

---

## 七、潛在改進區域

### 7.1 代碼去重

**問題**: `test_point.py` 和 `test_point_runAllTest.py` 有大量重複代碼

**建議**: 合併為單個文件，使用參數控制行為

### 7.2 錯誤處理

**問題**: 某些異常處理不夠完善

**建議**:
- 添加更詳細的異常信息
- 統一異常處理策略
- 添加重試機制

### 7.3 文檔

**問題**: 缺少詳細的 docstrings

**建議**:
- 為所有公共方法添加 docstrings
- 使用標準文檔格式 (Google/NumPy)
- 添加使用示例

### 7.4 測試

**問題**: 缺少單元測試

**建議**:
- 使用 pytest 添加單元測試
- 測試覆蓋率目標 > 80%
- 添加集成測試

### 7.5 類型提示

**問題**: 缺少 Python 類型提示

**建議**:
```python
def measure(self) -> None:
    pass

def execute(self, value: str, runAllTest: str, raiseOnFail: bool = True) -> bool:
    pass
```

### 7.6 日誌改進

**問題**: 日誌記錄不夠結構化

**建議**:
- 添加結構化日誌 (JSON 格式)
- 支持日誌級別動態調整
- 添加性能監控

### 7.7 性能優化

**問題**: 大量測試點時可能存在性能瓶頸

**建議**:
- 支持並行執行
- 緩存常用配置
- 優化序列化/反序列化

### 7.8 配置驗證

**問題**: 配置文件缺少驗證

**建議**:
- 添加配置模式定義
- 驗證配置完整性
- 提供配置錯誤提示

---

## 八、關鍵文件索引

| 文件路徑 | 行數 | 核心功能 | 依賴 |
|----------|------|----------|------|
| `polish/__init__.py` | 19 | 模組導出 | 所有子模組 |
| `polish/measurement/measurement.py` | 161 | 測量基類 | mfg_common |
| `polish/test_point/test_point.py` | 405 | 測試點實現 | mfg_common |
| `polish/test_point/test_point_map.py` | 127 | 測試點映射 | test_point |
| `polish/mfg_common/canister.py` | 33 | 動態屬性字典 | 無 |
| `polish/mfg_common/deps.py` | 74 | 依賴解析 | 無 |
| `polish/mfg_common/config_reader.py` | 80 | INI 讀取 | canister |
| `polish/mfg_config_readers/limits_table_reader.py` | 38 | 限制表讀取 | 無 |
| `polish/reports/default_report.py` | 120 | CSV 報告 | mfg_common |
| `polish/reports/print_receipt.py` | 139 | 收據打印 | canister |
| `polish/setup/default_setup.py` | 48 | 測試環境設置 | 所有模組 |
| `polish/dut_comms/ls_comms/ls_mod.py` | 301 | 串口通訊 | serial, zlib |
| `polish/dut_comms/ltl_chassis_fixt_comms/chassis_msgs.py` | 234 | 底盤消息 | struct |
| `polish/util_funcs.py` | 23 | 工具函數 | 無 |

---

## 九、使用示例

### 9.1 基本測試執行

```python
from polish import (
    default_setup,
    default_teardown,
    Measurement,
    MeasurementList
)

# 1. 設置
logger, test_point_map, meas_assets = default_setup('limits.csv')

# 2. 創建測量
class MyMeasurement(Measurement):
    test_point_uids = ('test_1', 'test_2')

    def measure(self):
        # 收集數據
        value1 = 10.5
        value2 = "OK"

        # 執行測試點
        self.test_points.test_1.execute(value1, "OFF", True)
        self.test_points.test_2.execute(value2, "OFF", True)

# 3. 執行
measurement_list = MeasurementList()
measurement_list.add(MyMeasurement(meas_assets))
measurement_list.run_measurements()

# 4. 清理
default_teardown()
```

### 9.2 依賴測量

```python
class MeasurementA(Measurement):
    test_point_uids = ('test_a',)

    def measure(self):
        self.test_points.test_a.execute(10, "OFF", True)

    @classmethod
    def define_deps(cls):
        cls.deps = tuple()

class MeasurementB(Measurement):
    test_point_uids = ('test_b',)

    def measure(self):
        # 使用 MeasurementA 的結果
        a_value = meas_assets.test_point_map['test_a'].value
        self.test_points.test_b.execute(a_value + 5, "OFF", True)

    @classmethod
    def define_deps(cls):
        cls.deps = (MeasurementA,)

# 解析依賴
from polish.mfg_common.deps import resolve_deps
resolve_deps([MeasurementA, MeasurementB])
```

---

## 十、總結

**polish** 是一個功能完整的製造測試框架，具有以下特點：

### 優點
✅ 模組化設計清晰
✅ 支持多種測試類型
✅ 靈活的依賴管理
✅ 可擴展的架構
✅ 多種通訊協議支持

### 需要改進
⚠️ 代碼重複問題
⚠️ 缺少單元測試
⚠️ 文檔不完善
⚠️ 性能優化空間
⚠️ 配置驗證不足

### 適用場景
- ✅ 製造測試
- ✅ 設備驗證
- ✅ 質量控制
- ✅ 生產線自動化

---

**文檔版本**: 1.0
**最後更新**: 2026-01-27
**分析者**: Claude Code
