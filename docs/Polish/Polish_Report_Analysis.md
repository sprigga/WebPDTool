# Polish Reports 模組分析

> 分析日期: 2026-01-28
> 版本: PDTool4
> 目錄: `polish/reports/`

---

## 📋 目錄結構

```
polish/reports/
├── __init__.py              # 模組導出（空檔案）
├── default_report.py        # CSV 報告生成器 (120 行)
├── print_receipt.py         # 收據打印格式化 (139 行)
└── thermal_printer.py       # 熱敏打印機驅動 (86 行)
```

---

## 一、模組概覽

**polish/reports/** 是報告生成模組，提供三種報告輸出方式：

| 組件 | 功能 | 輸出格式 |
|------|------|----------|
| **default_report.py** | CSV 報告生成 | `.csv` 檔案 |
| **print_receipt.py** | 測試摘要打印 | 控制台文本 / 熱敏打印機 |
| **thermal_printer.py** | 打印機驅動 | Windows/Linux 熱敏打印機 |

**核心特點**：
- ✅ CSV 格式測試報告生成
- ✅ 支持序列號作為文件名
- ✅ 自動時間戳格式化
- ✅ 收據格式化打印（30 字符寬度）
- ✅ 跨平台打印機支持（Windows/Linux）
- ✅ 結果編碼（P/F/空格）

---

## 二、default_report.py - CSV 報告生成器

### 2.1 檔案信息

| 屬性 | 值 |
|------|-----|
| 行數 | 120 |
| 主要函數 | `generate_default_report()` |
| 內部類 | `TestPoint` (本地類，非同名外類) |
| 依賴 | `csv`, `os`, `time`, `datetime`, `operator` |

### 2.2 常量定義

```python
TEST_NAME = 'atlas'                    # 測試名稱（預設）
REPORT_NAME = 'dflt'                   # 報告名稱（預設）
FILENAME_TEMPLATE = '{serial_num}_{date_and_time}.csv'  # 文件名模板
```

**文件名範例**：
```
0202190200063_26-01-28_14:30:45.csv
```

### 2.3 TestPoint 類（本地類）

**注意**：這是一個**本地類**（local class），與 `polish/test_point/test_point.py` 中的 `TestPoint` 是不同的類。

#### 構造函數

```python
def __init__(
    self,
    uid,                  # 唯一標識符
    value,                # 測量值
    unit,                 # 單位
    passed,               # 通過狀態 (True/False/None)
    equality_limit,       # 相等限制
    upper_limit,          # 上限
    lower_limit           # 下限
)
```

#### 比較運算符重載

```python
def __lt__(self, other):   # 小於
    return self.value < other.value

def __gt__(self, other):   # 大於
    return self.value > other.value

def __le__(self, other):   # 小於等於
    return self.value <= other.value

def __ge__(self, other):   # 大於等於
    return self.value >= other.value

def __eq__(self, other):   # 等於
    return self.value == other.value

def __ne__(self, other):   # 不等於
    return self.value != other.value
```

**用途**：允許對 TestPoint 對象進行排序（基於 `value`）

**問題**：重載的比較運算符實際上在代碼中**沒有被使用**

### 2.4 generate_default_report() 函數

#### 函數簽名

```python
def generate_default_report(
    test_point_map,          # 測試點映射對象
    uid_serial_num,          # 序列號測試點 UID
    test_name = TEST_NAME,   # 測試名稱
    report_name = REPORT_NAME,  # 報告名稱
    date_and_time = None,    # 日期時間（可選）
    leader_path = 'default_reports',  # 報告目錄
    filename_template = FILENAME_TEMPLATE  # 文件名模板
)
```

#### 執行流程

```
1. 獲取序列號
   │
   ├─ 從 test_point_map 獲取 uid_serial_num 的 value
   │   ├─ 成功：使用該值作為 serial_num
   │   └─ 失敗：使用 'Default_SN'
   │
2. 處理日期時間
   │
   ├─ 如果 date_and_time 為 None
   │   └─ 使用當前 UTC 時間
   ├─ 如果 date_and_time 是 datetime 對象
   │   └─ 轉換為 struct_time
   └─ 格式化為 DATE_TIME_FORMAT
   │
3. 遍歷所有測試點
   │
   ├─ 獲取測試點狀態
   │   │
   │   ├─ passed = True  → 'P' (Pass)
   │   ├─ passed = False → 'F' (Fail)
   │   └─ passed = None  → ' ' (未執行)
   │
   ├─ 只記錄已執行的測試點（P 或 F）
   │   │
   │   ├─ 處理限制值
   │   │   ├─ equality_limit → None → ' '
   │   │   ├─ upper_limit → None → ' '
   │   │   └─ lower_limit → None → ' '
   │   │
   │   └─ 處理測量值
   │       ├─ None → ''
   │       └─ 非空 → 替換空格為下劃線
   │
   └─ 添加到報告列表
       │
       每行包含：
       ├─ ItemKey
       ├─ ID (unique_id)
       ├─ LL (lower_limit)
       ├─ UL (upper_limit)
       ├─ TestValue
       ├─ TestDateTime
       └─ Result (passed)
       │
4. 生成文件路徑
   │
   ├─ 使用 setup_path() 處理 leader_path
   ├─ 使用 filename_template 格式化文件名
   ├─ 替換冒號為下劃線（Windows 兼容）
   └─ 合並路徑
   │
5. 寫入 CSV 文件
   │
   ├─ 打開文件（'w' 模式）
   ├─ 創建 csv.writer
   ├─ 寫入標題行
   │   └─ ['ItemKey', 'ID', 'LL', 'UL', 'TestValue', 'TestDateTime', 'Result']
   └─ 寫入數據行
```

#### CSV 格式示例

```csv
ItemKey,ID,LL,UL,TestValue,TestDateTime,Result
Voltage,Voltage_1,10.0,15.0,12.5,26-01-28_14:30:45,P
Current,Current_2,0.1,1.0,0.8,26-01-28_14:30:46,P
Resistance,Resistance_3,95,105,102,26-01-28_14:30:47,P
Temperature,Temp_4,-10,80,25.5,26-01-28_14:30:48,F
```

#### 結果編碼

| 狀態 | 編碼 | 說明 |
|------|------|------|
| 通過 | `P` | Pass |
| 失敗 | `F` | Fail |
| 未執行 | ` ` (空格) | Skipped/Not executed |

### 2.5 關鍵特性

#### 2.5.1 序列號提取

```python
try:
    serial_num = test_point_map.get_test_point(uid_serial_num).value
except:
    serial_num = 'Default_SN'
```

**異常處理**：如果測試點不存在，使用默認序列號

**TODO 注釋**：代碼中有 TODO 提示重構此功能為通用工具函數

#### 2.5.2 時間處理

```python
from ..mfg_common.constants import DATE_TIME_FORMAT
# DATE_TIME_FORMAT = '%y-%m-%d_%H:%M:%S'
```

**支持的時間格式**：
1. `None` → 使用當前 UTC 時間
2. `datetime` 對象 → 轉換為 `struct_time`
3. `struct_time` → 直接格式化

**示例**：
```python
# 當前時間
'26-01-28_14:30:45'

# datetime 對象
datetime.datetime(2026, 1, 28, 14, 30, 45)
  ↓
'26-01-28_14:30:45'
```

#### 2.5.3 測量值處理

```python
TestValue = test_point.value.replace(' ', '_') if test_point.value is not None else ''
```

**處理邏輯**：
- `None` → 空字符串
- 非空值 → 替換空格為下劃線

**範例**：
```
'12.5 V'    → '12.5_V'
'OK'        → 'OK'
'Pass Test' → 'Pass_Test'
```

#### 2.5.4 限制值處理

```python
eql = ' ' if test_point.equality_limit is None else test_point.equality_limit
ul = ' ' if test_point.upper_limit is None else test_point.upper_limit
ll = ' ' if test_point.lower_limit is None else test_point.lower_limit
```

**邏輯**：如果限制值為 `None`，使用空格代替

**範例**：
```
equality_limit = 'OK'      → 'OK'
upper_limit = None          → ' '
lower_limit = 10.0          → '10.0'
```

### 2.6 依賴關係

```python
from ..mfg_common.constants import DATE_TIME_FORMAT
from ..mfg_common.path_utils import setup_path
```

**依賴模組**：
- `mfg_common.constants` - 時間格式常量
- `mfg_common.path_utils` - 路徑設置工具

### 2.7 潛在問題

#### 問題 1：本地 TestPoint 類未使用

**代碼**：
```python
class TestPoint:
    def __init__(self, uid, value, unit, passed, equality_limit, upper_limit, lower_limit):
        ...

    def __lt__(self, other):
        return self.value < other.value
    # ... 其他比較運算符
```

**問題**：
- 定義了本地 `TestPoint` 類
- 重載了所有比較運算符
- 但**從未在代碼中使用**這個類
- 實際使用的是從 `test_point_map` 獲取的測試點對象

**影響**：
- 增加了代碼複雜度
- 可能導致混淆（與同名外類）

#### 問題 2：註釋的代碼未清理

**代碼**：
```python
#kevin
# FILENAME_TEMPLATE = '{test_name}_{serial_num}_{report_name}_{date_and_time}.csv'
```

**問題**：舊的文件名模板被註釋掉但未刪除

#### 問題 3：異常處理過於寬泛

**代碼**：
```python
try:
    serial_num = test_point_map.get_test_point(uid_serial_num).value
except:
    serial_num = 'Default_SN'
```

**問題**：使用裸 `except` 捕獲所有異常

**建議**：
```python
try:
    serial_num = test_point_map.get_test_point(uid_serial_num).value
except (AttributeError, KeyError):
    serial_num = 'Default_SN'
```

#### 問題 4：註釋掉的標題行

**代碼**：
```python
# report_writer.writerow(['ID', 'Unit', 'Passed', 'Equality Limit', 'Upper Limit', 'Lower Limit', 'Value'])
```

**問題**：舊的 CSV 標題格式未清理

---

## 三、print_receipt.py - 收據打印格式化

### 3.1 檔案信息

| 屬性 | 值 |
|------|-----|
| 行數 | 139 |
| 主要類 | `Receipt` |
| 依賴 | `mfg_common.canister`, `time.strftime` |
| 平台 | 跨平台（Windows/Linux） |

### 3.2 常量定義

```python
DATE_TIME_FMT = '%y/%m/%d %H:%M:%S'  # 日期時間格式
TEST_GROUP = 'atlas_test'             # 測試組名稱
```

### 3.3 Receipt 類

#### 3.3.1 類屬性

```python
class Receipt:
    # 失敗信息模板
    template = """----------
FItem:{fail_name},
FInfo:{fail_info},
FailVal:{fail_val},
Ulimit:{ulimit}, Llimit:{llimit}, Elimit:{elimit}
"""

    # 橫幅定義（PASS/FAIL/ERROR/SKIPPED）
    banner = {
        'PASS': """
     ---------------
         P A S S
     ---------------
""",
        'FAIL': """
     ***************
     **  F A I L  **
     ***************
""",
        'ERROR': """
     !!!!!!!!!!!!!!!!!
     !   E R R O R   !
     !!!!!!!!!!!!!!!!!
""",
        'SKIPPED': """
     !!!!!!!!!!!!!!!!!
     !   T E S T S   !
     ! S K I P P E D !
     !!!!!!!!!!!!!!!!!
"""
    }

    # 結果常量
    PASS = 'PASS'
    FAIL = 'FAIL'
    ERROR = 'ERROR'
    SKIPPED = 'SKIPPED'
```

#### 3.3.2 構造函數

```python
def __init__(self, meas_assets):
    # self.rec_printer = meas_assets.rec_printer  # 註釋掉的打印機配置
    self.test_result = None     # 測試結果（預設 None）
    self.err_info = ''          # 錯誤信息
```

**參數**：
- `meas_assets`: 測量資源對象（Canister）

**初始化狀態**：
- `test_result = None`: 測試結果未設定
- `err_info = ''`: 無錯誤信息

#### 3.3.3 print_summary() 方法

**方法簽名**：
```python
def print_summary(self, test_point_map):
```

**參數**：
- `test_point_map`: 測試點映射對象

**執行流程**：

```
1. 處理測試結果橫幅
   │
   ├─ 如果 self.test_result 為 None
   │   └─ 使用 get() 獲取默認值（避免 KeyError）
   └─ 否則
       └─ 直接從 banner 字典獲取
   │
2. 創建打印參數對象 (Canister)
   │
   prargs = Canister()
   │
   ├─ 設置測試組名稱
   │   └─ prargs.test_group = TEST_GROUP
   │
   ├─ 設置日期時間
   │   └─ prargs.date_time = strftime(DATE_TIME_FMT)
   │
   ├─ 設置序列號
   │   ├─ 嘗試從測試點獲取
   │   │   └─ 'info_vcu_serial_num'
   │   └─ 失敗使用默認值
   │       └─ 'Default_SN'
   │
   ├─ 設置執行統計
   │   └─ prargs.n_exec, prargs.n_total = test_point_map.count_executed()
   │
   └─ 設置測試結果
       └─ prargs.result = self.test_result
   │
3. 處理失敗信息
   │
   ├─ 獲取失敗的測試點 UID
   │   └─ fail_info = test_point_map.get_fail_uid()
   │
   ├─ 初始化失敗相關字段
   │   ├─ prargs.fail_name = ''
   │   ├─ prargs.fail_val = ''
   │   ├─ prargs.elimit = ''
   │   ├─ prargs.llimit = ''
   │   └─ prargs.ulimit = ''
   │
   ├─ 如果存在失敗信息
   │   │
   │   ├─ 獲取失敗測試點的詳細信息
   │   │   ├─ name
   │   │   ├─ value
   │   │   ├─ equality_limit
   │   │   ├─ lower_limit
   │   │   └─ upper_limit
   │   │
   │   └─ 填充到 prargs
   │
   └─ 否則
       └─ prargs.fail_info = ''
   │
4. 處理錯誤信息
   │
   ├─ 如果結果為 ERROR
   │   └─ prargs.fail_info = self.err_info
   └─ 否則
       └─ prargs.fail_info = fail_info
   │
5. 格式化並輸出
   │
   ├─ 使用 template.format(**prargs) 生成文本
   └─ print(text)  # 輸出到控制台
```

#### 3.3.4 輸出示例

**PASS 情況**：
```
----------
FItem:,
FInfo:,
FailVal:,
Ulimit: , Llimit: , Elimit:

     ---------------
         P A S S
     ---------------
```

**FAIL 情況**：
```
----------
FItem:Voltage_Test,
FInfo:voltage_1,
FailVal:18.5,
Ulimit:15.0, Llimit:10.0, Elimit:

     ***************
     **  F A I L  **
     ***************
```

**ERROR 情況**：
```
----------
FItem:,
FInfo:Instrument connection failed,
FailVal:,
Ulimit: , Llimit: , Elimit:

     !!!!!!!!!!!!!!!!!
     !   E R R O R   !
     !!!!!!!!!!!!!!!!!
```

### 3.4 關鍵特性

#### 3.4.1 安全的結果處理

**代碼**：
```python
if self.test_result is not None:
    res_banner = self.banner[self.test_result]
else:
    res_banner = self.banner.get(self.test_result, "default_value")
```

**用途**：
- 避免在 `test_result` 為 `None` 時觸發 `KeyError`
- 允許用戶在測試未完成時關閉測試窗口

**註釋**：
```python
# 新增看run完 按x可不可以不出現KeyError:None
```

#### 3.4.2 熱敏打印機支持（已註釋）

**代碼**：
```python
# from thermal_printer import ThermPrint

# if self.rec_printer != None:
#     if self.test_result == self.PASS or self.test_result == self.FAIL:
#         pr = ThermPrint()
#         pr.therm_print(text, self.rec_printer)
```

**狀態**：
- 熱敏打印機功能已註釋掉
- 但代碼邏輯仍然保留
- 可通過取消註釋啟用

#### 3.4.3 30 字符寬度設計

**文檔字串說明**：
```python
"""
Prints a test summary on a receipt printer. It handles 30 chars wide.
"""
```

**示例格式**：
```
000000000111111111122222222223
123456789012345678901234567890
------------------------------
SN:0202190200063
Test:vcu_test Tstr:TV03
SW:3.10 Fxtr:FV03
HWrev:17
PN:820-00122-01
Date:19/03/22 11:16:58
F4:0_15_10.bin
F3:f3-safety-test-gen2.hex
Lim:limits_vcu18fw24-26V.csv
NExec:22 of 100
Result:FAIL
Info:init_current_off_21
Ulimit:0.01
FailVal:1.3828
Llimit:-0.001

     ***************
     **  F A I L  **
     ***************
```

### 3.5 依賴關係

```python
from __future__ import print_function
from ..mfg_common.canister import Canister
from time import strftime
# from thermal_printer import ThermPrint  # 已註釋
```

**依賴模組**：
- `mfg_common.canister` - 動態屬性字典
- `time.strftime` - 時間格式化
- `thermal_printer` - 熱敏打印機驅動（可選）

### 3.6 潛在問題

#### 問題 1：註釋的代碼過多

**問題**：大量註釋掉的代碼未清理

**影響**：
- 增加代碼複雜度
- 可能導致混淆
- 增加維護成本

#### 問題 2：硬編碼的測試點 UID

**代碼**：
```python
test_point_map.get_test_point('info_vcu_serial_num').value
test_point_map.get_test_point('info_date_time').value
```

**問題**：
- 測試點 UID 硬編碼
- 缺乏靈活性

**建議**：使用參數化或配置

#### 問題 3：異常處理不一致

**代碼**：
```python
try:
    prargs.sn = test_point_map.get_test_point('info_vcu_serial_num').value
except:
    prargs.sn = 'Default_SN'
```

**問題**：使用裸 `except`

**建議**：使用具體異常類型

---

## 四、thermal_printer.py - 熱敏打印機驅動

### 4.1 檔案信息

| 屬性 | 值 |
|------|-----|
| 行數 | 86 |
| 主要類 | `ThermPrint` |
| 平台 | Windows (win32) / Linux (USB) |
| 打印機型號 | POS-58 / ZJ-58 |

### 4.2 硬件信息

**打印機型號**：
- POS-58 USB thermal receipt printer
- USB Vendor ID: `0x0416`
- USB Product ID: `0x5011`
- Amazon 購買鏈接: https://www.amazon.com/dp/B016BD1D5K
- Windows 驅動: http://www.zjiang.com/en/init.php/service/driver

**驅動名稱**：
- Neutral driver: `POS-58`
- Branded driver: `ZJ-58`

### 4.3 ThermPrint 類

#### 4.3.1 print_windows() 方法

**方法簽名**：
```python
def print_windows(self, data, printer_name):
```

**參數**：
- `data`: 要打印的文本數據
- `printer_name`: 打印機名稱（如 'POS-58' 或 'ZJ-58'）

**執行流程**：

```
1. 導入 Windows 打印機模組
   │
   └─ import win32print
       │
2. 打開打印機
   │
   hPrinter = win32print.OpenPrinter(printer_name)
   │
3. 檢查打印機狀態
   │
   status = win32print.GetPrinter(hPrinter)
   │
   ├─ 如果狀態 != PRINTER_READY (64)
   │   └─ 打印警告："WARNING: Printer not ready. Test result not printed."
   │       └─ 返回（不打印）
   │
   └─ 否則
       └─ 繼續打印
       │
4. 創建打印作業
   │
   hJob = win32print.StartDocPrinter(
       hPrinter,
       1,                           # 默認級別
       ("Test Results Summary",      # 文檔名
        None,                       # 輸出文件（None = 打印機）
        "RAW")                      # 數據類型（原始數據）
   )
   │
5. 開始打印頁面
   │
   win32print.StartPagePrinter(hPrinter)
   │
6. 寫入數據
   │
   win32print.WritePrinter(hPrinter, data)
   │
7. 結束打印頁面
   │
   win32print.EndPagePrinter(hPrinter)
   │
8. 結束打印作業
   │
   win32print.EndDocPrinter(hPrinter)
   │
9. 關閉打印機
   │
   win32print.ClosePrinter(hPrinter)
```

**常量**：
```python
PRINTER_READY = 64  # 打印機就緒狀態碼
```

**異常處理**：
```python
try:
    hJob = win32print.StartDocPrinter(...)
    try:
        win32print.StartPagePrinter(hPrinter)
        win32print.WritePrinter(hPrinter, data)
        win32print.EndPagePrinter(hPrinter)
    finally:
        win32print.EndDocPrinter(hPrinter)
finally:
    win32print.ClosePrinter(hPrinter)
```

**保證**：無論是否成功，都會確保打印機資源被釋放

#### 4.3.2 print_linux() 方法

**方法簽名**：
```python
def print_linux(self, data, usb_vid, usb_pid):
```

**參數**：
- `data`: 要打印的文本數據
- `usb_vid`: USB Vendor ID（預設 `0x0416`）
- `usb_pid`: USB Product ID（預設 `0x5011`）

**執行流程**：

```
1. 導入 USB 模組
   │
   import usb.core
   import usb.util
   │
2. 查找 USB 設備
   │
   dev = usb.core.find(idVendor=usb_vid, idProduct=usb_pid)
   │
   ├─ 如果 dev 為 None
   │   └─ 打印警告："WARNING: Printer not ready. Test result not printed."
   │       └─ 返回（不打印）
   │
   └─ 否則
       └─ 繼續
       │
3. 處理內核驅動
   │
   ├─ 檢查是否內核驅動激活
   │   │
   │   └─ dev.is_kernel_driver_active(0)
   │       │
   │       ├─ 如果激活
   │       │   ├─ 標記需要重新附加
   │       │   │   └─ needs_reattach = True
   │       │   └─ 分離內核驅動
   │       │       └─ dev.detach_kernel_driver(0)
   │       │
   │       └─ 否則
   │           └─ needs_reattach = False
   │
4. 設置活動配置
   │
   dev.set_configuration()
   │
5. 獲取配置和接口
   │
   cfg = dev.get_active_configuration()
   intf = cfg[(0, 0)]  # 獲取接口 0
   │
6. 查找 OUT 端點
   │
   ep = usb.util.find_descriptor(
       intf,
       custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT
   )
   │
   ├─ 如果 ep 為 None
   │   └─ 打印警告："WARNING: USB Endpoint not found. Printer problem. Test result not printed."
   │       └─ 返回（不打印）
   │
   └─ 否則
       └─ 繼續
       │
7. 寫入數據
   │
   ep.write(data)
   │
8. 重置設備
   │
   dev.reset()
   │
9. 重新附加內核驅動（如果需要）
   │
   if needs_reattach:
       dev.attach_kernel_driver(0)
       print "Reattached USB device to kernel driver"
```

**Linux 依賴**：
```python
# 需要 udev 規則
# 用戶需要是 lp (line printer) 組成員
# 詳見: https://github.com/vpatron/usb_receipt_printer
```

#### 4.3.3 therm_print() 方法（統一接口）

**方法簽名**：
```python
def therm_print(
    self,
    data,
    printer_name='POS-58',
    usb_vid=0x0416,
    usb_pid=0x5011
):
```

**參數**：
- `data`: 要打印的文本數據
- `printer_name`: 打印機名稱（Windows）
- `usb_vid`: USB Vendor ID（Linux）
- `usb_pid`: USB Product ID（Linux）

**執行流程**：

```
1. 檢測平台
   │
   ├─ 'win32' in platform
   │   └─ 調用 print_windows(data, printer_name)
   │
   ├─ 'linux' in platform
   │   └─ 調用 print_linux(data, usb_vid, usb_pid)
   │
   └─ 其他平台
       └─ 斷言失敗：'Platform "%s" is not supported by receipt printer'
```

**平台檢測**：
```python
from sys import platform

if 'win32' in platform:
    # Windows
elif 'linux' in platform:
    # Linux
else:
    # 不支持
```

### 4.4 關鍵特性

#### 4.4.1 跨平台支持

| 平台 | 實現方式 | 依賴 |
|------|----------|------|
| Windows | `win32print` API | pywin32 |
| Linux | `usb.core` 直接訪問 | pyusb |

#### 4.4.2 Linux 內核驅動處理

**問題**：Linux 內核可能自動掛載 USB 設備

**解決方案**：
1. 檢查內核驅動是否激活
2. 如果激活，先分離驅動
3. 打印完成後重新附加驅動

**代碼**：
```python
needs_reattach = False
if dev.is_kernel_driver_active(0):
    needs_reattach = True
    dev.detach_kernel_driver(0)

# ... 打印操作 ...

if needs_reattach:
    dev.attach_kernel_driver(0)
```

#### 4.4.3 資源管理

**Windows**：
```python
finally:
    win32print.ClosePrinter(hPrinter)
```

**Linux**：
```python
dev.reset()
if needs_reattach:
    dev.attach_kernel_driver(0)
```

**保證**：無論是否成功，都會正確釋放資源

### 4.5 依賴關係

```python
from sys import platform
```

**可選依賴**：
- **Windows**: `pywin32` (win32print)
- **Linux**: `pyusb` (usb.core, usb.util)

### 4.6 使用示例

#### Windows 示例

```python
from polish.reports.thermal_printer import ThermPrint

pr = ThermPrint()
data = """
     ---------------
         P A S S
     ---------------
"""
pr.therm_print(data, printer_name='POS-58')
```

#### Linux 示例

```python
from polish.reports.thermal_printer import ThermPrint

pr = ThermPrint()
data = """
     ***************
     **  F A I L  **
     ***************
"""
pr.therm_print(data, usb_vid=0x0416, usb_pid=0x5011)
```

### 4.7 潛在問題

#### 問題 1：Python 2 print 語法

**代碼**：
```python
print "WARNING: Printer not ready. Test result not printed."
print "Reattached USB device to kernel driver"
```

**問題**：使用 Python 2 的 print 語法

**影響**：
- Python 3 不兼容
- 應該使用 `print()` 函數

**建議**：
```python
print("WARNING: Printer not ready. Test result not printed.")
print("Reattached USB device to kernel driver")
```

#### 問題 2：缺少文檔字符串

**問題**：類和方法沒有 docstring

**建議**：添加詳細的文檔說明

#### 問題 3：平台檢測不夠精確

**代碼**：
```python
if 'win32' in platform:
    ...
elif 'linux' in platform:
    ...
```

**問題**：
- 'win32' 也會匹配 'win32cygwin'
- 'linux' 也會匹配 'linux2', 'linux3'

**建議**：使用更精確的檢查
```python
if platform == 'win32':
    ...
elif platform.startswith('linux'):
    ...
```

---

## 五、模組整合分析

### 5.1 整合流程圖

```
測試完成
    ↓
┌─────────────────────────────────────┐
│ 1. CSV 報告生成                    │
│    (default_report.py)              │
│                                     │
│ generate_default_report(            │
│     test_point_map,                │
│     uid_serial_num,                 │
│     ...                            │
│ )                                   │
│      ↓                              │
│ ┌───────────────────────────────┐  │
│ │ • 獲取序列號                  │  │
│ │ • 格式化時間                 │  │
│ │ • 遍歷測試點                 │  │
│ │ • 生成 CSV 文件               │  │
│ └───────────────────────────────┘  │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 2. 收據打印                        │
│    (print_receipt.py)               │
│                                     │
│ receipt = Receipt(meas_assets)      │
│ receipt.test_result = 'PASS'/'FAIL' │
│ receipt.print_summary(             │
│     test_point_map                 │
│ )                                   │
│      ↓                              │
│ ┌───────────────────────────────┐  │
│ │ • 格式化失敗信息              │  │
│ │ • 生成橫幅                    │  │
│ │ • 輸出到控制台                │  │
│ │ • 可選：熱敏打印機            │  │
│ └───────────────────────────────┘  │
└─────────────────────────────────────┘
    ↓
[可選] 熱敏打印
    ↓
┌─────────────────────────────────────┐
│ 3. 打印機驅動                       │
│    (thermal_printer.py)             │
│                                     │
│ ThermPrint.therm_print(             │
│     data,                           │
│     printer_name / usb_vid, usb_pid │
│ )                                   │
│      ↓                              │
│ ┌───────────────────────────────┐  │
│ │ Windows:                      │  │
│ │ • win32print API              │  │
│ │ • 檢查打印機狀態              │  │
│ │ • 原始數據打印                │  │
│ ├───────────────────────────────┤  │
│ │ Linux:                        │  │
│ │ • USB 直接訪問                │  │
│ │ • 內核驅動處理                │  │
│ │ • USB 端點寫入               │  │
│ └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

### 5.2 數據流

```
test_point_map (TestPointMap)
    │
    ├─ generate_default_report()
    │   │
    │   ├─ 遍歷 test_point_map.get_dict().values()
    │   ├─ 提取每個測試點的：
    │   │   ├─ ItemKey
    │   │   ├─ unique_id
    │   │   ├─ lower_limit
    │   │   ├─ upper_limit
    │   │   ├─ value
    │   │   ├─ TestDateTime
    │   │   └─ passed
    │   │
    │   └─ 生成 CSV 文件
    │
    └─ Receipt.print_summary()
        │
        ├─ 獲取序列號
        │   └─ test_point_map.get_test_point('info_vcu_serial_num').value
        │
        ├─ 獲取執行統計
        │   └─ test_point_map.count_executed()
        │
        ├─ 獲取失敗信息
        │   └─ fail_info = test_point_map.get_fail_uid()
        │   │
        │   └─ 如果失敗：
        │       ├─ fail_name
        │       ├─ fail_val
        │       ├─ elimit
        │       ├─ llimit
        │       └─ ulimit
        │
        └─ 格式化輸出
```

### 5.3 調用示例

```python
from polish.reports.default_report import generate_default_report
from polish.reports.print_receipt import Receipt
from polish.reports.thermal_printer import ThermPrint

# 假設測試完成後
test_point_map = ...  # 測試點映射對象
meas_assets = ...     # 測量資源對象
uid_serial_num = 'info_vcu_serial_num'  # 序列號測試點 UID

# 1. 生成 CSV 報告
generate_default_report(
    test_point_map=test_point_map,
    uid_serial_num=uid_serial_num,
    test_name='atlas',
    report_name='dflt',
    leader_path='default_reports'
)

# 2. 打印收據
receipt = Receipt(meas_assets)
receipt.test_result = 'PASS'  # 或 'FAIL', 'ERROR', 'SKIPPED'
receipt.print_summary(test_point_map)

# 3. 可選：熱敏打印機打印
if receipt.rec_printer is not None:
    pr = ThermPrint()
    data = receipt.template.format(...)
    pr.therm_print(data, printer_name='POS-58')
```

### 5.4 與其他模組的依賴關係

```
polish/reports/
    │
    ├─ 依賴 ── polish/mfg_common/
    │   │
    │   ├─ constants (DATE_TIME_FORMAT)
    │   ├─ path_utils (setup_path)
    │   └─ canister (Canister)
    │
    ├─ 被依賴 ── 主程序
    │   │
    │   └─ oneCSV_atlas_2.py, measure_window.py 等
    │
    └─ 可選依賴 ── 打印機驅動
        │
        ├─ Windows: pywin32
        └─ Linux: pyusb
```

---

## 六、設計模式分析

### 6.1 策略模式 (Strategy)

**應用**：不同的報告生成策略

```python
# CSV 報告策略
def generate_default_report(...):
    # CSV 生成邏輯

# 收據打印策略
class Receipt:
    def print_summary(...):
        # 文本格式化邏輯
```

### 6.2 工廠模式 (Factory)

**應用**：文件名生成

```python
filename_template = '{serial_num}_{date_and_time}.csv'
filename = filename_template.format(**locals())
```

### 6.3 模板方法模式 (Template Method)

**應用**：打印機驅動的統一接口

```python
def therm_print(self, data, printer_name, usb_vid, usb_pid):
    if 'win32' in platform:
        self.print_windows(data, printer_name)    # 子方法 1
    elif 'linux' in platform:
        self.print_linux(data, usb_vid, usb_pid) # 子方法 2
```

### 6.4 適配器模式 (Adapter)

**應用**：跨平台打印機接口

```python
# Windows 適配器
def print_windows(self, data, printer_name):
    import win32print
    # Windows API 調用

# Linux 適配器
def print_linux(self, data, usb_vid, usb_pid):
    import usb.core
    # USB 直接訪問
```

---

## 七、測試場景覆蓋

### 7.1 CSV 報告生成場景

| 場景 | 輸入 | 預期輸出 | 覆蓋 |
|------|------|----------|------|
| 正常生成 | 有效 test_point_map | CSV 文件 | ✅ |
| 序列號不存在 | 無效 uid_serial_num | 使用 'Default_SN' | ✅ |
| 時間為 None | date_and_time=None | 使用當前時間 | ✅ |
| 時間為 datetime | datetime 對象 | 格式化時間 | ✅ |
| 測試點通過 | passed=True | 結果 'P' | ✅ |
| 測試點失敗 | passed=False | 結果 'F' | ✅ |
| 測試點未執行 | passed=None | 不記錄 | ✅ |
| 值為 None | value=None | 空字符串 | ✅ |
| 值含空格 | value='12.5 V' | '12.5_V' | ✅ |
| 限制為 None | limit=None | 空格 | ✅ |

### 7.2 收據打印場景

| 場景 | 輸入 | 預期輸出 | 覆蓋 |
|------|------|----------|------|
| PASS | test_result='PASS' | PASS 橫幅 | ✅ |
| FAIL | test_result='FAIL' | FAIL 橫幅 + 失敗信息 | ✅ |
| ERROR | test_result='ERROR' | ERROR 橫幅 + 錯誤信息 | ✅ |
| SKIPPED | test_result='SKIPPED' | SKIPPED 橫幅 | ✅ |
| 未設定 | test_result=None | 默認值（不報錯） | ✅ |
| 序列號不存在 | 無效測試點 | 'Default_SN' | ✅ |
| 有失敗 | get_fail_uid() 返回值 | 顯示失敗詳情 | ✅ |
| 無失敗 | get_fail_uid() 返回 None | 空失敗信息 | ✅ |

### 7.3 熱敏打印機場景

| 場景 | 平台 | 條件 | 預期行為 | 覆蓋 |
|------|------|------|----------|------|
| 正常打印 | Windows | 打印機就緒 | 成功打印 | ✅ |
| 打印機未就緒 | Windows | 狀態 != READY | 警告，不打印 | ✅ |
| 正常打印 | Linux | USB 設備存在 | 成功打印 | ✅ |
| 設備不存在 | Linux | find() 返回 None | 警告，不打印 | ✅ |
| 內核驅動激活 | Linux | is_kernel_driver_active() | 分離並重新附加 | ✅ |
| 內核驅動未激活 | Linux | 驅動未激活 | 直接打印 | ✅ |
| 端點未找到 | Linux | ep 為 None | 警告，不打印 | ✅ |
| 不支持平台 | macOS | platform 不匹配 | 斷言失敗 | ❌ |

---

## 八、性能分析

### 8.1 時間複雜度

| 操作 | 複雜度 | 說明 |
|------|--------|------|
| `generate_default_report()` | O(n) | n = 測試點數量 |
| `Receipt.print_summary()` | O(1) | 固定操作 |
| `ThermPrint.print_windows()` | O(1) | 系統調用 |
| `ThermPrint.print_linux()` | O(1) | USB 傳輸 |

### 8.2 空間複雜度

| 操作 | 複雜度 | 說明 |
|------|--------|------|
| `generate_default_report()` | O(n) | 報告列表大小 |
| `Receipt.print_summary()` | O(1) | 固定字符串 |
| CSV 文件 | O(n) | 測試點數量 |

### 8.3 I/O 操作

| 操作 | 類型 | 數量 |
|------|------|------|
| CSV 生成 | 文件寫入 | 1 次 |
| 收據打印 | 控制台輸出 | 1 次 |
| 打印機打印 | USB/打印機 | 1 次 |

### 8.4 性能瓶頸

**潛在瓶頸**：
1. **文件 I/O**：大量測試點時，CSV 寫入可能較慢
2. **打印機速度**：熱敏打印機的物理打印速度
3. **USB 傳輸**：Linux 下的 USB 數據傳輸

**優化建議**：
- 使用緩衝寫入
- 批量處理測試點
- 異步打印機操作

---

## 九、潛在改進建議

### 9.1 高優先級

#### 改進 1：移除未使用的本地 TestPoint 類

**問題**：`default_report.py` 中的本地 `TestPoint` 類未被使用

**影響**：
- 增加代碼複雜度
- 可能導致混淆

**建議**：
```python
# 刪除以下代碼（第 17-43 行）
class TestPoint:
    def __init__(self, uid, value, unit, passed, equality_limit, upper_limit, lower_limit):
        ...
```

#### 改進 2：修復 Python 2 print 語法

**問題**：`thermal_printer.py` 使用 Python 2 語法

**影響**：與 Python 3 不兼容

**建議**：
```python
# 修改前
print "WARNING: Printer not ready. Test result not printed."

# 修改後
print("WARNING: Printer not ready. Test result not printed.")
```

#### 改進 3：清理註釋代碼

**問題**：大量註釋的代碼未清理

**影響**：
- 增加維護成本
- 可能導致混淆

**建議**：刪除或移動到文檔

### 9.2 中優先級

#### 改進 4：改進異常處理

**問題**：使用裸 `except` 捕獲所有異常

**建議**：
```python
# default_report.py
try:
    serial_num = test_point_map.get_test_point(uid_serial_num).value
except (AttributeError, KeyError, TypeError):
    serial_num = 'Default_SN'

# print_receipt.py
try:
    prargs.sn = test_point_map.get_test_point('info_vcu_serial_num').value
except (AttributeError, KeyError, TypeError):
    prargs.sn = 'Default_SN'
```

#### 改進 5：添加類型提示

**問題**：缺少 Python 類型提示

**建議**：
```python
from typing import Optional, Dict, List

def generate_default_report(
    test_point_map: TestPointMap,
    uid_serial_num: str,
    test_name: str = TEST_NAME,
    report_name: str = REPORT_NAME,
    date_and_time: Optional[time.struct_time] = None,
    leader_path: str = 'default_reports',
    filename_template: str = FILENAME_TEMPLATE
) -> str:
    ...
```

#### 改進 6：參數化硬編碼值

**問題**：測試點 UID 硬編碼

**建議**：
```python
class Receipt:
    def __init__(
        self,
        meas_assets,
        serial_num_uid='info_vcu_serial_num',
        date_time_uid='info_date_time'
    ):
        self.serial_num_uid = serial_num_uid
        self.date_time_uid = date_time_uid
        ...
```

### 9.3 低優先級

#### 改進 7：添加文檔字符串

**問題**：缺少詳細的 docstring

**建議**：為所有公共類和方法添加 docstring

#### 改進 8：改進平台檢測

**問題**：平台檢測不夠精確

**建議**：
```python
from sys import platform

if platform == 'win32':
    # Windows
elif platform.startswith('linux'):
    # Linux
else:
    raise OSError(f'Platform "{platform}" is not supported')
```

#### 改進 9：添加日誌記錄

**問題**：警告信息直接打印到控制台

**建議**：使用 Python logging 模組

#### 改進 10：支持更多報告格式

**建議**：添加 JSON、XML、HTML 等格式支持

---

## 十、代碼質量評估

### 10.1 優點

| 優點 | 說明 |
|------|------|
| ✅ 職責清晰 | CSV 生成、格式化、打印驅動分離 |
| ✅ 跨平台支持 | Windows 和 Linux 打印機支持 |
| ✅ 錯誤處理 | 打印機未就緒時的優雅降級 |
| ✅ 資源管理 | 正確的 finally 塊和資源釋放 |
| ✅ 靈活性 | 可選的熱敏打印機功能 |

### 10.2 缺點

| 缺點 | 影響 |
|------|------|
| ⚠️ 代碼重複 | 本地 TestPoint 類與同名外類混淆 |
| ⚠️ 註釋代碼 | 大量未清理的註釋代碼 |
| ⚠️ Python 2 語法 | `thermal_printer.py` 不兼容 Python 3 |
| ⚠️ 異常處理 | 使用裸 `except` |
| ⚠️ 缺少文檔 | 類和方法缺少 docstring |
| ⚠️ 硬編碼值 | 測試點 UID 硬編碼 |

### 10.3 代碼複雜度

| 文件 | 行數 | 類數 | 函數數 | 複雜度 |
|------|------|------|--------|--------|
| `__init__.py` | 1 | 0 | 0 | 低 |
| `default_report.py` | 120 | 1 | 1 | 中 |
| `print_receipt.py` | 139 | 1 | 2 | 中 |
| `thermal_printer.py` | 86 | 1 | 3 | 中 |
| **總計** | **346** | **3** | **6** | **中** |

---

## 十一、使用場景

### 11.1 製造測試

**場景**：生產線上的產品測試

**流程**：
```
1. 產品上線
    ↓
2. 執行測試計劃
    ↓
3. 測試完成
    ↓
4. 生成 CSV 報告（存檔）
    ↓
5. 打印收據（操作員簽名）
    ↓
6. 產品下線
```

### 11.2 質量控制

**場景**：產品質量追蹤

**用途**：
- CSV 報告：數據分析、統計、追溯
- 收據打印：現場記錄、簽字確認

### 11.3 設備驗證

**場景**：設備校驗和驗證

**用途**：
- 生成測試報告
- 打印驗證結果

---

## 十二、關鍵 API 文檔

### 12.1 generate_default_report()

```python
def generate_default_report(
    test_point_map: TestPointMap,
    uid_serial_num: str,
    test_name: str = 'atlas',
    report_name: str = 'dflt',
    date_and_time: Optional[time.struct_time] = None,
    leader_path: str = 'default_reports',
    filename_template: str = '{serial_num}_{date_and_time}.csv'
) -> None
```

**功能**：生成 CSV 格式的測試報告

**參數**：
- `test_point_map`: 測試點映射對象
- `uid_serial_num`: 序列號測試點的 UID
- `test_name`: 測試名稱（默認 'atlas'）
- `report_name`: 報告名稱（默認 'dflt'）
- `date_and_time`: 日期時間（可選，默認當前時間）
- `leader_path`: 報告目錄（默認 'default_reports'）
- `filename_template`: 文件名模板

**返回值**：無

**異常**：可能拋出文件 I/O 異常

### 12.2 Receipt.print_summary()

```python
class Receipt:
    def __init__(self, meas_assets: Canister):
        ...

    def print_summary(self, test_point_map: TestPointMap) -> None:
        ...
```

**功能**：打印測試摘要到控制台

**屬性**：
- `test_result`: 測試結果（'PASS', 'FAIL', 'ERROR', 'SKIPPED'）
- `err_info`: 錯誤信息

**方法**：
- `print_summary(test_point_map)`: 打印測試摘要

**參數**：
- `test_point_map`: 測試點映射對象

**返回值**：無

### 12.3 ThermPrint.therm_print()

```python
class ThermPrint:
    def therm_print(
        self,
        data: str,
        printer_name: str = 'POS-58',
        usb_vid: int = 0x0416,
        usb_pid: int = 0x5011
    ) -> None:
        ...
```

**功能**：通過熱敏打印機打印數據

**參數**：
- `data`: 要打印的文本數據
- `printer_name`: 打印機名稱（Windows）
- `usb_vid`: USB Vendor ID（Linux）
- `usb_pid`: USB Product ID（Linux）

**返回值**：無

**平台**：
- Windows: `win32` 或 `win32cygwin`
- Linux: `linux`, `linux2`, `linux3`

---

## 十三、集成示例

### 13.1 完整集成流程

```python
from polish import default_setup, Measurement, MeasurementList
from polish.reports.default_report import generate_default_report
from polish.reports.print_receipt import Receipt
from polish.reports.thermal_printer import ThermPrint

# 1. 設置測試環境
logger, test_point_map, meas_assets = default_setup('limits.csv')

# 2. 執行測試
class MyMeasurement(Measurement):
    test_point_uids = ('test_1', 'test_2')

    def measure(self):
        self.test_points.test_1.execute(10.5, "OFF", True)
        self.test_points.test_2.execute("OK", "OFF", True)

measurement_list = MeasurementList()
measurement_list.add(MyMeasurement(meas_assets))
measurement_list.run_measurements()

# 3. 生成報告
generate_default_report(
    test_point_map=test_point_map,
    uid_serial_num='info_vcu_serial_num',
    leader_path='default_reports'
)

# 4. 打印收據
receipt = Receipt(meas_assets)

# 判斷測試結果
if test_point_map.all_executed_all_pass():
    receipt.test_result = Receipt.PASS
else:
    receipt.test_result = Receipt.FAIL

receipt.print_summary(test_point_map)

# 5. 可選：熱敏打印機打印
if hasattr(meas_assets, 'rec_printer') and meas_assets.rec_printer:
    pr = ThermPrint()
    data = receipt.template.format(...)
    pr.therm_print(data, printer_name='POS-58')

# 6. 清理
from polish import default_teardown
default_teardown()
```

### 13.2 與 oneCSV_atlas_2.py 的集成

```python
# 在 oneCSV_atlas_2.py 中

from polish.reports.default_report import generate_default_report
from polish.reports.print_receipt import Receipt

# 測試完成後
def finalize_test(test_point_map, meas_assets):
    # 生成 CSV 報告
    generate_default_report(
        test_point_map=test_point_map,
        uid_serial_num='info_vcu_serial_num',
        test_name=TEST_NAME,
        report_name='dflt'
    )

    # 打印收據
    receipt = Receipt(meas_assets)
    if test_point_map.all_executed_all_pass():
        receipt.test_result = Receipt.PASS
    else:
        receipt.test_result = Receipt.FAIL

    receipt.print_summary(test_point_map)
```

---

## 十四、總結

### 14.1 模組特點

**polish/reports/** 模組提供了完整的報告生成和打印解決方案：

**優點**：
- ✅ CSV 報告生成簡單高效
- ✅ 收據格式化清晰易讀
- ✅ 跨平台打印機支持
- ✅ 資源管理正確
- ✅ 錯誤處理合理

**缺點**：
- ⚠️ 代碼重複（本地 TestPoint 類）
- ⚠️ Python 2 語法兼容性問題
- ⚠️ 大量註釋代碼未清理
- ⚠️ 異常處理不夠精確
- ⚠️ 缺少詳細文檔

### 14.2 適用場景

✅ 製造測試
✅ 質量控制
✅ 設備驗證
✅ 生產線自動化
✅ 測試結果追蹤

### 14.3 技術棧

| 技術 | 用途 |
|------|------|
| Python csv 模組 | CSV 生成 |
| Python time 模組 | 時間格式化 |
| Canister 類 | 動態屬性字典 |
| win32print (pywin32) | Windows 打印機 API |
| usb.core (pyusb) | Linux USB 訪問 |

### 14.4 未來改進方向

1. **清理代碼**：移除未使用的代碼和註釋
2. **Python 3 兼容**：修復 Python 2 語法
3. **異常處理**：使用具體異常類型
4. **文檔完善**：添加詳細的 docstring
5. **參數化**：減少硬編碼值
6. **擴展格式**：支持 JSON、XML、HTML 等格式
7. **異步操作**：改進打印機性能
8. **單元測試**：添加測試覆蓋

---

**文檔版本**: 1.0
**最後更新**: 2026-01-28
**分析者**: Claude Code
**相關文檔**:
- `docs/Polish_Analysis.md` - Polish 模組總體分析
- `docs/Polish_Test_Point_Analysis.md` - 測試點模組分析
