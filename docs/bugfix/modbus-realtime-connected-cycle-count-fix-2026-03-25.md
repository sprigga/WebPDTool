# Bugfix: Modbus Live Status 的 Connected 和 Cycle Count 欄位未即時更新

**日期：** 2026-03-25
**影響範圍：**
- `frontend/src/views/ModbusConfig.vue`
- `backend/app/api/modbus_ws.py`
- `backend/app/services/modbus/modbus_manager.py`
- `backend/app/services/modbus/modbus_listener.py`
**嚴重性：** UI 顯示缺陷（功能正常，但欄位不即時反映後端狀態）
**狀態：** ✅ 已修正

---

## 問題描述

Modbus Config 頁面的 **Live Status** 區塊有兩個欄位在 Listener 啟動後無法即時更新：

### 症狀

| 欄位 | 預期行為 | 實際行為 |
|------|----------|----------|
| **Connected** | Listener 連上 Modbus 設備後立即顯示 `Yes` | 保持顯示 `No`，直到下次 `get_status` 快照 |
| **Cycle Count** | 每次輪詢完成後累計數字即時更新 | 停在 0 或過時的舊值，直到下次 `get_status` 快照 |

此問題是在修復 `Last SN` 未即時更新問題（同日另一份 bugfix 文件）時發現的獨立問題。

---

## 根本原因分析

### 同源問題

與 `Last SN` 未更新的根本原因相同：

```
WebSocket 訊息架構：

┌─────────────┬────────────────────────────────────────────────┐
│ 訊息類型    │ 說明                                            │
├─────────────┼────────────────────────────────────────────────┤
│ "status"    │ 完整狀態快照，包含 running/connected/           │
│             │ last_sn/cycle_count，由 get_status / start /   │
│             │ stop 觸發                                       │
├─────────────┼────────────────────────────────────────────────┤
│ "sn_received"│ 即時 SN 通知，callback 驅動，不含狀態快照     │
└─────────────┴────────────────────────────────────────────────┘
```

`connected` 和 `cycle_count` 的值只存在 `status` 快照中。後端的 `ModbusListenerService._run_async()` 雖然在內部更新這兩個屬性，但沒有任何機制主動推送到 WebSocket。

### 後端問題：無回調觸發點

`ModbusListenerService` 只定義了三個 callback：

```python
# 修正前
self.on_sn_received: Optional[Callable[[str], None]] = None
self.on_error: Optional[Callable[[str], None]] = None
self.on_status_change: Optional[Callable[[str], None]] = None
```

`self.connected` 和 `self.cycle_count` 在 `_run_async()` 中被更新，但沒有任何 callback 會在更新時通知外部：

```python
# connected 更新但無推送
self.connected = True   # line 157（修正前）

# cycle_count 更新但無推送
self.cycle_count += 1   # line 170（修正前）
```

### 前端問題：無對應訊息處理器

前端的 `onmessage` handler 只處理三種訊息類型（`status`、`sn_received`、`error`），即使後端推送了新的事件類型，也沒有處理邏輯。

---

## 除錯過程

### 1. 追蹤 `connected` 更新路徑

檢查 `modbus_listener.py`，找出 `self.connected` 被賦值的所有位置：

```
grep: self.connected =
  line 57:  self.connected = False  (初始化)
  line 88:  ← 已刪除重複設定
  line 119: self.connected = False  (stop)
  line 149: self.connected = False  (連線失敗)
  line 157: self.connected = True   (連線成功)
  line 195: self.connected = False  (finally 清理)
```

確認每次賦值都只改變內部狀態，沒有任何 callback 觸發。

### 2. 追蹤 `cycle_count` 更新路徑

```
grep: cycle_count
  line 170: self.cycle_count += 1  (每次輪詢成功)
```

同樣沒有推送機制。

### 3. 確認 `get_status` 是唯一的快照來源

`modbus_manager.get_status()` → `listener.get_status()` 回傳包含兩個欄位的字典：

```python
return {
    "running": self.running,
    "connected": self.connected,   # 快照時才同步
    "last_sn": self.last_sn,
    "cycle_count": self.cycle_count,  # 快照時才同步
    ...
}
```

在 start/stop 時後端只發送一次 `status` 快照，之後 `connected` 和 `cycle_count` 的變化不再被推送。

### 4. 決定修正方向

對比 `Last SN` 的修正方式（在前端 `sn_received` handler 中直接更新 `listenerStatus.value.last_sn`），此問題需要在後端增加新的 callback 機制，因為 `connected` 和 `cycle_count` 的變化發生在後端非同步迴圈中。

---

## 修正方式

### 1. `modbus_listener.py` — 新增兩個 Callback

```python
# 新增 callback 欄位定義
self.on_connected: Optional[Callable[[bool], None]] = None  # (connected: bool)
self.on_cycle: Optional[Callable[[int], None]] = None       # (cycle_count: int)
```

