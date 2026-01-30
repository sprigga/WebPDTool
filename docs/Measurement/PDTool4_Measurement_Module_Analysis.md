# PDTool4 測量模組架構分析

## 概述

本文檔詳細分析 PDTool4 系統中 `PDtool.py` 如何呼叫與整合各種測量相關模組，特別是 `oneCSV_atlas_2.py` 中的測量執行機制。

## 系統架構概覽

### 主要元件
1. **PDtool.py** - 主要GUI應用程式
2. **oneCSV_atlas_2.py** - 測量執行引擎
3. **Polish Framework** - 測量框架核心
4. **測量模組** - 各種測量實作

## 呼叫流程分析

### 1. PDtool.py 啟動流程

#### 1.1 主要類別
```python
class testThread(QThread):
    # 負責執行測試的執行緒
    def run(self):
        # 執行 oneCSV_atlas_2.py 或 oneCSV_atlas_2.exe
        child = self.execute_child_process('oneCSV_atlas_2.exe', 'oneCSV_atlas_2.py',
                               self.cfg.limits_atlas, self.barcode,
                               self.runAllTest, self.SFC_status)
```

#### 1.2 測試啟動機制
- 使用 `subprocess.check_output()` 執行測量引擎
- 支援 .exe 和 .py 兩種執行方式
- 傳遞參數：測試計畫檔案、條碼、測試模式、SFC狀態

### 2. oneCSV_atlas_2.py 測量引擎

#### 2.1 核心導入模組
```python
# Polish 框架核心
from polish import default_setup, default_teardown
from polish import generate_default_report
from polish import Measurement
from polish import Receipt
from polish.test_point import test_point

# 測量模組導入
import SFC_GONOGOMeasurement, PowerSetMeasurement, PowerReadMeasurement
import CommandTestMeasurement, getSNMeasurement, OPjudgeMeasurement
import OtherMeasurement, FinalMeasurement

# SFC功能模組
from SFCFunctions import SFCFunctions
```

#### 2.2 主要執行流程
```python
def main(script_name, limits_csv_filename, barcode, runAllTest, SFC_status):
    # 1. 初始化Polish框架
    polish_logger, test_point_map, meas_assets = default_setup(limits_csv_filename)
    
    # 2. 建立測試資料收集容器
    test_results = {}  # 測量值收集
    used_instruments = {}  # 使用儀器記錄
    
    # 3. 讀取並處理CSV測試計畫
    with open(limits_csv_filename, "r") as file:
        reader = csv.DictReader(file)
        
        # 4. 逐項執行測試
        for row in reader:
            uid = row['ID']
            exec_name = variable_dict['ExecuteName']
            case = variable_dict['case']
            TestParams = {key: value for key, value in variable_dict.items() if value}
            
            # 5. 根據ExecuteName分派到對應測量模組
            if exec_name == 'SFCtest':
                SFC_GONOGOMeasurement.MeasureSwitchON(...).run()
            elif exec_name == 'PowerSet':
                PowerSetMeasurement.MeasureSwitchON(...).run()
            elif exec_name == 'PowerRead':
                PowerReadMeasurement.MeasureSwitchON(...).run()
            # ... 其他測量類型
```

## 測量模組架構

### 1. Polish Framework 基礎架構

#### 1.1 Measurement 基礎類別
```python
class Measurement(DepsResolver):
    test_point_uids = tuple()  # 測試點識別碼
    
    def __init__(self, meas_assets):
        self.test_points = Canister()
        # 建立測試點對應關係
        
    def run(self):
        try:
            self.setup()    # 設置
            self.measure()  # 執行測量
            self.check_test_points()  # 檢查測試點
        finally:
            self.teardown()  # 清理
```

#### 1.2 測試點管理
- `test_point_map` - 管理所有測試點
- `test_points` - 儲存測量值與限制條件
- `execute()` - 執行測試點驗證

### 2. 各測量模組實作

#### 2.1 SFC測量模組 (SFC_GONOGOMeasurement.py)
```python
class SFC_GONOGOMeasurement(Measurement):
    def __init__(self, meas_assets, test_point, switch, runAllTest, TestParams, test_results):
        # 初始化SFC功能
        self.sfc_funcs = SFCFunctions()
        
    def measure(self):
        if self.switch_select == 'webStep1_2':
            response = self.sfc_funcs.sfc_Web_step1_txt()
        elif self.switch_select == 'URLStep1_2':
            response = self.sfc_funcs.sfc_url_step1_txt()
        # 執行測試點
        self.test_points[self.test_point_uids[0]].execute(response, self.runAllTest)
```

#### 2.2 電源設定測量 (PowerSetMeasurement.py)
- 負責儀器電源設定
- 支援多種電源供應器
- 記錄使用的儀器資訊

