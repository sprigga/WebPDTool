# Bugfix: Modbus Auto-Trigger 兩個關鍵問題修正

**日期：** 2026-03-25
**影響範圍：**
- `backend/app/services/modbus/modbus_listener.py`
- `frontend/src/views/TestMain.vue`
**嚴重性：** 高（Auto-Trigger 功能完全失效）
**狀態：** ✅ 已修正

---

## 背景

Modbus Auto-Trigger 功能的工作流程：

```
Modbus 設備設 ready_status=0x01
  → backend 輪詢偵測
  → _read_sn_async() 讀取 SN
  → 推送 WS sn_received 事件
  → TestMain.vue 自動觸發測試
  → 測試完成後 write_result WS → write_test_result()
  → 寫回 PASS/FAIL 至 test_result 暫存器
  → 清除 _testing flag，允許下次觸發
```

本次修正的兩個 bug 都會導致此流程中斷，使 Auto-Trigger 無法持續正常運作。

---

## Bug 1：`_str2hex()` 地址轉換錯誤

### 症狀

使用 Modbus Tool Server 監控時，發現測試完成後寫入的是 **400034**（`0x01`），而非 DB 設定的 **400022**（test_result_address）。

ModbusTools 截圖顯示：
- 400031+3 行被寫入 `0x0001` ← 錯誤位置
- 400022 沒有任何寫入 ← 預期位置

### 根本原因

`_str2hex()` 函式對**所有**輸入都呼叫 `int(hex_str, 16)`（十六進制解析），但 DB 中存放了兩種格式的字串：

| DB 欄位 | DB 值 | 格式 |
|---------|-------|------|
| `test_result_address` | `"400022"` | 十進制 ModbusTools 位址，**無 0x 前綴** |
| `test_pass_value` | `"0x01"` | 十六進制值，**有 0x 前綴** |
| `ready_status_length` | `"0x1"` | `hex(1)` 輸出，**有 0x 前綴** |

`int("400022", 16)` 解析結果：

```
int("400022", 16) = 0x400022 = 4194338  ← 被當作十六進制！
0x400022 >= 0x400001 → wire address = (0x400022 & 0xFFFF) - 1 = 33
display address = 33 + 400001 = 400034  ← 錯誤！應為 400022
```

正確轉換應為：

```
int("400022", 10) = 400022  ← 十進制
400022 >= 400001 → wire address = 400022 - 400001 = 21
display address = 21 + 400001 = 400022  ← 正確！
```

### 除錯過程

1. **觀察截圖**：ModbusTools 顯示 400034 被寫入，而非 400022
2. **計算偏差**：`400034 - 400022 = 12`，偏移 12 個暫存器
3. **追蹤 `_str2hex("400022")`**：
   - 舊碼：`int("400022", 16) = 0x400022`
   - `0x400022 >= 0x400001` → `(0x400022 & 0xFFFF) - 1 = 33`
   - 新碼：`int("400022", 10) = 400022`，`400022 - 400001 = 21`
4. **確認 DB 值格式**：
   ```sql
   SELECT test_result_address, test_pass_value FROM modbus_configs;
   -- test_result_address: 400022  ← 無 0x 前綴
   -- test_pass_value: 0x01        ← 有 0x 前綴
   ```
5. **驗證修正邏輯**（Python 腳本）：確認所有 DB 實際值計算結果正確

### 修正方式

**檔案：** `backend/app/services/modbus/modbus_listener.py`，`_str2hex()` 函式

```python
# 修正前
def _str2hex(self, hex_str: str) -> int:
    val = int(hex_str, 16)   # BUG: "400022" 被解析為十六進制 0x400022
    if val >= 0x400001:
        return (val & 0xFFFF) - 1   # 返回 33，應為 21
    return val

# 修正後
def _str2hex(self, hex_str: str) -> int:
    """
    Two formats stored in DB:
      - Register addresses: decimal ModbusTools notation, no '0x' prefix
          e.g. "400022" -> holding register 22 -> wire address 21 (400001-based)
      - Value fields: hex strings with '0x' prefix
          e.g. "0x01" -> 1 (returned as-is)
    """
    # Hex value strings (e.g. "0x01", "0x00") — parse as hex, return as-is
    if hex_str.lower().startswith("0x"):
        return int(hex_str, 16)
    # Decimal ModbusTools register addresses (e.g. "400022") — convert to 0-based wire
    val = int(hex_str, 10)
    if val >= 400001:
        return val - 400001
    return val
```

