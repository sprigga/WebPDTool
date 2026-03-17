# TestResults 詳情對話框空白 & wall_time_ms 修正

**日期：** 2026-03-16
**影響範圍：** `frontend/src/views/TestMain.vue`, `frontend/src/views/TestResults.vue`

---

## 問題描述

使用者反映：在「測試結果詳情」對話框中，沒有任何測試項目的明細顯示。

---

## 除錯過程

### Step 1：確認 API 正常

查看 Nginx access log，發現使用者點擊的是 Session 211：

```
GET /api/tests/sessions/211/results HTTP/1.1" 200 2
```

回應大小為 **2 bytes**，即空陣列 `[]`。

直接查詢 DB 確認：

```sql
SELECT COUNT(*) FROM test_results WHERE session_id = 211;
-- 結果: 0
```

**結論：** API 和前端邏輯都正確，是 Session 211 本身在 `test_results` 表中確實沒有資料列。

### Step 2：追蹤 Session 211 的來源

Session 211 是前一次除錯過程（時區修正驗證）中手動建立的，透過 API 呼叫 `/complete` 時設定了 `total_items=1, pass_items=1`，但實際的 `test_results` 資料列儲存在其他 session（214）下。

```sql
SELECT id, serial_number, final_result, total_items FROM test_sessions
WHERE id IN (211, 212, 213, 214, 215);
```

| id  | serial_number     | final_result | total_items |
|-----|-------------------|--------------|-------------|
| 211 | TEST-TZ-FIX       | PASS         | 1           |
| 212 | TEST-TZ-FIX-2     | PASS         | 1           |
| 213 | TEST-WALL-TIME    | NULL         | NULL        |
| 214 | TEST-WALL-TIME-2  | NULL         | NULL        |
| 215 | AUTO-xxx          | PASS         | 4           |

Session 215（由 UI 正常執行的測試）有 4 筆結果，API 正確回傳 → 前端正常運作。

### Step 3：發現 wall_time_ms 永遠為 null

檢查 `TestMain.vue` 的程式碼邏輯：

```javascript
// 外層迴圈
const itemWallStart = Date.now()
const result = await executeSingleItem(item, index)  // ← createTestResult 在此函式「內部」被呼叫
item.wall_time_ms = Date.now() - itemWallStart        // ← 設定在「外層」，已經太晚

// executeSingleItem 內部
await createTestResult(currentSession.value.id, {
  ...
  wall_time_ms: item.wall_time_ms || null  // ← 此時 item.wall_time_ms 仍是 undefined！
})
```

**根本原因：** `createTestResult` 在 `executeSingleItem` 內部呼叫，但 `item.wall_time_ms` 在 `executeSingleItem` 回傳之後才被賦值，造成 `wall_time_ms` 永遠為 `null`。

### Step 4：確認問題與 UX 缺陷

兩個獨立問題：

1. **wall_time_ms 永遠為 null** — 時序錯誤（程式碼 bug）
2. **對話框顯示空白但無說明訊息** — UX 問題（當 session 確實無資料時，使用者無法分辨是資料問題還是程式錯誤）

---

## 修正方案

### Fix 1：TestMain.vue — 將 createTestResult 移至外層迴圈

**修改前（錯誤時序）：**

```
外層迴圈:
  itemWallStart = Date.now()
  result = await executeSingleItem(item, index)
    └─ executeSingleItem 內部:
         ...執行量測...
         await createTestResult({ wall_time_ms: item.wall_time_ms })  ← undefined!
  item.wall_time_ms = Date.now() - itemWallStart  ← 太晚了
```

**修改後（正確時序）：**

```
外層迴圈:
  itemWallStart = Date.now()
  result = await executeSingleItem(item, index)
    └─ executeSingleItem 內部:
         ...執行量測...
         return { result, measured_value_str, execution_duration_ms }  ← 只回傳，不儲存
  wallTimeMs = Date.now() - itemWallStart  ← 正確計算
  item.wall_time_ms = wallTimeMs
  await createTestResult({ ..., wall_time_ms: wallTimeMs })  ← 正確的值
```

**`executeSingleItem` 的回傳值新增 `measured_value_str` 和 `execution_duration_ms`：**

```javascript
// 修改後的 return（移除 createTestResult，新增回傳欄位）
return {
  result: result,
  measured_value: response.measured_value,
  measured_value_str: measuredValueStr,          // 新增: 供外層 createTestResult 使用
  error_message: response.error_message,
  execution_duration_ms: response.execution_duration_ms  // 新增
}
```

**外層迴圈新增 createTestResult 呼叫：**

```javascript
const itemWallStart = Date.now()
const result = await executeSingleItem(item, index)

if (currentSession.value && item.id) {
  const wallTimeMs = Date.now() - itemWallStart
  item.wall_time_ms = wallTimeMs
  try {
    await createTestResult(currentSession.value.id, {
      session_id: currentSession.value.id,
      test_plan_id: item.id,
      item_no: item.item_no,
      item_name: item.item_name,
      measured_value: result.measured_value_str,
      lower_limit: item.lower_limit,
      upper_limit: item.upper_limit,
      unit: item.unit,
      result: result.result,
      error_message: result.error_message,
      execution_duration_ms: result.execution_duration_ms,
      wall_time_ms: wallTimeMs   // ← 現在有正確的值
    })
  } catch (saveError) {
    console.error('Failed to save test result:', saveError)
    addStatusMessage(`保存測試結果失敗: ${saveError.message}`, 'warning')
  }
}
```

### Fix 2：TestResults.vue — 新增空資料提示訊息

在詳情對話框的 `el-table` 前加入 `el-alert`，當確實沒有資料時顯示說明：

```html
<el-alert
  v-if="!resultsLoading && sessionResults.length === 0"
  title="此 Session 無測試項目明細"
  type="info"
  :closable="false"
  style="margin-bottom: 12px"
/>
<el-table
  v-else
  :data="sessionResults"
  v-loading="resultsLoading"
  stripe
  max-height="500"
>
```

---

## 驗證

重新建置前端 Docker 映像後確認：

```bash
docker-compose build --no-cache frontend
docker-compose up -d frontend
```

確認 built JS 含有修正內容：

```python
# TestResults-elcZHyAT.js
'此 Session 無測試項目明細' in content  # True
'Wall Time' in content                   # True

# TestMain-CPdGup5D.js
# wall_time_ms 現在在外層迴圈計算後傳入 createTestResult
content.count('wall_time_ms')  # 2 (正確位置)
```

---

## 設計要點

### 為何將 createTestResult 移出 executeSingleItem？

`executeSingleItem` 的職責是「執行量測並回傳結果」。將 `createTestResult`（DB 寫入）放在內部違反了單一職責原則，且造成時序依賴（`wall_time_ms` 必須在外層計算）。

移出後：
- `executeSingleItem` = 純量測執行（與 DB 解耦）
- 外層迴圈 = 負責 DB 寫入和時間計算
- `wall_time_ms` = 真實的前端端到端時間（量測 + 網路 + DB 寫入）

### wall_time_ms 的語義

| 欄位 | 計量範圍 | 儲存者 |
|------|----------|--------|
| `execution_duration_ms` | 後端純執行時間（硬體/指令）| 後端 |
| `wall_time_ms` | 前端端到端時間（量測 + 網路 + DB 寫入）| 前端 |
| Overhead = wall - execution | 系統 overhead（網路延遲 + DB overhead）| 前端計算顯示 |
