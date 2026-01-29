# Measurement 模組 Codebase 深度分析

> 分析日期: 2026-01-27
> 版本: PDTool4
> 目錄: `polish/measurement/`

---

## 📋 模組概覽

### 文件結構

```
polish/measurement/
├── __init__.py              # 模組導出 (空文件)
└── measurement.py           # 核心測量框架 (160 行)
```

### 統計信息

| 項目 | 值 |
|------|-----|
| 代碼行數 | 160 行 |
| 類數量 | 4 個 |
| 類別 | 測量基類、列表管理器、任務執行器 |
| 設計模式 | 模板方法、策略、工廠 |

---

## 一、核心類層次結構

```
DepsResolver (mfg_common.deps)
    ↓
Measurement (測量基類)
    ├─ getSNMeasurement (SN 讀取測量)
    ├─ PowerSetMeasurement (電源設置測量)
    ├─ PowerReadMeasurement (電源讀取測量)
    ├─ CommandTestMeasurement (命令測試測量)
    ├─ OPjudgeMeasurement (操作判斷測量)
    ├─ OtherMeasurement (其他測量)
    ├─ SFC_GONOGOMeasurement (SFC Go/No-Go 測量)
    └─ FinalMeasurement (最終測量)

MeasurementList (測量列表管理器)

Job (獨立任務執行器)
    ↓
(無直接子類，用於特殊任務)
```

---

## 二、核心類詳細分析

### 2.1 MeaurementImplementationError

**類型**: 自定義異常類

```python
class MeaurementImplementationError(NotImplementedError):
    pass
```

**用途**: 測量實現錯誤異常

**拋出場景**:
- 測量結束時未執行所有測試點
- 子類未正確實現 `measure()` 方法

---

### 2.2 Measurement 類 (核心測量基類)

#### 類定義

```python
class Measurement(DepsResolver):
    test_point_uids = tuple()  # 測試點 UID 列表（子類必須定義）
```

#### 繼承關係

```python
Measurement(DepsResolver)
    ↓ 繼承自 DepsResolver (mfg_common.deps)
```

**DepsResolver 提供的功能**:
- 依賴定義 (`define_deps()`)
- 依賴解析 (`resolve_deps()`)
- `resolved_deps` 屬性（已解析的依賴列表）

#### 2.2.1 類屬性

| 屬性 | 類型 | 默認值 | 說明 |
|------|------|----------|------|
| `test_point_uids` | tuple | `tuple()` | 測試點唯一標識符列表 |
| `deps` | tuple | (由 `define_deps()` 定義) | 依賴測量列表 |
| `deps_resolver` | class | (動態創建) | 依賴解析器類 |
| `resolved_deps` | list | (解析後) | 已解析的依賴列表 |

#### 2.2.2 實例屬性

```python
def __init__(self, meas_assets):
    # 創建 Canister 存儲測試點
    self.test_points = Canister()      # {uid: TestPoint}

    # 獲取測試點映射
    test_point_map = meas_assets.test_point_map

    # 將 test_point_uids 轉換為列表
    self.test_point_uids = make_list(self.test_point_uids)

    # 為每個 UID 獲取測試點
    for uid in self.test_point_uids:
        test_point = test_point_map[uid]
        self.test_points[uid] = test_point

    # 保存測試點映射引用
    self.test_point_map = test_point_map
```

**屬性說明**:

| 屬性 | 類型 | 說明 |
|------|------|------|
| `test_points` | Canister | 測試點字典（可通過屬性訪問） |
| `test_point_map` | TestPointMap | 測試點映射引用 |
| `test_point_uids` | list | 測試點 UID 列表 |

#### 2.2.3 核心方法

##### `__init__(self, meas_assets)`

**參數**:
- `meas_assets` (Canister): 測量資源對象
  - `meas_assets.test_point_map`: 測試點映射
  - `meas_assets.instruments`: 儀器資源（可選）
  - `meas_assets.dut_comms`: DUT 通訊（可選）
  - `meas_assets.test_config`: 測試配置（可選）

**功能**:
1. 初始化 `test_points` Canister
2. 從 `meas_assets.test_point_map` 獲取測試點
3. 將測試點映射到 `test_points` 屬性

**錯誤處理**:
- 如果 UID 不存在於測試點映射中，拋出 `KeyError`

---

##### `run(self)` - 執行完整測量流程

**執行流程**:

```python
def run(self):
    tick = time.time()  # 開始計時

    try:
        try:
            self.setup()           # 1. 測量前設置
            self.measure()         # 2. 執行測量（核心）
            self.check_test_points()  # 3. 檢查所有測試點
        finally:
            self.teardown()       # 4. 測量後清理
    finally:
        after = time.time()  # 計算執行時間
        print(self, 'completed in %0.3f secs' % (after - tick))

        # 寫入 result.txt
        current_path = os.path.dirname(os.path.abspath(__file__))
        FILE_NAME = os.path.join(current_path, '../../result.txt')
        f = open(FILE_NAME, 'a')
        f.write(',' + '%0.3f' % (after - tick) + '\n')
        f.close()
```

**時間記錄格式**:
```
,{elapsed_time_seconds}\n
```

**異常保護**:
- 兩層 `try/finally` 確保 `teardown()` 總是執行
- 即使測量失敗，也會記錄執行時間

---

##### `setup(self)` - 測量前設置

```python
def setup(self):
    pass
```

**用途**: 鉤子方法，子類可覆蓋

**典型用途**:
- 初始化儀器
- 配置通訊接口
- 設置測試環境
- 準備測試數據結構

**示例**:
```python
def setup(self):
    # 打開串口連接
    self.serial_port = serial.Serial('COM3', 9600)
    # 初始化 DAQ
    self.daq.initialize()
```

---

##### `measure(self)` - 執行測量（核心抽象方法）

```python
def measure(self):
    raise MeaurementImplementationError()
    # subclass this to collect data and execute test points
    pass
```

**用途**: 抽象方法，子類必須實現

**要求**:
1. 從 DUT、治具或儀器收集數據
2. 將數據傳遞給測試點
3. 調用 `test_points[uid].execute(value, runAllTest, raiseOnFail)`

**執行規則**:
- 必須執行所有在 `test_point_uids` 中定義的測試點
- 如果有測試點未執行，`check_test_points()` 會拋出異常

**典型模式**:

```python
def measure(self):
    # 1. 收集數據
    value1 = self.collect_voltage()
    value2 = self.collect_current()
    value3 = self.collect_temperature()

    # 2. 執行測試點
    self.test_points.test_point_1.execute(value1, self.runAllTest)
    self.test_points.test_point_2.execute(value2, self.runAllTest)
    self.test_points.test_point_3.execute(value3, self.runAllTest)
```

