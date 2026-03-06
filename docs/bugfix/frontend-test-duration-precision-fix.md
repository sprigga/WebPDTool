# 問題追蹤和解決方案文檔

## Issue: 測試時長精度損失（Math.round 截斷浮點數）

### 問題描述
**錯誤日期**: 2026-03-06
**錯誤類型**: 資料精度問題
**發生位置**: `frontend/src/views/TestMain.vue:984`

測試結果查詢頁面（TestResults.vue）的「測試時長」欄位顯示 1 秒，但每一個測試項目的實際執行時間為 0.521 秒。

**症狀範例（Session ID: 121）**:
- 每個測試項目執行時間：0.521 s
- 「測試時長」顯示：1 s（應為約 0.521 s）

### 根本原因

`TestMain.vue` 在完成測試 session 時，使用 `Math.round()` 將浮點數秒數四捨五入為整數：

```javascript
// frontend/src/views/TestMain.vue（修正前）
test_duration_seconds: Math.round(elapsedSeconds)
// elapsedSeconds = 0.521 → Math.round(0.521) = 1
```

這導致所有不足一秒的測試時長都被錯誤地顯示為 1 秒。

### 解決方案

移除 `Math.round()`，直接使用浮點數值：

```javascript
// frontend/src/views/TestMain.vue（修正後）
test_duration_seconds: elapsedSeconds
```

**修改的文件**: `frontend/src/views/TestMain.vue`（Line 984）

### 附加說明

- `TestResults.vue` 的 `formatDuration()` 函式本身正確（使用 `toFixed(6)` 顯示六位小數），顯示層沒有問題
- 資料庫 `schema.sql` 定義 `test_duration_seconds INT`，但 SQLAlchemy model 定義為 `Float`，存在不一致。MySQL 的 INT 欄位接收浮點值時會截斷小數，若需要高精度可將 schema 改為 `FLOAT` 或 `DECIMAL`

### 影響範圍

- `frontend/src/views/TestMain.vue`
- 所有已完成的測試 session 的 `test_duration_seconds` 歷史資料已儲存為整數，無法回溯修正

### 變更歷史

| 日期 | 變更內容 |
|------|---------|
| 2026-03-06 | 修正 Math.round 導致時長精度損失 |
