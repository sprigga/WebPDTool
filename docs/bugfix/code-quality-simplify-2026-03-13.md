# 程式碼品質精簡修正 — 2026-03-13

## 背景

使用 `/simplify` 指令對最近修改的儀器驅動程式和前端檔案進行全面程式碼審查。
三個並行代理（程式碼重用、程式碼品質、效率）各自獨立分析，最終合併結果修正。

**審查範圍：**
- `backend/app/services/instruments/comport_command.py`
- `backend/app/services/instruments/console_command.py`
- `backend/app/services/instrument_connection.py`
- `backend/app/core/instrument_config.py`
- `frontend/src/stores/instruments.js`

---

## 問題 1：`asyncio.get_event_loop()` 已棄用

### 嚴重程度：Critical

### 症狀

在 Python 3.10+ 環境下執行時出現 `DeprecationWarning`；在 Python 3.12 中若從已有執行中的事件迴圈的協程呼叫，會直接拋出 `RuntimeError`。

```
DeprecationWarning: There is no current event loop
RuntimeError: no running event loop
```

### 根本原因

`asyncio.get_event_loop()` 在 Python 3.10 起被標記為棄用。當從 `asyncio.run()` 啟動的協程（如 FastAPI/uvicorn 的請求處理器）內部呼叫時，它不再保證回傳當前正在執行的迴圈，行為因 Python 版本而異。

**影響位置（共 18 處）：**
- `instrument_connection.py`：9 處（`VISAInstrumentConnection` 和 `SerialInstrumentConnection` 的 connect/disconnect/write/query/read 方法）
- `comport_command.py`：9 處（initialize, _write_command, _read_response, close 方法）

### 如何偵測

```bash
grep -rn "asyncio.get_event_loop()" backend/app/services/
```

### 修正方法

將所有 `asyncio.get_event_loop()` 替換為 `asyncio.get_running_loop()`。

`get_running_loop()` 的優點：
1. 在協程內部使用時速度更快（無策略查詢開銷）
2. 若在非協程環境呼叫，立即拋出 `RuntimeError`，讓 bug 一目了然
3. 是 Python 官方推薦的異步替代方案

```bash
# 使用 sed 批次替換（已執行）
sed -i 's/asyncio\.get_event_loop()/asyncio.get_running_loop()/g' \
    backend/app/services/instrument_connection.py \
    backend/app/services/instruments/comport_command.py
```

**修正前：**
```python
loop = asyncio.get_event_loop()
await loop.run_in_executor(None, self._resource.write, command)
```

**修正後：**
```python
loop = asyncio.get_running_loop()
await loop.run_in_executor(None, self._resource.write, command)
```

---

## 問題 2：無效的 Python 型別標注 `str or List[str]`

### 嚴重程度：Critical

### 症狀

IDE 型別檢查器（mypy、Pyright）回報錯誤；函式簽章對呼叫者顯示誤導性的提示。

### 根本原因

`str or List[str]` 是一個布林運算式，**不是**型別標注。Python 在執行期把它解析為：
```python
bool(str) or List[str]  →  True or List[str]  →  str  # 因為 str 是 truthy
```
結果是 `List[str]` 的分支被靜默丟棄，型別標注等同於只寫了 `str`。

**位置：** `console_command.py:75`（`_execute_command` 函式簽章）

### 核心問題：語法誤解

開發者意圖表達「`command` 參數可以是 `str` **或** `List[str]`」，但 Python 的語法解析規則並非如此。

**Python 執行期實際解析過程：**
```python
str or List[str]
↓
bool(str) or List[str]     # Python 評估布林運算式
↓
True or List[str]          # str 是 truthy（非空類型）
↓
str                        # 短路求值，直接返回 str
```

由於 `str` 在布林運算中為 `True`，Python 的短路求值（short-circuit evaluation）會直接返回 `str`，**完全忽略** `List[str]` 部分。

### 造成的具體問題

1. **型別檢查器報錯**
   ```bash
   # mypy 會回報：
   error: invalid type comment or annotation
   ```

2. **誤導開發者**：函式簽章看起來支援 `str` 和 `List[str]` 兩種輸入，但實際上型別檢查工具只認為是 `str`。若呼叫者傳入 `List[str]`，型別檢查器會錯誤地標記為類型不符。

3. **IDE 自動補全失效**：錯誤的標注導致 IDE 提供錯誤的警告紅線、不正確的自動補全建議，以及重構工具誤判。

### 如何偵測

```bash
python3 -c "import ast; ast.parse(open('backend/app/services/instruments/console_command.py').read()); print('OK')"
# 語法層面不會報錯，但 mypy 會：
# error: invalid type comment or annotation
```

### 修正方法

1. 在 `typing` 導入中加入 `Union`
2. 將標注改為 `Union[str, List[str]]`

**修正前：**
```python
from typing import Dict, Any, Optional, List

async def _execute_command(self, command: str or List[str], ...):
```

