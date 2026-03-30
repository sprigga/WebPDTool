# Stub 分析與實作路線圖

**Date**: 2026-03-27
**Author**: Claude Code
**Status**: Reference

---

## 概覽

本文件記錄 WebPDTool 後端中所有尚未完整實作（stub）的程式碼，作為後續開發的參考基準。

> CLAUDE.md 明確說明：「Most implementations are stubs. Real hardware drivers need implementation in `backend/app/services/instruments/`.」

---

## 1. NotImplementedError（明確標記未實作）

| 檔案 | 行號 | 內容 | 性質 |
|------|------|------|------|
| `app/services/instruments/analog_discovery_2.py` | ~216 | `raise NotImplementedError("Oscilloscope mode not implemented in Phase 2")` | **需實作** |
| `app/services/instrument_manager.py` | ~35 | `raise NotImplementedError("Subclass must implement send_command")` | 設計上正常（抽象方法） |
| `app/services/instruments/base.py` | ~44, ~52 | `@abstractmethod initialize()` / `reset()` 為 pass | 設計上正常（抽象方法） |

---

## 2. 含模擬模式（Simulation Mode）的驅動程式

這些驅動程式使用 `sim://...` 地址時返回硬編碼假資料，**沒有真實硬體驅動邏輯**。

### 2.1 CMW100（Rohde & Schwarz 無線通訊測試儀）

**檔案：** `app/services/instruments/cmw100.py`

| 模擬方法 | 假資料內容 |
|---------|-----------|
| `_simulate_ble_measurement()` (L221) | BLE TX 功率：隨機 -10~+15 dBm ±2 dB |
| `_simulate_wifi_measurement()` (L448) | WiFi EVM：-35~-50 dB；TX 功率：15.5；頻率誤差：5000 |

**缺少的真實實作：**
- 透過 RsInstrument / VISA 連接實體儀器
- 真實 BLE/WiFi 量測指令序列

### 2.2 MT8872A（Anritsu LTE 測試儀）

**檔案：** `app/services/instruments/mt8872a.py`

| 模擬方法 | 假資料內容 |
|---------|-----------|
| `_simulate_lte_tx_measurement()` (L460) | LTE TX 功率：15-30 dBm |
| `_simulate_lte_rx_measurement()` (L613) | LTE RX 回傳空 `{}` |

**缺少的真實實作：**
- LTE RX 靈敏度量測
- ACLR / SEM 解析

### 2.3 ComPort Command

**檔案：** `app/services/instruments/comport_command.py`

- 序列埠無法開啟時自動切入模擬模式
- 返回 `conn_config.sim_response`（可配置的假回應）
- 真實 COM port 通訊框架已存在，但錯誤處理路徑依賴模擬

---

## 3. TODO / FIXME 標記

### 3.1 chassis_controller.py — stop_rotation() 缺少硬體命令

**檔案：** `app/services/dut_comms/chassis_controller.py`

```python
# 行 ~193
# TODO: Implement stop command if supported by hardware
self._is_rotating = False
return True
```

**問題：** `stop_rotation()` 只更新內部狀態，未向硬體發送停止命令。

### 3.2 relay_controller.py — 繼電器控制待實作

**檔案：** `app/services/dut_comms/relay_controller.py`

```python
# 行 ~57
# TODO: Implement actual relay control via serial port or other interface
```

**問題：** 舊的模擬程式碼已被移除，新的真實串列埠控制邏輯尚未補全。

### 3.3 measurement_service.py — 暫時後備程式碼

**檔案：** `app/services/measurement_service.py`

| 行號 | 內容 |
|------|------|
| ~544 | `# TODO: Remove this once all instruments have proper async drivers` |
| ~688 | `# TODO: 將以下所有規則遷移到 MEASUREMENT_TEMPLATES 後可移除此段` |

**問題：** 這些是過渡期的後備邏輯，應在驅動程式完整後清理。

---

## 4. 使用模擬延遲的驅動程式（asyncio.sleep）

以下驅動程式用 `asyncio.sleep(0.1)` 模擬硬體回應時間，可能是 stub 也可能是合理等待（需個別判斷）：

