# oneCSV_atlas_2.py 程式碼詳細分析

## 核心職能

這是一個**測試執行引擎**，負責讀取測試計畫 CSV 檔案並執行各種測量。

## 程式結構

### 1. 匯入模組 (1-23行)

```python
import sys
import time
import polish
import subprocess
import os
from polish import default_setup, default_teardown
from polish import generate_default_report
from polish import Measurement
import collections
import test_info
import traceback
# 測量模組
import SFC_GONOGOMeasurement
import PowerSetMeasurement
import PowerReadMeasurement
import CommandTestMeasurement
import getSNMeasurement
import OPjudgeMeasurement
import OtherMeasurement
import FinalMeasurement
from polish import Receipt
from SFCFunctions import SFCFunctions
from polish.test_point import test_point
import csv
```

**核心依賴**:

- **核心測試框架**: `polish` (測試基礎架構)
- **測量模組**: 8個測量類型 (SFC、PowerSet、PowerRead、CommandTest、getSN、OPjudge、Other、Final)
- **SFC整合**: `SFCFunctions` (Shop Floor Control 工廠生產控制系統)
- **工具**: subprocess (執行外部腳本)、csv (讀取測試計畫)

### 2. 範例測試類 (25-77行)

#### chassisTestOne (25-58行)

```python
class chassisTestOne(Measurement):
    test_point_uids = ('Test_one',)

    def OpJudgeCode(self):
        try:
            child = subprocess.check_output(['python', 'opJudge.py',], )
            print(child)
            output = child
        except:
            output = "None"
        return output

    def measure(self):
        curr = 0.5
        self.test_points.Test_one.execute(curr)
        try:
            child = subprocess.check_output(['python', 'OpJudgeUI/opJudge.py'])
            output = child
        except:
            output = "None"

        print('%s' % output)

        if '1' in output:
            print('pass')
        else:
            print('fail')
```

#### chassisTestTwo (61-68行)

```python
class chassisTestTwo(Measurement):
    test_point_uids = ('Test_two',)

    def measure(self):
        curr = 90.98657
        self.test_points.Test_two.execute(curr)
```

#### chassisTestThree (70-77行)

```python
class chassisTestThree(Measurement):
    test_point_uids = ('Test_three',)

    def measure(self):
        curr = 1
        self.test_points.Test_three.execute(curr)
```

**設計模式**:
- 繼承自 `Measurement` 基類
- 定義 `test_point_uids` 元組指定測試點識別碼
- 實作 `measure()` 方法執行測試
- 使用 `self.test_points.<uid>.execute(value)` 記錄測試結果

### 3. 全域變數 (79-80行)

```python
test_results = {}      # 蒐集測量值 {'ID':'value'}
used_instruments = {}  # 蒐集使用的儀器 {'位置':'腳本路徑'}
```

**用途**:
- `test_results`: 在不同測試項目間共享測量結果 (透過 UseResult 參數)
- `used_instruments`: 追蹤測試過程中使用的儀器，以便測試結束後重置

### 4. 主函式 main() (82-336行)

#### 函式簽章

```python
def main(script_name, limits_csv_filename, barcode, runAllTest, SFC_status):
```

**參數說明**:
- `script_name`: 腳本名稱
- `limits_csv_filename`: 測試計畫 CSV 檔案路徑
- `barcode`: 待測產品序號
- `runAllTest`: 是否執行所有測試 (True=失敗後繼續, False=失敗即停止)
- `SFC_status`: SFC 狀態 ("on" 或 "off")

#### 執行流程