---

##### `teardown(self)` - 測量後清理

```python
def teardown(self):
    pass
```

**用途**: 鉤子方法，子類可覆蓋

**典型用途**:
- 關閉儀器連接
- 釋放資源
- 重置測試環境
- 清理臨時文件

**示例**:
```python
def teardown(self):
    # 關閉串口
    if hasattr(self, 'serial_port'):
        self.serial_port.close()
    # 釋放 DAQ 資源
    if hasattr(self, 'daq'):
        self.daq.close()
```

---

##### `check_test_points(self)` - 檢查所有測試點是否已執行

```python
def check_test_points(self):
    for uid, test_point in self.test_points.items():
        try:
            if not test_point.executed:
                raise MeaurementImplementationError(
                    'Reached end of measurement execution without feeding data '
                    'to all test points. Measurement is incorrectly implemented. '
                    '%s %s' % (test_point, self)
                )
        except:
            continue
```

**功能**:
1. 遍歷所有測試點
2. 檢查 `test_point.executed` 標志
3. 如果有未執行的測試點，拋出異常

**異常處理**:
- 捕獲異常並繼續（防止單個測試點失敗導致整個測量崩潰）

---

#### 2.2.4 依賴管理

##### `define_deps(cls)` - 定義依賴（類方法）

```python
@classmethod
def define_deps(cls):
    cls.deps = tuple()
    raise NotImplementedError('Subclasses must override define_deps')
```

**用途**: 定義測量依賴關係

**子類實現**:
```python
@classmethod
def define_deps(cls):
    # 依賴於其他測量
    cls.deps = (OtherMeasurement, AnotherMeasurement)
```

##### `resolve_deps(cls)` - 解析依賴（類方法）

**繼承自 DepsResolver**:

```python
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

**功能**:
1. 創建動態類繼承所有依賴
2. 使用 Python MRO 解析依賴順序
3. 生成 `resolved_deps` 列表

**使用示例**:
```python
# 定義依賴
class MeasurementA(Measurement):
    @classmethod
    def define_deps(cls):
        cls.deps = tuple()

class MeasurementB(Measurement):
    @classmethod
    def define_deps(cls):
        cls.deps = (MeasurementA,)

# 解析依賴
resolve_deps([MeasurementA, MeasurementB])

# 結果
MeasurementB.resolved_deps = [MeasurementA]
```

---

### 2.3 MeasurementList 類 (測量列表管理器)

#### 類定義

```python
class MeasurementList(object):
    def __init__(self):
        self._measurements = list()
```

#### 2.3.1 實例屬性

| 屬性 | 類型 | 說明 |
|------|------|------|
| `_measurements` | list | 測量對象列表 |

---

#### 2.3.2 核心方法

##### `__init__(self)`

```python
def __init__(self):
    self._measurements = list()
```

---

##### `add(self, measurements)` - 添加測量

```python
def add(self, measurements):
    '''
    add one or many measurements
    '''
    try:
        len(measurements)
        self._measurements.extend(measurements)  # 添加多個
    except TypeError:
        self._measurements.append(measurements)   # 添加單個
```

**參數**:
- `measurements`: 單個 `Measurement` 對象或 `Measurement` 列表

**行為**:
- 如果是列表/元組，使用 `extend()`
- 如果是單個對象，使用 `append()`

**示例**:
```python
measurement_list = MeasurementList()

# 添加單個測量
measurement_list.add(MyMeasurement(meas_assets))

# 添加多個測量
measurement_list.add([
    Measurement1(meas_assets),
    Measurement2(meas_assets),
    Measurement3(meas_assets)
])
```

---

##### `measurements` 屬性

```python
@property
def measurements(self):
    return self._measurements
```

**用途**: 只讀屬性，訪問測量列表

---

##### `run_measurements(self)` - 執行所有測量

```python
def run_measurements(self):
    # filter for enabled, get dependencies, dedupe, sort by original order
    ordered_measurements = get_ordered_measurments(self._measurements)
    print(ordered_measurements)

    for meas in ordered_measurements:
        print(meas)
        meas.run()
```

**執行流程**:

```
1. get_ordered_measurments(self._measurements)
   ↓
   - 複製測量列表
   - 添加所有依賴測量
   - 去重（dedupe）
   - 排序（sort）
   ↓
2. 依次執行每個測量
   ↓
   meas.run()
```

**依賴解析**:
- 自動解析並包含所有依賴
- 確保依賴在依賴者之前執行

---

### 2.4 Job 類 (獨立任務執行器)

#### 類定義

```python
class Job(Measurement):
    def run(self):
        tick = time.time()
        try:
            self.job()
        finally:
            after = time.time()
            print(self, 'completed in %0.3f secs' % (after - tick))

    def job(self):
        pass
```

#### 2.4.1 與 Measurement 的區別

| 特性 | Measurement | Job |
|------|------------|-----|
| 測試點要求 | 必須有 test_point_uids | 可選（無測試點） |
| 執行流程 | setup → measure → teardown | 只執行 job() |
| 應用場景 | 測試測量 | 獨立任務 |

#### 2.4.2 核心方法

##### `run(self)` - 執行任務

```python
def run(self):
    tick = time.time()
    try:
        self.job()      # 執行任務
    finally:
        after = time.time()
        print(self, 'completed in %0.3f secs' % (after - tick))
```

**與 Measurement.run() 的區別**:
- 無 setup/teardown
- 不調用 check_test_points()
- 不寫入 result.txt

---

##### `job(self)` - 任務執行（抽象方法）

```python
def job(self):
    pass
```

**用途**: 抽象方法，子類必須實現

**典型用途**:
- 初始化操作
- 數據處理
- 批量操作
- 不需要測試點的任務

**示例**:
```python
class InitializeJob(Job):
    def job(self):
        # 初始化 DUT
        subprocess.call(['python', 'initialize_dut.py'])
        # 等待就緒
        time.sleep(5)
```

---

## 三、輔助函數

### 3.1 `sort_measurements(measurements)`

```python
def sort_measurements(measurements):
    ''''
    dedupe and sort
    '''
    # assign indexes and removes duplicates
    indexed_set = {i: meas for i, meas in enumerate(measurements)}
    # sort and strip indexes
    return [meas for i, meas in sorted(indexed_set.items())]
```

**功能**:
1. 去重（使用字典鍵唯一性）
2. 保持原始順序（使用索引）

**輸入/輸出**:
```python
# 輸入
[meas1, meas2, meas1, meas3, meas2]

