# Modbus Auto-Trigger Test

**實作日期：** 2026-03-25
**相關 Commits：** `b89ec19` → `a8100a9`（共 4 commits）
**修改檔案：** `frontend/src/views/TestMain.vue`（僅此一個檔案）

---

## 目標

當 Modbus Listener 在某個 station 啟動後，`TestMain.vue` 應自動連接同一 station 的 Modbus WebSocket，接收 PLC 推送的 `sn_received` 事件，並自動填入序號、觸發測試——完全不需要操作員手動掃描或點擊「開始測試」。

---

## 背景：功能缺口的發現過程

### Playwright 測試驗證

透過 Playwright 對 `Demo Project 2 → Station 3` 進行端對端測試，確認了以下現況：

1. `ModbusConfig.vue` 啟動 Listener 後，後端正確推送 `sn_received` 事件
2. `ModbusStatusIndicator.vue`（Loop 旁的狀態圓點）只處理 `type === 'status'`，對 `sn_received` 完全忽略
3. `TestMain.vue` 完全沒有連接 Modbus WebSocket

**缺口的根本原因：**

```
後端推送:  {"type": "sn_received", "sn": "TESE12345670"}
                    ↓
ModbusConfig.vue WebSocket → 顯示 Toast ✅
ModbusStatusIndicator.vue   → 只處理 'status'，sn_received 被丟棄 ❌
TestMain.vue                → 完全沒有連接 Modbus WebSocket ❌
```

---

## 實作方案

### 設計原則

最小化改動：`TestMain.vue` 已有 `barcode` ref 和 `handleStartTest()`，只需在選定 station 後連接 Modbus WebSocket，收到 `sn_received` 後填入 `barcode.value` 並呼叫 `handleStartTest()`。

### 新增的邏輯（TestMain.vue）

```
選擇 station
    ↓
connectModbusWs(stationId)
    ↓ WebSocket open
ws.send({ action: 'get_status' })
    ↓ 後端回傳 { type: 'status', data: { running: true, ... } }
modbusAutoMode = true → 顯示綠色 "Modbus Auto" 標籤
    ↓ 後端推送 { type: 'sn_received', sn: 'TESE12345670' }
barcode.value = 'TESE12345670'
handleStartTest()  → 自動執行測試
```

### 關鍵程式碼

```js
// frontend/src/views/TestMain.vue

let modbusWs = null
const modbusAutoMode = ref(false)

const connectModbusWs = (stationId) => {
  disconnectModbusWs()

  const ws = modbusApi.connectWebSocket(stationId)
  modbusWs = ws
  const myWs = ws  // 閉包捕捉，用於 stale socket 檢查

  ws.onopen = () => {
    if (modbusWs !== myWs) return
    ws.send(JSON.stringify({ action: 'get_status' }))
  }

  ws.onmessage = (event) => {
    if (modbusWs !== myWs) return
    try {
      const data = JSON.parse(event.data)
      if (data.type === 'status' && data.data) {
        modbusAutoMode.value = !!data.data.running
      } else if (data.type === 'sn_received' && data.sn) {
        if (testing.value) return  // 防重複觸發
        barcode.value = data.sn
        addStatusMessage(`Modbus 收到 SN: ${data.sn}，自動啟動測試`, 'info')
        handleStartTest()  // fire-and-forget async
      }
    } catch (e) {
      console.warn('Modbus WS: invalid message', e)
    }
  }

  ws.onerror = () => {
    if (modbusWs !== myWs) return
    modbusAutoMode.value = false
  }

  ws.onclose = () => {
    if (modbusWs !== myWs) return
    modbusAutoMode.value = false
  }
}

const disconnectModbusWs = () => {
  if (modbusWs) {
    modbusWs.close()
    modbusWs = null
  }
  modbusAutoMode.value = false
}
```

### WebSocket 生命週期管理

| 事件 | 動作 |
|------|------|
| 選擇 station（`handleStationChange`） | `disconnectModbusWs()` → `connectModbusWs(newId)` |
| 清除 station 選擇 | `disconnectModbusWs()` |
| 頁面載入（`onMounted`） | 若已有 station，`connectModbusWs(stationId)` |
| 離開頁面（`onUnmounted`） | `disconnectModbusWs()` |

