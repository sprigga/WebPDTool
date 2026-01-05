#!/bin/bash
# 批量匯入測試計畫 CSV 檔案
# 使用方法: ./batch_import.sh [專案代碼]

PROJECT_CODE=${1:-"default"}

echo "開始批量匯入測試計畫..."
echo "專案代碼: $PROJECT_CODE"
echo "=" 60

# 計數器
SUCCESS=0
FAIL=0

# 遍歷所有 CSV 檔案
for file in /app/testplans/*.csv; do
    if [ -f "$file" ]; then
        filename=$(basename "$file" .csv)
        echo ""
        echo "處理: $filename"

        # 執行匯入
        if docker exec webpdtool-backend uv run python scripts/import_testplan.py \
            -f "/app/testplans/$filename.csv" \
            -p "$PROJECT_CODE" \
            -s "${filename%_testPlan}" \
            -n "$filename"; then
            ((SUCCESS++))
            echo "✓ $filename 匯入成功"
        else
            ((FAIL++))
            echo "✗ $filename 匯入失敗"
        fi
    fi
done

echo ""
echo "=" 60
echo "批量匯入完成"
echo "成功: $SUCCESS 個檔案"
echo "失敗: $FAIL 個檔案"