# 輸出（去重且保持順序）
[meas1, meas2, meas3]
```

---

### 3.2 `get_ordered_measurments(measurements)`

```python
def get_ordered_measurments(measurements):
    # working copy
    meas_and_deps = measurements[:]

    for meas in measurements:
        # add each dep set
        meas_and_deps.extend(meas.resolved_deps)

    # dedupe and sort
    return sort_measurements(meas_and_deps)
```

**功能**:
1. 複製測量列表
2. 添加所有依賴測量
3. 去重並排序

**依賴解析流程**:

```
[MeasurementA, MeasurementB(依賴A)]
    ↓
添加依賴
    ↓
[MeasurementA, MeasurementB, MeasurementA]
    ↓
去重並排序
    ↓
[MeasurementA, MeasurementB]
```

**結果**: 依賴總是在依賴者之前

---

## 四、實際使用示例

### 4.1 基本 Measurement 實現

```python
from polish import Measurement
import subprocess

class VoltageMeasurement(Measurement):
    test_point_uids = ('voltage_test',)

    def __init__(self, meas_assets, runAllTest):
        super().__init__(meas_assets)
        self.runAllTest = runAllTest

    def measure(self):
        # 調用儀器腳本
        response = subprocess.check_output([
            'python', './src/lowsheen_lib/voltmeter.py'
        ])

        # 解析結果
        voltage = float(response.decode('utf-8').strip())

        # 執行測試點
        self.test_points.voltage_test.execute(voltage, self.runAllTest)
```

**使用**:
```python
voltage_meas = VoltageMeasurement(meas_assets, "OFF")
voltage_meas.run()
```

---

### 4.2 帶依賴的 Measurement

```python
class TemperatureMeasurement(Measurement):
    test_point_uids = ('temperature_test',)

    @classmethod
    def define_deps(cls):
        cls.deps = (VoltageMeasurement,)  # 依賴電壓測量

    def measure(self):
        # 獲取電壓測量的結果
        voltage = meas_assets.test_point_map['voltage_test'].value

        # 計算溫度（基於電壓）
        temperature = voltage * 0.5 + 25.0

        # 執行測試點
        self.test_points.temperature_test.execute(temperature, "OFF")
```

**使用**:
```python
# 解析依賴
resolve_deps([VoltageMeasurement, TemperatureMeasurement])

# 執行（會自動先執行 VoltageMeasurement）
temperature_meas.run()
```

---

### 4.3 使用 MeasurementList

```python
# 創建測量列表
measurement_list = MeasurementList()

# 添加測量
measurement_list.add(VoltageMeasurement(meas_assets, "OFF"))
measurement_list.add(CurrentMeasurement(meas_assets, "OFF"))
measurement_list.add(TemperatureMeasurement(meas_assets, "OFF"))

# 執行所有測量
measurement_list.run_measurements()
```

**執行順序**:
```
VoltageMeasurement → CurrentMeasurement → TemperatureMeasurement
```

---

### 4.4 Job 使用

```python
class InitializeJob(Job):
    def job(self):
        print("Initializing DUT...")
        subprocess.call(['python', 'init_dut.py'])
        time.sleep(3)
        print("Initialization complete")

class CleanupJob(Job):
    def job(self):
        print("Cleaning up...")
        subprocess.call(['python', 'cleanup_dut.py'])
        print("Cleanup complete")
```

**使用**:
```python
# 執行任務
init_job = InitializeJob()
init_job.run()

cleanup_job = CleanupJob()
cleanup_job.run()
```

---

## 五、典型 Measurement 實現模式分析

### 5.1 getSNMeasurement (SN 讀取測量)

```python
class getSNMeasurement(Measurement):
    test_point_uids = tuple()

    def __init__(self, meas_assets, test_point, switch, runAllTest,
                 TestParams, test_results):
        super().__init__(meas_assets)
        self.test_results = test_results

        # 覆蓋 test_point_uids
        self.test_point_uids = (test_point,)
        self.switch_select = switch
        self.runAllTest = runAllTest
        self.TestParams = TestParams

    def measure(self):
        if self.switch_select == 'console':
            # 設置測試時間
            self.test_points[self.test_point_uids[0]].TestDateTime = \
                datetime.datetime.utcnow().strftime('%Y%m%d_%H:%M:%S')

            # 檢查必要參數
            TestParams_str = ' '.join(self.TestParams)
            required_args = ['Command']
            missing_args = [arg for arg in required_args
                          if arg not in TestParams_str]

            if missing_args:
                response = f"Error: Missing arguments [{missing_args}]"
                self.test_points[self.test_point_uids[0]].execute(
                    response, self.runAllTest
                )
                return

            # 執行命令
            try:
                response = subprocess.check_output([
                    'python', './src/lowsheen_lib/ConSoleCommand.py',
                    str(self.test_point_uids), str(self.TestParams)
                ])
                response = response.splitlines()[0].decode()

                # 寫入 SN 文件
                if response != None:
                    with open('SN_file.txt', 'w') as f:
                        f.write(response)

                # 執行測試點
                self.test_points[self.test_point_uids[0]].execute(
                    response, self.runAllTest
                )
                self.test_results[self.test_point_uids[0]] = response

            except Exception as e:
                print("Exception:", e)
                response = "Error, stopping test."
                self.test_points[self.test_point_uids[0]].execute(
                    response, self.runAllTest
                )
                self.test_results[self.test_point_uids[0]] = response
