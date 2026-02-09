-- 完整的 test_plans 表結構遷移腳本
-- 此腳本將 test_plans 表從舊結構遷移到新結構
-- 新增 project_id, test_plan_name 以及所有 CSV 匯入欄位

USE webpdtool;

-- 檢查並新增 project_id 欄位
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

-- 檢查並新增 test_plan_name 欄位
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

-- 檢查並新增 item_key 欄位
SET @column_exists = (
    SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = 'webpdtool'
    AND TABLE_NAME = 'test_plans'
    AND COLUMN_NAME = 'item_key'
);

SET @sql = IF(@column_exists = 0,
    'ALTER TABLE test_plans ADD COLUMN item_key VARCHAR(50) NULL COMMENT "ItemKey - 項目鍵值" AFTER sequence_order',
    'SELECT "Column item_key already exists" AS message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 檢查並新增 value_type 欄位
SET @column_exists = (
    SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = 'webpdtool'
    AND TABLE_NAME = 'test_plans'
    AND COLUMN_NAME = 'value_type'
);

SET @sql = IF(@column_exists = 0,
    'ALTER TABLE test_plans ADD COLUMN value_type VARCHAR(50) NULL COMMENT "ValueType - 數值類型" AFTER item_key',
    'SELECT "Column value_type already exists" AS message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 檢查並新增 limit_type 欄位
SET @column_exists = (
    SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = 'webpdtool'
    AND TABLE_NAME = 'test_plans'
    AND COLUMN_NAME = 'limit_type'
);

SET @sql = IF(@column_exists = 0,
    'ALTER TABLE test_plans ADD COLUMN limit_type VARCHAR(50) NULL COMMENT "LimitType - 限制類型" AFTER value_type',
    'SELECT "Column limit_type already exists" AS message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 檢查並新增 eq_limit 欄位
SET @column_exists = (
    SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = 'webpdtool'
    AND TABLE_NAME = 'test_plans'
    AND COLUMN_NAME = 'eq_limit'
);

SET @sql = IF(@column_exists = 0,
    'ALTER TABLE test_plans ADD COLUMN eq_limit VARCHAR(100) NULL COMMENT "EqLimit - 等於限制" AFTER limit_type',
    'SELECT "Column eq_limit already exists" AS message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 檢查並新增 pass_or_fail 欄位
SET @column_exists = (
    SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = 'webpdtool'
    AND TABLE_NAME = 'test_plans'
    AND COLUMN_NAME = 'pass_or_fail'
);

SET @sql = IF(@column_exists = 0,
    'ALTER TABLE test_plans ADD COLUMN pass_or_fail VARCHAR(20) NULL COMMENT "PassOrFail - 通過或失敗" AFTER eq_limit',
    'SELECT "Column pass_or_fail already exists" AS message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 檢查並新增 measure_value 欄位
SET @column_exists = (
    SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = 'webpdtool'
    AND TABLE_NAME = 'test_plans'
    AND COLUMN_NAME = 'measure_value'
);

SET @sql = IF(@column_exists = 0,
    'ALTER TABLE test_plans ADD COLUMN measure_value VARCHAR(100) NULL COMMENT "measureValue - 測量值" AFTER pass_or_fail',
    'SELECT "Column measure_value already exists" AS message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 檢查並新增 execute_name 欄位
SET @column_exists = (
    SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = 'webpdtool'
    AND TABLE_NAME = 'test_plans'
    AND COLUMN_NAME = 'execute_name'
);

SET @sql = IF(@column_exists = 0,
    'ALTER TABLE test_plans ADD COLUMN execute_name VARCHAR(100) NULL COMMENT "ExecuteName - 執行名稱" AFTER measure_value',
    'SELECT "Column execute_name already exists" AS message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 檢查並新增 case_type 欄位
SET @column_exists = (
    SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = 'webpdtool'
    AND TABLE_NAME = 'test_plans'
    AND COLUMN_NAME = 'case_type'
);

SET @sql = IF(@column_exists = 0,
    'ALTER TABLE test_plans ADD COLUMN case_type VARCHAR(50) NULL COMMENT "case - 案例類型" AFTER execute_name',
    'SELECT "Column case_type already exists" AS message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 檢查並新增 command 欄位
SET @column_exists = (
    SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = 'webpdtool'
    AND TABLE_NAME = 'test_plans'
    AND COLUMN_NAME = 'command'
);

SET @sql = IF(@column_exists = 0,
    'ALTER TABLE test_plans ADD COLUMN command VARCHAR(500) NULL COMMENT "Command - 命令" AFTER case_type',
    'SELECT "Column command already exists" AS message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 檢查並新增 timeout 欄位
SET @column_exists = (
    SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = 'webpdtool'
    AND TABLE_NAME = 'test_plans'
    AND COLUMN_NAME = 'timeout'
);

SET @sql = IF(@column_exists = 0,
    'ALTER TABLE test_plans ADD COLUMN timeout INT NULL COMMENT "Timeout - 超時時間(毫秒)" AFTER command',
    'SELECT "Column timeout already exists" AS message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 檢查並新增 use_result 欄位
SET @column_exists = (
    SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = 'webpdtool'
    AND TABLE_NAME = 'test_plans'
    AND COLUMN_NAME = 'use_result'
);

SET @sql = IF(@column_exists = 0,
    'ALTER TABLE test_plans ADD COLUMN use_result VARCHAR(100) NULL COMMENT "UseResult - 使用結果" AFTER timeout',
    'SELECT "Column use_result already exists" AS message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 檢查並新增 wait_msec 欄位
SET @column_exists = (
    SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = 'webpdtool'
    AND TABLE_NAME = 'test_plans'
    AND COLUMN_NAME = 'wait_msec'
);

SET @sql = IF(@column_exists = 0,
    'ALTER TABLE test_plans ADD COLUMN wait_msec INT NULL COMMENT "WaitmSec - 等待毫秒" AFTER use_result',
    'SELECT "Column wait_msec already exists" AS message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 為現有資料填充 project_id (從 stations 表取得)
UPDATE test_plans tp
INNER JOIN stations s ON tp.station_id = s.id
SET tp.project_id = s.project_id
WHERE tp.project_id IS NULL OR tp.project_id = 0;

-- 新增外鍵約束 (如果尚未存在)
SET @fk_exists = (
    SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS
    WHERE CONSTRAINT_SCHEMA = 'webpdtool'
    AND TABLE_NAME = 'test_plans'
    AND CONSTRAINT_NAME = 'test_plans_ibfk_project'
);

SET @sql = IF(@fk_exists = 0,
    'ALTER TABLE test_plans ADD CONSTRAINT test_plans_ibfk_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE',
    'SELECT "Foreign key test_plans_ibfk_project already exists" AS message'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 顯示最終結構
SHOW COLUMNS FROM test_plans;

-- 顯示遷移統計
SELECT
    'Migration Complete' AS status,
    COUNT(*) AS total_records,
    COUNT(DISTINCT project_id) AS projects,
    COUNT(DISTINCT station_id) AS stations,
    COUNT(DISTINCT test_plan_name) AS test_plans
FROM test_plans;
