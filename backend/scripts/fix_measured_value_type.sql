-- 修正 test_results.measured_value 欄位類型
-- 日期: 2026-02-10
-- 描述: 將 measured_value 從 DECIMAL(15,6) 改為 VARCHAR(100) 以支援字串類型測量值

-- 問題:
-- 1. 資料庫中 measured_value 是 DECIMAL(15,6)
-- 2. 模型定義是 String(100)
-- 3. 空字串 '' 無法轉換為 DECIMAL，導致錯誤:
--    (1366, "Incorrect decimal value: '' for column 'measured_value' at row 1")

-- 解決方案: 修改欄位類型為 VARCHAR(100)，支援數字和字串兩種類型
ALTER TABLE test_results
MODIFY COLUMN measured_value VARCHAR(100) NULL
COMMENT '測量值 (支援數字和字串類型，例如: "1.5", "Hello World", "PASS")';

-- 驗證
DESCRIBE test_results;
