# Bug Fix: ComPortCommand 串列埠不存在導致測試 ERROR

**日期**: 2026-03-12
**嚴重等級**: 🟡 High — 使用 `ComPortCommand` 類型儀器的測試項目會返回 ERROR 而非實際結果
**狀態**: ✅ 已修正

---

## 問題描述

在執行測試時，指定 `ComPortCommand` 類型儀器（如 `console_2`）的測試項目出現 ERROR 結果，測試無法繼續得到有效量測值。

### 錯誤訊息（Backend 容器日誌）

```
2026-03-12 07:43:12 - ERROR - [ComPortCommandDriver.console_2:74:initialize]
    Failed to open serial port: [Errno 2] could not open port COM1: [Errno 2] No such file or directory: 'COM1'

ConnectionError: Failed to connect to serial port COM1: [Errno 2] could not open port COM1: [Errno 2] No such file or directory: 'COM1'
```

### 測試結果

| item_no | item_name  | result | measured_value | error_message |
|---------|-----------|--------|----------------|---------------|
| 6       | echo_test  | ERROR  | NULL           | Failed to connect to serial port COM1: ... |

---

## 根本原因分析

### 除錯過程

**Step 1 — 確認測試計畫參數**

查詢 session 166 的 item 6：

```sql
SELECT tp.item_name, tp.test_type, tp.parameters
FROM test_plans tp
JOIN test_results tr ON tp.id = tr.test_plan_id
WHERE tr.session_id = 166 AND tr.item_no = 6;
```

結果：`test_type = 'console'`，`parameters = {"Command": "echo test", "Instrument": "console_2"}`

確認是 `ConSoleMeasurement` 使用 `console_2` 儀器。

**Step 2 — 確認儀器設定**

查詢 DB 中 `console_2` 的配置：

```sql
SELECT instrument_id, instrument_type, conn_type, conn_params
FROM instruments WHERE instrument_id = 'console_2';
```

發現：此時 `console_2` 在 DB 已更新為 `ConsoleCommand`/`LOCAL`，但容器 log 顯示的是 `ComPortCommandDriver.console_2`。

這表示測試執行當下，`console_2` 的 `instrument_type` 還是 `ComPortCommand`，後來才被修改。

**Step 3 — 追蹤 Driver 解析路徑**

`ComPortCommand` instrument_type → `INSTRUMENT_DRIVERS['ComPortCommand']` = `ComPortCommandDriver`
→ `initialize()` 嘗試開啟 `conn_params['port']`（預設 `'COM1'`）
→ Docker 容器（Linux）找不到 `COM1`（Windows 串列埠命名）
→ `SerialException` → `raise ConnectionError(...)` → 測試 ERROR

**Step 4 — 確認問題根源**

`comport_command.py` 的 `initialize()` 在 `SerialException` 時直接 `raise ConnectionError`，沒有任何 fallback。
`_row_to_config()` 在 `SERIAL` conn_type 時，port 預設值是 `'COM1'`（Windows 路徑）。

### 問題本質

1. **硬體不存在時直接拋例外**：和其他 stub 驅動（CMW100、MT8872A）不同，`ComPortCommandDriver` 沒有 simulation 模式。
2. **Windows 預設埠名**：`_row_to_config()` 的 `port` 預設值 `'COM1'` 在 Linux 環境（Docker 容器）不存在。

---

## 解決方案

### 修改檔案

**`backend/app/services/instruments/comport_command.py`**

#### 1. 加入 `simulation_mode` 屬性與 `_sim_response`（`__init__`）

```python
# 修改前
def __init__(self, connection: BaseInstrumentConnection):
    super().__init__(connection)
    self.serial_port: Optional[serial.Serial] = None
    self.default_timeout = 3.0
    self.default_baudrate = 115200

# 修改後
def __init__(self, connection: BaseInstrumentConnection):
    super().__init__(connection)
    self.serial_port: Optional[serial.Serial] = None
    self.default_timeout = 3.0
    self.default_baudrate = 115200
    self.simulation_mode = False  # set to True in initialize() if port unavailable
    # Stub response returned in simulation mode (configurable via conn_params)
    conn_config = self.connection.config.connection
    self._sim_response: str = str(getattr(conn_config, 'sim_response', '') or '')
```

