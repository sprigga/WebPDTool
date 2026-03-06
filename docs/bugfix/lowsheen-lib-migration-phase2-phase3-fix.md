# lowsheen_lib 遷移 Phase 2 & Phase 3 修正

**日期**: 2026-03-06
**類型**: 架構遷移 / 技術債清理
**嚴重性**: High（高風險：legacy subprocess 在 Docker 環境中路徑失效）
**狀態**: 已修正

---

## 問題描述

`measurement_service.py` 中有兩個方法仍使用 `lowsheen_lib` subprocess 呼叫路徑，與 Phase 1 完成的現代化 async driver 架構不一致。

### 受影響方法

| 方法 | 位置 | 問題 |
|------|------|------|
| `_cleanup_used_instruments()` | `measurement_service.py:376` | subprocess `--final` 呼叫（CWD 依賴、fire-and-forget） |
| `reset_instrument()` | `measurement_service.py:658` | 硬編碼 if/elif，僅支援 2 種儀器 |

---

## 根本原因

### Phase 2 問題：`_cleanup_used_instruments()`

```python
# 舊版實作（問題版本）
async def _cleanup_used_instruments(self, used_instruments: Dict[str, str]):
    for instrument_location, script_name in used_instruments.items():
        script_path = f"./src/lowsheen_lib/{script_name}"
        test_params = {"Instrument": instrument_location}
        # 問題 1: create_subprocess_exec 結果從未被 await，為 fire-and-forget
        # 問題 2: 依賴 CWD=backend/，Docker 容器中路徑失效
        await asyncio.create_subprocess_exec(
            "python3", script_path, "--final", str(test_params),
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
```

三個問題同時存在：
1. `asyncio.create_subprocess_exec()` 返回 `Process` 物件但未 await `.wait()`，subprocess 在背景執行，cleanup 在實際完成前就返回
2. `./src/lowsheen_lib/` 路徑依賴 CWD=`backend/`，Docker 容器的工作目錄變更時路徑失效
3. `session_data` 在 `execute_batch_measurements()` 初始化時從未設定 `used_instruments` key，導致此方法實際上永遠接收空字典，清理從未真正執行

### Phase 3 問題：`reset_instrument()`

```python
# 舊版實作（問題版本）
async def reset_instrument(self, instrument_id: str) -> Dict[str, Any]:
    if instrument_id.startswith("daq973a"):
        script_path = "./src/lowsheen_lib/DAQ973A_test.py"
    elif instrument_id.startswith("model2303"):
        script_path = "./src/lowsheen_lib/2303_test.py"
    else:
        raise Exception(f"Unknown instrument: {instrument_id}")  # 僅支援 2 種，其餘全部 raise
    await self._execute_instrument_command(script_path=script_path, ...)
```

問題：
1. 硬編碼 if/elif 僅支援 `daq973a` 和 `model2303` 兩種儀器，系統共有 11 種驅動
2. 其他所有儀器 ID 均會拋出 `Exception`
3. `InstrumentExecutor.reset_instrument()` 已完整實作所有儀器類型的現代化路徑，卻未被使用

---

## 解決方案

### `_cleanup_used_instruments()` 修正

委派給 `InstrumentExecutor.cleanup_instruments()`，後者呼叫每個驅動的 `reset()` async 方法。各驅動的 `reset()` 與舊版 `--final` flag 等效：
- 測量儀器（DAQ973A、APS7050、MDO34 等）：發送 `*RST`
- 電源供應器（MODEL2303、IT6723C 等）：發送 `OUTP OFF`

```python
# 新版實作
async def _cleanup_used_instruments(self, used_instruments: Dict[str, str]):
    from app.services.instrument_executor import InstrumentExecutor

    instrument_ids = list(used_instruments.keys())
    if not instrument_ids:
        return

    executor = InstrumentExecutor()
    await executor.cleanup_instruments(instrument_ids)
```

### `reset_instrument()` 修正

委派給 `InstrumentExecutor.reset_instrument()`，支援所有 11 種儀器類型。若無對應驅動則記錄 warning 並 gracefully 返回（不再 raise Exception）。

```python
# 新版實作
async def reset_instrument(self, instrument_id: str) -> Dict[str, Any]:
    from app.services.instrument_executor import InstrumentExecutor

    executor = InstrumentExecutor()
    await executor.reset_instrument(instrument_id)
    return {"status": "IDLE"}
```

---

## 修改的檔案

| 檔案 | 變更內容 |
|------|---------|
| `backend/app/services/measurement_service.py` | `_cleanup_used_instruments()` 替換為 `InstrumentExecutor.cleanup_instruments()` |
| `backend/app/services/measurement_service.py` | `reset_instrument()` 替換為 `InstrumentExecutor.reset_instrument()` |

---

## `InstrumentExecutor` 現有能力

`InstrumentExecutor.reset_instrument()`（`instrument_executor.py:103-130`）：
- 從 `instrument_settings` 取得儀器配置
- 呼叫 `get_driver_class(config.type)` 取得現代驅動類別
- 若無現代驅動：記錄 warning 並 gracefully 返回（不再 raise）
- 若有現代驅動：`async with connection_pool` 取得連線，呼叫 `driver.reset()`

`InstrumentExecutor.cleanup_instruments()`（`instrument_executor.py:232-243`）：
- 批次呼叫 `reset_instrument()` 於所有傳入的 ID
- 每個儀器獨立 try/except，單一失敗不影響其他清理

---

## 殘留技術債追蹤

| 項目 | 位置 | 說明 | 狀態 |
|------|------|------|------|
| `self.instrument_reset_map` | `measurement_service.py:44-59` | `__init__` 中的 legacy 映射字典，無任何呼叫者 | ✅ 已移除 (2026-03-06) |
| `instrument_executor.py` script_map | `instrument_executor.py:164-180` | 15 項 legacy script 映射，仍作為 `_execute_legacy_script()` fallback，由 `execute_instrument_command()` 在無現代驅動時呼叫 | ✅ 保留並加說明（不可移除，仍為有效 fallback） |
| `used_instruments` 從未填入 | `measurement_service.py:179-187` | `session_data` 初始化無此 key，cleanup 永遠接收空字典 | ✅ 已修正：初始化加入 `"used_instruments": {}`，測量迴圈中追蹤每次使用的 `instrument_id → switch_mode` |

---

## 背景：lowsheen_lib 遷移整體狀態

| Phase | 說明 | 狀態 |
|-------|------|------|
| Phase 1 | 主執行路徑：`execute_single_measurement()` 完全委派給 `implementations.py` | 已完成 |
| Phase 2 | 清理路徑：`_cleanup_used_instruments()` 遷移至現代驅動 | **本次修正** |
| Phase 3 | 重置路徑：`reset_instrument()` 遷移至現代驅動 | **本次修正** |
| Phase 4 | 移除殘留 legacy 程式碼（instrument_reset_map）；script_map 確認保留為有效 fallback | ✅ 已完成 (2026-03-06) |

---

## 相關文件

- `docs/analysis/lowsheen_lib_migration_validation_2026_02_24.md` — 遷移缺口分析原始文件
- `backend/app/services/instrument_executor.py` — 現代化執行器完整實作
- `backend/app/services/instruments/base.py` — `BaseInstrumentDriver.reset()` 抽象方法定義
