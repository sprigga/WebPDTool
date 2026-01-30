# DUT 通訊功能重構完成報告

## 概述

本文檔記錄 WebPDTool 中對 PDTool4 的 DUT（Device Under Test）通訊功能的完整重構，包括繼電器控制（MeasureSwitchON/OFF）和機箱底座旋轉（MyThread_CW/CCW）功能。

**重構日期**: 2026-01-30
**影響模組**: 測量系統、服務層、API 層
**測試狀態**: ✅ 所有測試通過（29 個測試）

---

## 重構目標

### PDTool4 原始功能

1. **繼電器控制** (`OtherMeasurement.py`)
   - `MeasureSwitchON` - 繼電器開啟（SWITCH_OPEN = 0）
   - `MeasureSwitchOFF` - 繼電器關閉（SWITCH_CLOSED = 1）

2. **機箱底座旋轉** (`OtherMeasurement.py`)
   - `MyThread_CW` - 順時針旋轉（命令碼 = 6）
   - `MyThread_CCW` - 逆時針旋轉（命令碼 = 9）
   - 使用 QThread 非同步執行
   - 呼叫外部腳本 `chassis_fixture_bat.py`
   - 通過序列埠 `/dev/ttyACM0` 控制硬體

### 重構需求

- ✅ 保持 PDTool4 完整功能相容性
- ✅ 採用非同步架構（asyncio）
- ✅ 模組化設計，易於擴展和維護
- ✅ 提供 RESTful API 端點
- ✅ 完整的測試覆蓋
- ✅ 內建錯誤處理和日誌記錄

---

## 架構設計

### 1. 服務層 (`app/services/dut_comms/`)

新建專用的 DUT 通訊服務模組，包含：

#### 1.1 RelayController (`relay_controller.py`)

**類別**: `RelayController`

**主要方法**:
```python
async def set_relay_state(state: RelayState, channel: int) -> bool
async def switch_on(channel: int) -> bool  # 映射 MeasureSwitchON
async def switch_off(channel: int) -> bool  # 映射 MeasureSwitchOFF
async def get_current_state() -> Optional[RelayState]
async def reset(channel: int) -> bool
```

**列舉類型**: `RelayState`
- `SWITCH_OPEN = 0`  (ON 狀態)
- `SWITCH_CLOSED = 1` (OFF 狀態)

**特點**:
- Singleton 模式（通過 `get_relay_controller()`）
- 支援多通道控制（1-16）
- 狀態追蹤和查詢
- 完整的錯誤處理和日誌

---

## PDTool4 相容性對照表

| PDTool4 功能 | WebPDTool 實現 | 相容性 | 備註 |
|-------------|---------------|--------|------|
| `MeasureSwitchON` | `RelayMeasurement` (state=ON) | ✅ 完整 | 命令映射支援 |
| `MeasureSwitchOFF` | `RelayMeasurement` (state=OFF) | ✅ 完整 | 命令映射支援 |
| `SWITCH_OPEN = 0` | `RelayState.SWITCH_OPEN = 0` | ✅ 完整 | 數值完全相同 |
| `SWITCH_CLOSED = 1` | `RelayState.SWITCH_CLOSED = 1` | ✅ 完整 | 數值完全相同 |
| `MyThread_CW` | `ChassisRotationMeasurement` (direction=CW) | ✅ 完整 | 非同步化改進 |
| `MyThread_CCW` | `ChassisRotationMeasurement` (direction=CCW) | ✅ 完整 | 非同步化改進 |

## 測試覆蓋

總計: 29 個測試全部通過 ✅

