# Pytest 測試框架設定總結

本文檔說明 WebPDTool 專案的 pytest 測試環境設定。

## 已創建的文件

### 1. pytest.ini
專案根目錄的 pytest 配置文件，包含：
- 測試發現規則
- 命令列選項
- 測試標記（markers）定義

### 2. tests/conftest.py
共享的 pytest fixtures 和配置：
- `async_client`: FastAPI 測試用 HTTP 客戶端
- `db_session`: 測試用資料庫會話（in-memory SQLite）
- `instrument_executor`: 儀器執行器實例
- `sim_connection`: 模擬連接 fixture
- `sample_test_plan`: 樣本測試計畫
- 自動標記系統

### 3. 測試文件改寫

#### 原始寫法（❌ 不推薦）
```python
async def test_34970a():
    print("Testing 34970A...")
    try:
        result = await executor.execute_instrument_command(...)
        print(f"✓ Result: {result}")
    except Exception as e:
        print(f"✗ Failed: {e}")

async def main():
    await test_34970a()
    await test_model2306()

if __name__ == "__main__":
    asyncio.run(main())
```

#### Pytest 寫法（✅ 推薦）
```python
@pytest.mark.instruments
@pytest.mark.simulation
@pytest.mark.asyncio
class Test34970ADriver:
    async def test_open_channels(self, instrument_executor):
        result = await instrument_executor.execute_instrument_command(
            instrument_id="34970A_1",
            params={'Item': 'OPEN', 'Channel': '01'},
            simulation=True
        )
        assert result is not None
```

## 執行測試的方法

### 方法 1: 使用腳本（推薦）

```bash
# 執行所有測試（快速、模擬模式）
./scripts/run_tests.sh

# 執行測量驗證測試
./scripts/run_tests.sh measurements

# 執行儀器測試
./scripts/run_tests.sh instruments

# 執行特定儀器測試
./scripts/run_tests.sh 34970a

# 產生覆蓋率報告
./scripts/run_tests.sh -c

# 只執行單元測試
./scripts/run_tests.sh -u

# 執行整合測試
./scripts/run_tests.sh -i

# 包含硬體測試
./scripts/run_tests.sh -w

# 詳細輸出並在第一次失敗時停止
./scripts/run_tests.sh -v -x
```

### 方法 2: 直接使用 pytest

```bash
# 執行所有測試
pytest

# 只執行模擬模式測試
pytest -m simulation

# 只執行單元測試
pytest -m unit

# 排除慢速測試
pytest -m "not slow"

# 執行特定測試文件
pytest tests/test_measurements_refactoring.py

# 執行特定測試類別
pytest tests/test_measurements_refactoring.py::TestLowerLimitValidation

# 執行特定測試方法
pytest tests/test_measurements_refactoring.py::TestLowerLimitValidation::test_lower_limit_validation

# 產生覆蓋率報告
pytest --cov=app --cov-report=html
```

### 方法 3: 使用 uv

```bash
# 根據 CLAUDE.md 規範，使用 uv 執行測試
cd /home/ubuntu/python_code/WebPDTool

# 執行所有測試
uv run pytest

# 執行特定測試
uv run pytest tests/test_measurements_refactoring.py
```

## 測試標記系統

### 按速度分類
- `slow`: 執行時間 > 1 秒的測試
- `fast`: 執行時間 < 1 秒的測試

### 按類型分類
- `unit`: 單元測試（快速、隔離、無外部依賴）
- `integration`: 整合測試（使用外部服務）
- `e2e`: 端對端測試（完整系統測試）

### 按硬體需求分類
- `hardware`: 需要實體硬體
- `simulation`: 模擬模式（不需要硬體）

### 按儀器分類
- `instrument_34970a`: 34970A 數據採集器
- `instrument_model2306`: MODEL2306 雙通道電源
- `instrument_it6723c`: IT6723C 可編程電源
- `instrument_2260b`: 2260B 可編程電源
- `instrument_cmw100`: CMW100 射頻分析儀
- `instrument_mt8872a`: MT8872A 網路測試儀

### 按組件分類
- `measurements`: 測量層測試
- `instruments`: 儀器驅動測試
- `api`: API 端點測試
- `services`: 服務層測試

## 遷移檢查清單

### 現有測試文件狀態

| 文件 | 狀態 | 建議 |
|------|------|------|
| `test_high_priority_instruments.py` | ❌ 舊寫法 | 已建立 `test_instruments_pytest_style.py` |
| `test_refactoring.py` | ❌ 舊寫法 | 已建立 `test_measurements_refactoring.py` |
| `test_medium_priority_instruments.py` | ❌ 舊寫法 | 需要遷移 |
| `test_instrument_drivers.py` | ❌ 舊寫法 | 需要遷移 |
| `test_custom_scripts.py` | ❌ 舊寫法 | 需要遷移 |
| `test_instruments/test_cmw100.py` | ✅ 標準 pytest | 無需變更 |
| `test_instruments/test_mt8872a.py` | ? 待檢查 | 需要確認 |

### 遷移步驟

1. **保留原始文件**（已註解）
2. **創建新的 pytest 風格文件**
3. **更新 `conftest.py`** 如需新增 fixtures
4. **執行測試確保功能相同**
5. **更新 CI/CD 配置**（如有）

## Pytest vs 舊寫法對照表

| 功能 | 舊寫法 | Pytest |
|------|--------|--------|
| 測試發現 | 手動 main 函數 | 自動發現 `test_*.py` |
| 斷言 | `assert` + 手動錯誤處理 | `assert` + 自動錯誤訊息 |
| 測試分類 | 無 | `@pytest.mark.marker` |
| 參數化測試 | 手動迴圈 | `@pytest.mark.parametrize` |
| Fixture | 手動 setup/teardown | `@pytest.fixture` |
| 非同步測試 | `asyncio.run()` | `@pytest.mark.asyncio` |
| 測試隔離 | 共享狀態 | 獨立執行，自動清理 |
| 報告 | print 輸出 | 標準 pytest 輸出 |
| 覆蓋率 | 手動整合 | `pytest-cov` 插件 |

## 常見問題

### Q: 為什麼要遷移到 pytest？
A:
- 更好的測試發現和組織
- 強大的斷言機制和錯誤訊息
- 豐富的插件生態
- 標準化的測試寫法
- 更好的 CI/CD 整合

### Q: 舊測試還能用嗎？
A: 是的，可以直接用 Python 執行：
```bash
python3 tests/test_high_priority_instruments.py
```

### Q: 如何混合使用？
A: 沒問題！pytest 相容性很好：
```bash
# 新舊測試一起執行
pytest tests/test_instruments_pytest_style.py tests/test_refactoring.py
```

## 下一步

1. **更新 CI/CD 配置**（如 GitHub Actions）
2. **遷移剩餘的舊測試文件**
3. **添加更多測試覆蓋率**
4. **設置測試覆蓋率目標**
5. **整合 pre-commit hooks**