**修正後：**
```python
from typing import Dict, Any, Optional, List, Union

async def _execute_command(self, command: Union[str, List[str]], ...):
```

**Python 3.10+ 替代寫法：**
```python
async def _execute_command(self, command: str | list[str], ...):
```

### 正確寫法比較

| 寫法 | 本質 | 結果 |
|------|------|------|
| `str or List[str]` | 布林運算式 | ❌ 執行期返回 `str`，型別檢查器報錯 |
| `Union[str, List[str]]` | 型別標注 | ✅ 正確表達聯合類型 |
| `str \| list[str]` (Python 3.10+) | 型別標注 | ✅ 新語法，更簡潔 |

---

## 問題 3：函式內部的 `import os` / `import sys`

### 嚴重程度：Important

### 症狀

每次呼叫 `_execute_command()` 和 `execute_script()` 時都執行 `import os` / `import sys`。雖然 Python 會快取模組（`sys.modules` 查詢），但仍有不必要的開銷，且不符合 PEP 8 和本專案的程式碼風格。

**位置：**
- `console_command.py:123`：`_execute_command` 內部的 `import os`
- `console_command.py:291`：`execute_script` 內部的 `import sys`

### 修正方法

將兩個 import 移至模組頂層：

**修正前：**
```python
# 模組頂部沒有 import os / import sys

async def _execute_command(self, ...):
    import os  # 每次呼叫都執行
    proc_env = os.environ.copy()

async def execute_script(self, ...):
    import sys  # 每次呼叫都執行
    command = [sys.executable, script_path]
```

**修正後：**
```python
import os   # 模組頂層
import sys  # 模組頂層

async def _execute_command(self, ...):
    proc_env = os.environ.copy()  # 直接使用

async def execute_script(self, ...):
    command = [sys.executable, script_path]  # 直接使用
```

---

## 問題 4：`__del__` 中的裸 `except: pass`

### 嚴重程度：Important

### 症狀

`comport_command.py` 的 `__del__` 析構函式使用裸 `except`，會靜默捕捉所有例外，包含：
- `SystemExit`
- `KeyboardInterrupt`
- 硬體 I/O 錯誤

這使得序列埠關閉失敗時完全不可見，難以除錯資源洩漏問題。

**位置：** `comport_command.py:301`

### 如何偵測

```bash
grep -n "except:" backend/app/services/instruments/comport_command.py
# 輸出：301:            except:
```

### 修正方法

改為 `except Exception: pass`，保留對 `SystemExit` 和 `KeyboardInterrupt` 的傳播。

**修正前：**
```python
def __del__(self):
    if self.serial_port and self.serial_port.is_open:
        try:
            self.serial_port.close()
        except:
            pass
```

**修正後：**
```python
def __del__(self):
    if self.serial_port and self.serial_port.is_open:
        try:
            self.serial_port.close()
        except Exception:
            pass
```

---

## 問題 5：`_refresh_cache` 在鎖內執行資料庫查詢

### 嚴重程度：Important

### 症狀

`instrument_config.py` 的 `_refresh_cache` 在持有 `threading.Lock` 的狀態下執行同步資料庫查詢。若查詢耗時 50–200 ms（網路資料庫、冷啟動），所有需要儀器設定的執行緒都會被阻塞整個查詢期間。

### 根本原因

原本的雙重檢查鎖定（double-checked locking）模式正確，但 DB fetch 被錯誤地放在鎖的保護範圍內：

```python
def _refresh_cache(self):
    with self._lock:  # ← 鎖住
        if cache_valid:
            return dict(self._cache)
        rows = self._repo.list_enabled()  # ← DB 查詢在鎖內！耗時操作
        self._cache = result
```

### 為什麼這是錯誤的？

**`with self._lock:` 的保護範圍**涵蓋了從進入 `with` 區塊到離開區塊之間的**所有操作**，包含：

| 操作 | 說明 | 是否需要在鎖內 |
|------|------|----------------|
| 快取有效性檢查 | 檢查 `cache_valid` | ✅ 是（快速，微秒級） |
| **資料庫查詢** | `self._repo.list_enabled()` | ❌ **否**（慢速，50–200 ms） |
| 寫入快取 | `self._cache = result` | ✅ 是（快速，微秒級） |

原先做法將**整個函式邏輯**包在單一 `with self._lock:` 區塊內，導致耗時的 DB 查詢也被鎖保護。

### 造成的影響

當 DB 查詢在鎖內時，多執行緒環境下會發生以下情況：

```
時間軸：
T0: Thread A 取得鎖，開始執行 DB 查詢（耗時 100ms）
T1: Thread B 嘗試取得鎖 → 被阻塞
T2: Thread C 嘗試取得鎖 → 被阻塞
...
T100: Thread A 完成 DB 查詢，寫入快取，釋放鎖
T101: Thread B 取得鎖，但快取已有效，直接返回
```