```
參數輸入
  ↓
default_setup() 初始化測試環境 (86-90行)
  ↓
test_info.WriteInfo() 記錄測試資訊 (95-98行)
  ↓
建立 Receipt 物件 (103行)
  ↓
讀取測試計畫 CSV (106-128行)
  ├─ 標題重複檢查 (110-116行)
  └─ 測項 ID 重複檢查 (118-124行)
  ↓
逐行執行測試項目 (131-191行)
  ↓
異常處理 (197-204行)
  ├─ 測試點失敗 (TestPointEqualityLimitFailure 等)
  └─ 一般異常 (Exception)
  ↓
寫入 result.txt (211-214行)
  ↓
generate_default_report() 生成報告 (218行)
  ↓
重置所有使用過的儀器 (248-264行)
  ↓
SFC step3.4 交互 (278-327行)
  ├─ 收集失敗資訊 (282-297行)
  ├─ 呼叫 SFC API (301-308行)
  └─ 寫入最終測試狀態 (298-327行)
  ↓
default_teardown() 清理 (331行)
  ↓
列印測試收據 (333行)
  ↓
返回結果 (335行)
```

#### 支援的測試類型

| ExecuteName | 模組 | 功能 | 代碼位置 |
|------------|------|------|---------|
| SFCtest | SFC_GONOGOMeasurement | 工廠生產控制系統測試 | 158-171行 |
| PowerSet | PowerSetMeasurement | 電源設定 | 172-174行 |
| PowerRead | PowerReadMeasurement | 電源讀取/測量 | 175-177行 |
| CommandTest | CommandTestMeasurement | 指令測試 | 178-180行 |
| getSN | getSNMeasurement | 序號讀取 | 181-183行 |
| OPjudge | OPjudgeMeasurement | 操作判斷 | 184-186行 |
| Other | OtherMeasurement | 其他測量 | 187-189行 |

#### 關鍵邏輯

**1. UseResult 參數處理 (143-155行)**

```python
for key, value in TestParams.items():
    if 'Command' in key:
        og_Command = value
    if 'UseResult' in key:
        UseResult_key = value
        UseResult = test_results[UseResult_key]
        edit_Command = og_Command + ' ' + UseResult

if og_Command is not None and edit_Command is not None:
    for key in TestParams.keys():
        if 'Command' in key:
            TestParams[key] = edit_Command
            break
```

**功能**: 支援使用前面測試的結果作為後續測試的參數

**2. runAllTest 模式**

- 當 `runAllTest=True`: 執行所有測試項目，即使某些項目失敗
- 當 `runAllTest=False`: 遇到第一個失敗即停止測試

**3. 儀器重置 (248-264行)**

```python
for instrument_location, instrument_py in used_instruments.items():
    try:
        TestParams = {'Instrument': f'{instrument_location}'}
        subprocess.check_output(['python', f'./src/lowsheen_lib/{instrument_py}', '--final', str(TestParams)])
        print(f"  >>>>>  '{instrument_location}' instrument has been reset/closed")
    except Exception as e:
        print(f"Error occurred while resetting instrument at {instrument_location}: {e}")
```

**功能**: 測試結束後自動呼叫各儀器腳本的 `--final` 參數進行清理/關閉

**4. SFC整合 (278-327行)**

```python
if 'SFCway' in locals() and SFC_status.lower() == 'on':
    fail_info = test_point_map.get_fail_uid()
    # 收集失敗資訊
    if fail_info != None:
        fail_name = test_point_map.get_test_point(fail_info).name
        fail_val = test_point_map.get_test_point(fail_info).value
        final_error_msgs = f'{fail_name}'
        PASSorFAIL = 'FAIL'
    else:
        PASSorFAIL = 'PASS'

    sfc_funcs = SFCFunctions()
    if 'SFC' not in final_error_msgs:
        if SFCway == 'WebService':
            step4Res = sfc_funcs.sfc_Web_step3_txt(PASSorFAIL, testtime, final_error_msgs)
        elif SFCway == 'URL':
            step4Res = sfc_funcs.sfc_url_step3_txt(PASSorFAIL, testtime, final_error_msgs)

    if 'PASS' in step4Res:
        PASSorFAIL = 'PASS'
    else:
        PASSorFAIL = 'FAIL'
```

**功能**: 根據測試結果與 SFC 系統交互
- 支援兩種 SFC 連線方式: WebService 和 URL
- 上傳測試結果和失敗資訊
- 接收 SFC 系統的最終判斷

#### 異常處理

