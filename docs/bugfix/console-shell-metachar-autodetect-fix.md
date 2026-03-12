# Console Command Shell 特殊字元自動偵測修正

**日期：** 2026-03-12
**影響範圍：** `backend/app/services/instruments/console_command.py`
**嚴重性：** Medium — 功能性錯誤，影響所有含 shell 特殊字元的 console 指令

---

## 問題描述

在 TestPlanManage.vue 編輯測試項目時，設定：
- 測試類型：`console`
- 儀器模式：`console`
- Command：`echo $((1+1))`
- 限制類型：`partial`
- 等於限制：`2`

執行測試後，預期輸出應為 `2`，但實際出現錯誤訊息：

```
Partial failed: '2' not in '$((1+1))'
```

---

## 根本原因

### 1. `ConSoleCommandDriver` 預設 `shell=False`

```python
# console_command.py
self.use_shell = False  # shell=False for security by default
```

當 `shell=False` 時，driver 使用 `create_subprocess_exec`，直接將命令字串傳遞給 OS，不透過 `/bin/sh -c`。

### 2. Bash 算術展開需要 shell 環境

`$((1+1))` 是 Bash arithmetic expansion，只有在 shell 環境下才會被展開為 `2`。
在 exec 模式下，`echo` 收到的參數是字面字串 `$((1+1))`，因此輸出也是 `$((1+1))`。

### 3. `Shell` 參數 UI 顯示為 placeholder，用戶未填入

在 DynamicParamForm 中，`Shell` 參數顯示為選填，範例值為 `False`（灰色佔位文字），
用戶若不填入，`shell` 參數為 `None`，最終 `use_shell = False`。

### 資料流追蹤

```
用戶設定 Command = "echo $((1+1))"，Shell 欄位留空
  → params['Shell'] = None
  → console_command.py: use_shell = self.use_shell if shell is None else shell
  → use_shell = False (預設值)
  → create_subprocess_exec('echo', '$((1+1))')
  → 輸出: "$((1+1))"  (字面字串，未展開)
  → partial check: '2' in '$((1+1))' → False
  → 錯誤: "Partial failed: '2' not in '$((1+1))'"
```

---

## 解決方案

在 `_execute_command()` 中，當 `shell` 參數未明確設定（`None`）時，
自動偵測命令字串是否包含 shell 特殊字元，若有則自動啟用 `shell=True`。

### 新增正則表達式（檔案頂端）

```python
# Shell metacharacters that require shell=True to work correctly
_SHELL_METACHAR_RE = re.compile(
    r'\$\(\(|'     # arithmetic expansion: $((
    r'\$\(|'       # command substitution: $(
    r'\$\{|'       # variable expansion: ${
    r'[|&;<>]|'    # pipes, redirects, semicolons
    r'[\*\?\[\]]|' # glob wildcards
    r'~/'          # tilde expansion
)
```

### 修改 `_execute_command()` 方法

```python
# 原有程式碼
use_shell = self.use_shell if shell is None else shell

# 修改: 自動偵測 shell 特殊字元
use_shell = self.use_shell if shell is None else shell

if shell is None and isinstance(command, str) and _SHELL_METACHAR_RE.search(command):
    use_shell = True
    self.logger.info(f"Auto-detected shell metacharacters in command, enabling shell mode")
```

---

## 設計考量

| 情境 | 行為 |
|------|------|
| 用戶未設定 `Shell`，命令無特殊字元 | `shell=False`（安全預設） |
| 用戶未設定 `Shell`，命令含 `$((...))`、`\|` 等 | **自動** `shell=True` |
| 用戶明確設定 `Shell=True` | `shell=True`（尊重用戶設定） |
| 用戶明確設定 `Shell=False` | `shell=False`（尊重用戶設定，即使含特殊字元） |

自動偵測僅在 `shell is None` 時觸發，不覆蓋用戶的明確設定。

---

## 覆蓋的 Shell 特殊字元範例

| 命令 | 需要 shell | 偵測結果 |
|------|-----------|---------|
| `echo $((1+1))` | ✅ | 自動啟用 |
| `echo $(date)` | ✅ | 自動啟用 |
| `echo ${HOME}` | ✅ | 自動啟用 |
| `ls \| grep foo` | ✅ | 自動啟用 |
| `cat > file.txt` | ✅ | 自動啟用 |
| `ls *.txt` | ✅ | 自動啟用 |
| `echo hello` | ❌ | 維持 exec 模式 |
| `python3 script.py arg1` | ❌ | 維持 exec 模式 |

---

## 修改的檔案

- `backend/app/services/instruments/console_command.py`
  - 新增 `import re`
  - 新增模組層級 `_SHELL_METACHAR_RE` 正則表達式
  - 在 `_execute_command()` 中新增自動偵測邏輯

---

## 除錯過程

1. **看錯誤訊息** `Partial failed: '2' not in '$((1+1))'`
   → 表示 `measured_value` 是 `$((1+1))` 而非 `2`，命令輸出未展開

2. **追蹤 `partial` 驗證邏輯** → `base.py:299`
   → `str(self.eq_limit) in str(measured_value)` → `'2' in '$((1+1))'` → False

3. **確認 console_command.py 的執行模式**
   → `use_shell = False` → `create_subprocess_exec` → shell 展開不發生

4. **確認 Shell 參數傳遞路徑**
   → UI 中 `Shell` 為選填欄位，留空 → `get_param()` 返回 `None` → `use_shell = False`

5. **確認解法可行性**
   → `$((1+1))` 必須透過 shell 執行；自動偵測是最佳 UX（用戶不需了解底層差異）

6. **驗證正則表達式**
   ```bash
   python3 -c "import re; ..."  # 測試所有案例全部通過
   ```