```

**關鍵模式**:
1. 動態設置 `test_point_uids`（運行時確定）
2. 參數驗證
3. subprocess 調用外部腳本
4. 結果處理和存儲
5. 執行測試點
6. 錯誤處理

---

### 5.2 PowerSetMeasurement (電源設置測量)

```python
class PowerSetMeasurement(Measurement):
    test_point_uids = tuple()

    def __init__(self, meas_assets, test_point, switch, runAllTest,
                 TestParams, test_results, used_instruments):
        super().__init__(meas_assets)
        self.test_results = test_results
        self.used_instruments = used_instruments

        self.test_point_uids = (test_point,)
        self.switch_select = switch
        self.runAllTest = runAllTest
        self.TestParams = TestParams

    def measure(self):
        if self.switch_select == 'DAQ973A':
            # 設置測試時間
            self.test_points[self.test_point_uids[0]].TestDateTime = \
                datetime.datetime.utcnow().strftime('%Y%m%d_%H:%M:%S')

            # 參數驗證
            TestParams_str = ' '.join(self.TestParams)
            required_args = ['Instrument', 'Channel', 'Item']
            missing_args = [arg for arg in required_args
                          if arg not in TestParams_str]

            if missing_args:
                response = f"Error: Missing arguments [{missing_args}]"
                self.test_points[self.test_point_uids[0]].execute(
                    response, self.runAllTest
                )
                return

            # 記錄已使用儀器
            if self.TestParams['Instrument'] not in self.used_instruments:
                self.used_instruments[self.TestParams['Instrument']] = 'DAQ973A_test.py'

            try:
                # 執行設置命令
                response = subprocess.check_output([
                    'python', './src/lowsheen_lib/DAQ973A_test.py',
                    str(self.test_point_uids), str(self.TestParams)
                ])
                response = response.decode('utf-8')

                # 處理響應
                if '1' in response:
                    response = '1'
                else:
                    response = '0'

                # 執行測試點
                self.test_points[self.test_point_uids[0]].execute(
                    response, self.runAllTest
                )
                self.test_results[self.test_point_uids[0]] = response

            except subprocess.CalledProcessError as e:
                if e.returncode == 10:
                    response = "No instrument found"
                else:
                    print("Error:", e)
                    response = "Error, stopping test."

                self.test_points[self.test_point_uids[0]].execute(
                    response, self.runAllTest
                )
                self.test_results[self.test_point_uids[0]] = response

        # ... 其他儀器類型處理 (MODEL2303, MODEL2306, 34970A, ...)
```

**關鍵模式**:
1. 支持多種儀器類型（switch 模式）
2. 儀器使用追蹤（`used_instruments`）
3. 統一的錯誤處理
4. 響應標準化

---

### 5.3 CommandTestMeasurement (命令測試測量)

```python
class CommandTestMeasurement(Measurement):
    test_point_uids = tuple()

    def __init__(self, meas_assets, test_point, switch, runAllTest,
                 TestParams, test_results):
        super().__init__(meas_assets)
        self.test_results = test_results

        self.test_point_uids = (test_point,)
        self.switch_select = switch
        self.runAllTest = runAllTest
        self.TestParams = TestParams

    def measure(self):
        if self.switch_select == 'comport':
            # 設置測試時間
            self.test_points[self.test_point_uids[0]].TestDateTime = \
                datetime.datetime.utcnow().strftime('%Y%m%d_%H:%M:%S')

            TestParams_str = ' '.join(self.TestParams)
            required_args = ['Port', 'Baud', 'Command']

            # 條件參數
            if 'keyWord' in TestParams:
                required_args.extend(['keyWord', 'spiltCount', 'splitLength'])

            missing_args = [arg for arg in required_args
                          if arg not in TestParams_str]

            if missing_args:
                response_str = f"Error: Missing arguments [{missing_args}]"
                self.test_points[self.test_point_uids[0]].execute(
                    response_str, self.runAllTest
                )
                return

            try:
                # 提取參數
                args = {key: self.TestParams[key]
                        for key in list(self.TestParams.keys())[2:]}

                # 模式 1: 關鍵字提取
                if 'keyWord' in args and args['keyWord'] != '':
                    response = subprocess.check_output([
                        'python', './src/lowsheen_lib/ComPortCommand.py',
                        str(self.test_point_uids), str(self.TestParams)
                    ])
                    print(response.decode('utf-8').replace('\r\n', '\n'))

                    response_str = response.decode('utf-8').replace('\r\n', '\n')
                    keyWord = args['keyWord']
                    spiltCount = int(args['spiltCount'])
                    splitLength = int(args['splitLength'])

                    # 使用正則表達式提取
                    match = re.search(f'{re.escape(keyWord)}(.*)', response_str).group(1)

                    if match:
                        start_pos = spiltCount - 1
                        end_pos = start_pos + splitLength
                        if start_pos >= 0 and end_pos <= len(match):
                            response = match[start_pos:end_pos]
                        else:
                            response = "Error: spiltCount and splitLength out of bounds."
                    else:
                        response = f"Error: 'keyWord' not found in output."

                    response_str = response

                # 模式 2: 相等限制
                elif 'EqLimit' in args and args['EqLimit'] != '':
                    response = subprocess.check_output([
                        'python', './src/lowsheen_lib/ComPortCommand.py',
                        str(self.test_point_uids), str(self.TestParams)
                    ], encoding='utf-8')

                    response = response.replace('\r\n', '\n')
                    print(response)

                    lines = response.split('\n')
                    EqLimit = args['EqLimit']
                    found_line = ''

                    # 查找包含 EqLimit 的行
                    for line in lines:
                        if EqLimit in line:
                            found_line = line.splitlines()[0]

                    if not found_line:
                        # 查找錯誤信息
                        for line in lines:
                            if "Failed" in response:
                                found_line = line.splitlines()[0]
                        found_line = "[EqLimit] not found in output"

                    response_str = found_line

                else:
                    # 模式 3: 直接返回
                    response = subprocess.check_output([
                        'python', './src/lowsheen_lib/ComPortCommand.py',
                        str(self.test_point_uids), str(self.TestParams)
                    ])
                    response = response.decode('utf-8', errors='ignore').replace('\r\n', '')
                    print(response)

                    if isinstance(response, bytes):
                        response_str = response.decode('utf-8').replace('\r\n', '\n')
                    else:
                        response_str = response

                    response_str = response_str.replace('\n', '')

                    if args['LimitType'] == 'none':
                        response_str = ''

                # 執行測試點
                self.test_points[self.test_point_uids[0]].execute(
                    response_str, self.runAllTest
                )
                self.test_results[self.test_point_uids[0]] = response_str

            except subprocess.CalledProcessError as e:
                if e.returncode == 10:
                    response_str = "No comport found"
                else:
                    print("Error:", e)
                    response_str = "Error, stopping test."

                self.test_points[self.test_point_uids[0]].execute(
                    response_str, self.runAllTest
                )
                self.test_results[self.test_point_uids[0]] = response_str

        # ... 其他模式 (console, tcpip, PEAK)
