# ISSUE7: Database Schema Mismatch - test_plans Table Missing Columns

## 問題編號
ISSUE7

## 發現日期
2026-02-09

## 問題分類
Database Schema / Migration

## 嚴重程度
🔴 Critical - API 端點返回 500 錯誤，測試計畫功能完全不可用

---

## 問題描述

### 症狀
Backend terminal 顯示以下 API 端點返回 500 Internal Server Error:

```
INFO:     127.0.0.1:44198 - "GET /api/stations/3/testplan-names?project_id=2 HTTP/1.1" 500 Internal Server Error
INFO:     127.0.0.1:44202 - "GET /api/stations/3/testplan-map?enabled_only=true&project_id=2 HTTP/1.1" 500 Internal Server Error
INFO:     127.0.0.1:44212 - "GET /api/stations/3/testplan?enabled_only=true&project_id=2 HTTP/1.1" 500 Internal Server Error
```

### 錯誤訊息
```python
(pymysql.err.OperationalError) (1054, "Unknown column 'test_plans.project_id' in 'field list'")
(pymysql.err.OperationalError) (1054, "Unknown column 'test_plans.test_plan_name' in 'field list'")
```

### 影響範圍
- ❌ 無法取得測試計畫名稱列表
- ❌ 無法建立 TestPointMap
- ❌ 無法查詢測試計畫項目
- ❌ 測試執行功能受阻

---

## 根本原因分析

### 資料庫結構缺陷

**實際資料庫結構** (僅 13 個欄位):
```sql
CREATE TABLE test_plans (
    id INT PRIMARY KEY,
    station_id INT NOT NULL,
    item_no INT NOT NULL,
    item_name VARCHAR(100) NOT NULL,
    test_type VARCHAR(50) NOT NULL,
    parameters JSON,
    lower_limit DECIMAL(15,6),
    upper_limit DECIMAL(15,6),
    unit VARCHAR(20),
    enabled BOOLEAN,
    sequence_order INT NOT NULL,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**ORM 模型期望** (`app/models/testplan.py` - 27 個欄位):
```python
class TestPlan(Base):
    __tablename__ = "test_plans"

    id = Column(Integer, primary_key=True)
    # ⚠️ 缺少的必要欄位
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    station_id = Column(Integer, ForeignKey('stations.id'), nullable=False)
    test_plan_name = Column(String(100), nullable=True)

    # 核心欄位 (存在)
    item_no = Column(Integer, nullable=False)
    item_name = Column(String(100), nullable=False)
    # ... 其他欄位

    # ⚠️ 缺少的 CSV 匯入欄位 (12 個)
    item_key = Column(String(50))
    value_type = Column(String(50))
    limit_type = Column(String(50))
    eq_limit = Column(String(100))
    pass_or_fail = Column(String(20))
    measure_value = Column(String(100))
    execute_name = Column(String(100))
    case_type = Column(String(50))
    command = Column(String(500))
    timeout = Column(Integer)
    use_result = Column(String(100))
    wait_msec = Column(Integer)
```

### 缺少的欄位列表

#### 1. 關聯欄位 (2 個)
- **project_id** - 專案 ID (必要，有外鍵約束)
- **test_plan_name** - 測試計畫名稱

#### 2. CSV 匯入欄位 (12 個，對應 PDTool4 格式)
| 欄位名稱 | 類型 | 用途 |
|---------|------|------|
| item_key | VARCHAR(50) | 項目鍵值 |
| value_type | VARCHAR(50) | 數值類型 (string/integer/float) |
| limit_type | VARCHAR(50) | 限制類型 (lower/upper/both/equality/inequality/partial/none) |
| eq_limit | VARCHAR(100) | 等於限制 |
| pass_or_fail | VARCHAR(20) | 通過或失敗標記 |
| measure_value | VARCHAR(100) | 測量值 |
| execute_name | VARCHAR(100) | 執行名稱 |
| case_type | VARCHAR(50) | 案例類型 |
| command | VARCHAR(500) | 執行命令 |
| timeout | INT | 超時時間(毫秒) |
| use_result | VARCHAR(100) | 使用結果 |
| wait_msec | INT | 等待毫秒數 |

### 為何會發生？

1. **Schema 漂移**: 原始 `database/schema.sql` 沒有包含完整欄位定義
2. **ORM 模型演進**: `app/models/testplan.py` 已更新但資料庫未同步遷移
3. **缺少遷移機制**: 沒有使用 Alembic 自動遷移追蹤變更

---

## 解決方案

### 步驟 1: 建立診斷腳本

建立測試腳本確認錯誤:

```python
# backend/scripts/test_endpoints.py
from app.core.database import SessionLocal
from app.services.test_plan_service import test_plan_service

