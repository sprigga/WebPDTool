
import sys

# 原始檔案: PDTool4/src/lowsheen_lib/testUTF/123.py
# 複製到: backend/scripts/test123.py
# 用途: 測試腳本，根據參數輸出不同結果

if len(sys.argv) > 1:
    if sys.argv[1] == '123':
        print('456')
else:
    print('123')

# print(sys.argv)
# print('123')
# UseResult = sys.argv[2]