```

**關鍵模式**:
1. 多種命令模式支持
2. 正則表達式提取
3. 行查找和匹配
4. 靈活的響應處理
5. 條件參數處理

---

## 六、執行流程詳細圖解

### 6.1 單個測量執行流程

```
┌─────────────────────────────────────────────────────────────┐
│ measurement.run()                                       │
├─────────────────────────────────────────────────────────────┤
│                                                       │
│ 1. 開始計時                                           │
│    tick = time.time()                                   │
│                                                       │
│    ↓                                                   │
│                                                       │
│ 2. 執行 setup()                                       │
│    ├── 初始化儀器                                      │
│    ├── 打開連接                                         │
│    └── 準備環境                                         │
│                                                       │
│    ↓                                                   │
│                                                       │
│ 3. 執行 measure() (核心)                              │
│    ├── 收集數據                                         │
│    │   └── subprocess.check_output([...])                 │
│    ├── 解析響應                                         │
│    │   ├── decode('utf-8')                              │
│    │   ├── 正則表達式提取                                 │
│    │   └── 行查找                                      │
│    └── 執行測試點                                       │
│        └── test_points[uid].execute(value, runAllTest)    │
│                                                       │
│    ↓                                                   │
│                                                       │
│ 4. 檢查測試點                                         │
│    └── check_test_points()                               │
│        └── 遍歷所有 test_point_uids                     │
│            └── 驗證 executed = True                       │
│                                                       │
│    ↓                                                   │
│                                                       │
│ 5. 執行 teardown() (總是執行)                         │
│    ├── 關閉連接                                         │
│    ├── 釋放資源                                         │
│    └── 清理環境                                         │
│                                                       │
│    ↓                                                   │
│                                                       │
│ 6. 結束計時並記錄                                      │
│    after = time.time()                                  │
│    elapsed = after - tick                               │
│    └── 寫入 result.txt                                  │
│                                                       │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 多測量執行流程 (MeasurementList)

```
┌─────────────────────────────────────────────────────────────┐
│ MeasurementList.run_measurements()                       │
├─────────────────────────────────────────────────────────────┤
│                                                       │
│ 1. 獲取有序測量列表                                     │
│    ordered = get_ordered_measurments(_measurements)       │
│                                                       │
│    ↓                                                   │
│    get_ordered_measurments():                            │
│    ├── 複製列表: meas_and_deps = measurements[:]         │
│    ├── 添加依賴: meas_and_deps.extend(meas.resolved_deps) │
│    ├── 去重: indexed_set = {i: meas for i, meas...}   │
│    └── 排序: sorted(indexed_set.items())                │
│                                                       │
│    ↓                                                   │
│                                                       │
│ 2. 依次執行測量                                       │
│    for meas in ordered_measurements:                      │
│        ├── print(meas)                                   │
│        └── meas.run()                                   │
│                                                       │
│        ↓ (每個測量重複 6.1 流程)                          │
│                                                       │
└─────────────────────────────────────────────────────────────┘
```

### 6.3 依賴解析流程

```
┌─────────────────────────────────────────────────────────────┐
│ 依賴定義階段                                            │
├─────────────────────────────────────────────────────────────┤
│                                                       │
│ class MeasurementA(Measurement):                          │
│     @classmethod                                       │
│     def define_deps(cls):                               │
│         cls.deps = tuple()                            │
│                                                       │
│ class MeasurementB(Measurement):                          │
│     @classmethod                                       │
│     def define_deps(cls):                               │
│         cls.deps = (MeasurementA,)  # 依賴 A        │
│                                                       │
│ class MeasurementC(Measurement):                          │
│     @classmethod                                       │
│     def define_deps(cls):                               │
│         cls.deps = (MeasurementA, MeasurementB)       │
│                                                       │
│    ↓                                                   │
│                                                       │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 依賴解析階段                                            │
├─────────────────────────────────────────────────────────────┤
│                                                       │
│ resolve_deps([MeasurementA, MeasurementB, MeasurementC]) │
│                                                       │
│ 對於每個測量:                                          │
│                                                       │
│ MeasurementA.resolve_deps():                              │
│     deps_resolver = type(                                │
│         'MeasurementA_deps_res',                         │
│         tuple(),  # A 無依賴                           │
│         {}                                               │
│     )                                                  │
│     resolved_deps = []  # A 無依賴                      │
│                                                       │
│ MeasurementB.resolve_deps():                              │
│     deps_resolver = type(                                │
│         'MeasurementB_deps_res',                         │
│         (MeasurementA.deps_resolver,)  # B 繼承 A 的 deps  │
│         {}                                               │
│     )                                                  │
│     resolved_deps = [MeasurementA]  # B 依賴 A        │
│                                                       │
│ MeasurementC.resolve_deps():                              │
│     deps_resolver = type(                                │
│         'MeasurementC_deps_res',                         │
│         (MeasurementA.deps_resolver, MeasurementB.deps_resolver,) │
│         {}                                               │
│     )                                                  │
│     resolved_deps = [MeasurementB, MeasurementA]  # C 依賴 B, B 依賴 A │
│                                                       │
│    ↓                                                   │
│                                                       │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 執行順序 (通過 MRO 自動確定)                          │
├─────────────────────────────────────────────────────────────┤
│                                                       │
│ get_ordered_measurments([A, B, C])                    │
│                                                       │
│ 結果: [A, B, C]                                      │
│                                                       │
│ 執行:                                                  │
│ 1. A (無依賴)                                        │
│ 2. B (依賴 A，A 已執行)                              │
│ 3. C (依賴 B，B 已執行；B 依賴 A，A 已執行)     │
│                                                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 七、設計模式分析

### 7.1 模板方法模式 (Template Method)

**應用**: `Measurement.run()`

**結構**:
```python
class Measurement:
    def run(self):  # 模板方法
        try:
            self.setup()      # 鉤子方法 1
            self.measure()    # 鉤子方法 2（抽象）
            self.check_test_points()  # 鉤子方法 3
        finally:
            self.teardown()  # 鉤子方法 4
```

**優點**:
- 定義執行骨架
- 子類只需實現 `measure()`
- 統一的錯誤處理
- 統一的時間記錄

---

### 7.2 策略模式 (Strategy)

**應用**: 測量實現的 switch 模式

**結構**:
```python
class PowerSetMeasurement(Measurement):
    def measure(self):
        if self.switch_select == 'DAQ973A':
            self._daq973a_logic()
        elif self.switch_select == 'MODEL2303':
            self._model2303_logic()
        elif self.switch_select == '34970A':
            self._34970a_logic()
        # ...
```

**優點**:
- 支持多種儀器類型
- 易於添加新類型
- 每種類型獨立處理

**改進建議**:
- 使用策略對象替換 if-elif 鏈
- 儀器工廠模式

---

### 7.3 工廠模式 (Factory)

**應用**: `new_test_point_map()` (在 test_point 模組)

**結構**:
```python
def new_test_point_map(limits_table):
    test_point_map = TestPointMap()
    for row in limits_table:
        test_point = TestPoint(*row)  # 工廠方法
        test_point_map.add_test_point(test_point)
    return test_point_map