**測試點失敗 (197-199行)**:

```python
except (polish.test_point.test_point.TestPointEqualityLimitFailure,
        polish.test_point.test_point.TestPointLowerLimitFailure,
        polish.test_point.test_point.TestPointUpperLimitFailure) as e:
    print (str(e))
    receipt.test_result = Receipt.FAIL
```

**一般異常 (200-204行)**:

```python
except Exception as e:
    err_info = str(e)
    receipt.err_info = err_info
    receipt.test_result = Receipt.ERROR
    print (traceback.format_exc())
```

**特點**:
- 區分測試點失敗和一般異常
- 記錄完整錯誤堆疊追蹤
- 更新 Receipt 物件的狀態

#### 輸出

**1. result.txt**

位置: `/home/ubuntu/WebPDTool/PDTool4/result.txt`

內容範例:
```
--- TEST END ---
TEST STATUS = PASS
```

**2. reports.csv**

位置: `/home/ubuntu/WebPDTool/PDTool4/default_reports/reports.csv`

由 `generate_default_report()` 生成

**3. 控制台輸出**

- 測試計畫檔名
- 測試項目執行進度
- 測試結果 (PASS/FAIL)
- 儀器重置資訊
- SFC 交互結果
- 總測試時間

## 呼叫方式

### 命令列執行

```bash
uv run python oneCSV_atlas_2.py <limits_csv> <barcode> <runAllTest> <SFC_status>
```

**參數範例**:

```bash
uv run python oneCSV_atlas_2.py testPlan/Other/selfTest/UseResult_testPlan.csv TEST123 0 OFF
```

**參數說明**:

- `limits_csv`: 測試計畫 CSV 檔案路徑
- `barcode`: 待測產品序號
- `runAllTest`: `1` 執行所有測試，`0` 失敗即停止
- `SFC_status`: `ON` 啟用 SFC，`OFF` 禁用 SFC

### 模組匯入呼叫

```python
import oneCSV_atlas_2

result = oneCSV_atlas_2.main(
    script_name='oneCSV_atlas_2.py',
    limits_csv_filename='testPlan/IB/myTest.csv',
    barcode='SN123456',
    runAllTest=True,
    SFC_status='off'
)
```

## 設計特點

### 1. 動態測試分配

根據 CSV 中的 `ExecuteName` 欄位動態載入對應測量模組

**優點**:
- 不需修改程式碼即可新增測試類型
- 靈活的測試組合配置

### 2. 參數驅動

測試行為完全由 CSV 檔案控制

**CSV 結構**:
```
ID,ExecuteName,case,Command,UseResult,...(其他參數)
```

**範例**:
```
getSN,getSN,read,,
PowerSet,PowerSet,setVoltage,Command=VOLT 5.0,
PowerRead,PowerRead,readCurrent,UseResult=getSN,
```

### 3. 資料共享

`test_results` 字典讓測試項目間可以共享結果

**流程**:
1. 測試 A 完成後，將結果存入 `test_results['ID_A']`
2. 測試 B 透過 `UseResult=ID_A` 參數引用 A 的結果
3. B 的指令會自動注入 A 的結果值

### 4. 儀器管理

自動追蹤並清理使用的儀器資源

**機制**:
- 測試執行時記錄使用的儀器
- 測試結束後自動呼叫各儀器的清理腳本
- 支援 `--final` 參數標識清理動作

### 5. SFC 整合

與工廠生產控制系統無縫整合

**特性**:
- 支援 WebService 和 URL 兩種連線方式
- 自動上傳測試結果和失敗資訊
- 接收 SFC 系統的最終判斷

## 測試計畫 CSV 格式

### 必要欄位

| 欄位 | 說明 | 範例 |
|------|------|------|
| ID | 測試項目識別碼 | `getSN`、`VoltageTest` |
| ExecuteName | 執行的測試類型 | `PowerSet`、`CommandTest` |
| case | 測試案例名稱 | `setVoltage`、`readCurrent` |

### 可選欄位