### Template UI

```html
<!-- Loop 旁的 Modbus 自動模式標籤 -->
<el-tag
  v-if="modbusAutoMode"
  type="success"
  size="small"
  style="margin-left: 6px; vertical-align: middle"
>
  Modbus Auto
</el-tag>
```

---

## 除錯過程與修正

### Bug 1：Stale Socket Race Condition

**發現方式：** Code Quality Review（第二階段審查）

**問題描述：**
`disconnectModbusWs()` 呼叫 `ws.close()` 後，舊 WebSocket 的 `onclose` 是**非同步**觸發的。若切換 station 速度夠快，時序如下：

```
1. 切換 station A → B
2. disconnectModbusWs() → ws_A.close() [非同步，尚未觸發]
3. connectModbusWs(B) → 建立 ws_B，get_status 回傳 running=true
4. modbusAutoMode = true  ← 正確
5. ws_A.onclose 才觸發 → modbusAutoMode = false  ← 錯誤覆蓋！
```

**修正方式：**
使用閉包 ID 比對（closure identity pattern）：

```js
const myWs = ws  // 閉包捕捉當下的 socket 物件
// 所有 callback 開頭加上：
if (modbusWs !== myWs) return  // stale socket，忽略
```

當 `connectModbusWs` 被再次呼叫，`modbusWs` 指向新 socket，舊 socket 的所有 callback 因為 `modbusWs !== myWs` 而被靜默丟棄。

### Bug 2：JSON.parse 無防護

**發現方式：** Code Quality Review（第二階段審查）

**問題描述：**
`ws.onmessage` 中的 `JSON.parse(event.data)` 沒有 `try/catch`。後端雖然總是送 JSON，但 Nginx proxy 超時或網路異常可能傳送非 JSON 格式的訊息，導致未捕捉的例外靜默消失，可能使 `modbusAutoMode` 停留在錯誤狀態。

**修正方式：**
```js
try {
  const data = JSON.parse(event.data)
  // ... 處理邏輯
} catch (e) {
  console.warn('Modbus WS: invalid message', e)
}
```

### Bug 3：onopen 也需要 Stale Guard

**發現方式：** Code Quality Review re-review（修正 Bug 1、2 後的再次審查）

**問題描述：**
Bug 1 的修正在 `onmessage`、`onerror`、`onclose` 加了 stale guard，但遺漏了 `onopen`。若舊 socket 建立連線後觸發 `onopen`，仍會送出 `get_status` 請求（雖然影響輕微，但語義上不正確）。

**修正方式：**
```js
ws.onopen = () => {
  if (modbusWs !== myWs) return  // 補上
  ws.send(JSON.stringify({ action: 'get_status' }))
}
```

---

## 重要設計決策

### `modbusAutoMode` 的初始化邏輯

當 station 沒有 Modbus listener 在運行時，後端 `get_status` 回傳：
```json
{"type": "status", "data": null}
```
（不是 `{"data": {"running": false}}`）

前端的 `&& data.data` 條件判斷當 `data.data` 為 `null` 時為 `false`，`modbusAutoMode` 保持 `false`，正確靜默地不啟動自動模式。

### 防重複觸發

```js
if (testing.value) return  // 測試進行中時，略過新的 sn_received
```

`testing.value` 在 `handleStartTest()` 開始時設為 `true`，結束後設為 `false`。Modbus listener 的 polling delay（通常 1 秒）可能在同一次測試期間觸發多次 `sn_received`，此 guard 確保不重複觸發。

### Fire-and-Forget 呼叫

```js
handleStartTest()  // fire-and-forget async; errors handled inside handleStartTest's own catch block
```

`handleStartTest` 是 `async` 函式，但 WebSocket `onmessage` callback 是同步的，無法有意義地 `await`。`handleStartTest` 內部有完整的 `try/catch`（設定 `testing.value = false`、顯示錯誤訊息），因此 rejection 不會靜默消失。

---

## 後續除錯：Simulation Mode 下圓點不亮、modbusAutoMode 不觸發