```

---

### 7.4 依賴注入 (Dependency Injection)

**應用**: `meas_assets` 參數

**結構**:
```python
def __init__(self, meas_assets):
    self.test_point_map = meas_assets.test_point_map
    self.instruments = meas_assets.instruments  # 注入依賴
    self.dut_comms = meas_assets.dut_comms
```

**優點**:
- 鬆耦合
- 易於測試
- 資源集中管理

---

### 7.5 迭代器模式 (Iterator)

**應用**: `MeasurementList` 和測試點遍歷

**結構**:
```python
for uid, test_point in self.test_points.items():
    # 處理測試點

for meas in ordered_measurements:
    # 處理測量
```

---

### 7.6 責任鏈模式 (Chain of Responsibility)

**應用**: 測試點執行鏈

**結構**:
```python
def check_test_points(self):
    for uid, test_point in self.test_points.items():
        try:
            if not test_point.executed:
                # 如果有問題，繼續下一個
                raise MeaurementImplementationError(...)
        except:
            continue  # 跳過當前，繼續下一個
```

---

## 八、關鍵技術點

### 8.1 Canister 使用模式

```python
# 創建 Canister
self.test_points = Canister()

# 添加項目（字典風格）
self.test_points['test_point_1'] = test_point_1

# 訪問項目（屬性風格）
value = self.test_points.test_point_1
```

**優點**:
- 動態屬性訪問
- 更清晰的語法
- 保持字典的靈活性

---

### 8.2 subprocess 集成

```python
# 基本調用
response = subprocess.check_output([
    'python', './script.py', 'arg1', 'arg2'
])

# 解碼
response_str = response.decode('utf-8')

# 錯誤處理
try:
    response = subprocess.check_output([...])
except subprocess.CalledProcessError as e:
    if e.returncode == 10:
        # 特定錯誤處理
        pass
    else:
        # 一般錯誤處理
        pass
```

---

### 8.3 日期時間處理

```python
import datetime

# UTC 時間戳
test_time = datetime.datetime.utcnow().strftime('%Y%m%d_%H:%M:%S')

# 設置到測試點
self.test_points[uid].TestDateTime = test_time
```

---

### 8.4 正則表達式提取

```python
import re

# 提取關鍵字後的內容
pattern = f'{re.escape(keyWord)}(.*)'
match = re.search(pattern, response_str)

if match:
    extracted = match.group(1)
    start_pos = spiltCount - 1
    end_pos = start_pos + splitLength
    result = extracted[start_pos:end_pos]
```

---

### 8.5 條件參數處理

```python
TestParams_str = ' '.join(self.TestParams)
required_args = ['Command']

# 條件擴展
if 'keyWord' in TestParams:
    required_args.extend(['keyWord', 'spiltCount', 'splitLength'])

# 檢查缺失參數
missing_args = [arg for arg in required_args
              if arg not in TestParams_str]

if missing_args:
    response = f"Error: Missing arguments [{missing_args}]"
```

---

## 九、常見問題和最佳實踐

### 9.1 問題 1: 忘記執行所有測試點

**錯誤示例**:
```python
class BadMeasurement(Measurement):
    test_point_uids = ('test1', 'test2', 'test3')

    def measure(self):
        # 只執行了 test1
        value = collect_data()
        self.test_points.test1.execute(value, self.runAllTest)
        # 忘記執行 test2 和 test3
```

**結果**: `check_test_points()` 拋出異常

**修正**:
```python
class GoodMeasurement(Measurement):
    test_point_uids = ('test1', 'test2', 'test3')

    def measure(self):
        # 執行所有測試點
        value1 = collect_data_1()
        self.test_points.test1.execute(value1, self.runAllTest)

        value2 = collect_data_2()
        self.test_points.test2.execute(value2, self.runAllTest)

        value3 = collect_data_3()
        self.test_points.test3.execute(value3, self.runAllTest)
```

---

### 9.2 問題 2: 未正確處理異常

**錯誤示例**:
```python
class BadMeasurement(Measurement):
    def measure(self):
        # 無異常處理
        response = subprocess.check_output([...])
        # 如果失敗，會拋出異常
        self.test_points.test1.execute(response, self.runAllTest)
```

**修正**:
```python
class GoodMeasurement(Measurement):
    def measure(self):
        try:
            response = subprocess.check_output([...])
            response_str = response.decode('utf-8')
            self.test_points.test1.execute(response_str, self.runAllTest)
        except subprocess.CalledProcessError as e:
            # 處理特定錯誤
            if e.returncode == 10:
                response_str = "No instrument found"
            else:
                response_str = "Error, stopping test."
            self.test_points.test1.execute(response_str, self.runAllTest)
        except Exception as e:
            print("Exception:", e)
            response_str = "Error, stopping test."
            self.test_points.test1.execute(response_str, self.runAllTest)
```

---

### 9.3 問題 3: 混淆 `runAllTest` 參數

**說明**:
- `runAllTest = "ON"`: 繼續執行（失敗不停止）
- `runAllTest = "OFF"` 或其他: 失敗時停止

**正確用法**:
```python
def measure(self):
    value = collect_data()
    self.test_points.test1.execute(value, self.runAllTest)
```

**錯誤用法**:
```python
def measure(self):
    value = collect_data()
    self.test_points.test1.execute(value, True)  # 錯誤！應該用 self.runAllTest
```

---

### 9.4 問題 4: 未正確設置 test_point_uids

**錯誤示例**:
```python
class BadMeasurement(Measurement):
    test_point_uids = tuple()  # 錯誤：空元組

    def measure(self):
        # 嘗試訪問不存在的測試點
        self.test_points.test1.execute(value, self.runAllTest)  # KeyError!
```

**修正 1**:
```python
class GoodMeasurement1(Measurement):
    test_point_uids = ('test1', 'test2')  # 正確：在類層級定義
```

**修正 2**:
```python
class GoodMeasurement2(Measurement):
    test_point_uids = tuple()  # 默認空

    def __init__(self, meas_assets, test_point, ...):
        super().__init__(meas_assets)
        self.test_point_uids = (test_point,)  # 運行時設置
```

---

### 9.5 最佳實踐 1: 使用 teardown 釋放資源

```python
class GoodMeasurement(Measurement):
    def setup(self):
        # 打開資源
        self.serial_port = serial.Serial('COM3', 9600)
        self.daq = DAQ('192.168.1.100')

    def measure(self):
        # 使用資源
        response = self.serial_port.read(1024)
        self.test_points.test1.execute(response, self.runAllTest)

    def teardown(self):
        # 總是執行，確保資源釋放
        if hasattr(self, 'serial_port'):
            self.serial_port.close()
        if hasattr(self, 'daq'):
            self.daq.close()