**結果：** 所有需要儀器設定的執行緒都被阻塞整個 DB 查詢期間（50–200 ms），即使快取已經是有效的。

### 修正方法

將 DB 查詢移至鎖外，只在寫入快取時重新取得鎖：

**修正後：**
```python
def _refresh_cache(self):
    # 第一次檢查（快速路徑，在鎖內）
    with self._lock:
        if cache_valid:
            return dict(self._cache)
    # DB 查詢在鎖外，不阻塞其他執行緒
    rows = self._repo.list_enabled()
    result = {row.instrument_id: self._row_to_config(row) for row in rows}
    # 重新取得鎖寫入快取（兩個執行緒競爭時，後寫者獲勝，無害）
    with self._lock:
        self._cache = result
        self._cache_time = _time.monotonic()
        return dict(result)
```

**取捨說明：** 兩個執行緒可能同時執行 DB 查詢（因為 fetch 在鎖外），但這是無害的競爭（最後一個寫入者獲勝，結果相同）。相對於持鎖期間阻塞所有執行緒，這是更好的選擇。

---

## 問題 6：Pinia Store 中的死碼（Dead Code）

### 嚴重程度：Important

### 症狀

`instruments.js` store 暴露了三個 mutation 方法（`addInstrument`, `modifyInstrument`, `removeInstrument`），但 `InstrumentManage.vue` 完全繞過這些方法，直接呼叫 API 層。Store 的 mutation 方法從未被任何元件使用。

### 什麼是 Mutation 方法？

在 Pinia（Vue 3 的狀態管理庫）中，**mutation** 是一種專門用來**同步修改 store 狀態**的方法。這類似於 Vuex 中的 mutation 概念。

在該文件中的具體脈絡，三個 mutation 方法指的是：

| 方法 | 用途 |
|------|------|
| `addInstrument` | 新增儀器到 store |
| `modifyInstrument` | 修改 store 中的儀器資料 |
| `removeInstrument` | 從 store 中移除儀器 |

這些方法被定義在 `frontend/src/stores/instruments.js` 中，原本設計用來修改 store 中的儀器狀態。

### 為什麼被標記為「死碼（Dead Code）」

`InstrumentManage.vue` 元件**完全沒有使用**這三個 mutation 方法：

- 元件直接從 `@/api/instruments` 導入 API 函式（`createInstrument`, `updateInstrument`, `deleteInstrument`）
- 操作後直接呼叫 `instrumentsStore.fetchInstruments()` 重新獲取完整列表
- 這三個 mutation 方法從未被任何元件呼叫，成為未使用的死碼

### 根本原因

元件在實作時直接從 `@/api/instruments` 導入 `createInstrument`、`updateInstrument`、`deleteInstrument`，操作後再手動呼叫 `instrumentsStore.fetchInstruments()`，導致：

1. Store 的 mutation 方法（死碼）和元件的本地 loading state 雙重管理
2. 未來開發者若從 store 呼叫這些方法，會觸發雙重 `fetchInstruments()`

### 如何偵測

```bash
# 搜尋 store 方法在元件中的使用
grep -n "addInstrument\|modifyInstrument\|removeInstrument" frontend/src/views/InstrumentManage.vue
# 無輸出 → 確認為死碼
```

### 修正方法

從 store 中移除未使用的三個 mutation 方法，保留唯一被呼叫的 `fetchInstruments`。

**修正前的 store（72 行）：** 含 `addInstrument`, `modifyInstrument`, `removeInstrument`

**修正後的 store（27 行）：** 僅保留 `fetchInstruments`

---

## 驗證

修正完成後執行語法驗證：

```bash
cd /home/ubuntu/python_code/WebPDTool/backend
python3 -c "
import ast
for f in [
    'app/services/instruments/console_command.py',
    'app/services/instruments/comport_command.py',
    'app/services/instrument_connection.py',
    'app/core/instrument_config.py',
]:
    ast.parse(open(f).read())
    print(f'  OK: {f}')
"
```

預期輸出：
```
  OK: app/services/instruments/console_command.py
  OK: app/services/instruments/comport_command.py
  OK: app/services/instrument_connection.py
  OK: app/core/instrument_config.py
```

---

## 修正摘要

| # | 檔案 | 問題 | 嚴重程度 |
|---|------|------|----------|
| 1 | `instrument_connection.py`, `comport_command.py` | `asyncio.get_event_loop()` → `asyncio.get_running_loop()` (18 處) | Critical |
| 2 | `console_command.py` | 無效型別標注 `str or List[str]` → `Union[str, List[str]]` | Critical |
| 3 | `console_command.py` | `import os/sys` 移至模組頂層 | Important |
| 4 | `comport_command.py` | 裸 `except:` → `except Exception:` | Important |
| 5 | `instrument_config.py` | DB 查詢移至 Lock 外部 | Important |
| 6 | `instruments.js` | 移除未使用的 Store mutation 方法 | Important |