### 轉換正確性驗證

| DB 值 | 格式 | 舊結果（wire） | 新結果（wire） | 預期（wire） |
|-------|------|--------------|--------------|-------------|
| `"400001"` | 十進制位址 | 0 ✅ | 0 ✅ | 0 |
| `"400022"` | 十進制位址 | **33 ❌** | 21 ✅ | 21 |
| `"400021"` | 十進制位址 | **32 ❌** | 20 ✅ | 20 |
| `"0x01"` | 十六進制值 | 1 ✅ | 1 ✅ | 1 |
| `"0x00"` | 十六進制值 | 0 ✅ | 0 ✅ | 0 |
| `"0x1"` | hex(1) 輸出 | 1 ✅ | 1 ✅ | 1 |
| `"11"` | SN 長度 | — | 11 ✅ | 11 |

---

## Bug 2：`_testing` flag 永久卡住導致 Auto-Trigger 停止

### 症狀

第一次 Auto-Trigger 成功後，Modbus 設備再次設 `ready_status=0x01`，backend log 顯示持續讀取到 `0x0001`，但 **SN 讀取再也不觸發**：

```
[Modbus] host.docker.internal:502 ReadHoldingReg addr=0x0000 count=1 -> 0x0001 (1)
[Modbus] host.docker.internal:502 ReadHoldingReg addr=0x0000 count=1 -> 0x0001 (1)
... (不斷重複，無 SN 讀取 log)
```

而 `write_result` WS 訊息在 backend log 中**從未出現**。

### 根本原因（兩層問題）

**層次 1：前端 `write_result` 未送出**

`executeMeasurements()` 完成後，`write_result` 的發送條件：

```javascript
if (modbusAutoMode.value && modbusWs && modbusWs.readyState === WebSocket.OPEN) {
    modbusWs.send(JSON.stringify({ action: 'write_result', ... }))
}
```

問題：`modbusAutoMode.value` 依賴 `{"type": "status", "data": {"running": true}}` 訊息設定，但在 `sn_received` 觸發測試時，`status` 訊息可能因 WS 重連時序而尚未到達，導致 `modbusAutoMode.value = false`，條件不成立，`write_result` 未送出。

**層次 2：backend `_testing` flag 無逾時保護**

`_testing = True` 在 `_read_sn_async()` 設定，預期由 `write_test_result()` 的 `finally` 清除。若 `write_result` 從未抵達，`_testing` 永遠為 `True`：

```python
async def _read_sn_async(self) -> None:
    if self._testing:
        logger.debug("_read_sn skipped, previous test still in progress")
        return  # ← 永遠在這裡返回
```

### 除錯過程

1. **確認 backend log 中無 `write_result` 接收紀錄**：
   ```bash
   docker-compose logs backend | grep "write_result\|Test result written\|No active Modbus"
   # 無輸出 ← write_result 從未被 backend 收到
   ```

2. **確認 `_testing` 已設為 True**：log 顯示 SN 讀取後沒有 `write_test_result` 呼叫，`_testing` 卡住。

3. **追蹤前端 `modbusAutoMode` 設定路徑**：
   - 只在 `{"type": "status", "data": ...}` 時更新
   - `sn_received` 事件到達時不更新此 flag
   - 若 WS 在 listener 啟動後重連，`get_status` 回應的 `status` 訊息可能比 `sn_received` 晚到

4. **確認 `write_result` 條件過嚴**：`modbusAutoMode.value` 不可靠，應直接用 WS 連線狀態判斷。

### 修正方式

