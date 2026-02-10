# 修正 measured_value 資料庫錯誤

## 問題描述

在測試執行後保存測試結果時，出現以下錯誤：

```
ERROR - Failed to create test result: (pymysql.err.DataError) (1366, "Incorrect decimal value: '' for column 'measured_value' at row 1")
```

## 錯誤日誌

```
2026-02-10 15:41:06 - ERROR - Failed to create test result: (pymysql.err.DataError) (1366, "Incorrect decimal value: '' for column 'measured_value' at row 1")
[SQL: INSERT INTO test_results (..., measured_value, ...) VALUES (..., %(measured_value)s, ...)]
[parameters: {..., 'measured_value': '', ...}]
```

## 根本原因

1. **資料庫 Schema 不同步**
   - 資料庫中 `test_results.measured_value` 欄位類型是 `DECIMAL(15,6)`
   - 程式碼模型中定義為 `String(100)`（`backend/app/models/test_result.py` line 26）
   - 兩者不一致導致類型轉換錯誤

2. **空字串無法轉換為 DECIMAL**
   - 當測試項目沒有測量值時，前端傳遞空字串 `''`
   - MySQL 無法將空字串轉換為 DECIMAL 類型
   - 導致 `DataError: (1366, "Incorrect decimal value: '' for column 'measured_value' at row 1")`

3. **測試失敗原因**
   - 從日誌可以看到 `error_message: "Partial failed: '456' not in 'None'"`
   - 這是 `limit_type='partial'` 的驗證失敗（部分包含驗證）
   - 測量值為 `None`，無法進行字串包含檢查

## 解決方案

### 1. 修改資料庫欄位類型

```sql
-- 將 measured_value 從 DECIMAL(15,6) 改為 VARCHAR(100)
ALTER TABLE test_results
MODIFY COLUMN measured_value VARCHAR(100) NULL
COMMENT '測量值 (支援數字和字串類型，例如: "1.5", "Hello World", "PASS")';
```

**為什麼需要 VARCHAR？**
- PDTool4 支援多種測量值類型：數字（1.5）、字串（"Hello World"）、狀態（"PASS"）
- WebPDTool 繼承了這個設計，需要支援所有類型
- DECIMAL 只能存儲數字，無法滿足需求

### 2. 修正後端程式碼

**backend/app/api/tests.py** (line 255-270):

```python
# 修正: 確保 measured_value 正確處理空字串和 NULL
measured_value_str = None
if result_data.measured_value is not None:
    value_str = str(result_data.measured_value).strip()
    # 空字串或 "None" 視為 NULL
    if value_str and value_str.lower() != 'none':
        measured_value_str = value_str

db_result = TestResultModel(
    # ...
    measured_value=measured_value_str,  # 空字串轉換為 NULL
    # ...
)
```

**處理邏輯：**
1. 如果 `measured_value` 是 `None` → 存儲為 `NULL`
2. 如果是空字串 `''` → 轉換為 `NULL`
3. 如果是字串 `"None"` → 轉換為 `NULL`
4. 其他情況 → 轉換為字串並存儲

### 3. 修正前端程式碼

**frontend/src/views/TestMain.vue** (line 1113-1120):

```javascript
// 修正: 將 measured_value 轉換為字串，避免類型不匹配
const measuredValueStr = response.measured_value !== null && response.measured_value !== undefined
  ? String(response.measured_value)
  : null

await createTestResult(currentSession.value.id, {
  // ...
  measured_value: measuredValueStr,
  // ...
})
```

## 額外問題：報告目錄權限

### 錯誤訊息

```
ERROR - Failed to save report for session 69: [Errno 13] Permission denied: 'reports/Demo Project 1/Test Station 1/20260210'
```

### 原因

- `reports/Demo Project 1/` 目錄的擁有者是 `root`
- 後端服務以 `ubuntu` 用戶運行
- 無法在 `root` 擁有的目錄下創建子目錄

