# Instrument Driver Migration Guide

## 概述

本文檔說明如何從 PDTool4 的儀器腳本遷移到 WebPDTool Backend 的現代化架構。

## 架構變更

### PDTool4 (舊架構)

```
oneCSV_atlas_2.py (同步執行)
    ↓ subprocess.check_output()
src/lowsheen_lib/DAQ973A_test.py (獨立腳本)
    ↓ pyvisa
儀器硬體
```

**特點**:
- ✅ 簡單直接
- ❌ 同步阻塞
- ❌ 無連線池
- ❌ 無類型安全
- ❌ 配置分散 (test_xml.ini)

### WebPDTool Backend (新架構)

```
measurement_service.py (異步執行)
    ↓
instrument_executor.py (執行層)
    ↓
instrument_connection.py (連線池)
    ↓
instruments/daq973a.py (驅動器)
    ↓ async wrapper → pyvisa
儀器硬體
```

**特點**:
- ✅ 完全異步 (非阻塞)
- ✅ 連線池管理 (重用連線)
- ✅ 類型安全 (Pydantic 驗證)
- ✅ 統一配置 (JSON/環境變數)
- ✅ 模擬模式 (無硬體測試)
- ✅ 向後兼容 (可回退到 subprocess)

## 遷移策略

### 階段 1: 使用 Legacy Mode (即時可用)

在驅動器未完成前,使用 subprocess 執行原始腳本:

```python
# measurement_service.py 自動偵測
result = await self._execute_instrument_command(
    script_path="./src/lowsheen_lib/DAQ973A_test.py",
    test_point_id=test_point_id,
    test_params=test_params
)
```

**優點**: 立即可用,無需改動
**缺點**: 仍然是同步阻塞

### 階段 2: 重構為現代驅動器 (推薦)

創建新的驅動器類:

```python
# backend/app/services/instruments/daq973a.py
from app.services.instruments.base import BaseInstrumentDriver

class DAQ973ADriver(BaseInstrumentDriver):
    async def measure_voltage(self, channels, type='DC'):
        cmd = f"MEAS:VOLT:{type}? (@{channels})"
        response = await self.connection.query(cmd)
        return Decimal(response)
```

**優點**: 完全異步、類型安全、可測試
**缺點**: 需要重寫程式碼

## 配置系統

### PDTool4 配置 (test_xml.ini)

```ini
[Setting]
DAQ973A_1 = TCPIP0::192.168.1.10::inst0::INSTR
MODEL2303_1 = COM3/baud:115200
```

### Backend 配置 (instruments.json)

```json
{
  "instruments": {
    "DAQ973A_1": {
      "type": "DAQ973A",
      "name": "Keysight DAQ973A #1",
      "connection": {
        "type": "VISA",
        "address": "TCPIP0::192.168.1.10::inst0::INSTR",
        "timeout": 5000
      },
      "enabled": true
    }
  }
}
```

**配置方式**:

1. **環境變數**:
```bash
export INSTRUMENTS_CONFIG_FILE=/path/to/instruments.json
```

2. **.env 文件**:
```bash
INSTRUMENTS_CONFIG_FILE=./instruments.json
```

3. **直接 JSON 字串**:
```bash
export INSTRUMENTS_CONFIG_JSON='{"instruments": {...}}'
```

## 驅動器開發指南

### 1. 創建驅動器類

```python
# app/services/instruments/your_instrument.py
from app.services.instruments.base import BaseInstrumentDriver
from typing import Dict, Any
from decimal import Decimal

class YourInstrumentDriver(BaseInstrumentDriver):

    async def initialize(self):
        """初始化儀器"""
        await self.reset()

    async def reset(self):
        """重置儀器 (cleanup)"""
        await self.write_command('*RST')

    async def your_measurement(self, params) -> Decimal:
        """自定義測量方法"""
        cmd = f"MEAS:YOUR:COMMAND? {params}"
        response = await self.query_command(cmd)
        return Decimal(response)

    async def execute_command(self, params: Dict[str, Any]) -> str:
        """
        PDTool4 兼容接口

        Args:
            params: 參數字典 (來自 test_params)

        Returns:
            字串結果 (for backward compatibility)
        """
        item = params.get('Item')

        if item == 'YOUR_COMMAND':
            value = await self.your_measurement(params)
            return f'{value:.3f}'
        else:
            raise ValueError(f"Unknown command: {item}")
```

### 2. 註冊驅動器

```python
# app/services/instruments/__init__.py
from app.services.instruments.your_instrument import YourInstrumentDriver

INSTRUMENT_DRIVERS = {
    "YOUR_INSTRUMENT": YourInstrumentDriver,
}
```

### 3. 測試驅動器

```python
# scripts/test_your_instrument.py
async def test():
    executor = get_instrument_executor()

    result = await executor.execute_instrument_command(
        instrument_id="YOUR_INSTRUMENT_1",
        params={'Item': 'YOUR_COMMAND', 'Param': 'value'},
        simulation=True  # 模擬模式
    )
    print(f"Result: {result}")
```

## 連線類型支援

### 1. VISA (USB/LAN/GPIB)

```json
{
  "connection": {
    "type": "VISA",
    "address": "TCPIP0::192.168.1.10::inst0::INSTR",
    "timeout": 5000
  }
}
```

