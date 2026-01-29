# OtherMeasurement.py 程式碼分析

## 核心架構

**基底類別：OtherMeasurement**
- 繼承自 `polish.Measurement`（框架基底類別）
- 設計用於彈性、參數驅動的測量執行
- 實作等待/延遲功能和機箱底座控制

## 主要元件

### 1. 類別結構
```
OtherMeasurement (基底類別)
├── MeasureSwitchON (子類別)
└── MeasureSwitchOFF (子類別)

QThread 類別：
├── MyThread_CW
└── MyThread_CCW
```

### 2. 初始化模式 (`__init__` at line 21)
- 從輸入參數動態設定 `test_point_uids` (line 27)
- 儲存執行時參數：`switch_select`、`runAllTest`、`TestParams`、`test_results`
- 透過 `runAllTest` 旗標支援多種執行模式

### 3. 主要執行邏輯 (`measure()` at line 34)

**等待模式** (switch_select == 'wait')：
- **時間戳記**：設定 UTC 時間的 `TestDateTime` (line 38)
- **參數驗證**：檢查必要的 `WaitmSec` 參數 (lines 40-46)
- **子行程執行**：呼叫外部 Python 腳本 (line 49)：
  ```python
  Wait_test.py <test_uid> <TestParams>
  ```
- **錯誤處理**：攔截例外，傳回錯誤訊息 (lines 56-58)
- **結果記錄**：儲存至 test_points 和 test_results (lines 60-61)

### 4. 子類別

**MeasureSwitchON** (line 73)：
- 設定 `relay_state = SWITCH_OPEN` (0)

**MeasureSwitchOFF** (line 78)：
- 設定 `relay_state = SWITCH_CLOSED` (1)

**用途**：定義硬體繼電器狀態（目前未在執行流程中使用）

### 5. 機箱控制執行緒 (Lines 81-98)

**MyThread_CW** (順時針)：
- 執行：`chassis_fixture_bat.py /dev/ttyACM0 6 1`
- 裝置：`/dev/ttyACM0` (USB 序列埠)
- 參數：`6` (方向)、`1` (指令)

**MyThread_CCW** (逆時針)：
- 執行：`chassis_fixture_bat.py /dev/ttyACM0 9 1`
- 參數：`9` (方向)、`1` (指令)

**用途**：在獨立的 QThread 中控制硬體底座旋轉，避免阻塞 GUI

## 設計模式

1. **Template Method**：子類別繼承但未覆寫行為
2. **Strategy Pattern**：根據 `switch_select` 參數決定不同行為
3. **Async Execution**：使用 QThread 進行非同步硬體控制
4. **Result Storage**：雙重儲存 (test_points + test_results dict)

## 相依性

- **框架**：`polish` (自訂測試框架)
- **外部腳本**：
  - `./src/lowsheen_lib/Wait_test.py`
  - `./chassis_comms/chassis_fixture_bat.py`
- **GUI**：PySide2/Qt (用於執行緒處理)

## 當前限制

1. 僅實作 `wait` 模式（其他模式未定義）
2. 子類別 (`MeasureSwitchON/OFF`) 無功能性覆寫
3. `teardown()` 為空函式
4. QThreads 未連接至 UI 或主要流程
5. 許多註解的匯入和程式碼 (lines 1, 3, 5, 48, 52-55, 67-69)

## 使用情境

在測試執行引擎 (oneCSV_atlas_2.py) 中用於：
- 在測試步驟之間加入延遲
- 控制機箱底座旋轉
- 管理繼電器狀態測試
