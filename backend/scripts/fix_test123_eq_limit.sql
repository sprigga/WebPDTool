-- 修正 test123 測試項目的 eq_limit 配置
-- 日期: 2026-02-10
-- 描述: 將 123_2 的 eq_limit 從 "123" 改為 "456"，以符合預期的測試邏輯

-- 問題:
-- 123_2 使用 123_1 的測量結果作為參數
-- 123_1 的測量結果是 "123"
-- test123.py 收到參數 "123" 時輸出 "456"
-- 因此 123_2 的預期測量值是 "456"，eq_limit 應該設為 "456" 而非 "123"

-- 查看當前配置
SELECT item_no, item_name, use_result, eq_limit, limit_type
FROM test_plans
WHERE item_name IN ('123_1', '123_2')
ORDER BY item_no;

-- 修正 123_2 的 eq_limit
UPDATE test_plans
SET eq_limit = '456'
WHERE item_name = '123_2';

-- 驗證修正結果
SELECT item_no, item_name, use_result, eq_limit, limit_type
FROM test_plans
WHERE item_name IN ('123_1', '123_2')
ORDER BY item_no;

-- 預期結果:
-- item_no=2, item_name='123_1', use_result=NULL,    eq_limit='123', limit_type='partial'
-- item_no=4, item_name='123_2', use_result='123_1', eq_limit='456', limit_type='partial'
