-- 新增 test_plans 表的欄位
-- 這個腳本會為 test_plans 表新增 12 個新欄位

USE webpdtool;

-- 新增欄位到 test_plans 表
ALTER TABLE test_plans
ADD COLUMN item_key VARCHAR(50) NULL COMMENT 'ItemKey - 項目鍵值' AFTER sequence_order,
ADD COLUMN value_type VARCHAR(50) NULL COMMENT 'ValueType - 數值類型' AFTER item_key,
ADD COLUMN limit_type VARCHAR(50) NULL COMMENT 'LimitType - 限制類型' AFTER value_type,
ADD COLUMN eq_limit VARCHAR(100) NULL COMMENT 'EqLimit - 等於限制' AFTER limit_type,
ADD COLUMN pass_or_fail VARCHAR(20) NULL COMMENT 'PassOrFail - 通過或失敗' AFTER eq_limit,
ADD COLUMN measure_value VARCHAR(100) NULL COMMENT 'measureValue - 測量值' AFTER pass_or_fail,
ADD COLUMN execute_name VARCHAR(100) NULL COMMENT 'ExecuteName - 執行名稱' AFTER measure_value,
ADD COLUMN case_type VARCHAR(50) NULL COMMENT 'case - 案例類型' AFTER execute_name,
ADD COLUMN command VARCHAR(500) NULL COMMENT 'Command - 命令' AFTER case_type,
ADD COLUMN timeout INT NULL COMMENT 'Timeout - 超時時間(毫秒)' AFTER command,
ADD COLUMN use_result VARCHAR(100) NULL COMMENT 'UseResult - 使用結果' AFTER timeout,
ADD COLUMN wait_msec INT NULL COMMENT 'WaitmSec - 等待毫秒' AFTER use_result;

-- 顯示結果
SHOW COLUMNS FROM test_plans;
