-- 添加 switch_mode 欄位到 test_plans 表
-- 日期: 2026-02-10
-- 描述: 修正資料庫 schema 與模型不同步的問題

-- 添加 switch_mode 欄位 (儀器模式/腳本名稱)
ALTER TABLE test_plans
ADD COLUMN IF NOT EXISTS switch_mode VARCHAR(50) NULL AFTER test_type
COMMENT '儀器模式或腳本名稱 (DAQ973A, MODEL2303, test123, wait, relay, etc.)';

-- 遷移舊資料: 將 case_type 的值複製到 switch_mode (向後相容)
UPDATE test_plans
SET switch_mode = case_type
WHERE switch_mode IS NULL AND case_type IS NOT NULL AND case_type != '';

-- 驗證
SELECT COUNT(*) as total_items,
       COUNT(switch_mode) as with_switch_mode,
       COUNT(case_type) as with_case_type
FROM test_plans;
