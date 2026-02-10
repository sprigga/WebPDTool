# 修正 switch_mode 資料庫 Schema 問題

## 問題描述

在測試執行時，出現以下錯誤：

```
保存測試結果失敗: Request failed with status code 500
```

後端日誌顯示：

```
sqlalchemy.exc.OperationalError: (pymysql.err.OperationalError) (1054, "Unknown column 'switch_mode' in 'field list'")
```

## 根本原因

1. **資料庫 Schema 不同步**
   - 程式碼模型（`backend/app/models/testplan.py`）定義了 `switch_mode` 欄位
   - 但資料庫 `test_plans` 表中沒有這個欄位
   - 導致 SQLAlchemy 查詢時發生 1054 錯誤

2. **缺少資料庫遷移**
   - `switch_mode` 欄位是新增的功能，用於取代 `case_type`
   - 但沒有執行對應的 database migration
   - 導致資料庫結構與程式碼不一致

## 解決方案

### 1. 添加 switch_mode 欄位

執行以下 SQL 語句：

```sql
ALTER TABLE test_plans
ADD COLUMN switch_mode VARCHAR(50) NULL AFTER test_type
COMMENT '儀器模式或腳本名稱 (DAQ973A, MODEL2303, test123, wait, relay, etc.)';
```

### 2. 遷移現有資料

將 `case_type` 的值複製到 `switch_mode`（向後相容）：

```sql
UPDATE test_plans
SET switch_mode = case_type
WHERE switch_mode IS NULL AND case_type IS NOT NULL AND case_type != '';
```

### 3. 程式碼修正

#### 前端 (TestMain.vue)

修正測量值類型轉換問題：

```javascript
// Line 1113-1120: 確保 measured_value 始終為字串
const measuredValueStr = response.measured_value !== null && response.measured_value !== undefined
  ? String(response.measured_value)
  : null

await createTestResult(currentSession.value.id, {
  // ...
  measured_value: measuredValueStr,
  // ...
})
```

#### 後端 (tests.py)

添加錯誤處理和類型轉換：

```python
# Line 255-291: 確保 measured_value 轉換為字串
try:
    measured_value_str = None
    if result_data.measured_value is not None:
        measured_value_str = str(result_data.measured_value)

    db_result = TestResultModel(
        # ...
        measured_value=measured_value_str,
        # ...
    )
    db.add(db_result)
    db.commit()
    db.refresh(db_result)
    return db_result
except Exception as e:
    db.rollback()
    logger.error(f"Failed to create test result: {e}")
    raise HTTPException(status_code=500, detail=f"Failed to create test result: {str(e)}")
```

## 執行步驟

### 方法 1: 使用 SQL 腳本

```bash
cd /home/ubuntu/python_code/WebPDTool/backend
mysql -h localhost -P 33306 -u pdtool -ppdtool123 webpdtool < scripts/add_switch_mode_column.sql
```

### 方法 2: 使用 Python 腳本

```bash
cd /home/ubuntu/python_code/WebPDTool/backend
uv run python << 'EOF'
from sqlalchemy import create_engine, text
engine = create_engine('mysql+pymysql://pdtool:pdtool123@localhost:33306/webpdtool')

with engine.connect() as conn:
    # 添加欄位
    conn.execute(text("""
        ALTER TABLE test_plans
        ADD COLUMN IF NOT EXISTS switch_mode VARCHAR(50) NULL AFTER test_type
    """))

    # 遷移資料
    conn.execute(text("""
        UPDATE test_plans
        SET switch_mode = case_type
        WHERE switch_mode IS NULL AND case_type IS NOT NULL AND case_type != ''
    """))

    conn.commit()
    print("✅ Switch mode 欄位已添加並遷移完成")
EOF
```

## 驗證

檢查資料庫結構：

```sql
DESCRIBE test_plans;
```

應該看到 `switch_mode VARCHAR(50) NULL` 欄位。

檢查資料遷移：

```sql
SELECT COUNT(*) as total_items,
       SUM(CASE WHEN switch_mode IS NOT NULL THEN 1 ELSE 0 END) as with_switch_mode,
       SUM(CASE WHEN case_type IS NOT NULL THEN 1 ELSE 0 END) as with_case_type
FROM test_plans;
```

## 注意事項

1. **向後相容性**
   - `case_type` 欄位保留不刪除
   - 舊的測試計劃仍然可以使用 `case_type`
   - 程式碼優先使用 `switch_mode`，若為 NULL 則回退到 `case_type`

2. **資料一致性**
   - 新建立的測試項目應該設定 `switch_mode` 而非 `case_type`
   - CSV 匯入時應該將 `case` 欄位映射到 `switch_mode`

3. **未來遷移**
   - 考慮使用 Alembic 管理資料庫遷移
   - 避免手動修改資料庫 schema

## 相關檔案

- `backend/app/models/testplan.py` - TestPlan 模型定義
- `backend/app/schemas/testplan.py` - TestPlan Schema 定義
- `backend/scripts/add_switch_mode_column.sql` - Migration SQL 腳本
- `frontend/src/views/TestMain.vue` - 測試執行介面
- `backend/app/api/tests.py` - 測試結果 API

## 修正時間

2026-02-10