#### 2.3 電源讀取測量 (PowerReadMeasurement.py)
- 讀取電源相關參數
- 電壓、電流測量
- 功率計算

#### 2.4 指令測試測量 (CommandTestMeasurement.py)
- 執行各種儀器指令
- 序列埠通訊
- 網路通訊測試

## 測試執行機制

### 1. CSV驅動的測試執行

#### 1.1 CSV格式結構
| ID | ExecuteName | case | Command | UseResult | ... |
|----|-------------|------|---------|-----------|-----|
| test_001 | PowerSet | voltage_5v | SET:5.0V | | ... |
| test_002 | PowerRead | current | READ:CURR | test_001 | ... |

#### 1.2 動態參數處理
```python
# 原始指令
og_Command = "READ:CURR"

# 使用前一個測試結果
if 'UseResult' in TestParams:
    UseResult_key = TestParams['UseResult']
    UseResult = test_results[UseResult_key]
    edit_Command = og_Command + ' ' + UseResult
```

### 2. 測量模組分派機制

```python
# 根據ExecuteName分派到對應的測量類別
measurement_dispatch = {
    'SFCtest': SFC_GONOGOMeasurement.MeasureSwitchON,
    'PowerSet': PowerSetMeasurement.MeasureSwitchON,
    'PowerRead': PowerReadMeasurement.MeasureSwitchON,
    'CommandTest': CommandTestMeasurement.MeasureSwitchON,
    'getSN': getSNMeasurement.MeasureSwitchON,
    'OPjudge': OPjudgeMeasurement.MeasureSwitchON,
    'Other': OtherMeasurement.MeasureSwitchON
}

# 執行對應測量
if exec_name in measurement_dispatch:
    measurement_class = measurement_dispatch[exec_name]
    measurement_instance = measurement_class(
        meas_assets, str(uid), 
        switch=case, 
        runAllTest=runAllTest, 
        TestParams=TestParams, 
        test_results=test_results
    )
    measurement_instance.run()
```

## 資料流與狀態管理

### 1. 測量資料收集
```python
test_results = {}  # 格式: {'ID':'value','ID2':'value2',...}
used_instruments = {}  # 格式: {'儀器位置':'要執行的py'}
```

### 2. 測試點狀態追蹤
- **PASS** - 測試通過
- **FAIL** - 測試失敗
- **ERROR** - 執行錯誤

### 3. SFC整合
- WebService模式
- URL模式
- skip模式（SFC關閉時）

## 儀器資源管理

### 1. 儀器初始化與清理
```python
# 測試結束後儀器重置
for instrument_location, instrument_py in used_instruments.items():
    TestParams = {'Instrument': f'{instrument_location}'}
    subprocess.check_output([
        'python', f'./src/lowsheen_lib/{instrument_py}', 
        '--final', str(TestParams)
    ])
```

### 2. 支援的儀器類型
- 電源供應器 (Power Supply)
- 數位萬用表 (DMM)
- 示波器 (Oscilloscope)
- 信號產生器 (Signal Generator)
- 網路分析儀 (Network Analyzer)

## 錯誤處理與日誌

### 1. 異常處理機制
```python
try:
    # 測量執行
except (TestPointEqualityLimitFailure, TestPointLowerLimitFailure, TestPointUpperLimitFailure) as e:
    receipt.test_result = Receipt.FAIL
except Exception as e:
    receipt.test_result = Receipt.ERROR
    print(traceback.format_exc())
finally:
    # 清理與報告生成
    generate_default_report(test_point_map, 'info_vcu_serial_num')
    default_teardown()
```

### 2. 日誌記錄
- 測試開始/結束時間
- 測量值記錄
- 錯誤訊息追蹤
- 儀器操作日誌

## 結論

PDTool4的測量架構採用模組化設計，通過以下機制實現靈活的測試執行：

1. **CSV驅動** - 測試計畫完全由CSV檔案定義
2. **動態分派** - 根據ExecuteName動態載入對應測量模組
3. **Polish框架** - 提供統一的測量基礎設施
4. **資源管理** - 自動管理儀器資源的使用與清理
5. **錯誤處理** - 完整的錯誤捕捉與報告機制

這種架構使得系統具有高度的可擴展性和維護性，新增測量功能只需實作對應的測量類別並在分派表中註冊即可。

---

# WebPDTool 重構實現狀態

## 概述

本節分析 WebPDTool (backend/app/) 中對 PDTool4 測量模組的重構實現狀態，特別關注 Other Measurement 相關功能。

## 架構對照

### PDTool4 → WebPDTool 元件映射

