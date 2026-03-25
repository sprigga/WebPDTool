# Modbus Start/Stop Listener 按鈕狀態不切換問題修正 (2026-03-25)

**日期：** 2026-03-25
**影響範圍：** `frontend/src/views/ModbusConfig.vue`
**嚴重性：** 功能性 — 使用者按下「Start Listener」後按鈕文字不變，無法停止 Listener
**狀態：** ✅ 已修正

---

## 問題描述

在 Modbus Config 頁面，按下「Start Listener」後：

- 按鈕文字沒有切換成「Stop Listener」
- 按鈕顏色也沒有從綠色（success）變為紅色（danger）
- 再次點擊按鈕仍然送出 `start` 動作（重複啟動）
- 無法透過 UI 停止已執行中的 Listener

---

## 根本原因

**前端 WebSocket 訊息處理邏輯只處理了一種 `status` 訊息格式，但後端實際上會送出兩種格式。**

### 後端送出的訊息格式（`modbus_ws.py`）

| 動作 | 後端回應 | 有無 `data` 欄位 |
|------|----------|----------------|
| `get_status` | `{"type": "status", "data": {"running": true/false, ...}}` | ✅ 有 |
| `start` | `{"type": "status", "status": "running", "message": "..."}` | ❌ 無 |
| `stop` | `{"type": "status", "status": "stopped", "message": "..."}` | ❌ 無 |

### 前端處理邏輯（修正前）

```javascript
// frontend/src/views/ModbusConfig.vue
websocket.value.onmessage = (event) => {
  const data = JSON.parse(event.data)
  if (data.type === 'status') {
    if (data.data) {                          // ← 只處理有 data.data 的情況
      listenerStatus.value = data.data
      listenerRunning.value = data.data.running
    }
    // ← start/stop 回應沒有 data.data，直接被略過
  }
  ...
}
```

`start`/`stop` 的回應沒有 `data` 子物件，進入 `if (data.data)` 時為 falsy，整個 block 被跳過。
`listenerRunning` 永遠不更新，按鈕狀態凍結。

---

## 除錯過程

1. **觀察 UI 行為** — 點擊「Start Listener」後按鈕沒有任何視覺變化
2. **確認按鈕繫結** — 按鈕 `type` 和 label 都依賴 `listenerRunning` ref，邏輯正確
   ```html
   <el-button :type="listenerRunning ? 'danger' : 'success'" @click="toggleListener">
     {{ listenerRunning ? 'Stop Listener' : 'Start Listener' }}
   </el-button>
   ```
3. **追蹤 `toggleListener`** — 確認 action 有正確送出 `start`/`stop`
4. **查看 `onmessage`** — 發現只有 `if (data.data)` 才會更新 `listenerRunning`
5. **對照後端 `modbus_ws.py`** — 確認 `start` 和 `stop` 的回應格式為 `{"type": "status", "status": "running"/"stopped"}`，**沒有 `data` 欄位**
6. **找到根因** — 訊息格式不一致導致前端 handler 無法識別 start/stop 的結果

---

## 修正方式

**檔案：** `frontend/src/views/ModbusConfig.vue`，`connectWebSocket()` 內的 `onmessage` handler

```javascript
// 修正前
websocket.value.onmessage = (event) => {
  const data = JSON.parse(event.data)
  if (data.type === 'status') {
    if (data.data) {
      listenerStatus.value = data.data
      listenerRunning.value = data.data.running
    }
  } else if (data.type === 'sn_received') {
    ...
  }
}

// 修正後
websocket.value.onmessage = (event) => {
  const data = JSON.parse(event.data)
  if (data.type === 'status') {
    if (data.data) {
      // Full status object from get_status
      listenerStatus.value = data.data
      listenerRunning.value = data.data.running
    } else if (data.status === 'running') {
      // Response from start action
      listenerRunning.value = true
    } else if (data.status === 'stopped') {
      // Response from stop action
      listenerRunning.value = false
    }
  } else if (data.type === 'sn_received') {
    ...
  }
}
```

### 修正邏輯說明

三種 `status` 訊息格式各自處理：

| 情況 | 判斷條件 | 動作 |
|------|----------|------|
| `get_status` 回應 | `data.data` 存在 | 更新完整狀態物件＋`listenerRunning` |
| `start` 成功 | `data.status === 'running'` | 設定 `listenerRunning = true` |
| `stop` 成功 | `data.status === 'stopped'` | 設定 `listenerRunning = false` |

---

## 修正後行為

- 按下「Start Listener」→ 按鈕立即切換為紅色「Stop Listener」
- 按下「Stop Listener」→ 按鈕立即切換回綠色「Start Listener」
- 頁面重新整理後（WebSocket 重連觸發 `get_status`）仍能正確顯示目前狀態

---

## 影響範圍

- `frontend/src/views/ModbusConfig.vue` — `connectWebSocket()` 的 `onmessage` handler

---

## 相關後端程式碼（未修改）

後端 `modbus_ws.py` 的訊息格式為歷史設計，三條路徑送出不同結構：

```python
# get_status（有 data 欄位）
await websocket.send_json({"type": "status", "data": status})

# start 成功（有 status 欄位）
await ws_manager.send_to_station(station_id, {"type": "status", "status": "running", "message": "..."})

# stop 成功（有 status 欄位）
await websocket.send_json({"type": "status", "status": "stopped", "message": "..."})
```

> **備注：** 若後端未來重構，建議統一回應格式為 `{"type": "status", "data": {"running": bool, ...}}`，讓前端只需一個 code path 處理。