```

---

### 9.6 最佳實踐 2: 參數驗證

```python
class GoodMeasurement(Measurement):
    def measure(self):
        # 驗證必要參數
        TestParams_str = ' '.join(self.TestParams)
        required_args = ['Param1', 'Param2']
        missing_args = [arg for arg in required_args
                      if arg not in TestParams_str]

        if missing_args:
            response = f"Error: Missing arguments [{missing_args}]"
            self.test_points.test1.execute(response, self.runAllTest)
            self.test_results['test1'] = response
            return  # 提前返回

        # 參數完整，繼續執行
        # ...
```

---

### 9.7 最佳實踐 3: 記錄測試結果

```python
class GoodMeasurement(Measurement):
    def __init__(self, meas_assets, test_point, ..., test_results):
        super().__init__(meas_assets)
        self.test_results = test_results  # 保存結果引用

    def measure(self):
        # 執行測試點
        self.test_points.test1.execute(value, self.runAllTest)

        # 保存結果
        self.test_results['test1'] = value
```

---

## 十、性能和擴展性分析

### 10.1 性能特徵

**優點**:
- 順序執行，資源競爭少
- 簡單的依賴管理
- 低內存開銷（測量完成後可釋放）

**缺點**:
- 無並行執行支持
- 大量測試點時較慢
- subprocess 調用開銷大

**改進建議**:
- 支持並行測量執行
- 批量 subprocess 執行
- 測量結果緩存

---

### 10.2 擴展性

**易於擴展的方面**:
- ✅ 添加新的 Measurement 子類
- ✅ 支持新的儀器類型
- ✅ 添加新的依賴關係
- ✅ 自定義 setup/teardown

**難以擴展的方面**:
- ❌ 修改核心執行流程
- ❌ 改變依賴解析邏輯
- ❌ 並行執行支持（需要大改動）

---

### 10.3 模組化程度

**高**:
- 清晰的職責分離
- 鬆耦合設計
- 可插拔的組件

**改進空間**:
- 儀器驅動可插拔
- 測試點執行器可配置
- 錯誤處理可定制

---

## 十一、潛在改進建議

### 11.1 代碼質量改進

#### 11.1.1 添加類型提示

**當前**:
```python
def __init__(self, meas_assets):
    self.test_points = Canister()
```

**建議**:
```python
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from polish.mfg_common.canister import Canister
    from polish.test_point.test_point_map import TestPointMap

def __init__(self, meas_assets: 'Canister') -> None:
    self.test_points: 'Canister' = Canister()
    self.test_point_map: 'TestPointMap' = meas_assets.test_point_map
```

---

#### 11.1.2 添加詳細的 docstrings

**當前**:
```python
def measure(self):
    raise MeaurementImplementationError()
```

**建議**:
```python
def measure(self) -> None:
    """
    Execute the measurement and feed data to test points.

    This method must be implemented by subclasses. It should:
    1. Collect data from DUT, fixtures, or instruments
    2. Execute all test points in test_point_uids
    3. Handle exceptions appropriately

    Raises:
        MeaurementImplementationError: If not implemented
        subprocess.CalledProcessError: If subprocess fails
        Exception: For other errors
    """
    raise MeaurementImplementationError(
        "Subclass must implement measure() method"
    )
```

---

#### 11.1.3 改進錯誤處理

**當前**:
```python
except:
    continue
```

**建議**:
```python
except KeyError as e:
    logger.warning(f"Test point not found: {e}")
    continue
except AttributeError as e:
    logger.error(f"Test point attribute error: {e}")
    raise
```

---

### 11.2 架構改進

#### 11.2.1 儀器工廠模式

**當前**:
```python
if self.switch_select == 'DAQ973A':
    self._daq973a_logic()
elif self.switch_select == 'MODEL2303':
    self._model2303_logic()
elif self.switch_select == '34970A':
    self._34970a_logic()
# ... 更多 if-elif
```

**建議**:
```python
# 儀器工廠
class InstrumentFactory:
    _registry = {}

    @classmethod
    def register(cls, instrument_type: str):
        def decorator(instrument_class):
            cls._registry[instrument_type] = instrument_class
            return instrument_class
        return decorator

    @classmethod
    def create(cls, instrument_type: str, *args, **kwargs):
        instrument_class = cls._registry.get(instrument_type)
        if not instrument_class:
            raise ValueError(f"Unknown instrument type: {instrument_type}")
        return instrument_class(*args, **kwargs)

# 儀器接口
class InstrumentDriver(ABC):
    @abstractmethod
    def set(self, **params) -> str:
        pass

# 具體實現
@InstrumentFactory.register('DAQ973A')
class DAQ973ADriver(InstrumentDriver):
    def set(self, **params) -> str:
        # 實現
        pass

# 使用
class PowerSetMeasurement(Measurement):
    def measure(self):
        driver = InstrumentFactory.create(
            self.TestParams['Instrument'],
            self.test_point_uids[0],
            self.runAllTest
        )
        response = driver.set(**self.TestParams)
        self.test_points[self.test_point_uids[0]].execute(
            response, self.runAllTest
        )
```

---

#### 11.2.2 測試點執行器

**當前**:
```python
self.test_points.test_point_1.execute(value, self.runAllTest)
self.test_points.test_point_2.execute(value, self.runAllTest)
self.test_points.test_point_3.execute(value, self.runAllTest)
```

**建議**:
```python
class TestPointExecutor:
    def __init__(self, test_points: Canister, runAllTest: str):
        self.test_points = test_points
        self.runAllTest = runAllTest

    def execute_all(self, data: dict) -> None:
        """
        Execute multiple test points with corresponding data.

        Args:
            data: {test_point_uid: value}
        """
        for uid, value in data.items():
            if uid in self.test_points:
                self.test_points[uid].execute(value, self.runAllTest)

# 使用
class MyMeasurement(Measurement):
    def measure(self):
        executor = TestPointExecutor(self.test_points, self.runAllTest)
        data = {
            'test1': value1,
            'test2': value2,
            'test3': value3
        }
        executor.execute_all(data)
```

---

### 11.3 功能增強

#### 11.3.1 支持並行測量

**建議**:
```python
from concurrent.futures import ThreadPoolExecutor