### 2. Serial (COM/TTY)

```json
{
  "connection": {
    "type": "SERIAL",
    "port": "COM3",
    "baudrate": 115200,
    "stopbits": 1,
    "timeout": 5000
  }
}
```

### 3. TCP/IP Socket

```json
{
  "connection": {
    "type": "TCPIP_SOCKET",
    "host": "192.168.1.20",
    "port": 2268,
    "timeout": 5000
  }
}
```

### 4. GPIB

```json
{
  "connection": {
    "type": "GPIB",
    "board": 0,
    "address": 16,
    "timeout": 5000
  }
}
```

## 依賴安裝

### 核心依賴 (必需)

```bash
cd backend
uv pip install pydantic pydantic-settings
```

### 儀器通訊依賴 (選用)

```bash
# VISA 支援
uv pip install pyvisa pyvisa-py

# Serial 支援
uv pip install pyserial

# NI-VISA 後端 (硬體支援更好,但需要安裝 NI-VISA 驅動)
# https://www.ni.com/en/support/downloads/drivers/download.ni-visa.html
```

## 測試與驗證

### 1. 模擬模式測試 (無硬體)

```bash
cd backend
uv run python scripts/test_instrument_drivers.py
```

### 2. 硬體測試

1. 配置實際儀器地址 (`instruments.json`)
2. 啟用儀器 (`"enabled": true`)
3. 運行測試:

```python
# 不使用 simulation 參數
result = await executor.execute_instrument_command(
    instrument_id="DAQ973A_1",
    params={'Item': 'VOLT', 'Channel': '101', 'Type': 'DC'}
    # simulation=False (default)
)
```

### 3. 整合測試

修改 `measurement_service.py` 的 `_execute_power_read()`:

```python
# 舊版 (subprocess)
result = await self._execute_instrument_command(
    script_path="./src/lowsheen_lib/DAQ973A_test.py",
    test_point_id=test_point_id,
    test_params=test_params
)

# 新版 (modern driver)
from app.services.instrument_executor import get_instrument_executor

executor = get_instrument_executor()
result = await executor.execute_instrument_command(
    instrument_id=test_params['Instrument'],
    params=test_params
)
```

## 已完成遷移

**初始驅動器** (2 個):
- ✅ `DAQ973A` - 完整驅動器
- ✅ `MODEL2303` - 完整驅動器

**高優先級驅動器** (4 個):
- ✅ `34970A` - 數據采集/開關單元 (2026-01-28)
- ✅ `MODEL2306` - 雙通道電源 (2026-01-28)
- ✅ `IT6723C` - 可編程電源 (2026-01-28)
- ✅ `2260B` - 直流電源 (2026-01-28)

**總計**: 6 / 19 儀器 (32% 完成)

## 待遷移清單

高優先級:
- ✅ (全部完成 - 2026-01-28)

中優先級:
- ✅ `DAQ6510` - 數據采集系統 (2026-01-28)
- ✅ `PSW3072` - 三路輸出電源 (2026-01-28)
- ✅ `KEITHLEY2015` - 音頻分析儀 (2026-01-28)
- ✅ `MDO34` - 混合域示波器 (2026-01-28)

低優先級:
- ⏳ `APS7050` - 電源供應器
- ⏳ `MT8870A_INF` - 無線通訊測試儀

命令類型 (可直接使用原始腳本):
- ✅ `ComPortCommand` - 串口命令 (Legacy mode)
- ✅ `ConSoleCommand` - 控制台命令 (Legacy mode)
- ✅ `TCPIPCommand` - TCP/IP 命令 (Legacy mode)

## 故障排除

### 問題 1: "pyvisa not installed"

```bash
uv pip install pyvisa pyvisa-py
```

### 問題 2: "Instrument not found"

檢查配置:
- 確認 `instruments.json` 存在
- 確認儀器 ID 正確
- 確認 `enabled: true`

### 問題 3: "Connection failed"

- 檢查儀器地址是否正確
- 檢查網路連線
- 檢查 VISA 驅動是否安裝
- 嘗試使用模擬模式測試邏輯

### 問題 4: subprocess 模式仍然使用舊路徑

確認 `sys.path` 包含正確的目錄:

```python
# measurement_service.py
script_path = "./src/lowsheen_lib/DAQ973A_test.py"
# 確保相對於 backend 目錄
```

## 最佳實踐

1. **優先使用模擬模式開發**: 先在模擬模式下驗證邏輯,再連接硬體
2. **連線池重用**: 避免頻繁連線/斷線,使用 connection pool
3. **錯誤處理**: 所有 instrument 操作都應該 try/catch
4. **類型安全**: 使用 Pydantic 驗證所有參數
5. **日誌記錄**: 使用 `self.logger` 記錄關鍵操作
6. **向後兼容**: 保持 `execute_command()` 接口與 PDTool4 兼容

## 參考資料

- [儀器配置範例](./instruments.example.json)
- [測試腳本](./scripts/test_instrument_drivers.py)
- [DAQ973A 驅動器](./app/services/instruments/daq973a.py)
- [MODEL2303 驅動器](./app/services/instruments/model2303.py)
- [PyVISA 文檔](https://pyvisa.readthedocs.io/)