| PDTool4 元件 | WebPDTool 元件 | 位置 |
|-------------|----------------|------|
| `oneCSV_atlas_2.py` | `test_engine.py` | `app/services/test_engine.py` |
| `OtherMeasurement.py` | `implementations.py` | `app/measurements/implementations.py` |
| Polish Framework | `BaseMeasurement` | `app/measurements/base.py` |
| `measurement_dispatch` | `MEASUREMENT_REGISTRY` | `app/measurements/implementations.py:310` |

## Other Measurement 重構狀態

### 已實現功能

#### 1. Wait 模式 ✅

**PDTool4 實現** (`OtherMeasurement.py:34-61`):
```python
def measure(self):
    if self.switch_select == 'wait':
        # 設定時間戳記
        TestDateTime = datetime.datetime.now(datetime.timezone.utc)

        # 呼叫外部子行程
        subprocess.check_output([
            'python', './src/lowsheen_lib/Wait_test.py',
            str(self.test_point_uids[0]), str(TestParams)
        ])
```

**WebPDTool 實現** (`implementations.py:278-304`):
```python
class WaitMeasurement(BaseMeasurement):
    async def execute(self) -> MeasurementResult:
        # 支援多種參數來源: wait_msec 或 WaitmSec
        wait_msec = (
            get_param(self.test_params, "wait_msec", "WaitmSec") or
            self.test_plan_item.get("wait_msec", 0)
        )

        # 參數驗證
        if not isinstance(wait_msec, (int, float)) or wait_msec <= 0:
            return self.create_result(
                result="ERROR",
                error_message=f"wait mode requires wait_msec > 0, got: {wait_msec}"
            )

        # 使用非阻塞 asyncio.sleep
        wait_seconds = wait_msec / 1000
        await asyncio.sleep(wait_seconds)

        return self.create_result(result="PASS", measured_value=Decimal("1.0"))
```

**改進點**:
- ✅ 從同步 `subprocess` 改為非阻塞 `asyncio.sleep`
- ✅ 移除外部依賴 `Wait_test.py`
- ✅ 統一錯誤處理機制

#### 2. Registry 映射 ✅

**位置**: `implementations.py:310-331`

```python
MEASUREMENT_REGISTRY = {
    "DUMMY": DummyMeasurement,
    "COMMAND_TEST": CommandTestMeasurement,
    "POWER_READ": PowerReadMeasurement,
    "POWER_SET": PowerSetMeasurement,
    "SFC_TEST": SFCMeasurement,
    "GET_SN": GetSNMeasurement,
    "OP_JUDGE": OPJudgeMeasurement,
    "WAIT": WaitMeasurement,          # wait 模式
    "OTHER": DummyMeasurement,        # Other 映射至 Dummy
    "FINAL": DummyMeasurement,
    # 小寫變體
    "wait": WaitMeasurement,
    "other": DummyMeasurement,
}
```

### 未實現功能

#### 1. MeasureSwitchON/OFF 繼電器控制 ❌

**PDTool4 原始功能**:
```python
class MeasureSwitchON(OtherMeasurement):
    def __init__(self, ...):
        self.relay_state = SWITCH_OPEN  # 0

class MeasureSwitchOFF(OtherMeasurement):
    def __init__(self, ...):
        self.relay_state = SWITCH_CLOSED  # 1
```

**WebPDTool 狀態**: 未實現

**建議實現**:
```python
class RelayMeasurement(BaseMeasurement):
    async def execute(self) -> MeasurementResult:
        relay_state = get_param(self.test_params, "relay_state", "case")
        # 繼電器控制邏輯
        # ...
```

#### 2. 機箱底座旋轉控制 (QThread) ❌

**PDTool4 原始功能** (`OtherMeasurement.py:81-98`):
```python
class MyThread_CW(QThread):
    def run(self):
        subprocess.check_output([
            'python', './chassis_comms/chassis_fixture_bat.py',
            '/dev/ttyACM0', '6', '1'  # 6=順時針, 1=指令
        ])

class MyThread_CCW(QThread):
    def run(self):
        subprocess.check_output([
            'python', './chassis_comms/chassis_fixture_bat.py',
            '/dev/ttyACM0', '9', '1'  # 9=逆時針, 1=指令
        ])
```

**WebPDTool 狀態**: 未實現

**建議實現**:
```python
class ChassisMeasurement(BaseMeasurement):
    async def execute(self) -> MeasurementResult:
        direction = get_param(self.test_params, "direction")  # CW/CCW
        # 非同步硬體控制
        process = await asyncio.create_subprocess_exec(
            'python', './chassis_comms/chassis_fixture_bat.py',
            '/dev/ttyACM0', '6' if direction == 'CW' else '9', '1'
        )
        await process.wait()
```

## 測量分派機制對照

### PDTool4 分派方式

