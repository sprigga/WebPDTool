-- 資料遷移腳本: 合併 case_type 到 switch_mode
-- 方案 A 實施: 統一使用 switch_mode 欄位
-- 日期: 2026-02-10
--
-- 說明:
-- 1. 將 case_type 的值複製到 switch_mode (如果 switch_mode 為空)
-- 2. 保留 case_type 欄位以支援 CSV 匯入向後相容
-- 3. 不刪除任何資料,確保安全

-- 備份說明
-- 建議在執行前先備份資料庫:
-- mysqldump -u pdtool -p webpdtool test_plans > test_plans_backup_$(date +%Y%m%d_%H%M%S).sql

-- 開始交易
START TRANSACTION;

-- 顯示遷移前的統計資訊
SELECT
    COUNT(*) as total_records,
    SUM(CASE WHEN switch_mode IS NULL OR switch_mode = '' THEN 1 ELSE 0 END) as empty_switch_mode,
    SUM(CASE WHEN case_type IS NOT NULL AND case_type != '' THEN 1 ELSE 0 END) as has_case_type,
    SUM(CASE WHEN (switch_mode IS NULL OR switch_mode = '') AND (case_type IS NOT NULL AND case_type != '') THEN 1 ELSE 0 END) as will_migrate
FROM test_plans;

-- 執行遷移: 將 case_type 複製到 switch_mode
-- 僅當 switch_mode 為空且 case_type 有值時執行
UPDATE test_plans
SET switch_mode = case_type
WHERE (switch_mode IS NULL OR switch_mode = '')
  AND case_type IS NOT NULL
  AND case_type != '';

-- 顯示遷移後的統計資訊
SELECT
    COUNT(*) as total_records,
    SUM(CASE WHEN switch_mode IS NULL OR switch_mode = '' THEN 1 ELSE 0 END) as empty_switch_mode_after,
    SUM(CASE WHEN case_type IS NOT NULL AND case_type != '' THEN 1 ELSE 0 END) as has_case_type,
    COUNT(DISTINCT switch_mode) as unique_switch_modes
FROM test_plans;

-- 顯示所有 switch_mode 的分布情況
SELECT
    switch_mode,
    COUNT(*) as count
FROM test_plans
WHERE switch_mode IS NOT NULL AND switch_mode != ''
GROUP BY switch_mode
ORDER BY count DESC
LIMIT 20;

-- 提交交易
-- 如果檢查結果正確,請取消下面的註解來提交
COMMIT;

-- 如果需要回滾,執行:
-- ROLLBACK;

-- 驗證遷移結果
-- 檢查是否有遺漏的資料
SELECT
    id,
    item_name,
    test_type,
    switch_mode,
    case_type
FROM test_plans
WHERE (switch_mode IS NULL OR switch_mode = '')
  AND (case_type IS NOT NULL AND case_type != '')
LIMIT 10;