### 解決方案

**方案 A: 修復目錄權限（需要 root 權限）**

```bash
sudo chown -R ubuntu:ubuntu reports/
```

**方案 B: 使用備用目錄（已實施）**

修改 `backend/app/services/report_service.py` (line 70-86):

```python
try:
    report_dir.mkdir(parents=True, exist_ok=True)
except PermissionError as e:
    # 如果遇到權限錯誤，使用備用目錄
    self.logger.warning(f"Permission denied creating {report_dir}, using fallback directory")
    fallback_dir = Path.home() / "webpdtool_reports" / project_name / station_name / date_str
    fallback_dir.mkdir(parents=True, exist_ok=True)
    self.logger.info(f"Using fallback report directory: {fallback_dir}")
    return fallback_dir
```

**備用目錄位置：**
- `~/webpdtool_reports/` (用戶主目錄下)
- 完整路徑：`/home/ubuntu/webpdtool_reports/{project}/{station}/{YYYYMMDD}/`

## 執行步驟

### 1. 修改資料庫結構

```bash
cd /home/ubuntu/python_code/WebPDTool/backend
uv run python << 'EOF'
from sqlalchemy import create_engine, text
engine = create_engine('mysql+pymysql://pdtool:pdtool123@localhost:33306/webpdtool')

with engine.connect() as conn:
    conn.execute(text("""
        ALTER TABLE test_results
        MODIFY COLUMN measured_value VARCHAR(100) NULL
    """))
    conn.commit()
    print("✅ measured_value 欄位類型已修改為 VARCHAR(100)")
EOF
```

### 2. 重新啟動後端（如果需要）

如果使用 `--reload` 模式，後端會自動重新載入。否則：

```bash
# 停止後端
pkill -f "uvicorn app.main:app"

# 重新啟動
cd /home/ubuntu/python_code/WebPDTool/backend
uv run uvicorn app.main:app --host 0.0.0.0 --port 8765 --reload
```

### 3. 修復報告目錄權限（可選）

```bash
# 方法 1: 修改擁有者（需要 sudo）
sudo chown -R ubuntu:ubuntu reports/

# 方法 2: 使用備用目錄（已自動處理）
# 系統會自動使用 ~/webpdtool_reports/ 作為備用目錄
```

## 驗證

### 1. 檢查資料庫欄位類型

```sql
DESCRIBE test_results;
```

應該看到：
```
measured_value | varchar(100) | YES | | NULL |
```

### 2. 重新執行測試

1. 刷新前端頁面
2. 開始測試
3. 觀察日誌，應該不再出現 `Incorrect decimal value` 錯誤

### 3. 檢查報告目錄

```bash
# 檢查原目錄
ls -la reports/

# 檢查備用目錄
ls -la ~/webpdtool_reports/
```

## 相關檔案

- `backend/app/models/test_result.py` - TestResult 模型定義
- `backend/app/schemas/test_result.py` - TestResult Schema 定義
- `backend/app/api/tests.py` - 測試結果 API
- `backend/app/services/report_service.py` - 報告生成服務
- `backend/scripts/fix_measured_value_type.sql` - Migration SQL 腳本
- `frontend/src/views/TestMain.vue` - 測試執行介面

## 注意事項

1. **資料遷移**
   - 如果資料庫中已有 DECIMAL 類型的測量值，會自動轉換為 VARCHAR
   - 數字會保留原有精度（例如 1.500000 → "1.500000"）

2. **向後相容性**
   - VARCHAR 類型可以存儲數字字串（"1.5"）和純文字（"Hello"）
   - 數值比較需要在應用層進行類型轉換

3. **測試項目配置**
   - 從錯誤日誌看到 `eq_limit='456'`，但測量值為 `None`
   - 建議檢查測試項目配置，確保 `limit_type` 和測量值類型匹配

## 修正時間

2026-02-10