| 欄位 | 說明 | 範例 |
|------|------|------|
| Command | 測試指令 | `VOLT 5.0` |
| UseResult | 引用前面測試的結果 | `getSN` |
| Instrument | 儀器位置 | `POWER1` |
| LowerLimit | 下限 | `4.8` |
| UpperLimit | 上限 | `5.2` |

### 範例 CSV

```csv
ID,ExecuteName,case,Command,LowerLimit,UpperLimit,Unit,Instrument Location
getSN,getSN,read,,,,
PowerSet,PowerSet,setVoltage,Command=VOLT 5.0,,,POWER1
PowerRead,PowerRead,readVoltage,UseResult=getSN,4.8,5.2,V,POWER1
CommandTest,CommandTest,sendCMD,Command=CMD001,,,
```

## 與其他模組的互動

### 1. polish 框架

```python
from polish import default_setup, default_teardown
from polish import generate_default_report
from polish import Receipt
```

- `default_setup()`: 初始化測試環境
- `default_teardown()`: 清理測試環境
- `generate_default_report()`: 生成測試報告
- `Receipt`: 測試收據物件

### 2. 測量模組

所有測量模組都實作相同的介面:

```python
MeasureSwitchON(meas_assets, uid, switch, runAllTest, TestParams, test_results, used_instruments).run()
```

**共同參數**:
- `meas_assets`: 測試資源管理器
- `uid`: 測試項目識別碼
- `switch`: 測試案例名稱
- `runAllTest`: 是否執行所有測試
- `TestParams`: 測試參數字典
- `test_results`: 測試結果字典
- `used_instruments`: 使用的儀器字典

### 3. SFC 系統

```python
from SFCFunctions import SFCFunctions

sfc_funcs = SFCFunctions()
step4Res = sfc_funcs.sfc_Web_step3_txt(PASSorFAIL, testtime, final_error_msgs)
```

**方法**:
- `sfc_Web_step3_txt()`: WebService 方式交互
- `sfc_url_step3_txt()`: URL 方式交互

## 擴展開發

### 新增測試類型

1. 建立新的測量模組: `MyMeasurement.py`

```python
from polish import Measurement

class MyMeasurement(Measurement):
    test_point_uids = ('my_test_point',)

    def measure(self):
        # 執行測試邏輯
        result = perform_my_test()
        self.test_points.my_test_point.execute(result)

class MeasureSwitchON:
    def __init__(self, meas_assets, uid, switch, runAllTest, TestParams, test_results, used_instruments):
        # 初始化參數

    def run(self):
        # 執行測試邏輯
```

2. 在 `oneCSV_atlas_2.py` 中匯入

```python
import MyMeasurement
```

3. 在 main() 中新增執行邏輯

```python
elif exec_name == 'MyTest':
    MyMeasurement.MeasureSwitchON(meas_assets, str(uid), switch=case, runAllTest=runAllTest, TestParams=TestParams, test_results=test_results).run()
```

4. 在測試計畫 CSV 中設定

```csv
ID,ExecuteName,case,...
MyTest,MyTest,myCase,...
```

## 故障排除

### 常見問題

1. **CSV 檔案格式錯誤**
   - 檢查標題是否重複
   - 檢查 ID 是否重複
   - 檢查分隔符號是否正確 (逗號)

2. **測試點失敗**
   - 檢查測試值是否在規格範圍內
   - 檢查儀器是否正常連線
   - 檢查測試參數是否正確

3. **SFC 連線失敗**
   - 檢查 SFC 設定檔 (test_xml.ini)
   - 檢查網路連線
   - 檢查 SFC 服務是否運作

4. **儀器無法重置**
   - 檢查儀器腳本是否存在
   - 檢查 `--final` 參數處理邏輯
   - 檢查儀器通訊設定

## 版本資訊

- **檔案**: `/home/ubuntu/WebPDTool/PDTool4/oneCSV_atlas_2.py`
- **行數**: 344 行
- **最後更新**: 2024年6月13日
- **Python 版本**: 3.x (使用 uv 管理)
