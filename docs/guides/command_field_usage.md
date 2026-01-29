# Command 字段使用說明

## 概述

本文檔說明如何在測試計劃管理系統中正確使用 `command` 字段來執行各種類型的命令。

## 修改背景

在修改前,系統只能執行 Python 腳本,且會自動在命令前加上 `python3`,導致無法執行其他類型的命令。

**修改後的優勢:**
- ✅ 支援完整的命令字符串 (例如: `python ./scripts/test.py`)
- ✅ 支援各種命令類型 (python, bash, node, 等)
- ✅ 使用 `shlex.split()` 正確處理帶引號的參數
- ✅ 保持向後相容性 (原有的 `script_path` 參數仍可使用)

## Command 字段支援格式

### 1. 完整命令 (推薦)

在 TestPlanManage.vue 的「命令」欄位中填寫完整的執行命令:

```
python ./scripts/test123.py arg1 arg2
python3 ./scripts/test123.py 123
bash ./scripts/test.sh
node ./app.js
```

**優點:**
- 明確指定執行的命令和參數
- 可以使用任何命令類型
- 靈活度高

### 2. 僅腳本路徑 (向後相容)

如果只填寫腳本路徑,系統會自動使用 `python3` 執行:

```
./scripts/test123.py
scripts/test.py
```

**注意:** 此方式僅適用於 Python 腳本

### 3. 絕對路徑

使用絕對路徑執行命令:

```
python /home/ubuntu/WebPDTool/backend/scripts/test123.py
bash /absolute/path/to/script.sh
```

## 使用範例

### 範例 1: Python 腳本 (帶參數)

**TestPlanManage.vue 設定:**
- 測試項目名稱: `Test Item 1`
- 執行名稱: `Other`
- 命令: `python ./scripts/test123.py 123`

**系統執行:**
```bash
python ./scripts/test123.py 123
```

### 範例 2: Bash 腳本

**TestPlanManage.vue 設定:**
- 測試項目名稱: `Run Shell Script`
- 執行名稱: `Other`
- 命令: `bash ./scripts/check_system.sh`

**系統執行:**
```bash
bash ./scripts/check_system.sh
```

### 範例 3: Node.js 腳本

**TestPlanManage.vue 設定:**
- 測試項目名稱: `Node Test`
- 執行名稱: `Other`
- 命令: `node ./app/test.js`

**系統執行:**
```bash
node ./app/test.js
```

### 範例 4: 帶引號的參數

**TestPlanManage.vue 設定:**
- 測試項目名稱: `Test With Quotes`
- 執行名稱: `Other`
- 命令: `python ./scripts/test.py "hello world" 123`

**系統執行:**
```bash
python ./scripts/test.py "hello world" 123
```

**說明:** 系統使用 `shlex.split()` 正確處理帶引號的參數,將 `"hello world"` 視為單一參數。

## 技術實現

### 後端處理流程 (measurement_service.py)

1. **接收 command 字段**
   ```python
   raw_command = test_params.get('command')
   # 例如: "python ./scripts/test123.py 123"
   ```

2. **使用 shlex.split() 解析命令**
   ```python
   command_parts = shlex.split(raw_command)
   # 結果: ['python', './scripts/test123.py', '123']
   ```

3. **解析相對路徑為絕對路徑**
   ```python
   if not os.path.isabs(executable) and '/' in executable:
       # 將相對路徑轉換為絕對路徑
       executable_abs = os.path.join(backend_dir, executable)
   ```

4. **執行命令**
   ```python
   result = subprocess.run(
       command,
       capture_output=True,
       text=True,
       timeout=timeout_seconds,
       cwd='/home/ubuntu/WebPDTool/backend'
   )
   ```

### 命令優先級

系統按以下優先級處理命令:

1. **優先級 1:** `test_params['command']` (來自資料庫 test_plans.command)
2. **優先級 2:** `test_params['script_path']` (向後相容)
3. **優先級 3:** 預設路徑 (僅限 test123)

## 注意事項

### ⚠️ 安全性

- **不要**執行未經驗證的腳本
- **不要**在 command 中使用敏感資訊 (密碼、API Key)
- 確保腳本檔案權限正確

### ⚠️ 路徑問題

- 相對路徑是相對於 `/home/ubuntu/WebPDTool/backend` 目錄
- 建議使用相對路徑而非絕對路徑,以便於移植
- 確保腳本檔案存在且可執行

### ⚠️ 參數處理

- 使用引號包裹包含空格的參數: `"hello world"`
- 多個參數用空格分隔: `python test.py arg1 arg2`
- 特殊字符需要適當轉義

### ⚠️ 超時設定

- 預設超時時間: 30 秒
- 可在測試計劃�中設定 `timeout` 欄位 (單位: ms)
- 可在測試計劃中設定 `wait_msec` 欄位 (單位: ms) 來延遲執行

## 常見問題

### Q1: 為什麼 "系統狀態" 顯示的執行指令和命令欄位不一樣?

**A:** 這是正常的。「系統狀態」顯示的是後端實際執行的完整命令,包含了路徑解析的結果。例如:
- 輸入: `python ./scripts/test123.py`
- 執行: `python /home/ubuntu/WebPDTool/backend/scripts/test123.py`

### Q2: 如何執行帶空格路徑的腳本?

**A:** 使用引號包裹路徑:
```
python "./scripts/my test.py"
```

### Q3: 如何傳遞多個參數?

**A:** 參數之間用空格分隔:
```
python ./scripts/test.py arg1 arg2 arg3
```

### Q4: 可以執行系統命令嗎?

**A:** 可以,但需謹慎使用:
```
ls -la
cat /proc/cpuinfo
```

### Q5: 如何調試命令執行問題?

**A:**
1. 查看「系統狀態」顯示的實際執行命令
2. 檢查「錯誤訊息」卡片中的詳細錯誤
3. 在手動執行命令測試: `cd /home/ubuntu/WebPDTool/backend && python ./scripts/test123.py`

## 版本歷史

- **v1.1 (2025-01-08):** 支援完整命令字符串解析,可執行各種類型命令
- **v1.0:** 僅支援 Python 腳本,自動添加 `python3` 前綴

## 相關文件

- [測試計劃管理使用手冊](./test_plan_management.md)
- [PDTool4 整合說明](./pdtool4_integration.md)
- [API 文檔](../backend/app/api/README.md)