**`connected` 改用邊緣觸發（Edge Detection）：**

```python
# 修正前（無推送）
self.connected = True

# 修正後（邊緣觸發，只在狀態改變時通知）
if not self.connected:
    self.connected = True
    if self.on_connected:
        self.on_connected(True)

# 連線失敗時同樣使用邊緣觸發
if self.connected:
    self.connected = False
    if self.on_connected:
        self.on_connected(False)
```

為何使用邊緣觸發而非每次都觸發：`connected = True` 的賦值在每次輪詢進入時都可能被執行（只要 `self.client.connected` 為 True），若無邊緣檢查，每次輪詢都會推送 `connected_change` 訊息，造成不必要的 WebSocket 流量。

**`cycle_count` 每次累計後觸發：**

```python
self.cycle_count += 1
if self.on_cycle:
    self.on_cycle(self.cycle_count)
```

### 2. `modbus_manager.py` — `start_listener` 新增參數

```python
# 修正前
async def start_listener(
    self,
    config: ModbusConfigCreate,
    on_sn_received: Optional[callable] = None,
    on_error: Optional[callable] = None
) -> ModbusListenerService:

# 修正後
async def start_listener(
    self,
    config: ModbusConfigCreate,
    on_sn_received: Optional[callable] = None,
    on_error: Optional[callable] = None,
    on_connected: Optional[callable] = None,
    on_cycle: Optional[callable] = None,
) -> ModbusListenerService:
    ...
    if on_connected:
        listener.on_connected = on_connected
    if on_cycle:
        listener.on_cycle = on_cycle
```

### 3. `modbus_ws.py` — 定義並綁定新 Callback

```python
def on_connected(connected: bool):
    """Callback when Modbus TCP connection state changes"""
    asyncio.create_task(
        ws_manager.send_to_station(station_id, {
            "type": "connected_change",
            "connected": connected,
        })
    )

def on_cycle(cycle_count: int):
    """Callback each polling cycle to keep cycle_count real-time"""
    asyncio.create_task(
        ws_manager.send_to_station(station_id, {
            "type": "cycle_update",
            "cycle_count": cycle_count,
        })
    )

await modbus_manager.start_listener(
    config_schema,
    on_sn_received=on_sn_received,
    on_error=on_error,
    on_connected=on_connected,
    on_cycle=on_cycle,
)
```

### 4. `ModbusConfig.vue` — 新增兩個訊息處理器

```javascript
} else if (data.type === 'connected_change') {
  // 即時更新 Connected 顯示，TCP 連線狀態改變時觸發
  if (listenerStatus.value) {
    listenerStatus.value.connected = data.connected
  }
} else if (data.type === 'cycle_update') {
  // 即時更新 Cycle Count，每次輪詢完成後觸發
  if (listenerStatus.value) {
    listenerStatus.value.cycle_count = data.cycle_count
  }
}
```

**`listenerStatus.value` null 檢查的原因：**

與 `Last SN` 的修正相同，WebSocket 可能在 `get_status` 初始化 `listenerStatus` 之前就推送事件（例如 Listener 已在後台運行）。

---

## 完整訊息流（修正後）

```
Listener 啟動並成功連線：
  後端：self.connected: False → True
  後端推送：{"type": "connected_change", "connected": true}
  前端更新：listenerStatus.value.connected = true
  顯示：Connected → Yes ✅

每次輪詢成功：
  後端：self.cycle_count += 1 → 1, 2, 3...
  後端推送：{"type": "cycle_update", "cycle_count": N}
  前端更新：listenerStatus.value.cycle_count = N
  顯示：Cycle Count → 1, 2, 3... ✅

連線中斷（重連失敗）：
  後端：self.connected: True → False
  後端推送：{"type": "connected_change", "connected": false}
  前端更新：listenerStatus.value.connected = false
  顯示：Connected → No ✅
```

---

## 相關檔案

| 檔案 | 修改說明 |
|------|---------|
| `frontend/src/views/ModbusConfig.vue` | 新增 `connected_change` 和 `cycle_update` 訊息處理器 |
| `backend/app/api/modbus_ws.py` | 新增 `on_connected` 和 `on_cycle` callback 定義，傳入 `start_listener` |
| `backend/app/services/modbus/modbus_manager.py` | `start_listener` 新增 `on_connected` 和 `on_cycle` 參數 |
| `backend/app/services/modbus/modbus_listener.py` | 新增 callback 欄位；`connected` 改邊緣觸發；`cycle_count` 遞增後觸發 |

## 關聯問題

- `docs/issues/2026-03-25-modbus-last-sn-not-realtime-update.md` — 同一個 `status` 快照架構缺陷，本次修正為其「已知的獨立問題」章節中的後續修正
