# 測試計畫資料匯入腳本說明

## 快速開始

```bash
# 1. 複製 CSV 檔案到 testplans 目錄
mkdir -p backend/testplans
cp PDTool4/testPlan/Other/selfTest/*.csv backend/testplans/

# 2. 匯入單個檔案
docker exec webpdtool-backend uv run python scripts/import_testplan.py \
  -f /app/testplans/UseResult_testPlan.csv \
  -p selfTest \
  -s Station1

# 3. 驗證匯入結果
docker exec webpdtool-backend uv run python -c "
from app.core.database import SessionLocal
from app.models.testplan import TestPlan
db = SessionLocal()
print(f'總計: {db.query(TestPlan).count()} 筆測試計畫')
db.close()
"
```

## 功能說明

此腳本用於將 PDTool4 的測試計畫 CSV 檔案匯入到 WebPDTool 資料庫中。

## 檔案位置

- 腳本: `/backend/scripts/import_testplan.py`
- 測試計畫來源: `/PDTool4/testPlan/` 目錄下的 CSV 檔案
- 容器內路徑: `/app/testplans/`

## CSV 檔案格式

CSV 欄位說明（對應資料庫欄位）：

| CSV 欄位 | 資料庫欄位 | 說明 |
|---------|----------|------|
| ID | item_name | 項目名稱/ID |
| ItemKey | item_key | 項目鍵值 |
| ValueType | value_type | 數值類型 |
| LimitType | limit_type | 限制類型 |
| EqLimit | eq_limit | 等於限制值 |
| LL | lower_limit | 下限 |
| UL | upper_limit | 上限 |
| PassOrFail | pass_or_fail | 通過或失敗條件 |
| measureValue | measure_value | 測量值 |
| ExecuteName | execute_name | 執行類型名稱 |
| case | case_type | 案例類型 |
| Command | command | 執行命令 |
| Timeout | timeout | 超時時間(毫秒) |
| UseResult | use_result | 使用前一項目的結果 |
| WaitmSec | wait_msec | 等待毫秒數 |

## 使用方法

### 1. 匯入單個檔案

```bash
# 基本用法（自動解析專案和站點代碼）
docker exec webpdtool-backend uv run python scripts/import_testplan.py -f /app/testplans/UseResult_testPlan.csv

# 指定專案和站點
docker exec webpdtool-backend uv run python scripts/import_testplan.py \
  -f /app/testplans/UseResult_testPlan.csv \
  -p selfTest \
  -s selfTestStation \
  -n "UseResult測試計畫"
```

參數說明：
- `-f, --file`: CSV 檔案路徑（必需）
- `-p, --project`: 專案代碼（可選，預設從檔名或路徑解析）
- `-s, --station`: 站點代碼（可選，預設從檔名解析）
- `-n, --name`: 測試計畫名稱（可選，預設使用檔案名稱）

### 2. 匯入所有檔案

```bash
docker exec webpdtool-backend uv run python scripts/import_testplan.py --all
```

### 3. 在本地環境執行（如果資料庫在本地）

```bash
cd backend
uv run python scripts/import_testplan.py -f ../PDTool4/testPlan/Other/selfTest/UseResult_testPlan.csv
```

## 準備 CSV 檔案

將需要匯入的 CSV 檔案複製到容器可訪問的位置：

```bash
# 建立目錄
mkdir -p backend/testplans

# 複製檔案
cp PDTool4/testPlan/Other/selfTest/*.csv backend/testplans/

# 或複製整個目錄
cp -r PDTool4/testPlan/* backend/testplans/
```

## 匯入範例

```bash
# 範例 1: 匯入 UseResult 測試計畫
docker exec webpdtool-backend uv run python scripts/import_testplan.py \
  -f /app/testplans/UseResult_testPlan.csv \
  -p selfTest \
  -s Station1 \
  -n "UseResult測試"

# 範例 2: 匯入多個檔案
docker exec webpdtool-backend uv run python scripts/import_testplan.py -f /app/testplans/file1.csv
docker exec webpdtool-backend uv run python scripts/import_testplan.py -f /app/testplans/file2.csv
```

## 驗證匯入結果

使用 Python 腳本查詢資料庫：

```bash
docker exec webpdtool-backend uv run python -c "
from app.core.database import SessionLocal
from app.models.testplan import TestPlan
from app.models.project import Project

db = SessionLocal()
plans = db.query(TestPlan).join(Project).filter(Project.project_code == 'selfTest').all()
for plan in plans:
    print(f'{plan.item_name}: {plan.test_type} - {plan.execute_name}')
db.close()
"
```

## 自動處理邏輯

1. **專案管理**：
   - 自動建立不存在的專案
   - 重複匯入時使用現有專案

2. **站點管理**：
   - 自動建立不存在的站點
   - 站點代碼預設從檔名提取（去除 `_testPlan.csv` 後綴）

3. **測試類型判斷**：
   - `CommandTest` → command
   - `SFCtest` → sfc
   - `Other` → other
   - `URL` → url
   - 其他 → general

4. **資料驗證**：
   - 檢查必要欄位（ID 不能為空）
   - 自動處理空值和數值轉換
   - 記錄跳過的資料列

## 注意事項

1. 匯入前確保 Docker 容器正在運行
2. CSV 檔案必須是 UTF-8 編碼
3. 檔名格式建議為 `{Station}_testPlan.csv`
4. 重複匯入同一檔案會新增更多資料（不會覆蓋）
5. 建議在測試環境先驗證再正式匯入

## 錯誤處理

- 檔案不存在：顯示錯誤並跳過
- 編碼錯誤：提示檢查檔案編碼
- 必要欄位缺失：跳過該列並記錄
- 資料庫錯誤：回滾交易並顯示錯誤訊息