| 檔案 | 行號 | 說明 |
|------|------|------|
| `instruments/daq973a.py` | L75, L106 | DAQ973A 資料擷取儀 |
| `instruments/model2303.py` | L57, L84 | Model 2303 電源供應器 |
| `instruments/psw3072.py` | L60, L87, L112 | PSW3072 電源供應器 |
| `instruments/peak_can.py` | L386 | PEAK CAN 介面 |

> 電源供應器的 `asyncio.sleep` 通常是必要的穩定等待，DAQ973A 和 PEAK_CAN 需進一步確認。

---

## 5. 驅動程式完整性矩陣

### ✅ 完整實作

| 驅動程式 | 檔案 | 說明 |
|---------|------|------|
| MODEL2303 | `model2303.py` | 雙通道電源供應器 |
| MODEL2306 | `model2306.py` | 雙通道電源供應器 |
| A2260B | `a2260b.py` | Keithley 電源 |
| IT6723C | `it6723c.py` | ITECH 電源供應器 |
| N5182A | `n5182a.py` | Agilent 信號產生器 |
| APS7050 | `aps7050.py` | 電源供應器 |
| PSW3072 | `psw3072.py` | 電源供應器 |
| FTM_ON | `ftm_on.py` | WiFi FTM 測試 |
| TCPIP_COMMAND | `tcpip_command.py` | TCP/IP 通用介面 |
| COMPORT_COMMAND | `comport_command.py` | COM Port 通用介面（含模擬後備） |
| CONSOLE_COMMAND | `console_command.py` | 主控臺命令 |
| WAIT_TEST | `wait_test.py` | 延遲工具 |

### ⚠️ 部分實作（有模擬後備）

| 驅動程式 | 檔案 | 缺少的部分 |
|---------|------|-----------|
| CMW100 | `cmw100.py` | 真實 BLE/WiFi 量測邏輯 |
| MT8872A | `mt8872a.py` | LTE RX 量測、ACLR/SEM 解析 |
| PEAK_CAN | `peak_can.py` | CAN 訊息處理部分功能 |
| SMCV100B | `smcv100b.py` | 多返回值解析 |
| L6MPU_SSH | `l6mpu_ssh.py` | SSH 連接部分功能 |
| L6MPU_POS_SSH | `l6mpu_pos_ssh.py` | 位置追蹤功能 |
| L6MPU_SSH_COMPORT | `l6mpu_ssh_comport.py` | 混合 SSH/COMPORT 協議 |
| DAQ973A | `daq973a.py` | 確認 sleep 是否為真實需求 |
| DAQ6510 | `daq6510.py` | 資料擷取邏輯不完整 |

### ❌ 未實作

| 驅動程式 | 檔案 | 說明 |
|---------|------|------|
| AnalogDiscovery2 (Oscilloscope) | `analog_discovery_2.py` | Oscilloscope 模式直接拋出 NotImplementedError |

---

## 6. 優先實作建議

依影響範圍排序：

| 優先級 | 項目 | 理由 |
|--------|------|------|
| P1 | **CMW100 真實驅動** | 無線通訊測試是核心功能，現全為模擬 |
| P1 | **relay_controller.py** | 繼電器控制影響測試夾具，舊程式碼已移除 |
| P2 | **MT8872A LTE RX** | LTE 接收靈敏度量測返回空資料 |
| P2 | **chassis_controller stop_rotation** | Stop 命令只更新標誌，硬體未停止 |
| P3 | **analog_discovery_2 Oscilloscope** | Phase 2 留下的 NotImplementedError |
| P3 | **measurement_service TODO 清理** | 待驅動程式補全後的技術債清理 |

---

## 相關文件

- `docs/plans/2026-02-05-phase3-rf-instrument-drivers-design.md` — CMW100 / MT8872A 驅動設計
- `docs/plans/2026-02-04-phase2-instruments.md` — Phase 2 儀器實作計畫
- `docs/plans/2026-02-05-phase3-low-priority-instruments-implementation.md` — 低優先級儀器