**日期：** 2026-03-25（功能上線後回報）

### 問題描述

在 Modbus tools server simulator 啟動的情況下，`TestMain.vue` 的：

1. **Loop 旁的狀態圓點（`ModbusStatusIndicator`）** — 一直顯示灰色（unknown），不亮燈
2. **「Modbus Auto」標籤** — 不出現，`modbusAutoMode` 始終為 `false`

### 診斷流程

#### Step 1：確認 `TestMain.vue` 的 WS 連線確實存在

檢索 `TestMain.vue` 中的 `connectModbusWs` 呼叫點：
- `onMounted`：頁面載入時，若已有 station 則呼叫 ✅
- `handleStationChange`：切換 station 時呼叫 ✅
- `onUnmounted`：離開頁面時 disconnect ✅

邏輯完整，WS 連線沒有問題。

#### Step 2：確認 `modbusAutoMode` 的更新條件

```js
if (data.type === 'status' && data.data) {
  modbusAutoMode.value = !!data.data.running
}
```

`data.data` 需為 truthy（非 null）且 `data.data.running` 為 `true`，才會設 `modbusAutoMode = true`。

後端 `get_status` 在 listener 未啟動時回傳 `{"type": "status", "data": null}`，在啟動後回傳完整狀態物件。**若 listener 已啟動，`data.data.running` 應為 `true`。**

→ 問題不在前端判斷邏輯。

#### Step 3：追蹤後端 `simulation_mode` 實作

查看 `ModbusListenerService.__init__`：
```python
self.simulation_mode = config.simulation_mode  # 有儲存
```

查看 `_run_async`：
```python
# simulation_mode 完全未被使用！
self.client = AsyncModbusTcpClient(
    host=self.server_host,
    port=self.server_port
)
```

**根本原因：** `simulation_mode` 被儲存但從未在 `_run_async` 中使用。不論是否為 simulation 模式，listener 都會嘗試建立真實 TCP 連線。若 Modbus tools server simulator 沒有在 `server_host:server_port` 監聽，連線失敗，`self.connected` 永遠是 `false`。

後果：
- `get_status` 回傳 `{"running": true, "connected": false}` — listener 已啟動但未連線
- `TestMain.vue` 的 `modbusAutoMode = !!data.data.running` → `true` ✅（這步是對的）
- 但 `ModbusStatusIndicator` 的 `statusClass` 需要 `running && connected` 才顯示綠燈，`connected: false` → 橘色（connecting）或灰色

另外發現：若 `server_port` 完全無法連線，`AsyncModbusTcpClient.connect()` 會拋出例外，listener `_run_async` 進入不斷重試循環，`on_connected(True)` 永遠不被呼叫，`connected` 永遠是 `false`。

#### Step 4：確認 `ModbusStatusIndicator` 缺少即時事件處理

原始程式碼只處理初始 `get_status` 回應：

```js
websocket.value.onmessage = (event) => {
  const data = JSON.parse(event.data)    // 無 try/catch
  if (data.type === 'status' && data.data) {
    status.value = data.data
  }
  // connected_change、cycle_update 事件全被忽略
}
```

後端在連線狀態改變時推送 `connected_change` 事件，但前端忽略，所以即使後來連線成功，圓點仍停在舊狀態。

### 修正方案

#### 修正 1：後端 `simulation_mode` 下跳過真實 TCP 連線

**檔案：** `backend/app/services/modbus/modbus_listener.py`

```python
async def _run_async(self) -> None:
    # --- Simulation mode: no real TCP client needed ---
    if self.simulation_mode:
        try:
            self.connected = True          # 直接標記已連線
            if self.on_connected:
                self.on_connected(True)    # 觸發 connected_change 推送
            while self.running:
                self.cycle_count += 1
                if self.on_cycle:
                    self.on_cycle(self.cycle_count)
                await asyncio.sleep(delay_time)
        except asyncio.CancelledError:
            pass
        finally:
            self.connected = False
        return
    # --- 以下為真實 TCP 模式 ---
    ...
```

SN 注入則透過新增的 `inject_sn()` 方法（見修正 2）。

