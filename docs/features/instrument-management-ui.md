# 儀器管理 UI 實作說明

## 概述

本文件說明儀器管理 CRUD 介面的前端實作過程，包含新增的檔案、修改的檔案、以及除錯過程中發現並修正的一個 driver registry 命名不一致問題。

後端 API (`/api/instruments`) 已於先前的提交中完成（`8823259`），本次實作僅涉及前端。

---

## 新增檔案

### `frontend/src/api/instruments.js`

儀器 API 客戶端模組，封裝對 `/api/instruments` 的 5 個操作：

```javascript
getInstruments(enabledOnly)        // GET  /api/instruments
getInstrument(instrumentId)        // GET  /api/instruments/:id
createInstrument(data)             // POST /api/instruments
updateInstrument(instrumentId, data) // PATCH /api/instruments/:id
deleteInstrument(instrumentId)     // DELETE /api/instruments/:id
```

與 `api/users.js` 的命名慣例一致。`apiClient` 的 response interceptor 會自動解包 `response.data`，因此呼叫端直接取得 payload。

### `frontend/src/stores/instruments.js`

Pinia Composition API store，提供：

- `instruments` (ref) — 儀器列表狀態
- `loading` (ref) — 載入狀態
- `fetchInstruments(enabledOnly)` — 拉取列表並更新 store
- `addInstrument(data)` / `modifyInstrument(id, data)` / `removeInstrument(id)` — 寫入後自動刷新列表

### `frontend/src/views/InstrumentManage.vue`

主要 CRUD 視圖，採用與 `UserManage.vue` 相同的結構模式：

| 功能 | 實作方式 |
|------|---------|
| 表格顯示 | `el-table` + `v-loading` |
| 新增/編輯 | `el-dialog` + `el-form` + `reactive()` |
| 刪除確認 | `ElMessageBox.confirm()` |
| 權限控制 | `isAdmin` computed，非 admin 顯示 `el-alert` 且按鈕 disabled |
| 表單驗證 | `instrument_id` 格式 regex、必填欄位 |

**動態連線參數表單**：根據 `conn_type` 切換顯示不同欄位群組（使用 `<template v-if>`），切換時呼叫 `handleConnTypeChange()` 重置 `conn_params` 物件，避免舊欄位污染新類型的 payload。

支援的連線類型及其對應欄位：

| conn_type | 欄位 |
|-----------|------|
| VISA | address |
| SERIAL | port, baudrate, databits, stopbits, parity |
| TCPIP_SOCKET | host, port |
| GPIB | address |
| LOCAL | command |

**更新操作**：使用 PATCH，並透過解構排除 `instrument_id`（後端不允許修改）：

```javascript
const { instrument_id, ...updateData } = instrumentData
await updateInstrument(editingInstrument.instrument_id, updateData)
```

---

## 修改檔案

### `frontend/src/router/index.js`

在 `/users` 路由後方新增：

```javascript
{
  path: '/instruments',
  name: 'InstrumentManage',
  component: () => import('@/views/InstrumentManage.vue'),
  meta: { requiresAuth: true }
}
```

### `frontend/src/components/AppNavBar.vue`

在「使用者管理」按鈕後新增導航按鈕，沿用相同的 `buttonType()` / `isCurrent()` 模式：

```vue
<el-button :type="buttonType('instruments')" size="default"
           :disabled="isCurrent('instruments')"
           @click="navigateTo('/instruments')">
  儀器管理
</el-button>
```

### `frontend/src/views/TestMain.vue`

在主畫面右上角導航列新增「儀器管理」按鈕（位於「使用者管理」與「報表分析」之間）：

```vue
<el-button size="default" @click="navigateTo('/instruments')">儀器管理</el-button>
```

### `CLAUDE.md`

在「Managing Users」章節後新增「Managing Instruments」章節，記錄所有相關檔案位置、API endpoints、支援的儀器類型與連線類型。

---

## 除錯：Driver Registry 命名不一致問題

### 問題描述

建立儀器時，`instrument_type` 欄位選擇 `ConsoleCommand`，`conn_type` 選擇 `LOCAL`。
執行測試時出現錯誤：

```
No driver for instrument type 'ConsoleCommand'
```

### 根本原因

`_row_to_config()` 將 DB 的 `instrument_type` 欄位直接作為 `config.type`：

```python
# backend/app/core/instrument_config.py
return InstrumentConfig(
    id=row.instrument_id,
    type=row.instrument_type,  # → "ConsoleCommand"
    ...
)
```

但 `INSTRUMENT_DRIVERS` registry（`backend/app/services/instruments/__init__.py`）只有小寫的 key：

```python
INSTRUMENT_DRIVERS = {
    ...
    "console": ConSoleCommandDriver,   # ← 小寫
    "comport": ComPortCommandDriver,
    "tcpip": TCPIPCommandDriver,
}
```

當 driver lookup 執行 `INSTRUMENT_DRIVERS.get("ConsoleCommand")` 時找不到對應 → 回傳 `None` → 產生錯誤訊息。

### 修正方式

在 `INSTRUMENT_DRIVERS` 新增 UI 儲存的大寫名稱作為別名：

```python
# backend/app/services/instruments/__init__.py

# Aliases matching instrument_type values stored in DB (via InstrumentManage UI)
"ConsoleCommand": ConSoleCommandDriver,
"ComPortCommand": ComPortCommandDriver,
"TCPIPCommand":   TCPIPCommandDriver,
```

### 為何選擇在 registry 加 alias 而非改 UI

- **加 alias 是加法操作**，不影響現有資料和測試
- UI 的 `instrument_type` 選項名稱來自 PDTool4 慣例，保持一致性對使用者較直觀
- 若改 UI 選項值，資料庫中已存在的舊資料仍為 `"ConsoleCommand"`，問題依然存在
- Registry alias 可同時相容新舊兩種命名

---

## 相關檔案總覽

| 檔案 | 類型 | 說明 |
|------|------|------|
| `frontend/src/api/instruments.js` | 新增 | API 客戶端 |
| `frontend/src/stores/instruments.js` | 新增 | Pinia store |
| `frontend/src/views/InstrumentManage.vue` | 新增 | CRUD 視圖 |
| `frontend/src/router/index.js` | 修改 | 新增 `/instruments` 路由 |
| `frontend/src/components/AppNavBar.vue` | 修改 | 新增導航按鈕 |
| `frontend/src/views/TestMain.vue` | 修改 | 主畫面新增導航連結 |
| `backend/app/services/instruments/__init__.py` | 修改 | 新增 driver alias |
| `CLAUDE.md` | 修改 | 新增文件章節 |
