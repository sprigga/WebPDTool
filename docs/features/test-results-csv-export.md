# 測試結果批次 CSV 匯出功能

> **版本**: 1.0
> **建立日期**: 2026-03-11
> **功能狀態**: ✅ 已實現

---

## 📋 功能概述

「測試結果查詢」頁面（`TestResults.vue`）的「匯出結果」按鈕，提供依篩選條件批次匯出測試 Session 及明細項目為 CSV 檔案的功能。

### 核心特性

- **批次匯出**：依當前查詢篩選條件（站別、專案、序號、結果、日期範圍、測試計劃）匯出所有符合的 Session
- **寬格式 CSV**：每行 = 一個測試項目，Session 摘要欄位只在第一個子項目行填入（便於 Excel 過濾）
- **Excel 相容**：使用 `utf-8-sig` BOM 編碼，確保 Windows Excel 正確顯示中文
- **即時串流**：後端以 `StreamingResponse` 回傳，不需預先存檔

---

## 🔍 除錯過程與問題診斷

### 問題現象

點擊「匯出結果」按鈕後，顯示 `匯出功能尚未啟用` 訊息，沒有任何 CSV 下載。

### 原因分析（逐層追蹤）

#### 1. 前端：錯誤被刻意抑制

`TestResults.vue` 的 `handleExport` 函式：

```js
// 修改前：錯誤直接被吃掉，顯示誤導性訊息
const handleExport = async () => {
  try {
    const blob = await exportTestResults(buildQueryParams())
    // ... 下載邏輯
  } catch (error) {
    ElMessage.info('匯出功能尚未啟用')  // ← stub 占位符，掩蓋真實錯誤
  }
}
```

這是典型的開發中 stub 寫法：功能未完成時先顯示提示訊息，但這同時也讓真實的 API 錯誤無法浮現。

#### 2. 前端 API：路徑正確，但後端端點不存在

`frontend/src/api/testResults.js`：

```js
export const exportTestResults = (params = {}) => {
  return apiClient.get('/api/tests/sessions/export', {
    params,
    responseType: 'blob'   // ← 正確設定，要求回傳 Blob
  })
}
```

路徑 `/api/tests/sessions/export` 是合理設計，但後端的 `/api/tests/sessions` 路由中根本沒有這個端點。

#### 3. 後端：只有單筆匯出，沒有批次匯出

`backend/app/api/results/export.py` 中只有：

```python
@router.get("/export/csv/{session_id}")   # 單筆，掛在 /api/measurement-results/
def export_session_csv(session_id: int, ...):
```

此端點路徑為 `/api/measurement-results/export/csv/{session_id}`，與前端呼叫的 `/api/tests/sessions/export` 完全不同，且只支援單一 Session。

### 路由衝突風險（關鍵細節）

FastAPI 路由匹配是**由上而下順序**：

```python
# 危險：若 /sessions/{session_id} 定義在 /sessions/export 之前
# "export" 字串會被當成 session_id，嘗試轉換 int 失敗並回傳 422

@router.get("/sessions/{session_id}", ...)  # 如果這行在前...
@router.get("/sessions/export", ...)        # ...這行永遠不會被匹配到
```

**修正方式**：`/sessions/export` 必須定義在 `/sessions/{session_id}` 之前。

---

## 🛠️ 實作說明

### 後端：新增批次匯出端點

**檔案**：`backend/app/api/tests.py`

**位置**：定義在第 154 行 `@router.get("/sessions/{session_id}")` 之前

```python
@router.get("/sessions/export")
async def export_test_sessions_csv(
    station_id: int = None,
    project_id: int = None,
    serial_number: str = None,
    test_plan_name: str = None,
    final_result: str = None,
    start_date: str = None,
    end_date: str = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
```

篩選邏輯與 `GET /sessions` 完全相同，確保「查什麼就匯出什麼」。

#### CSV 輸出格式（寬格式）

| Session ID | 序號 | 站別 ID | 測試計劃 | 最終結果 | 開始時間 | 結束時間 | 測試時長(秒) | 總項目 | 通過 | 失敗 | 項次 | 測試項目 | 測量值 | 下限 | 上限 | 單位 | 結果 | 錯誤訊息 | 執行時間(ms) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 42 | SN001 | 3 | Plan A | PASS | 2026-03-11T... | ... | 12.5 | 10 | 10 | 0 | 1 | 電壓測試 | 3.3 | 3.0 | 3.6 | V | PASS | | 52 |
|  |  |  |  |  |  |  |  |  |  |  | 2 | 電流測試 | 1.2 | 1.0 | 1.5 | A | PASS | | 48 |

Session 摘要欄位（前 11 欄）只在該 Session 的第一個測試項目行填入，後續項目行留空，方便 Excel 使用「填滿空白」或 VLOOKUP 關聯。

#### 編碼選擇：utf-8-sig

```python
return StreamingResponse(
    iter([output.getvalue().encode('utf-8-sig')]),  # BOM 讓 Excel 識別 UTF-8
    media_type="text/csv; charset=utf-8",
    headers={"Content-Disposition": f"attachment; filename={filename}"}
)
```

Windows 上直接雙擊開啟 CSV 時，Excel 預設以 ANSI 編碼讀取。加上 BOM（`\xef\xbb\xbf`）可讓 Excel 自動識別為 UTF-8，避免中文亂碼。

### 前端：修正 handleExport

**檔案**：`frontend/src/views/TestResults.vue`（第 478～490 行）

```js
// 修改後
const handleExport = async () => {
  try {
    const response = await exportTestResults(buildQueryParams())
    // apiClient 的 response interceptor 回傳 response.data（即 Blob）
    const blob = response instanceof Blob ? response : new Blob([response])
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `test-results-${new Date().toISOString().slice(0, 10)}.csv`
    link.click()
    window.URL.revokeObjectURL(url)
    ElMessage.success('匯出成功')
  } catch (error) {
    ElMessage.error('匯出失敗，請稍後再試')
  }
}
```

**修改重點**：
1. 移除 `ElMessage.info('匯出功能尚未啟用')` stub 佔位符
2. `instanceof Blob` 防禦性判斷（因 apiClient 的 interceptor 已解包 `response.data`）
3. 加入成功/失敗的明確回饋訊息

---

## 📁 修改檔案清單

| 檔案 | 修改類型 | 說明 |
|------|---------|------|
| `backend/app/api/tests.py` | 新增端點 | 在 `/sessions/{session_id}` 前新增 `GET /sessions/export` |
| `frontend/src/views/TestResults.vue` | 修正邏輯 | 移除 stub，實作真實下載與回饋訊息 |

---

## 🔗 相關端點對照

| 端點 | 用途 |
|------|------|
| `GET /api/tests/sessions` | 查詢 Session 列表（支援分頁） |
| `GET /api/tests/sessions/export` | **批次匯出 CSV**（本功能，不分頁） |
| `GET /api/tests/sessions/{id}/results` | 單一 Session 的明細結果 |
| `GET /api/measurement-results/export/csv/{id}` | 舊有單筆匯出（掛在不同路由前綴） |

---

## ⚠️ 注意事項

- 匯出不分頁，若符合條件的 Session 數量極多，建議縮小日期範圍後再匯出
- 篩選參數與查詢頁面共用 `buildQueryParams()`，確保「所見即所得」
- 若 Session 沒有任何測試項目，仍會輸出一行 Session 摘要（測試項目欄位留空）
