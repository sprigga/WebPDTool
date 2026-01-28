#!/usr/bin/env python3
import sys

# 測試腳本 123.py
# 用途：根據參數輸出不同結果

def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == '123':
            print('456')
        else:
            print(f'Received argument: {sys.argv[1]}')
    else:
        print('123')
    
    # 調試信息
    # print(f"Arguments: {sys.argv}", file=sys.stderr)

if __name__ == "__main__":
    main()
