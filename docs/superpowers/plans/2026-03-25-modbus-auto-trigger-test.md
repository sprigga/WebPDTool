# Modbus Auto-Trigger Test Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 當 Modbus Listener 啟動後，TestMain.vue 能在背景監聽 PLC 的 `sn_received` 事件，自動將 SN 填入序號欄並觸發測試。

**Architecture:** 在 TestMain.vue 中新增 Modbus WebSocket 連線管理邏輯（複用現有 `modbusApi.connectWebSocket()`），當選定 station 且該 station 有 Modbus listener 在運行時，訂閱 `sn_received` 事件；收到事件後自動填入 `barcode.value` 並呼叫現有的 `handleStartTest()`。連線在切換 station 或離開頁面時關閉。

**Tech Stack:** Vue 3 Composition API、WebSocket（原生）、`modbusApi.connectWebSocket()`（現有 `frontend/src/api/modbus.js`）

---

## File Map

| 檔案 | 動作 | 說明 |
|------|------|------|
| `frontend/src/views/TestMain.vue` | Modify | 新增 Modbus WebSocket 連線、`sn_received` 自動觸發邏輯 |

---

## Task 1: 在 TestMain.vue 新增 Modbus WebSocket 連線與自動觸發邏輯

**Files:**
- Modify: `frontend/src/views/TestMain.vue`

### 背景知識

- `barcode` ref（第 560 行）：序號輸入欄的雙向綁定值
- `handleStartTest()`（第 1378 行）：現有開始測試函式，會檢查 `barcode.value`
- `testing` ref（第 561 行）：測試進行中旗標，自動觸發時需防止重複觸發
- `currentStation` computed（第 489 行）：目前選定的 station 物件
- `handleStationChange()`（第 1601 行）：切換站別時的 handler
- `onUnmounted`（第 1674 行）：頁面離開時清理
- `modbusApi.connectWebSocket(stationId)`：回傳原生 WebSocket 物件

---

- [ ] **Step 1: 新增 modbusApi import**

在 `frontend/src/views/TestMain.vue` 第 459 行找到：

```js
import ModbusStatusIndicator from '@/components/ModbusStatusIndicator.vue'
```

在其後新增：

```js
import { modbusApi } from '@/api/modbus'
```

---

- [ ] **Step 2: 新增 WebSocket ref 和 auto-trigger 旗標**

在 `frontend/src/views/TestMain.vue` 第 583 行找到：

```js
// Polling
let statusPollInterval = null
```

在其後新增：

```js
// Modbus auto-trigger
let modbusWs = null
const modbusAutoMode = ref(false)  // 是否已連上 Modbus listener（有在跑才為 true）
```

---

- [ ] **Step 3: 新增 connectModbusWs / disconnectModbusWs 函式**

在 `frontend/src/views/TestMain.vue` 找到 `// Methods` 區塊（第 599 行附近），在其後新增以下兩個函式：

```js
// Modbus WebSocket — 自動觸發測試
const connectModbusWs = (stationId) => {
  disconnectModbusWs()  // 先關掉舊的

  const ws = modbusApi.connectWebSocket(stationId)
  modbusWs = ws

  ws.onopen = () => {
    ws.send(JSON.stringify({ action: 'get_status' }))
  }

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data)

    if (data.type === 'status' && data.data) {
      // 只要 listener 在跑，就開啟自動模式
      modbusAutoMode.value = !!data.data.running
    } else if (data.type === 'sn_received' && data.sn) {
      // listener 推送 SN — 自動填入並觸發測試
      if (testing.value) {
        // 測試進行中，略過此次 SN（避免重複觸發）
        return
      }
      barcode.value = data.sn
      addStatusMessage(`Modbus 收到 SN: ${data.sn}，自動啟動測試`, 'info')
      handleStartTest()
    }
  }

  ws.onerror = () => {
    modbusAutoMode.value = false
  }

  ws.onclose = () => {
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

---

- [ ] **Step 4: 在 handleStationChange 末尾呼叫 connectModbusWs**

找到 `handleStationChange` 函式（第 1601 行），在函式末尾 `}` 前新增：

```js
  // 若切換到新站別，嘗試連接 Modbus WebSocket（listener 有跑才會收到事件）
  if (currentStation.value) {
    connectModbusWs(currentStation.value.id)
  } else {
    disconnectModbusWs()
  }