```python
# oneCSV_atlas_2.py
if exec_name == 'Other':
    measurement_instance = OtherMeasurement.MeasureSwitchON(
        meas_assets, str(uid),
        switch=case,              # 決定行為模式
        runAllTest=runAllTest,
        TestParams=TestParams,
        test_results=test_results
    )
```

### WebPDTool 分派方式

```python
# measurement_service.py
test_command = test_plan_item.test_type
measurement_class = get_measurement_class(test_command)

measurement_instance = measurement_class(
    test_plan_item=test_plan_item,
    test_session_id=test_session_id,
    test_params=test_params,
    instrument_manager=instrument_manager
)

await measurement_instance.execute()
```

## PDTool4 相容性驗證

### 驗證邏輯實現

**WebPDTool** 完整實現 PDTool4 的驗證邏輯:

```python
# base.py: validate_result()
def validate_result(self, measured_value, lower_limit, upper_limit,
                   limit_type='both', value_type='float') -> Tuple[bool, str]:
    """
    7 種 limit_type: lower, upper, both, equality, inequality, partial, none
    3 種 value_type: string, integer, float
    """
```

### runAllTest 模式

**PDTool4 行為**: 失敗後繼續執行，收集所有錯誤

**WebPDTool 實現**:
```python
# measurement_service.py
if run_all_test:
    # 失敗不中斷，繼續執行
    test_results.append({
        "test_item_id": test_item_id,
        "status": "FAIL",
        "error": error_message
    })
else:
    # 失敗立即停止
    raise TestExecutionException(error_message)
```

## 總結對照表

| 功能類別 | PDTool4 | WebPDTool | 狀態 |
|---------|---------|-----------|------|
| **Wait 模式** | `OtherMeasurement.measure()` (wait) | `WaitMeasurement.execute()` | ✅ 完整 |
| **參數解析** | `TestParams['WaitmSec']` | `get_param(test_params, "wait_msec", "WaitmSec")` | ✅ 相容 |
| **非阻塞等待** | `subprocess` 外部呼叫 | `asyncio.sleep` 內建 | ✅ 改進 |
| **繼電器控制** | `MeasureSwitchON/OFF` | - | ❌ 待實現 |
| **機箱旋轉** | `MyThread_CW/CCW` | - | ❌ 待實現 |
| **CSV 驅動** | `oneCSV_atlas_2.py` | `test_engine.py` + CSV import | ✅ 完整 |
| **動態分派** | `measurement_dispatch` dict | `MEASUREMENT_REGISTRY` | ✅ 完整 |
| **測試點驗證** | `test_point.execute()` | `validate_result()` | ✅ 完整 |
| **7種 limit_type** | Polish framework | `BaseMeasurement.validate_result()` | ✅ 完整 |
| **runAllTest 模式** | `runAllTest` 參數 | `run_all_test` 參數 | ✅ 完整 |

## 後續實現建議

### 1. 繼電器控制實現

在 `implementations.py` 中新增:

```python
class RelayMeasurement(BaseMeasurement):
    """繼電器狀態控制測量"""

    async def execute(self) -> MeasurementResult:
        relay_state = get_param(self.test_params, "relay_state", "case")

        if relay_state in ["ON", "0", "SWITCH_OPEN"]:
            # 開啟繼電器邏輯
            pass
        elif relay_state in ["OFF", "1", "SWITCH_CLOSED"]:
            # 關閉繼電器邏輯
            pass

        return self.create_result(result="PASS")
```

### 2. 註冊到 Registry

```python
MEASUREMENT_REGISTRY = {
    # ...
    "RELAY": RelayMeasurement,
    "relay": RelayMeasurement,
}
```

### 3. 更新 command_map

```python
command_map = {
    # ...
    "MeasureSwitchON": "RELAY",
    "MeasureSwitchOFF": "RELAY",
}
```

## 架構演進洞察

`★ Insight ─────────────────────────────────────`
1. **同步到非同步架構**: PDTool4 使用同步 subprocess 呼叫外部腳本，WebPDTool 採用 FastAPI 非同步架構，使用 asyncio.sleep 取代外部 Wait_test.py，這是現代 Python 應用的標準演進模式。

2. **統一抽象層**: PDTool4 各測量模組直接繼承自 Polish.Measurement，WebPDTool 建立 BaseMeasurement 統一接口，支援 prepare/execute/cleanup 三階段生命週期，並集中實現 PDTool4 相容的驗證邏輯。

3. **去外部化設計**: PDTool4 依賴多個外部 Python 腳本 (Wait_test.py, chassis_fixture_bat.py)，WebPDTool 將核心功能內建於 implementations.py，降低維護複雜度並提升部署便利性。
`─────────────────────────────────────────────────`