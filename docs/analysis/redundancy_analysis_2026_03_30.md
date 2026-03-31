# WebPDTool 冗餘代碼與文件分析

**分析日期:** 2026-03-30
**驗證日期:** 2026-03-31（全部 7 類問題已確認修正完成）
**分析範圍:** `backend/` + `frontend/` 完整代碼庫

---

## 總覽

對 WebPDTool 項目進行完整掃描，發現 7 類冗餘，主要來源為 PDTool4 → WebPDTool 遷移期間保留的過渡代碼。

| 類別 | 文件/位置數量 | 優先級 | 建議操作 |
|------|-------------|--------|---------|
| `src/lowsheen_lib/` 整個舊驅動庫 | ~25 個文件 | 高 | 整目錄刪除 |
| 重複日志文件 | 1 個文件 | 高 | 刪除 `logging.py` |
| 臨時腳本 | 2 個文件 | 高 | 直接刪除 |
| 未歸類測試腳本 | 5 個文件 | 中 | 遷移或刪除 |
| SQL 遷移腳本 | 6 個文件 | 中 | 確認後刪除 |
| 注釋代碼塊 | 4 個文件中多處 | 低 | 清理注釋 |
| 前端硬編碼常量 | 1 個文件 | 低 | 從 API 動態加載 |

---

## 一、`backend/src/lowsheen_lib/`（高優先級）✅ 已完成（2026-03-31）

**問題：** 整個目錄是 PDTool4 遷移前的舊驅動庫，已被 `app/services/instruments/` 完整替代，但從未清理。

**替代對照表：**

| 舊文件 (`src/lowsheen_lib/`) | 替代文件 (`app/services/instruments/`) |
|------------------------------|----------------------------------------|
| `2260B.py` (76行) | `a2260b.py` (173行) |
| `34970A.py` | `a34970a.py` |
| `ComPortCommand.py` (147行) | `comport_command.py` (302行) |
| `ConSoleCommand.py` (43行) | `console_command.py` (298行) |
| `TCPIPCommand.py` (114行) | `tcpip_command.py` (281行) |
| `OPjudge_YorN.py` (81行) | `app/measurements/implementations.py` (`OPjudge` class) |
| `OPjudge_confirm.py` (69行) | 同上（PyQt5 GUI 版本，Docker 環境不可用） |
| `OPjudge_YorN_terminal.py` (132行) | 同上 |
| `OPjudge_confirm_terminal.py` (130行) | 同上 |
| `remote_instrument.py` (133行) | `app/measurements/base.py` |
| `testUTF/123.py` | 無用的測試文件 |
| 其餘 ~15 個文件 | 全部已重寫 |

**注意：** `lowsheen_lib_migration_validation_2026_02_24.md` 已確認遷移覆蓋率達 70%+，遷移驗證完成。

**建議：** 刪除整個 `backend/src/lowsheen_lib/` 目錄，包含子目錄 `testUTF/`。

**驗證（2026-03-31）：** 目錄已不存在，所有檔案已清除。

---

## 二、重複日誌系統（高優先級）✅ 已完成（2026-03-31）

**問題：** 兩個日誌文件並存，功能重疊。

| 文件 | 行數 | 功能 |
|------|------|------|
| `backend/app/core/logging.py` | 26 行 | 基礎文件+控制台輸出 |
| `backend/app/core/logging_v2.py` | 376 行 | Redis 支持、結構化日誌、async 處理、會話隔離 |

`logging.py` 是 `logging_v2.py` 的功能子集，屬於過渡期產物。

**建議：** 確認無文件直接 `import logging` 引用舊版後，刪除 `logging.py`。

**驗證（2026-03-31）：** `logging.py` 已不存在，`app/core/` 下只剩 `logging_v2.py`。

---

## 三、臨時腳本（高優先級）✅ 已完成（2026-03-31）

位於 `backend/scripts/`，屬於開發時的臨時文件，無保留價值：

- `hello_world.py` — 僅 2 行 `print("Hello World")`
- `test123.py` — 12 行臨時測試，含注釋代碼

**建議：** 直接刪除。

**驗證（2026-03-31）：** `hello_world.py` 與 `test123.py` 均已不存在。

---

## 四、未歸類測試腳本（中優先級）✅ 已完成（2026-03-31）

以下文件位於 `backend/scripts/`，實為手動執行的開發腳本，未以 pytest 格式組織，無法通過 `uv run pytest` 執行：

- `scripts/test_dut_control.py` (5.2KB)
- `scripts/test_instruments_simple.py` (5.8KB)
- `scripts/test_opjudge.py` (6.4KB)
- `scripts/test_redis_logging.py` (5.6KB)
- `scripts/test_refactoring_api.py` (8.3KB)

**建議：**
1. 評估是否仍需要這些測試邏輯
2. 若需要，遷移到 `tests/` 目錄並改寫為 pytest 格式
3. 若不再使用，直接刪除

**驗證（2026-03-31）：** 5 個 `test_*.py` 均已不存在，選擇直接刪除。

---

## 五、SQL 遷移腳本（中優先級）✅ 已完成（2026-03-31）

`backend/scripts/` 下存在 6 個 `.sql` 文件，這些是早期手動初始化腳本，功能已被 Alembic 遷移接管。

**建議：** 確認 `database/` 目錄下的 `schema.sql`/`seed_data.sql` 等為 CLAUDE.md 中記錄的正式初始化腳本後，刪除 `scripts/` 下的 `.sql` 文件。

**驗證（2026-03-31）：** `scripts/` 下已無任何 `.sql` 檔案，6 個遷移腳本均已刪除。

