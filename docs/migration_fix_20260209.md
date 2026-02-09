# Database Migration Fix - 2026-02-09

## 問題描述

Backend API 返回 500 錯誤，影響以下端點:
- `GET /api/stations/{station_id}/testplan-names`
- `GET /api/stations/{station_id}/testplan-map`
- `GET /api/stations/{station_id}/testplan`

## 錯誤原因

資料庫結構與 ORM 模型不一致：

### 缺少的欄位
1. **project_id** - 專案 ID (必要欄位，有外鍵約束)
2. **test_plan_name** - 測試計畫名稱
3. **12 個 CSV 匯入欄位**:
   - item_key
   - value_type
   - limit_type
   - eq_limit
   - pass_or_fail
   - measure_value
   - execute_name
   - case_type
   - command
   - timeout
   - use_result
   - wait_msec

### 錯誤訊息範例
```
(pymysql.err.OperationalError) (1054, "Unknown column 'test_plans.project_id' in 'field list'")
(pymysql.err.OperationalError) (1054, "Unknown column 'test_plans.test_plan_name' in 'field list'")
```

## 解決方案

### 1. 建立遷移腳本

建立 `backend/scripts/migrate_test_plans_schema.sql`，包含:
- 安全檢查現有欄位（避免重複新增）
- 新增所有缺少的欄位
- 為現有資料填充 project_id（從 stations 表取得）
- 新增外鍵約束

### 2. 執行遷移

```bash
cd backend
uv run python -c "from sqlalchemy import text; from app.core.database import SessionLocal; ..."
```

或直接使用 MySQL:
```bash
mysql -h localhost -P 33306 -u pdtool -p webpdtool < scripts/migrate_test_plans_schema.sql
```

### 3. 驗證遷移

```bash
uv run python scripts/verify_migration.py
```

### 4. 更新 schema.sql

更新 `database/schema.sql` 中的 test_plans 表定義，確保未來部署時使用正確的結構。

## 遷移結果

### 遷移前
- **欄位數**: 13
- **缺少**: project_id, test_plan_name + 12 個 CSV 欄位

### 遷移後
- **欄位數**: 27
- **所有欄位**: ✓ 與 ORM 模型完全一致
- **外鍵約束**: ✓ project_id → projects(id)
- **外鍵約束**: ✓ station_id → stations(id)
- **索引**: 2 個 (idx_station_sequence, idx_project_station)

## 測試驗證

執行測試確認 API 正常運作:

```bash
# 測試端點 (應返回 200 OK)
curl http://localhost:8765/api/stations/3/testplan-names?project_id=2
curl http://localhost:8765/api/stations/3/testplan-map?project_id=2&enabled_only=true
curl http://localhost:8765/api/stations/3/testplan?project_id=2&enabled_only=true
```

## 相關檔案

### 新增檔案
- `backend/scripts/migrate_test_plans_schema.sql` - 遷移腳本
- `backend/scripts/verify_migration.py` - 驗證腳本
- `docs/migration_fix_20260209.md` - 此文件

### 修改檔案
- `database/schema.sql` - 更新 test_plans 表定義

### ORM 模型 (未修改)
- `backend/app/models/testplan.py` - 定義了完整的 27 個欄位

## 注意事項

1. **資料遷移**: 腳本會自動為現有記錄填充 project_id (從 stations.project_id)
2. **外鍵約束**: project_id 設定為 NOT NULL，確保資料完整性
3. **向下相容**: 所有新欄位都允許 NULL（除了 project_id），不會影響現有資料
4. **重複執行安全**: 遷移腳本可以安全地重複執行，會自動檢查欄位是否存在

## PDTool4 相容性

此次遷移確保 WebPDTool 與 PDTool4 CSV 匯入格式完全相容:

- **value_type**: string, integer, float
- **limit_type**: lower, upper, both, equality, inequality, partial, none
- **測試參數**: command, timeout, wait_msec 等執行參數
- **測試結果**: measure_value, pass_or_fail 等結果欄位

## 未來建議

1. 設定 Alembic 自動遷移，避免手動維護 SQL 腳本
2. 在 CI/CD 中加入資料庫結構驗證
3. 定期檢查 ORM 模型與資料庫結構的一致性
