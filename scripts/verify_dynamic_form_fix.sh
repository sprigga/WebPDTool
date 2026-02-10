#!/bin/bash
# 驗證動態參數表單修復
# 日期: 2026-02-10

set -e

echo "=========================================="
echo "動態參數表單修復驗證腳本"
echo "=========================================="
echo ""

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 測試計數器
PASSED=0
FAILED=0

# 測試函數
test_case() {
    local description=$1
    local expected=$2
    local actual=$3

    if [ "$actual" == "$expected" ]; then
        echo -e "${GREEN}✓${NC} PASS: $description"
        ((PASSED++))
    else
        echo -e "${RED}✗${NC} FAIL: $description"
        echo "   Expected: $expected"
        echo "   Actual: $actual"
        ((FAILED++))
    fi
}

echo "測試 1: 檢查後端 API 是否返回所有測試類型"
echo "----------------------------------------"

# 獲取測試類型列表
TEST_TYPES=$(curl -s http://localhost:9100/api/measurements/templates | \
    python3 -c "import sys, json; data = json.load(sys.stdin); print(','.join(sorted(data['test_types'])))" 2>/dev/null)

EXPECTED_TYPES="CommandTest,OPjudge,Other,PowerRead,PowerSet,Relay,SFCtest,Wait,getSN"

if [ "$TEST_TYPES" == "$EXPECTED_TYPES" ]; then
    echo -e "${GREEN}✓${NC} PASS: 所有 9 種測試類型已返回"
    echo "   測試類型: $TEST_TYPES"
    ((PASSED++))
else
    echo -e "${RED}✗${NC} FAIL: 測試類型不完整"
    echo "   Expected: $EXPECTED_TYPES"
    echo "   Actual: $TEST_TYPES"
    ((FAILED++))
fi

echo ""
echo "測試 2: 檢查單一 Switch Mode 測試類型"
echo "----------------------------------------"

# 測試 SFCtest
SFCTEST_MODES=$(curl -s http://localhost:9100/api/measurements/templates/SFCtest | \
    python3 -c "import sys, json; data = json.load(sys.stdin); print(','.join(data['switch_modes'].keys()))" 2>/dev/null)

test_case "SFCtest 只有 default switch mode" "default" "$SFCTEST_MODES"

# 測試 getSN
GETSN_MODES=$(curl -s http://localhost:9100/api/measurements/templates/getSN | \
    python3 -c "import sys, json; data = json.load(sys.stdin); print(','.join(data['switch_modes'].keys()))" 2>/dev/null)

test_case "getSN 只有 default switch mode" "default" "$GETSN_MODES"

# 測試 OPjudge
OPJUDGE_MODES=$(curl -s http://localhost:9100/api/measurements/templates/OPjudge | \
    python3 -c "import sys, json; data = json.load(sys.stdin); print(','.join(data['switch_modes'].keys()))" 2>/dev/null)

test_case "OPjudge 只有 default switch mode" "default" "$OPJUDGE_MODES"

echo ""
echo "測試 3: 檢查多 Switch Mode 測試類型"
echo "----------------------------------------"

# 測試 PowerSet
POWERSET_MODES=$(curl -s http://localhost:9100/api/measurements/templates/PowerSet | \
    python3 -c "import sys, json; data = json.load(sys.stdin); print(','.join(sorted(data['switch_modes'].keys())))" 2>/dev/null)

EXPECTED_POWERSET="DAQ973A,MODEL2303,MODEL2306"

if [ "$POWERSET_MODES" == "$EXPECTED_POWERSET" ]; then
    echo -e "${GREEN}✓${NC} PASS: PowerSet 有 3 個 switch modes"
    echo "   Switch modes: $POWERSET_MODES"
    ((PASSED++))
else
    echo -e "${RED}✗${NC} FAIL: PowerSet switch modes 不正確"
    echo "   Expected: $EXPECTED_POWERSET"
    echo "   Actual: $POWERSET_MODES"
    ((FAILED++))
fi

echo ""
echo "測試 4: 檢查參數模板完整性"
echo "----------------------------------------"

# 測試 SFCtest 必填參數
SFCTEST_REQUIRED=$(curl -s http://localhost:9100/api/measurements/templates/SFCtest | \
    python3 -c "import sys, json; data = json.load(sys.stdin); print(','.join(data['switch_modes']['default']['required']))" 2>/dev/null)

test_case "SFCtest 必填參數為 Mode" "Mode" "$SFCTEST_REQUIRED"

# 測試 Wait 必填參數
WAIT_REQUIRED=$(curl -s http://localhost:9100/api/measurements/templates/Wait | \
    python3 -c "import sys, json; data = json.load(sys.stdin); print(','.join(data['switch_modes']['default']['required']))" 2>/dev/null)

test_case "Wait 必填參數為 wait_msec" "wait_msec" "$WAIT_REQUIRED"

# 測試 Relay 必填參數
RELAY_REQUIRED=$(curl -s http://localhost:9100/api/measurements/templates/Relay | \
    python3 -c "import sys, json; data = json.load(sys.stdin); print(','.join(sorted(data['switch_modes']['default']['required'])))" 2>/dev/null)

test_case "Relay 必填參數為 Action,RelayName" "Action,RelayName" "$RELAY_REQUIRED"

echo ""
echo "測試 5: 檢查參數範例"
echo "----------------------------------------"

# 測試 SFCtest 範例值
SFCTEST_EXAMPLE=$(curl -s http://localhost:9100/api/measurements/templates/SFCtest | \
    python3 -c "import sys, json; data = json.load(sys.stdin); print(data['switch_modes']['default']['example']['Mode'])" 2>/dev/null)

test_case "SFCtest Mode 範例為 webStep1_2" "webStep1_2" "$SFCTEST_EXAMPLE"

# 測試 OPjudge 範例值
OPJUDGE_EXAMPLE=$(curl -s http://localhost:9100/api/measurements/templates/OPjudge | \
    python3 -c "import sys, json; data = json.load(sys.stdin); print(data['switch_modes']['default']['example']['Type'])" 2>/dev/null)

test_case "OPjudge Type 範例為 YorN" "YorN" "$OPJUDGE_EXAMPLE"

echo ""
echo "=========================================="
echo "測試結果總結"
echo "=========================================="
echo -e "通過: ${GREEN}$PASSED${NC}"
echo -e "失敗: ${RED}$FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}所有測試通過！動態參數表單修復成功。${NC}"
    echo ""
    echo "請在瀏覽器中驗證前端功能："
    echo "1. 訪問 http://localhost:9080/testplan"
    echo "2. 點擊「新增項目」"
    echo "3. 確認「測試類型」下拉選單顯示 9 個選項"
    echo "4. 選擇 SFCtest，確認參數表單自動顯示"
    echo "5. 填寫參數並保存測試項目"
    exit 0
else
    echo -e "${RED}部分測試失敗，請檢查修復是否正確應用。${NC}"
    exit 1
fi