db = SessionLocal()
try:
    # 測試會失敗並顯示具體錯誤訊息
    names = test_plan_service.get_test_plan_names(
        db=db, project_id=2, station_id=3
    )
except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
```

**執行結果**:
```
✗ Error: (pymysql.err.OperationalError) (1054, "Unknown column 'test_plans.test_plan_name' in 'field list'")
```

### 步驟 2: 建立遷移腳本

建立 `backend/scripts/migrate_test_plans_schema.sql`:

```sql
-- 完整的 test_plans 表結構遷移腳本
USE webpdtool;

-- 安全新增 project_id 欄位
SET @column_exists = (
    SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = 'webpdtool'
    AND TABLE_NAME = 'test_plans'
    AND COLUMN_NAME = 'project_id'
);

SET @sql = IF(@column_exists = 0,
    'ALTER TABLE test_plans ADD COLUMN project_id INT NOT NULL AFTER id',
    'SELECT "Column project_id already exists" AS message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 安全新增 test_plan_name 欄位
SET @column_exists = (
    SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = 'webpdtool'
    AND TABLE_NAME = 'test_plans'
    AND COLUMN_NAME = 'test_plan_name'
);

SET @sql = IF(@column_exists = 0,
    'ALTER TABLE test_plans ADD COLUMN test_plan_name VARCHAR(100) NULL AFTER station_id',
    'SELECT "Column test_plan_name already exists" AS message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 重複以上模式新增其他 12 個欄位
-- item_key, value_type, limit_type, eq_limit, pass_or_fail,
-- measure_value, execute_name, case_type, command, timeout,
-- use_result, wait_msec

-- 為現有資料填充 project_id (從 stations 表取得)
UPDATE test_plans tp
INNER JOIN stations s ON tp.station_id = s.id
SET tp.project_id = s.project_id
WHERE tp.project_id IS NULL OR tp.project_id = 0;

-- 新增外鍵約束
SET @fk_exists = (
    SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS
    WHERE CONSTRAINT_SCHEMA = 'webpdtool'
    AND TABLE_NAME = 'test_plans'
    AND CONSTRAINT_NAME = 'test_plans_ibfk_project'
);

SET @sql = IF(@fk_exists = 0,
    'ALTER TABLE test_plans ADD CONSTRAINT test_plans_ibfk_project
     FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE',
    'SELECT "Foreign key already exists" AS message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 顯示最終結構
SHOW COLUMNS FROM test_plans;
```

**關鍵設計特點**:
- ✅ **冪等性**: 可安全重複執行，會檢查欄位是否已存在
- ✅ **資料完整性**: 自動從 stations 表填充 project_id
- ✅ **外鍵約束**: 確保參考完整性
- ✅ **無損遷移**: 現有資料不受影響

### 步驟 3: 執行遷移

```bash
cd backend

# 方法 1: 使用 Python 執行
uv run python -c "
from sqlalchemy import text
from app.core.database import SessionLocal

with open('scripts/migrate_test_plans_schema.sql', 'r') as f:
    sql = f.read()

db = SessionLocal()
try:
    for stmt in sql.split(';'):
        if stmt.strip():
            db.execute(text(stmt))
            db.commit()
    print('✅ Migration completed!')
finally:
    db.close()
"

# 方法 2: 直接使用 MySQL
mysql -h localhost -P 33306 -u pdtool -p webpdtool < scripts/migrate_test_plans_schema.sql
```

**執行結果**:
```
✓ Statement 1/79 executed successfully
✓ Statement 2/79 executed successfully
...
✓ Statement 79/79 executed successfully
✅ Migration completed!
```

### 步驟 4: 建立驗證腳本

建立 `backend/scripts/verify_migration.py`:

```python
#!/usr/bin/env python3
from sqlalchemy import inspect
from app.core.database import engine
from app.models.testplan import TestPlan

def verify_migration():
    inspector = inspect(engine)

    # 取得實際欄位
    columns = inspector.get_columns('test_plans')
    column_names = {col['name'] for col in columns}

    # 取得 ORM 預期欄位
    expected_columns = {col.name for col in TestPlan.__table__.columns}

    # 檢查缺少的欄位
    missing = expected_columns - column_names
    if missing:
        print(f"✗ 缺少欄位: {missing}")
        return False

    print(f"✓ 所有 {len(expected_columns)} 個欄位都存在")

    # 檢查外鍵
    fks = inspector.get_foreign_keys('test_plans')
    fk_columns = {fk['constrained_columns'][0] for fk in fks}

    if 'project_id' in fk_columns:
        print("✓ project_id foreign key")
    if 'station_id' in fk_columns:
        print("✓ station_id foreign key")

    print("✅ Migration verification PASSED!")
    return True

if __name__ == "__main__":
    verify_migration()
```

**驗證結果**:
```
======================================================================
Test Plans Table Migration Verification
======================================================================

✓ 實際欄位數: 27
✓ 預期欄位數: 27
✓ 所有必要欄位都存在

檢查關鍵欄位:
  ✓ project_id
  ✓ station_id
  ✓ test_plan_name
  ✓ item_key
  ✓ value_type
  ✓ limit_type
  ✓ command
  ✓ timeout
  ✓ wait_msec

檢查外鍵約束:
  ✓ project_id foreign key
  ✓ station_id foreign key

檢查索引:
  ✓ 找到 2 個索引

✅ Migration verification PASSED!
```

### 步驟 5: 更新主 Schema 檔案

更新 `database/schema.sql` 確保未來部署使用正確結構:

```sql
-- Test Plans table (完整結構 - 包含所有 CSV 匯入欄位)
CREATE TABLE test_plans (
    id INT PRIMARY KEY AUTO_INCREMENT,
    -- 專案和工站關聯
    project_id INT NOT NULL,
    station_id INT NOT NULL,
    test_plan_name VARCHAR(100),
    -- 核心測試欄位
    item_no INT NOT NULL,
    item_name VARCHAR(100) NOT NULL,
    test_type VARCHAR(50) NOT NULL,
    parameters JSON,
    lower_limit DECIMAL(15,6),
    upper_limit DECIMAL(15,6),
    unit VARCHAR(20),
    enabled BOOLEAN DEFAULT TRUE,
    sequence_order INT NOT NULL,
    -- CSV 匯入欄位 (對應 PDTool4 格式)
    item_key VARCHAR(50) COMMENT 'ItemKey - 項目鍵值',
    value_type VARCHAR(50) COMMENT 'ValueType - 數值類型',
    limit_type VARCHAR(50) COMMENT 'LimitType - 限制類型',
    eq_limit VARCHAR(100) COMMENT 'EqLimit - 等於限制',
    pass_or_fail VARCHAR(20) COMMENT 'PassOrFail - 通過或失敗',
    measure_value VARCHAR(100) COMMENT 'measureValue - 測量值',
    execute_name VARCHAR(100) COMMENT 'ExecuteName - 執行名稱',
    case_type VARCHAR(50) COMMENT 'case - 案例類型',
    command VARCHAR(500) COMMENT 'Command - 命令',
    timeout INT COMMENT 'Timeout - 超時時間(毫秒)',
    use_result VARCHAR(100) COMMENT 'UseResult - 使用結果',
    wait_msec INT COMMENT 'WaitmSec - 等待毫秒',
    -- 時間戳記
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    -- 外鍵和索引
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (station_id) REFERENCES stations(id) ON DELETE CASCADE,
    INDEX idx_station_sequence (station_id, sequence_order),
    INDEX idx_project_station (project_id, station_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

---

## 測試驗證

### 遷移前測試
```bash
uv run python scripts/test_endpoints.py
```

**結果**:
```
1. Testing get_test_plan_names()...
   ✗ Error: (1054, "Unknown column 'test_plans.test_plan_name' in 'field list'")

2. Testing new_test_plan_map()...
   ✗ Error: (1054, "Unknown column 'test_plans.project_id' in 'field list'")

3. Testing get_test_plans()...
   ✗ Error: (1054, "Unknown column 'test_plans.project_id' in 'field list'")
```

### 遷移後測試
```bash
uv run python scripts/test_endpoints.py
```

**結果**:
```
1. Testing get_test_plan_names()...
   ✓ Success: []

2. Testing new_test_plan_map()...
   ✓ Success: Created map with 0 test points

3. Testing get_test_plans()...
   ✓ Success: Retrieved 0 test plans

✅ All tests PASSED!
```

### API 端點測試

```bash
# 測試計畫名稱列表
curl http://localhost:8765/api/stations/3/testplan-names?project_id=2
# 返回: 200 OK

# 測試計畫映射表
curl http://localhost:8765/api/stations/3/testplan-map?project_id=2&enabled_only=true
# 返回: 200 OK

# 測試計畫項目列表
curl http://localhost:8765/api/stations/3/testplan?project_id=2&enabled_only=true
# 返回: 200 OK
```

---

## 修正結果

### 遷移前後對比

| 項目 | 遷移前 | 遷移後 |
|-----|-------|-------|
| **欄位數量** | 13 | 27 ✅ |
| **project_id** | ❌ 缺少 | ✅ 存在 (NOT NULL, FK) |
| **test_plan_name** | ❌ 缺少 | ✅ 存在 |
| **CSV 匯入欄位** | ❌ 缺少 12 個 | ✅ 全部存在 |
| **外鍵約束** | 僅 station_id | ✅ project_id + station_id |
| **索引** | 1 個 | ✅ 2 個 |
| **API 狀態** | 500 Error | ✅ 200 OK |

### 受影響的端點 (已修復)

| 端點 | 狀態 | 說明 |
|-----|------|------|
| `GET /api/stations/{id}/testplan-names` | ✅ 修復 | 返回測試計畫名稱列表 |
| `GET /api/stations/{id}/testplan-map` | ✅ 修復 | 返回 TestPointMap |
| `GET /api/stations/{id}/testplan` | ✅ 修復 | 返回測試計畫項目 |

---

## 相關檔案

### 新增檔案
```
backend/scripts/
├── migrate_test_plans_schema.sql    # 資料庫遷移腳本
└── verify_migration.py              # 遷移驗證工具

docs/
├── migration_fix_20260209.md        # 完整遷移文件
└── bugfix/
    └── ISSUE7_database_schema_mismatch.md  # 本文件
```

### 修改檔案
```
database/
└── schema.sql                       # 更新 test_plans 表定義
```

### 參考檔案 (未修改)
```
backend/app/
├── models/testplan.py               # ORM 模型定義 (27 欄位)
├── services/test_plan_service.py    # 測試計畫服務
└── api/testplan/
    └── queries.py                   # API 端點實作
```

---

## 學習重點

### 1. Schema 漂移的危險

**問題**: ORM 模型與資料庫結構不同步

**原因**:
- 手動修改 ORM 模型但忘記遷移資料庫
- 沒有使用版本控制追蹤 Schema 變更
- 開發環境與生產環境不一致

**預防**:
```python
# ❌ 錯誤做法: 直接修改 ORM 不遷移
class TestPlan(Base):
    project_id = Column(Integer)  # 新增欄位但資料庫沒有

# ✅ 正確做法: 使用 Alembic
$ alembic revision --autogenerate -m "Add project_id to test_plans"
$ alembic upgrade head
```

### 2. 冪等性遷移腳本

**關鍵技巧**: 檢查欄位是否存在再新增

```sql
-- ✅ 安全: 可重複執行
SET @column_exists = (
    SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'test_plans'
    AND COLUMN_NAME = 'project_id'
);

SET @sql = IF(@column_exists = 0,
    'ALTER TABLE test_plans ADD COLUMN project_id INT NOT NULL',
    'SELECT "Already exists"'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
```

```sql
-- ❌ 危險: 重複執行會失敗
ALTER TABLE test_plans ADD COLUMN project_id INT NOT NULL;
-- Error: Duplicate column name 'project_id'
```

### 3. 資料完整性維護

**問題**: 新增 NOT NULL 欄位到有資料的表

**解決**:
```sql
-- 步驟 1: 新增欄位 (允許 NULL)
ALTER TABLE test_plans ADD COLUMN project_id INT NULL;

-- 步驟 2: 填充現有資料
UPDATE test_plans tp
INNER JOIN stations s ON tp.station_id = s.id
SET tp.project_id = s.project_id;

-- 步驟 3: 改為 NOT NULL
ALTER TABLE test_plans MODIFY COLUMN project_id INT NOT NULL;

-- 步驟 4: 新增外鍵
ALTER TABLE test_plans
ADD CONSTRAINT fk_project
FOREIGN KEY (project_id) REFERENCES projects(id);
```

### 4. 診斷工具的重要性

**策略**: 先診斷再修復

```python
# 1. 建立診斷腳本快速重現問題
def diagnose():
    try:
        result = service.method()
    except Exception as e:
        print(f"Error: {e}")  # 顯示具體錯誤
        traceback.print_exc()  # 顯示完整堆疊

# 2. 建立驗證腳本確認修復
def verify():
    actual = get_actual_schema()
    expected = get_expected_schema()
    assert actual == expected, f"Mismatch: {actual - expected}"
```

---

## PDTool4 相容性說明

此次遷移確保完整的 PDTool4 CSV 匯入相容性:

### Value Type 支援
- `string` - 字串比對
- `integer` - 整數比對 (進位轉換)
- `float` - 浮點數比對

### Limit Type 支援
- `lower` - 僅檢查下限
- `upper` - 僅檢查上限
- `both` - 雙向限制 (lower ≤ value ≤ upper)
- `equality` - 完全相等 (value == expected)
- `inequality` - 不相等 (value != expected)
- `partial` - 部分包含 (substring match)
- `none` - 無限制 (always pass)

### 測試參數欄位
- `command` - 執行命令
- `timeout` - 超時時間 (毫秒)
- `wait_msec` - 等待時間 (毫秒)
- `execute_name` - 執行名稱
- `case_type` - 案例類型

---

## 未來改進建議

### 1. 導入 Alembic 自動遷移

```bash
# 初始化 Alembic
cd backend
alembic init alembic

# 設定 alembic.ini
sqlalchemy.url = mysql+pymysql://pdtool:pdtool123@localhost:33306/webpdtool

# 建立遷移
alembic revision --autogenerate -m "Add missing columns to test_plans"

# 執行遷移
alembic upgrade head

# 回滾遷移
alembic downgrade -1
```

### 2. CI/CD 中加入 Schema 驗證

```yaml
# .github/workflows/test.yml
- name: Verify Database Schema
  run: |
    python scripts/verify_migration.py
    if [ $? -ne 0 ]; then
      echo "Schema mismatch detected!"
      exit 1
    fi
```

### 3. 定期 Schema 審計

```python
# scripts/audit_schema.py
def audit_schema():
    """定期檢查 ORM 與資料庫是否一致"""
    for model in [TestPlan, Station, Project]:
        verify_model_matches_db(model)
```

### 4. 資料庫版本控制

```
database/
├── migrations/
│   ├── v1_initial_schema.sql
│   ├── v2_add_test_plan_fields.sql
│   └── v3_add_project_id.sql
└── schema.sql  # 最新完整結構
```

---

## 總結

### 問題本質
資料庫 Schema 漂移導致 ORM 與實際表結構不一致

### 解決關鍵
1. ✅ 診斷腳本快速定位問題
2. ✅ 冪等性遷移腳本安全執行
3. ✅ 驗證腳本確認修復完整
4. ✅ 更新主 Schema 防止重複發生

### 修復效果
- 🎯 所有 API 端點恢復正常 (500 → 200)
- 🎯 資料庫結構與 ORM 完全一致 (13 → 27 欄位)
- 🎯 PDTool4 CSV 匯入功能完整支援
- 🎯 建立完整的遷移和驗證工具鏈

### 預防措施
- 使用 Alembic 追蹤所有 Schema 變更
- CI/CD 自動驗證 Schema 一致性
- 定期執行 Schema 審計
- 保持資料庫版本控制

---

**狀態**: ✅ 已修復並驗證
**優先級**: 🔴 Critical
**影響範圍**: 測試計畫管理功能
**修復時間**: 2026-02-09
**文件版本**: 1.0