```

完整的 `handleStationChange` 結尾應為：

```js
  if (currentStation.value) {
    addStatusMessage(`已選擇站別: ${currentStation.value.station_code} - ${currentStation.value.station_name}`, 'info')
    await loadTestPlanNames()
    // 新增: 先載入 TestPlanMap，再載入測試計劃項目
    await loadTestPlanMap()
    await loadTestPlanItems()
  }

  // 若切換到新站別，嘗試連接 Modbus WebSocket
  if (currentStation.value) {
    connectModbusWs(currentStation.value.id)
  } else {
    disconnectModbusWs()
  }
}
```

---

- [ ] **Step 5: 在 onMounted 末尾連接 Modbus WebSocket**

找到 `onMounted` 中已有的 station 載入完成處（第 1661 行附近）：

```js
  // 如果有選擇站別,載入測試計劃名稱、測試點映射表和測試項目
  if (currentStation.value) {
    await loadTestPlanNames()
    await loadTestPlanMap()
    await loadTestPlanItems()
  }
```

在其後新增：

```js
  // 若頁面載入時已有選定站別，嘗試連接 Modbus WebSocket
  if (currentStation.value) {
    connectModbusWs(currentStation.value.id)
  }
```

---

- [ ] **Step 6: 在 onUnmounted 中斷開 Modbus WebSocket**

找到 `onUnmounted`（第 1674 行）：

```js
onUnmounted(() => {
  stopStatusPolling()

  // Save SFC config to localStorage
  localStorage.setItem('sfcConfig', JSON.stringify(sfcConfig))
})
```

修改為：

```js
onUnmounted(() => {
  stopStatusPolling()
  disconnectModbusWs()

  // Save SFC config to localStorage
  localStorage.setItem('sfcConfig', JSON.stringify(sfcConfig))
})
```

---

- [ ] **Step 7: 在 Template 新增 Modbus 自動模式狀態提示（可選 UI）**

找到 TestMain.vue Template 中 `ModbusStatusIndicator` 的位置（第 109 行附近）：

```html
<!-- Modbus connection status indicator -->
<ModbusStatusIndicator
  v-if="currentStation"
  :station-id="currentStation.id"
  style="margin-left: 8px; vertical-align: middle"
/>
```

在 `ModbusStatusIndicator` 後新增自動模式標籤：

```html
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

- [ ] **Step 8: 手動測試驗證**

1. 確認 Docker 環境正常：`docker-compose ps`
2. 開瀏覽器到 `http://localhost:9080`
3. 選擇 **Demo Project 2 → Test Station 3**
4. 前往 **Modbus 設定**，確認 Station 3 的 listener 已啟動（Running + Connected）
5. 回到 **測試主畫面**，Loop 旁應出現綠色 "Modbus Auto" 標籤
6. 等待約 1 秒（delay_seconds=1），觀察：
   - 序號欄自動填入 SN（如 `TESE12345670`）
   - 系統狀態欄出現「Modbus 收到 SN: TESE12345670，自動啟動測試」
   - 測試自動開始執行

---

- [ ] **Step 9: 驗證防重複觸發**

確認在測試進行中（`testing.value = true`），若 Modbus 再次推送 `sn_received`，測試不會被重複觸發（程式碼中有 `if (testing.value) return` 保護）。

---

- [ ] **Step 10: Commit**

```bash
cd /home/ubuntu/python_code/WebPDTool
git add frontend/src/views/TestMain.vue
git commit -m "feat: auto-trigger test from Modbus sn_received in TestMain"
```

---

## 注意事項

1. **`modbusAutoMode`** 旗標：只有當 Modbus listener **正在運行**時才為 `true`（透過 `get_status` 回應判斷）。若 listener 停止，旗標自動變 `false`，UI 標籤消失。

2. **防重複觸發**：`if (testing.value) return` 確保測試進行中不會因下一個 cycle 的 `sn_received` 而中斷。

3. **WebSocket 生命週期**：
   - 建立：`handleStationChange()` 及 `onMounted()`（已有 station 時）
   - 清除：切換 station 時（先 disconnect 再 connect）、`onUnmounted()`

4. **無 Modbus 設定或 listener 未啟動時**：WebSocket 連接後 `get_status` 回傳 `{"type": "status", "data": null}`（不是 `running: false`），`ws.onmessage` 中的 `&& data.data` 條件判斷為 false，`modbusAutoMode` 保持 `false`，不影響手動操作。
