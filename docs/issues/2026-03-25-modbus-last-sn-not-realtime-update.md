# Issue: Modbus Live Status 的 Last SN 欄位未即時更新

**日期：** 2026-03-25
**影響範圍：** `frontend/src/views/ModbusConfig.vue`
**嚴重性：** UI 顯示缺陷（功能正常，但 Last SN 不即時反映）
**狀態：** ✅ 已修正

---

## 問題描述

Modbus Config 頁面的 **Live Status** 區塊有一個 `Last SN` 欄位，預期在後端讀取到 SN 後**立即顯示**最新的序號。

然而，實際行為是：
- 後端成功讀取 SN，並透過 WebSocket 推送 `sn_received` 事件
- 前端收到事件，彈出 `ElMessage` 通知
- **但 Last SN 欄位仍顯示 `N/A`，直到下次 `get_status` 回應才更新**

### 症狀

```
後端推送：{"type": "sn_received", "sn": "TESE12345678"}
前端彈出通知：SN received: TESE12345678   ← 有反應
Live Status Last SN：N/A                  ← 沒有更新
```

---

## 根本原因分析

### WebSocket 訊息流

前端的 `onmessage` handler 處理兩種獨立的訊息類型：

```
┌─────────────────────────────────────────────────────────┐
│ WebSocket 訊息類型                                        │
├──────────────┬──────────────────────────────────────────┤
│ "status"     │ 包含完整狀態快照（running/connected/      │
│              │ last_sn/cycle_count），來源：get_status   │
│              │ 請求、start/stop 回應                     │
├──────────────┬──────────────────────────────────────────┤
│ "sn_received"│ 即時 SN 通知，僅包含 sn 字串，來源：      │
│              │ Modbus callback 直接推送                  │
└──────────────┴──────────────────────────────────────────┘
```

### 問題程式碼

`ModbusConfig.vue` 的 `sn_received` handler（修正前）：

```javascript
// 修正前：只彈出通知，沒有更新 listenerStatus
} else if (data.type === 'sn_received') {
  ElMessage.success(`SN received: ${data.sn}`)
}
```

`listenerStatus.last_sn` 只有在收到 `status` 類型訊息時才會更新：

```javascript
if (data.type === 'status') {
  if (data.data) {
    listenerStatus.value = data.data       // ← 包含 last_sn
    listenerRunning.value = data.data.running
  }
}
```

由於 `sn_received` 是 callback 驅動的即時事件，`status` 快照可能在 SN 讀取之前就已送出，導致 `last_sn` 欄位長時間停在舊值。

---

## 除錯過程

### 1. 確認後端 WebSocket 訊息格式

查看 `backend/app/api/modbus_ws.py` 的 `on_sn_received` callback：

```python
def on_sn_received(sn: str):
    asyncio.create_task(
        ws_manager.send_to_station(station_id, {
            "type": "sn_received",
            "sn": sn,
        })
    )
```

確認後端確實有推送 `sn_received`，且 `sn` 欄位包含解碼後的字串。

### 2. 確認前端接收但未更新狀態

追蹤 `ModbusConfig.vue` 的 `onmessage` handler，發現 `sn_received` 分支只呼叫 `ElMessage`，沒有寫入 `listenerStatus.value`：

```javascript
} else if (data.type === 'sn_received') {
  ElMessage.success(`SN received: ${data.sn}`)
  // 缺少：listenerStatus.value.last_sn = data.sn
}
```

`listenerStatus` 是 Vue 的 `ref(null)`，只在收到 `status` 訊息時整體替換，`sn_received` 事件到達時不會觸發更新。

### 3. 使用 Playwright MCP 端對端驗證

**驗證流程：**

1. 導航至 `http://localhost:9080/modbus-config`
2. 選擇 Demo Project 2 → Test Station 3
3. Patch `window.WebSocket` constructor 捕捉 WS 實例並監聽訊息
4. 點擊 Start Listener，連接 ModbusTools（`host.docker.internal:502`）
5. 在 ModbusTools 將 `400001+0`（ready_status register）設為 `0x0001`

