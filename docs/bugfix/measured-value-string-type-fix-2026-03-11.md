# 修正 measured_value 字串類型無法儲存問題

**日期**: 2026-03-11
**狀態**: ✅ 已修正

---

## 問題描述

`test_type='console'` 的測試項目（如 `echo_hello`, `echo_test`）執行後，`測試結果查詢` 頁面的「測量值」欄位顯示空白。

後端 log 出現 500 錯誤：

```
ERROR - Failed to create test result: (pymysql.err.DataError) (1366, "Incorrect decimal value: 'hello' for column 'measured_value' at row 1")
ERROR - Failed to create test result: (pymysql.err.DataError) (1366, "Incorrect decimal value: 'test' for column 'measured_value' at row 1")
```

---

## 根本原因分析

### 問題 1：前端過濾字串值（TestMain.vue）

`frontend/src/views/TestMain.vue` 有一段舊的「修正」代碼，誤以為 DB 的 `measured_value` 是 `DECIMAL` 欄位，
因此強制將字串值轉為 `null`：

```javascript
// 舊代碼（有問題）
const asNum = Number(rawValue)
measuredValueStr = (!isNaN(asNum) && rawValue !== '') ? String(rawValue) : null
// → 'hello' 被轉為 null，不送到 API
```

這導致字串量測值（如 `'hello'`）在送出前被丟棄，測試結果的 `measured_value` 始終是 `null`。

### 問題 2：資料庫欄位類型不符

修正前端代碼後，字串值 `'hello'`、`'test'` 正確送到後端，但資料庫欄位 `measured_value` 實際類型為 `DECIMAL(15,6)`，
導致 MySQL DataError：

```
pymysql.err.DataError: (1366, "Incorrect decimal value: 'hello' for column 'measured_value' at row 1")
```

**三層不一致：**

| 層級 | 定義 | 實際狀態 |
|------|------|---------|
| `backend/app/models/test_result.py` | `String(100)` | ✅ 正確 |
| `database/schema.sql` | `DECIMAL(15,6)` | ❌ 過時 |
| 實際 MySQL DB | `DECIMAL(15,6)` | ❌ 過時 |

`schema.sql` 和 DB 未跟上 model 的變更，導致不一致。

---

## 修正內容

### 修正 1：前端 TestMain.vue（移除字串過濾限制）

**檔案：** `frontend/src/views/TestMain.vue`（約 line 1159）

```javascript
// 修正前（舊代碼，誤認 DB 欄位為 decimal）
const rawValue = response.measured_value
let measuredValueStr = null
if (rawValue !== null && rawValue !== undefined) {
  const asNum = Number(rawValue)
  measuredValueStr = (!isNaN(asNum) && rawValue !== '') ? String(rawValue) : null
}

// 修正後（DB 欄位已是 VARCHAR(100)，直接儲存字串）
const rawValue = response.measured_value
let measuredValueStr = null
if (rawValue !== null && rawValue !== undefined && String(rawValue).trim() !== '') {
  measuredValueStr = String(rawValue)
}
```

### 修正 2：資料庫欄位類型變更

```sql
ALTER TABLE test_results MODIFY COLUMN measured_value VARCHAR(100) NULL;
```

### 修正 3：同步 schema.sql

**檔案：** `database/schema.sql`（約 line 121）

```sql
-- 修正前
measured_value DECIMAL(15,6),

-- 修正後
measured_value VARCHAR(100),  -- Changed from DECIMAL(15,6) to support string measurement values (e.g. console output)
```

---

## Alembic Migration 設定

### 背景

此專案的 DB 一直是用 `schema.sql` 手動建立，Alembic 雖已設定但從未實際管理 DB。
`alembic_version` 表不存在，`alembic current` 回傳空白。

已存在的 migration 檔案：
```
base → 0232af89acc2 → 9dd55b733f64 → 20250109_change_measured_value → a8124fdea538 (head)
```

其中 `20250109_change_measured_value` 正是將 `measured_value` 從 `DECIMAL` 改為 `String` 的 migration，
但當時未套用到生產 DB。

### 解決方式：stamp 到 head

由於 DB 已透過 `ALTER TABLE` 手動改為 `VARCHAR(100)`，直接將 Alembic 標記至最新 revision：

```bash
docker-compose exec backend bash -c "cd /app && .venv/bin/alembic stamp a8124fdea538"
```

**驗證：**
```bash
docker-compose exec backend bash -c "cd /app && .venv/bin/alembic current"
# 應顯示: a8124fdea538 (head)
```

### 往後 schema 變更流程

```bash
# 1. 建立 migration
docker-compose exec backend bash -c "cd /app && .venv/bin/alembic revision --autogenerate -m '描述'"

# 2. 確認 backend/alembic/versions/ 中的新檔案內容

# 3. 套用
docker-compose exec backend bash -c "cd /app && .venv/bin/alembic upgrade head"
```

---

## 驗證

```sql
-- 確認 DB 欄位類型
SHOW COLUMNS FROM test_results LIKE 'measured_value';
-- Field: measured_value | Type: varchar(100) | Null: YES
```

重新執行測試後，`echo_hello` 和 `echo_test` 的測量值欄位正確顯示 `hello` 和 `test`。

---

## 影響範圍

| 元件 | 變更 |
|------|------|
| `frontend/src/views/TestMain.vue` | 移除字串值過濾邏輯 |
| `database/schema.sql` | `measured_value` 類型改為 `VARCHAR(100)` |
| MySQL DB | `ALTER TABLE` 已執行 |
| Alembic | `stamp a8124fdea538` 開始追蹤 |

## 相關檔案

- `backend/app/models/test_result.py:26` — `measured_value = Column(String(100), nullable=True)`
- `backend/app/api/tests.py:255` — `create_test_result` 端點
- `backend/alembic/versions/20250109_change_measured_value_to_string.py` — 對應的 migration 檔案