---

## 六、注釋掉的代碼塊（低優先級）✅ 已完成（2026-03-31）

遷移同步 DB 操作到 async 時遺留的注釋參考代碼，Git 歷史已保留原始代碼，注釋塊已無保留意義。

| 文件 | 位置 | 內容描述 |
|------|------|---------|
| `app/api/tests.py` | 行 80–141 | 注釋掉的舊同步 DB 代碼 |
| `app/api/projects.py` | 行 47, 71, 77, 102–104 | 舊同步查詢 |
| `app/api/stations.py` | 多處 | 舊導入和 DB 訪問代碼 |
| `app/api/auth.py` | 行 100–106 | 舊實現說明 |

**建議：** 直接刪除這些注釋塊。

**驗證（2026-03-31）：** 4 個檔案中的舊同步 DB 注釋代碼均已清除，僅保留必要的業務邏輯注釋。

---

## 七、前端硬編碼常量（已完成 — 2026-03-30）

**原問題：** `frontend/src/composables/useMeasurementParams.js` 中硬編碼了測量參數的下拉選項：

```javascript
// 原有硬編碼（已移除）
if (name === 'baud') return ['9600', '19200', '38400', '57600', '115200']
if (name === 'type') return ['DC', 'AC', 'RES', 'TEMP']
if (name === 'item') return ['volt', 'curr', 'res', 'temp', 'freq']
if (name === 'operator_judgment') return ['PASS', 'FAIL']
```

**實作方法：**

### 步驟一：後端 `MEASUREMENT_TEMPLATES` 加入 `options` 欄位

在 `backend/app/config/instruments.py` 的相關 switch_mode 定義中新增 `options` 欄位，作為單一真實來源。

> **注意：** 分析文件原本建議使用 `GET /api/measurements/types` 端點，但該端點實際上只回傳測試類型清單，不含參數選項。真正用於前端表單的是 `GET /api/measurements/templates`，回傳完整 `MEASUREMENT_TEMPLATES`。因此選擇在 `MEASUREMENT_TEMPLATES` 中直接加入 `options` 欄位，不需新增端點。

加入 options 的 switch_mode 清單：

| 測試類型 | Switch Mode | 新增 options |
|---------|------------|-------------|
| `PowerSet` | `DAQ973A` | `Item`: `["volt", "curr", "clos", "open"]` |
| `PowerSet` | `34970A` | `Item`: `["clos", "open", "volt", "curr"]` |
| `PowerRead` | `DAQ973A` | `Item`: `["volt", "curr"]`；`Type`: `["DC", "AC", "RES", "TEMP", "FREQ"]` |
| `PowerRead` | `34970A` | `Item`: `["volt", "curr", "res", "temp", "freq"]` |
| `PowerRead` | `6510` | `Item`: `["volt", "curr", "res", "temp", "freq"]` |
| `PowerRead` | `APS7050` | `Item`: `["volt", "curr"]` |
| `PowerRead` | `MDO34` | `Item`: `["volt", "curr", "res", "freq", "amp"]` |
| `Relay` | `default` | `Action`: `["ON", "OFF"]` |
| `OPjudge` | `YorN` | `operator_judgment`: `["PASS", "FAIL"]` |

### 步驟二：前端 `useMeasurementParams.js` 改為動態讀取

修改 `getParamOptions()` 和 `inferParamType()` 兩個函數：

```javascript
// 修改後: 從 API 模板動態讀取
const getParamOptions = (paramName) => {
  const templateOptions = currentTemplate.value?.options?.[paramName]
  if (templateOptions?.length > 0) return templateOptions
  return []
}

// inferParamType: 以 options 存在與否判斷是否為 select
if (currentTemplate.value?.options?.[paramName]?.length > 0) {
  return 'select'
}
```

原有硬編碼以注釋方式保留在原位，符合專案規範。

**效果：** 新增儀器時只需更新 `MEASUREMENT_TEMPLATES`，前端 UI 自動反映，消除前後端常量不同步風險。`GET /api/measurements/templates` 端點無需修改，因為它直接回傳整個 `MEASUREMENT_TEMPLATES` 結構。

---

## 建議執行順序

> **驗證日期：2026-03-31 — 全部 8 項均已完成。**

### 第一階段（立即，無風險）
1. ~~刪除 `backend/scripts/hello_world.py`~~ **已完成 (2026-03-31)**
2. ~~刪除 `backend/scripts/test123.py`~~ **已完成 (2026-03-31)**
3. ~~刪除 `backend/src/lowsheen_lib/` 整個目錄~~ **已完成 (2026-03-31)**

### 第二階段（確認後執行）
4. ~~刪除 `backend/app/core/logging.py`（確認無直接導入）~~ **已完成 (2026-03-31)**
5. ~~刪除 `backend/scripts/*.sql`（確認 `database/` 下有正式版本）~~ **已完成 (2026-03-31)**
6. ~~評估並處理 `scripts/test_*.py` 文件~~ **已完成 (2026-03-31)，選擇直接刪除**

### 第三階段（低優先，漸進清理）
7. ~~清理 4 個 API 文件中的注釋代碼塊~~ **已完成 (2026-03-31)**
8. ~~重構前端硬編碼常量改為 API 動態加載~~ **已完成 (2026-03-30)**

---

**相關文件：**
- [`lowsheen_lib_migration_validation_2026_02_24.md`](./lowsheen_lib_migration_validation_2026_02_24.md) — 確認 lowsheen_lib 遷移完成度
- [`ARCHITECTURE_INDEX.md`](./ARCHITECTURE_INDEX.md) — 架構文件總索引