#### 修正 2：新增 `inject_sn` 供 Simulation Mode 手動觸發

**檔案：** `backend/app/services/modbus/modbus_listener.py`

```python
async def inject_sn(self, sn: str) -> None:
    """Inject a SN directly (simulation mode only)."""
    if not self.simulation_mode or not self.running:
        return
    self.last_sn = sn
    if self.on_sn_received:
        self.on_sn_received(sn)
```

**檔案：** `backend/app/api/modbus_ws.py`，新增 WS action：

```python
elif action == "inject_sn":
    sn = data.get("sn", "")
    listener = modbus_manager.get_listener(station_id)
    if listener and listener.simulation_mode:
        await listener.inject_sn(sn)
        await websocket.send_json({"type": "status", "message": f"SN injected: {sn}"})
    else:
        await websocket.send_json({"type": "error", "message": "inject_sn only available in simulation mode"})
```

使用方式（可從 ModbusConfig 頁面 WS 或任何 WS 客戶端送出）：
```json
{"action": "inject_sn", "sn": "TEST0001"}
```

#### 修正 3：`ModbusStatusIndicator` 處理即時事件

**檔案：** `frontend/src/components/ModbusStatusIndicator.vue`

```js
websocket.value.onmessage = (event) => {
  try {
    const data = JSON.parse(event.data)
    if (data.type === 'status') {
      status.value = data.data || null     // 容許 null（listener 未啟動）
    } else if (data.type === 'connected_change' && status.value) {
      status.value = { ...status.value, connected: data.connected }  // 即時更新連線狀態
    } else if (data.type === 'cycle_update' && status.value) {
      status.value = { ...status.value, cycle_count: data.cycle_count }  // 即時更新 cycle
    }
  } catch (e) {
    console.warn('Modbus status WS: invalid message', e)
  }
}

websocket.value.onerror = () => {
  console.warn('Modbus status WebSocket error')
  status.value = null    // 補上：連線錯誤時清除狀態
}
```

### 修正後的行為

| 情況 | 修正前 | 修正後 |
|------|--------|--------|
| simulation_mode，listener 啟動 | `connected: false`，圓點橘色，modbusAutoMode 視 running 而定 | `connected: true`，圓點立即綠色，modbusAutoMode = true |
| simulation_mode，inject_sn | 無法觸發（無 action 支援） | WS action `inject_sn` 直接觸發 on_sn_received |
| 真實 TCP，connected_change 推送 | 前端忽略，圓點不即時更新 | 即時更新 connected 狀態 |
| WS 傳入非 JSON（網路異常） | JSON.parse 拋出未捕捉例外 | try/catch 靜默處理 |

### 後端行為差異（Simulation vs 真實）

```
simulation_mode = true:
  _run_async() → connected = True（立即） → idle loop（等 inject_sn）
  inject_sn(sn) → on_sn_received(sn) → WS 推送 sn_received → TestMain 自動測試

simulation_mode = false:
  _run_async() → AsyncModbusTcpClient → connect() → 輪詢暫存器 → SN 讀取
  → on_sn_received(sn) → WS 推送 sn_received → TestMain 自動測試
```

---

## 相關檔案

| 檔案 | 說明 |
|------|------|
| `frontend/src/views/TestMain.vue` | 自動觸發功能主要實作 |
| `frontend/src/api/modbus.js` | `connectWebSocket(stationId)` 的實作 |
| `frontend/src/components/ModbusStatusIndicator.vue` | Loop 旁的狀態圓點（即時處理所有 WS 事件） |
| `backend/app/api/modbus_ws.py` | WS endpoint，含 `inject_sn` action |
| `backend/app/services/modbus/modbus_listener.py` | Simulation mode 分支、`inject_sn()` 方法 |
| `docs/superpowers/plans/2026-03-25-modbus-auto-trigger-test.md` | 實作計畫 |
| `docs/issues/2026-03-25-modbus-last-sn-not-realtime-update.md` | 相關問題：ModbusConfig Last SN 不即時更新 |

## 參考

- [Modbus Listener Integration](./modbus-listener-integration.md) — 整體 Modbus 架構說明