**修正 2a：前端 `TestMain.vue`**

（1）收到 `sn_received` 時主動設定 `modbusAutoMode = true`（能收到就代表 listener 在跑）：

```javascript
// 修正前
} else if (data.type === 'sn_received' && data.sn) {
  if (testing.value) { return }
  barcode.value = data.sn
  handleStartTest()
}

// 修正後
} else if (data.type === 'sn_received' && data.sn) {
  modbusAutoMode.value = true  // ← 新增：能收到 sn_received 就代表 listener 在跑
  if (testing.value) { return }
  barcode.value = data.sn
  handleStartTest()
}
```

（2）`write_result` 發送條件改為直接用 WS 連線狀態，移除對 `modbusAutoMode` 的依賴：

```javascript
// 修正前
if (modbusAutoMode.value && modbusWs && modbusWs.readyState === WebSocket.OPEN) {

// 修正後
if (modbusWs && modbusWs.readyState === WebSocket.OPEN) {
// 注意：若 listener 未啟動，backend 的 write_result handler 會直接回傳 error，不做任何事
```

**修正 2b：backend `modbus_listener.py`**

新增 `_testing` 逾時自動清除機制（5 分鐘）：

```python
# __init__ 中新增
self._testing_since: Optional[datetime] = None
self._testing_timeout_seconds = 300  # 5 分鐘後自動清除

# _read_sn_async 中，設 _testing = True 時同時記錄時間
self._testing = True
self._testing_since = datetime.utcnow()

# _run_async 輪詢迴圈開頭新增逾時檢查
if self._testing and self._testing_since:
    elapsed = (datetime.utcnow() - self._testing_since).total_seconds()
    if elapsed > self._testing_timeout_seconds:
        logger.warning(f"Station {self.station_id}: _testing timed out after {elapsed:.0f}s, clearing flag")
        self._testing = False
        self._testing_since = None

# write_test_result 中所有 _testing = False 的地方同時清除 _testing_since
self._testing = False
self._testing_since = None
```

---

## 修正後的完整 Auto-Trigger 流程

```
[設備] ready_status=0x01
  ↓
[backend] _run_async() 輪詢：timeout 檢查 → 讀 ready_status → 值為 1
  ↓
[backend] _read_sn_async()：讀 SN → 清 ready_status → 寫 test_status=in_testing
          → _testing=True, _testing_since=now
  ↓
[WS] {"type": "sn_received", "sn": "TESE12345670"}
  ↓
[前端] modbusAutoMode=true → barcode=SN → handleStartTest()
  ↓
[前端] executeMeasurements() 執行完畢
  ↓
[WS] {"action": "write_result", "passed": true/false}   ← 條件：modbusWs 開著即送
  ↓
[backend] write_test_result()：寫 test_status=finished → 寫 test_result=PASS/FAIL
          → finally: _testing=False, _testing_since=None
  ↓
[backend] 下次輪詢可正常讀取新的 SN
```

---

## 相關檔案

| 檔案 | 修正內容 |
|------|---------|
| `backend/app/services/modbus/modbus_listener.py` | `_str2hex()` 地址轉換邏輯、`_testing` 逾時機制 |
| `frontend/src/views/TestMain.vue` | `sn_received` 設 `modbusAutoMode=true`、`write_result` 條件放寬 |

---

## 預防措施建議

1. **DB 欄位格式一致性**：建議 `test_result_address` 等位址欄位統一儲存為 `0x` 前綴的十六進制字串，避免格式混淆。目前 DB 中位址欄（無前綴十進制）與值欄（有前綴十六進制）混用需特別小心。

2. **`_testing` flag 狀態可視化**：可考慮將 `_testing` 狀態包含在 `get_status` 回應中，方便前端 debug 介面顯示「等待結果回寫中」狀態。

3. **`write_result` 確認回應**：目前 backend 的 `write_result` handler 回傳 `{"type": "status", "message": "..."}` 訊息，前端未處理此回應。可加入 log 或 UI 提示「結果已寫入」。