**ModbusTools register 配置：**

| Register | 值 | ASCII | 說明 |
|----------|----|-------|------|
| 400001+0 | 0001 | — | ready_status（觸發 SN 讀取） |
| 400001+1 | 5445 | TE | SN 第 1-2 字元 |
| 400001+2 | 5345 | SE | SN 第 3-4 字元 |
| 400001+3 | 3132 | 12 | SN 第 5-6 字元 |
| 400001+4 | 3334 | 34 | SN 第 7-8 字元 |
| 400001+5 | 3536 | 56 | SN 第 9-10 字元 |
| 400001+6 | 3738 | 78 | SN 第 11-12 字元 |

**Address 對應說明：**

`_str2hex("400001")` 轉換邏輯：
```
val = int("400001", 16) = 0x400001
val >= 0x400001 → wire address = (0x400001 & 0xFFFF) - 1 = 0x0000
```
→ 後端讀取 wire address `0x0000`（對應 ModbusTools 的 400001+0 欄位）

**後端 log 確認（修正後可見）：**
```
[Modbus] host.docker.internal:502 ReadHoldingReg addr=0x0000 count=1 -> 0x0001 (1)
SN Register values = [21573, 21317, 12594, 13108, 13622, 14136, 0, 0, 0, 0, 0]
SN value = TESE12345678
```

**Playwright 監聽結果：**
```javascript
window.__snReceived = "TESE12345678"  // ← sn_received 事件確認收到
```

---

## 修正方式

**檔案：** `frontend/src/views/ModbusConfig.vue`，`onmessage` handler 的 `sn_received` 分支

```javascript
// 修正前
} else if (data.type === 'sn_received') {
  ElMessage.success(`SN received: ${data.sn}`)
}

// 修正後
} else if (data.type === 'sn_received') {
  ElMessage.success(`SN received: ${data.sn}`)
  // 即時更新 Last SN 顯示，不需等待下次 get_status
  if (listenerStatus.value) {
    listenerStatus.value.last_sn = data.sn
  }
}
```

**`listenerStatus.value` null 檢查的原因：**

WebSocket 可能在 `get_status` 回應（初始化 `listenerStatus`）之前就推送 `sn_received`（例如 listener 已在後台運行），此時 `listenerStatus.value` 仍是 `null`，直接存取 `.last_sn` 會拋出 TypeError。

---

## 驗證結果

修正後使用 Playwright MCP 端對端測試截圖：

- **Running**: Running ✅
- **Connected**: Yes ✅
- **Last SN**: `TESE12345678` ✅（`sn_received` 事件觸發後立即更新）
- **Cycle Count**: 正常累計

---

## 已知的獨立問題（本次未修正）

### Connected 顯示 "No" 問題

即使後端已成功連接並讀取 SN，Live Status 的 `Connected` 欄位有時顯示 "No"。

**原因：** `listenerStatus` 來自 `get_status` 快照，在 listener 剛啟動時快照中的 `connected` 還是 `false`，而 `sn_received` callback 比下一次 `status` 快照更早到達，導致 `connected` 欄位過時。

**建議修正方向：** 類似本次修正，在 `sn_received` 事件 handler 中同時更新 `listenerStatus.value.connected = true`；或後端在 `sn_received` 推送時附帶完整狀態。

---

## 相關檔案

| 檔案 | 說明 |
|------|------|
| `frontend/src/views/ModbusConfig.vue` | 本次修正位置（line 274-278） |
| `backend/app/api/modbus_ws.py` | WebSocket endpoint，`on_sn_received` callback |
| `backend/app/services/modbus/modbus_listener.py` | `_read_sn_async()` 讀取並解碼 SN |
| `scripts/modbus_simulator.py` | 本地測試用 Modbus TCP 模擬器 |
