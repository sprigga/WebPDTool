# 修正 script 模式執行邏輯

## 問題描述

在測試執行時，當「儀器模式」（switch_mode）選擇為 `"script"` 時，系統嘗試執行 `scripts/script.py`，導致以下錯誤：

```
Script not found: /home/ubuntu/python_code/WebPDTool/backend/./scripts/script.py
(scripts_dir: /home/ubuntu/python_code/WebPDTool/backend/./scripts)
```

## 根本原因

原有的 `OtherMeasurement` 實作邏輯：
1. 從 `switch_mode` 讀取腳本名稱（例如 "script"）
2. 直接構建腳本路徑為 `scripts/{switch_mode}.py`
3. 嘗試執行該腳本

但當 `switch_mode="script"` 時，這是一個**通用腳本執行模式**的標識，而不是實際的腳本名稱。實際要執行的腳本路徑或命令應該從 `command` 欄位讀取。

## 解決方案

修改 `backend/app/measurements/implementations.py` 中的 `OtherMeasurement.execute()` 方法：

### 新增邏輯判斷

```python
# 當 switch_mode 為 "script" 時，從 command 欄位讀取腳本路徑或命令
if switch_mode.lower() == "script":
    # 從 command 欄位讀取
    command = self.test_plan_item.get("command", "").strip()
    if not command:
        return self.create_result(
            result="ERROR",
            error_message="switch_mode='script' requires 'command' field to specify script path or command"
        )

    # 使用 shell 模式執行 command 欄位中的內容
    process = await asyncio.create_subprocess_shell(
        full_command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=...
    )
else:
    # 原有邏輯: 從 switch_mode 構建腳本路徑
    script_path = os.path.join(scripts_dir, f"{switch_mode}.py")
    process = await asyncio.create_subprocess_exec(
        ["python3", script_path] + args,
        ...
    )
```

## 執行模式說明

### 模式 1: 通用腳本模式（switch_mode = "script"）

- **用途**: 執行「命令」欄位中指定的腳本或命令
- **配置**:
  - 儀器模式（switch_mode）: `"script"`
  - 命令（command）: 腳本路徑或完整命令，例如：
    - `python3 /path/to/custom_script.py`
    - `./scripts/test_script.sh`
    - `echo "Hello World"`
- **執行方式**: 使用 shell 模式執行 `command` 欄位內容

### 模式 2: 預定義腳本模式（switch_mode = 具體名稱）

- **用途**: 執行 `scripts/` 目錄下預定義的腳本
- **配置**:
  - 儀器模式（switch_mode）: 腳本名稱，例如 `"test123"`, `"123_1"`, `"WAIT_FIX_5sec"`
  - 命令（command）: 可選，不使用
- **執行方式**: 執行 `scripts/{switch_mode}.py`

## 測試驗證

### 測試案例 1: 通用腳本模式

**測試計劃配置**:
```json
{
  "item_name": "123_1",
  "test_type": "Other",
  "switch_mode": "script",
  "command": "python3 /home/ubuntu/python_code/WebPDTool/backend/scripts/test123.py"
}
```

**預期結果**: 執行 `test123.py` 並返回測量結果

### 測試案例 2: 預定義腳本模式

**測試計劃配置**:
```json
{
  "item_name": "test_hello",
  "test_type": "Other",
  "switch_mode": "hello_world",
  "command": ""
}
```

**預期結果**: 執行 `scripts/hello_world.py` 並返回測量結果

## 相關檔案

- `backend/app/measurements/implementations.py` - OtherMeasurement 類別
- `backend/app/config.py` - SCRIPTS_DIR 配置
- `backend/scripts/` - 預定義腳本目錄

## 注意事項

1. **安全性**: 使用 `asyncio.create_subprocess_shell` 執行 `command` 欄位時，需要注意命令注入風險。建議在生產環境中限制可執行的命令範圍。

2. **路徑解析**:
   - 通用腳本模式下，`command` 欄位可以使用相對路徑或絕對路徑
   - 相對路徑的工作目錄為 `backend/app/`

3. **參數傳遞**:
   - 兩種模式都支援 `use_result` 參數（依賴注入）
   - 兩種模式都支援 `timeout` 和 `wait_msec` 參數

## 修正時間

2026-02-10