class ParallelMeasurementList(MeasurementList):
    def run_measurements(self, max_workers: int = 4):
        """
        Execute measurements in parallel (respecting dependencies).
        """
        # 解析依賴和執行順序
        execution_plan = self._build_execution_plan()

        # 並行執行無依賴的測量
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for level in execution_plan:
                executor.map(lambda m: m.run(), level)

    def _build_execution_plan(self) -> list:
        """
        Build execution plan with dependency levels.
        """
        # 實現拓撲排序
        pass
```

---

#### 11.3.2 測量重試機制

**建議**:
```python
from functools import wraps

def retry(max_retries: int = 3, delay: float = 1.0):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"Attempt {attempt + 1} failed, retrying..."
                        )
                        time.sleep(delay)
            raise last_exception
        return wrapper
    return decorator

# 使用
class MyMeasurement(Measurement):
    @retry(max_retries=3, delay=2.0)
    def measure(self):
        # 如果失敗會自動重試 3 次
        response = subprocess.check_output([...])
        self.test_points.test1.execute(response, self.runAllTest)
```

---

#### 11.3.3 測量結果緩存

**建議**:
```python
class MeasurementCache:
    def __init__(self):
        self._cache = {}

    def get(self, measurement_class: type, test_point: str) -> Any:
        key = (measurement_class.__name__, test_point)
        return self._cache.get(key)

    def set(self, measurement_class: type, test_point: str, value: Any) -> None:
        key = (measurement_class.__name__, test_point)
        self._cache[key] = value

    def clear(self) -> None:
        self._cache.clear()

# 在 Measurement 中使用
class CachedMeasurement(Measurement):
    def __init__(self, meas_assets, cache: MeasurementCache, ...):
        super().__init__(meas_assets)
        self.cache = cache

    def measure(self):
        # 檢查緩存
        cached_value = self.cache.get(type(self), 'test1')
        if cached_value is not None:
            logger.info("Using cached value")
            self.test_points.test1.execute(cached_value, self.runAllTest)
            return

        # 執行測量
        value = self._collect_data()
        self.test_points.test1.execute(value, self.runAllTest)

        # 緩存結果
        self.cache.set(type(self), 'test1', value)
```

---

### 11.4 測試增強

#### 11.4.1 添加單元測試

**建議**:
```python
# tests/test_measurement.py
import unittest
from polish import Measurement
from polish.mfg_common.canister import Canister

class MockMeasurement(Measurement):
    test_point_uids = ('test1', 'test2')

    def measure(self):
        self.test_points.test1.execute(10.5, "OFF")
        self.test_points.test2.execute("OK", "OFF")

class TestMeasurement(unittest.TestCase):
    def setUp(self):
        self.test_point_map = self._create_mock_test_point_map()
        self.meas_assets = Canister()
        self.meas_assets.test_point_map = self.test_point_map

    def _create_mock_test_point_map(self):
        # 創建模擬測試點映射
        pass

    def test_measure_execution(self):
        """測試測量執行"""
        meas = MockMeasurement(self.meas_assets)
        meas.run()

        # 驗證測試點已執行
        tp1 = self.test_point_map['test1']
        self.assertTrue(tp1.executed)
        self.assertEqual(tp1.value, 10.5)

    def test_missing_test_point_execution(self):
        """測試未執行測試點時拋出異常"""
        class IncompleteMeasurement(Measurement):
            test_point_uids = ('test1', 'test2')

            def measure(self):
                self.test_points.test1.execute(10.5, "OFF")
                # 忘記執行 test2

        meas = IncompleteMeasurement(self.meas_assets)
        with self.assertRaises(MeasurementImplementationError):
            meas.run()

if __name__ == '__main__':
    unittest.main()
```

---

## 十二、總結

### 優點

✅ **清晰的設計**
- 模板方法模式定義明確的執行流程
- 依賴注入提供鬆耦合
- Canister 提供靈活的屬性訪問

✅ **可擴展性**
- 易於添加新的測量類型
- 支持動態測試點
- 靈活的參數處理

✅ **實用性**
- 支持 subprocess 集成
- 自動時間記錄
- 統一的錯誤處理框架

✅ **依賴管理**
- 自動依賴解析
- 基於 Python MRO 的優雅實現
- 確保正確的執行順序

---

### 需要改進

⚠️ **代碼質量**
- 缺少類型提示
- 缺少詳細的 docstrings
- 魔法字符串（"ON"/"OFF"）
- 過多的 if-elif 鏈

⚠️ **錯誤處理**
- 裸露的 `except:` 語句
- 錯誤信息不夠詳細
- 缺少日誌記錄

⚠️ **性能**
- 無並行執行支持
- subprocess 調用開銷大
- 無測量結果緩存

⚠️ **測試**
- 缺少單元測試
- 缺少集成測試
- 缺少測量重試機制

⚠️ **架構**
- 儀器驅動耦合度高
- 測試點執行重複代碼多
- 依賴解析難以定制

---

### 適用場景

✅ **製造測試**
- ✅ 組件測試
- ✅ 系統測試
- ✅ 回歸測試

✅ **儀器控制**
- ✅ DAQ 測量
- ✅ 電源設置
- ✅ 串口通訊

✅ **數據處理**
- ✅ 數據收集
- ✅ 數據驗證
- ✅ 結果報告

---

## 十三、關鍵文件索引

| 文件路徑 | 行數 | 類數量 | 核心功能 |
|----------|------|--------|----------|
| `polish/measurement/measurement.py` | 160 | 4 | 測量框架核心 |
| `getSNMeasurement.py` | 123 | 1 | SN 讀取測量 |
| `PowerSetMeasurement.py` | 381 | 1 | 電源設置測量 |
| `PowerReadMeasurement.py` | ~300 | 1 | 電源讀取測量 |
| `CommandTestMeasurement.py` | 589 | 1 | 命令測試測量 |
| `OtherMeasurement.py` | 99 | 1 | 其他測量 |

---

## 十四、參考資源

### 內部依賴
- `polish.mfg_common.deps` - 依賴解析
- `polish.mfg_common.canister` - 動態屬性字典
- `polish.util_funcs` - 工具函數

### 外部依賴
- `subprocess` - 進程執行
- `time` - 時間處理
- `os` - 文件系統操作

### 設計模式參考
- [Template Method Pattern](https://refactoring.guru/design-patterns/template-method)
- [Strategy Pattern](https://refactoring.guru/design-patterns/strategy)
- [Factory Pattern](https://refactoring.guru/design-patterns/factory-method)

---

**文檔版本**: 1.0
**最後更新**: 2026-01-27
**分析者**: Claude Code
**審計者**: PDTool4 開發團隊
