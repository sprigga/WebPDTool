# MDO34 Measurement Implementation

## Overview

Tektronix MDO34 混合域示波器的 `MDO34Measurement` class 已新增至 `implementations.py`，完成 `lowsheen_lib` 遷移分析中所記錄的 Gap。

**狀態：✅ Complete**（2026-02-26，參考 `docs/analysis/lowsheen_lib_migration_validation_2026_02_24.md` → "New Finding" 章節）

---

## 背景：遷移 Gap

根據遷移驗證分析，MDO34 存在以下缺口：

| 元件 | 狀態（修改前） |
|------|---------------|
| `backend/app/services/instruments/mdo34.py` (`MDO34Driver`) | ✅ 已存在 |
| `instrument_executor.py` `script_map` (`MDO34.py`) | ⚠️ Legacy，指向 `lowsheen_lib` |
| `implementations.py` `MDO34Measurement` class | ❌ **缺失** |
| `MEASUREMENT_REGISTRY["MDO34"]` | ❌ **未註冊** |

若任何 test plan 使用 MDO34 進行量測，`PowerReadMeasurement` 會走到 `else: raise ValueError(...)` 分支，回傳 `ERROR` 結果。本次實作補齊此缺口。

---

## 實作內容

### 新增：`MDO34Measurement` class

**位置：** `backend/app/measurements/implementations.py`（`SMCV100B Measurements` 章節之前）

```python
class MDO34Measurement(BaseMeasurement):
    """
    Oscilloscope measurement using Tektronix MDO34.

    Parameters:
        Instrument: Instrument name in config (default: 'MDO34')
        Channel: Oscilloscope channel number (1-4)
        Item: Measurement type index (1-38)
    """
```

**參數說明：**

| 參數 | 型別 | 必填 | 說明 |
|------|------|------|------|
| `Instrument` | string | 否（預設 `'MDO34'`） | instruments config 中的儀器名稱 |
| `Channel` | int | **是** | 示波器通道（1–4） |
| `Item` | string/int | **是** | 量測類型索引（1–38） |

**`Item` 索引對應表（常用）：**

| Item | SCPI 類型 | 說明 |
|------|-----------|------|
| `1` | `AMPlitude` | 振幅 |
| `9` | `FREQuency` | 頻率 |
| `13` | `MAXimum` | 最大值 |
| `14` | `MEAN` | 平均值 |
| `16` | `MINImum` | 最小值 |
| `25` | `PERIod` | 週期 |
| `27` | `PK2Pk` | 峰對峰值 |
| `32` | `RMS` | 均方根值 |

完整 38 種類型定義於 `MDO34Driver.MEASUREMENT_TYPES`（`backend/app/services/instruments/mdo34.py:24`）。

### 修改：`MEASUREMENT_REGISTRY`

```python
# MDO34 oscilloscope measurements
"MDO34": MDO34Measurement,
```

### 修改：`get_measurement_class()` command_map

```python
# MDO34 mappings
"MDO34": "MDO34",
```

---

## 執行路徑

```
test_plan (test_command: 'MDO34')
  → get_measurement_class('MDO34') → MDO34Measurement
  → MDO34Measurement.execute()
      → get_instrument_settings().get_instrument(instrument_name)
      → get_driver_class('MDO34') → MDO34Driver
      → connection_pool.get_connection(instrument_name)
      → MDO34Driver.initialize()              # *RST
      → MDO34Driver.execute_command(params)
          → select_channel(channel)           # SELECT:CH{n} ON/OFF
          → auto_setup()                      # :AUTOSet EXECute + BUSY? polling
          → write MEASUrement:MEAS4:SOURCE1
          → write MEASUrement:MEAS4:STATE ON
          → write MEASUrement:MEAS4:TYPE {type}
          → query MEASUrement:MEAS4:VALue?
          → return Decimal value string
      → create_result(PASS, measured_value=Decimal(result_str))
```

---

## 錯誤處理

| 情境 | 行為 |
|------|------|
| 缺少 `Channel` 參數 | 回傳 `ERROR "MDO34 measurement requires 'Channel' parameter (1-4)"` |
| 缺少 `Item` 參數 | 回傳 `ERROR "MDO34 measurement requires 'Item' parameter (1-38)"` |
| Instrument config 找不到 | 回傳 `ERROR "Instrument {name} not found in configuration"` |
| Driver class 找不到 | 回傳 `ERROR "No driver found for instrument type: MDO34"` |
| Driver 回傳空字串（timeout/硬體失敗） | 回傳 `ERROR "No instrument found"`（PDTool4 相容格式） |
| 其他 Exception | 回傳 `ERROR {exception message}` |

Driver 層的空字串回傳（`''`）被轉換為 `"No instrument found"`，符合 `BaseMeasurement.validate_result()` 的自動偵測儀器錯誤邏輯。

---

## Test Plan CSV 設定範例

```csv
項次,品名規格,test_command,Instrument,Channel,Item,下限值,上限值,limit_type,value_type
1,Output Frequency,MDO34,MDO34,1,9,49.5,50.5,both,float
2,Peak Voltage,MDO34,MDO34,2,27,3.2,3.4,both,float
```

---

## 相關檔案

| 檔案 | 用途 |
|------|------|
| `backend/app/measurements/implementations.py` | `MDO34Measurement` class、Registry 註冊 |
| `backend/app/services/instruments/mdo34.py` | `MDO34Driver`（SCPI 通訊、38 種量測類型） |
| `backend/app/services/instruments/__init__.py` | Driver registry（`"MDO34": MDO34Driver`） |
| `backend/app/config/instruments.py` | Instrument config（`rf_analyzers` 群組） |
| `backend/app/core/constants.py` | `InstrumentType.MDO34` enum |
| `docs/analysis/lowsheen_lib_migration_validation_2026_02_24.md` | 原始 Gap 分析文件 |
