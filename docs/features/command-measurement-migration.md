# Command Measurement Migration

## Overview

`lowsheen_lib` 的三個 command-type script（`ComPortCommand.py`、`ConSoleCommand.py`、`TCPIPCommand.py`）已完整遷移至現代的 async class-based 架構。遷移於 2026-02-24 完成，採用 Strangler Fig 模式。

**狀態：✅ Complete**（參考 `docs/analysis/lowsheen_lib_migration_validation_2026_02_24.md`）

---

## 遷移對照表

| `lowsheen_lib` Script | 新 Measurement Class | Instrument Driver | Registry Key |
|---|---|---|---|
| `ComPortCommand.py` | `ComPortMeasurement` | `ComPortCommandDriver` | `"comport"` |
| `ConSoleCommand.py` | `ConSoleMeasurement` | `ConSoleCommandDriver` | `"console"`, `"command"`, `"COMMAND_TEST"` |
| `TCPIPCommand.py` | `TCPIPMeasurement` | `TCPIPCommandDriver` | `"tcpip"` |

舊的 `CommandTestMeasurement`（直接 subprocess 執行 lowsheen_lib script）已被註釋保留，不再使用。

---

## 架構說明

### 執行路徑（Before → After）

**Before（Legacy）：**
```
test_plan (case: comport/console/tcpip)
  → CommandTestMeasurement.execute()
  → asyncio.create_subprocess_shell(lowsheen_lib script)
  → ./src/lowsheen_lib/ComPortCommand.py  ← subprocess
```

**After（Modern）：**
```
test_plan (case: comport/console/tcpip)
  → ComPortMeasurement / ConSoleMeasurement / TCPIPMeasurement
  → get_instrument_settings() → InstrumentConfig
  → get_driver_class(config.type) → Driver class
  → get_connection_pool().get_connection(instrument_name)
  → driver.initialize() + driver.send_command(test_params)
```

### 三種通訊協定

| Class | 通訊方式 | Driver |
|---|---|---|
| `ComPortMeasurement` | RS-232/USB serial port | `ComPortCommandDriver` — 管理 `serial.Serial` port，支援多行讀取、escape sequence |
| `ConSoleMeasurement` | OS subprocess | `ConSoleCommandDriver` — `asyncio.create_subprocess_exec`，支援 timeout、shell mode |
| `TCPIPMeasurement` | TCP socket | `TCPIPCommandDriver` — async TCP，支援 binary protocol + CRC32 checksum |

---

## Test Plan 參數

### ComPort（case: comport）

| 參數 | 必填 | 說明 |
|---|---|---|
| `Instrument` | ✅ | instrument_settings 中的 key（type 必須為 `comport`） |
| `Command` | ✅ | 傳送的命令字串，支援 `\n` escape |
| `Timeout` | — | 讀取逾時秒數（預設 3.0） |
| `ReslineCount` | — | 期望回應行數（不填 = 自動偵測） |
| `ComportWait` | — | port 開啟後等待秒數（預設 0） |
| `SettlingTime` | — | write 與 read 之間的延遲秒數（預設 0.5） |

### Console（case: console）

| 參數 | 必填 | 說明 |
|---|---|---|
| `Instrument` | ✅ | instrument_settings 中的 key（type 必須為 `console`） |
| `Command` | ✅ | 執行的 OS 命令字串 |
| `Timeout` | — | 執行逾時秒數（預設 5.0） |
| `Shell` | — | 是否使用 shell 模式（預設 False） |
| `WorkingDir` | — | 工作目錄 |

### TCPIP（case: tcpip）

| 參數 | 必填 | 說明 |
|---|---|---|
| `Instrument` | ✅ | instrument_settings 中的 key（type 必須為 `tcpip`） |
| `Command` | ✅ | 命令字串，hex 格式如 `"31;01;f0;00;00"` |
| `Timeout` | — | socket 讀取逾時秒數（預設 5.0） |
| `UseCRC32` | — | 是否附加 CRC32 checksum（預設 True） |
| `BufferSize` | — | 最大接收 bytes（預設 1024） |

---

## Registry 對應

`backend/app/measurements/implementations.py` 中的 `MEASUREMENT_REGISTRY`：

```python
"comport":      ComPortMeasurement,
"console":      ConSoleMeasurement,
"tcpip":        TCPIPMeasurement,
"COMMAND_TEST": ConSoleMeasurement,  # generic fallback
"command":      ConSoleMeasurement,  # generic fallback
```

---

## measured_value 行為

三個 class 均採相同策略（與舊的 `CommandTestMeasurement` 一致）：

- `value_type = string` → `measured_value = None`（字串不存入 Decimal 欄位）
- `value_type = float/integer` → 嘗試 `Decimal(response_str)`，失敗則 `None`
- 驗證邏輯（`validate_result`）永遠使用原始字串回應

---

## 相關檔案

| 類型 | 路徑 |
|---|---|
| Measurement classes | `backend/app/measurements/implementations.py` |
| ComPort driver | `backend/app/services/instruments/comport_command.py` |
| Console driver | `backend/app/services/instruments/console_command.py` |
| TCPIP driver | `backend/app/services/instruments/tcpip_command.py` |
| Tests | `backend/tests/test_measurements/test_command_measurements.py` |
| Legacy scripts (保留) | `backend/src/lowsheen_lib/ComPortCommand.py` |
| Legacy scripts (保留) | `backend/src/lowsheen_lib/ConSoleCommand.py` |
| Legacy scripts (保留) | `backend/src/lowsheen_lib/TCPIPCommand.py` |
| Migration analysis | `docs/analysis/lowsheen_lib_migration_validation_2026_02_24.md` |