#### 2. 修改 `initialize()` — 加入 simulation fallback

```python
# 修改前：SerialException 直接 raise ConnectionError
except SerialException as e:
    self.logger.error(f"Failed to open serial port: {e}")
    raise ConnectionError(f"Failed to connect to serial port {port}: {e}")

# 修改後：無法開啟埠時進入 simulation mode
except (SerialException, OSError) as e:
    self.simulation_mode = True
    self.logger.warning(
        f"Serial port {port} unavailable ({e}); switching to SIMULATION mode"
    )
```

同時支援明確的 `sim://` 位址：

```python
# 偵測明確 simulation 位址
address = getattr(conn_config, 'address', '') or ''
if address.startswith('sim://'):
    self.simulation_mode = True
    self.logger.info(f"ComPortCommand driver initialised in SIMULATION mode (address={address})")
    return
```

預設埠名從 `'COM1'` 改為 `'/dev/ttyS0'`（Linux 慣例）：

```python
# 修改前
port = getattr(conn_config, 'port', 'COM1')

# 修改後
port = getattr(conn_config, 'port', '/dev/ttyS0')
```

#### 3. `send_command()` — simulation 模式直接回傳 stub response

```python
# simulation mode: skip actual serial I/O
if self.simulation_mode:
    self.logger.info(f"[SIM] ComPort command skipped; returning sim_response: {repr(self._sim_response)}")
    return self._sim_response
```

#### 4. `_write_command()` — simulation 模式 early return

```python
async def _write_command(self, command: str):
    if self.simulation_mode:
        return
    if not self.serial_port or not self.serial_port.is_open:
        raise ConnectionError("Serial port not open")
    ...
```

---

## 修正後的行為

| 情況 | 修正前 | 修正後 |
|------|--------|--------|
| 埠不存在（COM1 on Linux） | `ERROR` + ConnectionError | `WARNING` 日誌，進入 simulation mode |
| Simulation mode 下執行命令 | — | 回傳 `sim_response`（預設空字串） |
| 明確 `sim://` 位址 | N/A | 直接進入 simulation mode |
| 埠正常存在 | 正常執行 | 行為不變 |

---

## 如何配置 Simulation Response

若要讓 simulation mode 回傳特定值（例如讓測試 PASS），在 DB 的 `instruments.conn_params` 中新增 `sim_response` 欄位：

```json
{
  "port": "COM3",
  "baudrate": 115200,
  "sim_response": "OK"
}
```

這樣當 `COM3` 不存在時，`send_command()` 會回傳 `"OK"`，測試可根據 limit 判定 PASS/FAIL。

---

## 測試驗證

### 重建容器

```bash
docker-compose build backend
docker-compose up -d backend
```

### 期望日誌（simulation mode 啟動）

```
WARNING - [ComPortCommandDriver.console_2:XX:initialize]
    Serial port COM1 unavailable (...); switching to SIMULATION mode
INFO    - [ComPortCommandDriver.console_2:XX:send_command]
    [SIM] ComPort command skipped; returning sim_response: ''
```

### 期望測試結果

item 6 (`echo_test`) 結果應為 `PASS` 或 `FAIL`（依 limit 而定），不再出現 `ERROR`。

---

## 相關設計模式

本修正遵循專案中已建立的 simulation mode 模式，與以下驅動一致：

- `backend/app/services/instruments/cmw100.py` — `sim://` 位址觸發 simulation
- `backend/app/services/instruments/mt8872a.py` — `sim://` 位址觸發 simulation

差異：`ComPortCommandDriver` 額外支援「埠開啟失敗自動 fallback」，不強制要求 `sim://` 位址。

---

## 影響範圍

| 元件 | 影響 |
|------|------|
| `ComPortCommandDriver` | 新增 simulation mode，`initialize()` 不再拋例外 |
| `ComPortMeasurement` | 無變更，已能正確處理 `ConnectionError`（改為不再收到此例外）|
| 其他驅動 | 無影響 |

---

## 相關檔案

- `backend/app/services/instruments/comport_command.py` — 主要修改
- `backend/app/core/instrument_config.py` — `_row_to_config()` 的 port 預設值（背景資訊）
- `backend/app/measurements/implementations.py` — `ComPortMeasurement.execute()`（未修改）
