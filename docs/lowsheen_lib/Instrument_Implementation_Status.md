# 儀器服務實現狀態比對

**文檔版本**: v1.0
**更新日期**: 2026-02-04
**專案**: WebPDTool - PDTool4 重構專案

---

## 📊 總覽

本文檔比對 PDTool4 lowsheen_lib 原始儀器驅動與 WebPDTool 後端服務的實現狀態。

**統計資訊:**
- ✅ **已實現**: 15 個儀器服務
- ❌ **待實現**: 11 個儀器/模組
- 📋 **特殊模組**: 3 個通訊協定文檔
- 📈 **完成度**: 57.7% (15/26)

---

## ✅ 已實現的儀器服務

以下儀器驅動已在 WebPDTool 中完成重構，位於 `backend/app/services/instruments/` 目錄。

### 實現清單

| # | 服務檔案 | 對應文檔 | 儀器型號 | 類型 | 通訊協定 | 狀態 |
|---|---------|---------|---------|------|----------|------|
| 1 | `a2260b.py` | `2260B_API_Analysis.md` | Keithley 2260B | 可程控直流電源 | GPIB/USB/LAN | ✅ 已實現 |
| 2 | `a34970a.py` | `34970A_API_Analysis.md` | Agilent 34970A | 數據採集/切換單元 | GPIB/LAN | ✅ 已實現 |
| 3 | `daq6510.py` | `DAQ6510_API_Analysis.md` | Keithley DAQ6510 | 數據採集系統 | USB/LAN | ✅ 已實現 |
| 4 | `daq973a.py` | `DAQ973A_test_API_Analysis.md` | Keysight DAQ973A | 數據採集單元 | USB/LAN | ✅ 已實現 |
| 5 | `it6723c.py` | `IT6723C_API_Analysis.md` | ITECH IT6723C | 可程控直流電源 | USB/LAN | ✅ 已實現 |
| 6 | `keithley2015.py` | `Keithley2015_API_Analysis.md` | Keithley 2015 | 6.5 位數位萬用表 | GPIB/USB | ✅ 已實現 |
| 7 | `mdo34.py` | `MDO34_API_Analysis.md` | Tektronix MDO34 | 混合域示波器 | USB/LAN | ✅ 已實現 |
| 8 | `model2303.py` | `2303_API_Analysis.md` | Keithley 2303 | 電源供應器 | GPIB/USB/LAN | ✅ 已實現 |
| 9 | `model2306.py` | `2306_API_Analysis.md` | Keithley 2306 | 雙通道電池模擬器 | GPIB/USB | ✅ 已實現 |
| 10 | `psw3072.py` | `PSW3072_API_Analysis.md` | GW Instek PSW3072 | 可程控切換式電源 | USB/LAN | ✅ 已實現 |
| 11 | `aps7050.py` | `APS7050_API_Analysis.md` | GW Instek APS-7050 | AC/DC 電源 + DMM | VISA/SCPI | ✅ Phase 2 |
| 12 | `n5182a.py` | `Agilent_N5182A_API_Analysis.md` | Agilent N5182A MXG | 訊號產生器 | GPIB/VISA | ✅ Phase 2 |
| 13 | `analog_discovery_2.py` | `AnalogDiscovery2_API_Analysis.md` | Digilent AD2 | USB 多功能儀器 | USB (WaveForms SDK) | ✅ Phase 2 |
| 14 | `ftm_on.py` | `FTM_On_API_Analysis.md` | FTM Mode Control | 測試模式控制 | ADB/Subprocess | ✅ Phase 2 |
| 15 | `base.py` | - | BaseInstrument | 抽象基類 | - | ✅ 已實現 |

### 已實現功能特性

#### 電源供應器類 (6 個)
- ✅ Keithley 2260B - 單通道可程控電源
- ✅ Keithley 2303 - 標準電源供應器
- ✅ Keithley 2306 - 雙通道電池/充電模擬器
- ✅ ITECH IT6723C - 大功率可程控電源
- ✅ GW Instek PSW3072 - 切換式電源供應器

#### 數據採集類 (3 個)
- ✅ Agilent 34970A - 多功能數據採集單元
- ✅ Keithley DAQ6510 - 高精度數據記錄系統
- ✅ Keysight DAQ973A - 模組化數據採集系統

#### 量測儀器類 (2 個)
- ✅ Keithley 2015 - 高精度數位萬用表 (DMM)
- ✅ Tektronix MDO34 - 混合域示波器 (時域/頻域)

---

## ❌ 待實現的儀器/模組

以下儀器驅動在 PDTool4 中存在，但尚未在 WebPDTool 中實現。

### 待實現清單

| # | 文檔名稱 | 儀器型號/類型 | 類型 | 通訊協定 | 主要功能 | 優先級 |
|---|---------|--------------|------|----------|----------|--------|
| ~~1~~ | ~~`APS7050_API_Analysis.md`~~ | ~~GW Instek APS-7050~~ | ~~AC/DC 電源 + DMM~~ | ~~VISA/SCPI~~ | ~~AC/DC 電源 + 內建 DMM + 繼電器控制~~ | ~~🔴 高~~ ✅ |
| ~~2~~ | ~~`Agilent_N5182A_API_Analysis.md`~~ | ~~Agilent N5182A MXG~~ | ~~訊號產生器~~ | ~~GPIB/VISA~~ | ~~CW/ARB 模式訊號產生~~ | ~~🟡 中~~ ✅ |
| ~~3~~ | ~~`AnalogDiscovery2_API_Analysis.md`~~ | ~~Digilent AD2~~ | ~~USB 多功能儀器~~ | ~~USB (WaveForms SDK)~~ | ~~示波器/函數產生器/數位 I/O/阻抗分析~~ | ~~🟡 中~~ ✅ |
| 4 | `CMW100_API_Analysis.md` | R&S CMW100 | 無線通訊測試儀 | TCPIP/GPIB | Bluetooth/WiFi/LTE 射頻測量 | 🟢 低 |
| 5 | `ComPortCommand_API_Analysis.md` | 通用 COM Port | 通用串口介面 | Serial | 通用串口命令執行 | 🔴 高 |
| 6 | `ConSoleCommand_API_Analysis.md` | Console Command | 控制台命令 | Console/Shell | 系統命令執行器 | 🟡 中 |
| ~~7~~ | ~~`FTM_On_API_Analysis.md`~~ | ~~FTM Mode Control~~ | ~~測試模式控制~~ | ~~DUT 特定~~ | ~~Factory Test Mode 啟動~~ | ~~🟡 中~~ ✅ |
| 8 | `L6MPU_POSssh_cmd_API_Analysis.md` | L6 MPU Position | MPU 控制器 | SSH | MPU 位置控制 (SSH) | 🟢 低 |
| 9 | `L6MPU_ssh_cmd_API_Analysis.md` | L6 MPU General | MPU 控制器 | SSH | MPU 一般控制 (SSH) | 🟢 低 |
| 10 | `L6MPU_ssh_comport_API_Analysis.md` | L6 MPU COM | MPU 控制器 | SSH + Serial | MPU 串口控制 (混合) | 🟢 低 |
| 11 | `PEAK_API_Analysis.md` | PEAK CAN | CAN 總線介面 | CAN Bus | CAN 總線通訊 | 🟢 低 |
| 12 | `RF_Tool_API_Analysis.md` | RF Test Tool | 射頻測試工具 | 多種協定 | RF 測試工具集 | 🟢 低 |
| 13 | `TCPIPCommand_API_Analysis.md` | 通用 TCP/IP | 通用網路介面 | TCP/IP Socket | 通用網路命令執行 | 🔴 高 |
| 14 | `Wait_test_API_Analysis.md` | Wait/Delay Test | 測試延遲 | N/A | 測試步驟間延遲/等待 | 🟡 中 |
| 15 | `smcv100b_API_Analysis.md` | SMC V100B | SMC 控制器 | 未知 | SMC 設備控制 | 🟢 低 |

### 優先級說明

#### 🔴 高優先級 (2 個)
**建議優先實現，影響範圍廣或使用頻率高**

1. **ComPortCommand** - 通用串口介面
   - 可支援多種自定義串口設備
   - 是許多測試項目的基礎通訊模組
   - 實現難度: 中等

2. **TCPIPCommand** - 通用 TCP/IP 介面
   - 支援網路設備的通用控制
   - 現代化儀器常用的通訊方式
   - 實現難度: 中等

~~3. **APS7050** - AC/DC 電源 + DMM~~ ✅ 已實現
   - 結合電源、DMM 和繼電器三合一功能
   - 功能豐富，適用於複雜測試場景
   - 實現難度: 高 (功能複雜)

#### 🟡 中優先級 (3 個)
**常見測試場景需要的儀器或功能模組**

~~4. **Agilent N5182A** - 訊號產生器~~ ✅ 已實現
   - 射頻測試的核心設備
   - CW 和 ARB 模式支援
   - 實現難度: 中等

~~5. **AnalogDiscovery2** - USB 多功能儀器~~ ✅ 已實現
   - 成本低廉的桌面測試解決方案
   - 多功能整合 (示波器/波形產生器/數位 I/O)
   - 實現難度: 高 (需整合 WaveForms SDK)

6. **ConSoleCommand** - 控制台命令
   - 執行系統級命令和腳本
   - 提供測試流程的靈活性
   - 實現難度: 低

7. **Wait_test** - 測試延遲
   - 測試步驟間的延遲控制
   - 簡單但實用的功能
   - 實現難度: 低

~~8. **FTM_On** - FTM 模式控制~~ ✅ 已實現
   - 啟動 DUT 的 Factory Test Mode
   - 特定產品測試需要
   - 實現難度: 中等 (依賴 DUT 規格)

#### 🟢 低優先級 (8 個)
**特定產品線專用或較少使用的功能**

9-15. **L6 MPU 系列** (3 個)、**PEAK CAN**、**RF_Tool**、**CMW100**、**smcv100b**
   - 特定產品線專用儀器
   - 使用場景有限
   - 可依實際需求再實現

---

## 📋 特殊模組 (非儀器驅動)

以下文檔描述的是通訊協定或基礎設施，而非儀器驅動程式。

| # | 文檔名稱 | 類型 | 說明 | 狀態 |
|---|---------|------|------|------|
| 1 | `Bootloader_Protocol_API_Reference.md` | 通訊協定 | VCU Bootloader 通訊協定規範 | 📖 文檔 |
| 2 | `Bootloader_Protocol_README.md` | 通訊協定 | VCU Bootloader 使用指南 | 📖 文檔 |
| 3 | `proto_utils_API_Reference.md` | 通訊協定 | VCU UDP 通訊 API 參考 | 📖 文檔 |
| 4 | `proto_utils_Design_Guide.md` | 通訊協定 | VCU 通訊設計指南 | 📖 文檔 |
| 5 | `proto_utils_README.md` | 通訊協定 | VCU 通訊模組說明 | 📖 文檔 |
| 6 | `remote_instrument_API_Analysis.md` | 基礎設施 | 儀器連接管理器 | ✅ 已重構 |

### 說明

- **Bootloader Protocol** - VCU (Vehicle Control Unit) 的 Bootloader 通訊協定
  - 用於車輛控制單元的韌體更新
  - 基於 Protocol Buffers 和 UDP
  - 特定產品線專用

- **proto_utils** - VCU 通訊工具庫
  - UDP 封包管理
  - CRC32 校驗
  - 馬達控制命令介面
  - 特定產品線專用

- **remote_instrument** - 儀器連接管理器
  - 原 PDTool4 的儀器連接抽象層
  - 在 WebPDTool 中已重構為 `InstrumentManager`
  - 位於 `backend/app/services/instrument_manager.py`

---

## 🎯 建議實現順序

### Phase 1 - 通用介面層 (基礎架構)
**目標**: 建立可重用的通訊介面，為後續儀器實現打基礎

| 順序 | 模組 | 預估工時 | 依賴項 | 效益 |
|-----|------|---------|-------|------|
| 1 | `ComPortCommand` | 2-3 天 | `serial` 庫 | 支援多種串口設備 |
| 2 | `TCPIPCommand` | 2-3 天 | `socket` 庫 | 支援網路設備通訊 |
| 3 | `ConSoleCommand` | 1-2 天 | `subprocess` | 執行系統命令 |
| 4 | `Wait_test` | 0.5 天 | `asyncio` | 測試流程延遲控制 |

**Phase 1 里程碑**: 完成通用介面，可支援自定義設備接入

---

### Phase 2 - 常用測試儀器 (擴充儀器庫)
**目標**: 實現常用的測試儀器，提升測試覆蓋率

| 順序 | 模組 | 預估工時 | 依賴項 | 效益 |
|-----|------|---------|-------|------|
| 5 | `APS7050` | 3-4 天 | PyVISA | AC/DC 電源 + DMM 三合一 |
| 6 | `Agilent_N5182A` | 2-3 天 | PyVISA | 射頻訊號產生 |
| 7 | `AnalogDiscovery2` | 4-5 天 | WaveForms SDK | 低成本多功能儀器 |
| 8 | `FTM_On` | 2-3 天 | DUT 規格 | FTM 模式啟動 |

**Phase 2 里程碑**: 覆蓋 80% 常見測試場景

---

### Phase 3 - 特殊應用儀器 (按需實現)
**目標**: 依據實際專案需求，逐步實現特定儀器

| 順序 | 模組 | 預估工時 | 依賴項 | 說明 |
|-----|------|---------|-------|------|
| 9 | `CMW100` | 5-7 天 | RsInstrument | 無線通訊測試 (BT/WiFi/LTE) |
| 10 | `RF_Tool` | 3-4 天 | 待確認 | RF 測試工具集 |
| 11 | `L6MPU` 系列 | 4-5 天 | paramiko (SSH) | MPU 控制器系列 |
| 12 | `PEAK_API` | 3-4 天 | python-can | CAN 總線通訊 |
| 13 | `smcv100b` | 2-3 天 | 待確認 | SMC 控制器 |

**Phase 3 策略**: 依實際專案需求，按優先順序實現

---

## 🔧 技術實現考量

### 1. 架構設計原則

#### 統一介面
所有儀器服務繼承自 `BaseInstrument` 抽象基類:

```python
# backend/app/services/instruments/base.py
from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseInstrument(ABC):
    """Base class for all instrument drivers"""

    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to instrument"""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection"""
        pass

    @abstractmethod
    async def execute_command(self, command: str, params: Dict[str, Any]) -> Any:
        """Execute instrument-specific command"""
        pass

    @abstractmethod
    async def reset(self) -> None:
        """Reset instrument to default state"""
        pass
```

#### 異步支援
所有儀器操作使用 `async/await` 模式，避免阻塞事件循環:

```python
async def measure_voltage(self, channel: int) -> float:
    """Non-blocking voltage measurement"""
    result = await self.instrument.query_async(f'MEAS:VOLT? (@{channel})')
    return float(result)
```

#### 錯誤處理
統一的錯誤處理和重試機制:

```python
from app.core.exceptions import InstrumentConnectionError, InstrumentTimeoutError

try:
    result = await instrument.execute_command(cmd, params)
except TimeoutError:
    raise InstrumentTimeoutError(f"Timeout: {instrument.name}")
except ConnectionError:
    raise InstrumentConnectionError(f"Connection lost: {instrument.name}")
```

---

### 2. 通訊協定整合

#### PyVISA (GPIB/USB/LAN)
適用於: 大部分標準測試儀器

```python
import pyvisa
from pyvisa import ResourceManager

rm = ResourceManager()
instrument = rm.open_resource('TCPIP0::192.168.1.100::5025::SOCKET')
instrument.timeout = 5000  # 5 seconds
```

#### pySerial (COM Port)
適用於: 串口設備

```python
import serial

port = serial.Serial(
    port='COM3',
    baudrate=115200,
    timeout=1.0
)
```

#### Socket (Raw TCP/IP)
適用於: 自定義網路協定

```python
import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('192.168.1.100', 5025))
sock.settimeout(5.0)
```

#### SSH (遠程命令)
適用於: L6 MPU 系列

```python
import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('192.168.1.100', username='user', password='pass')
stdin, stdout, stderr = client.exec_command('command')
```

#### CAN Bus
適用於: PEAK CAN

```python
import can

bus = can.interface.Bus(channel='PCAN_USBBUS1', bustype='pcan')
msg = can.Message(arbitration_id=0x123, data=[0x11, 0x22, 0x33])
bus.send(msg)
```

---

### 3. 配置管理

#### 儀器配置檔 (JSON/YAML)
取代原 PDTool4 的 `test_xml.ini`:

```yaml
# config/instruments.yaml
instruments:
  PSW3072_1:
    type: psw3072
    address: TCPIP0::192.168.1.100::5025::SOCKET
    timeout: 5000

  Keithley2015_1:
    type: keithley2015
    address: ASRL2::INSTR
    baudrate: 115200
    stopbits: 1

  APS7050_1:
    type: aps7050
    address: GPIB0::9::INSTR
```

#### 動態載入
`InstrumentManager` 動態載入儀器配置:

```python
# backend/app/services/instrument_manager.py
class InstrumentManager:
    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self.instruments = {}

    async def get_instrument(self, name: str) -> BaseInstrument:
        if name not in self.instruments:
            inst_config = self.config['instruments'][name]
            inst_class = self._get_instrument_class(inst_config['type'])
            self.instruments[name] = inst_class(inst_config)
            await self.instruments[name].connect()

        return self.instruments[name]
```

---

### 4. 測試策略

#### 單元測試
每個儀器服務需包含單元測試:

```python
# tests/test_instruments/test_aps7050.py
import pytest
from app.services.instruments.aps7050 import APS7050

@pytest.mark.asyncio
async def test_aps7050_voltage_measurement():
    instrument = APS7050({
        'address': 'GPIB0::9::INSTR',
        'timeout': 5000
    })

    await instrument.connect()
    voltage = await instrument.measure_voltage(channel=101, type='DC')
    assert isinstance(voltage, float)
    await instrument.disconnect()
```

#### 模擬儀器
開發階段使用模擬儀器:

```python
# app/services/instruments/mock.py
class MockInstrument(BaseInstrument):
    """Mock instrument for testing without hardware"""

    async def execute_command(self, command: str, params: Dict) -> Any:
        # Return fake data
        if command == 'measure_voltage':
            return 12.345
        return None
```

#### 整合測試
完整的測試流程測試:

```python
@pytest.mark.integration
async def test_full_test_sequence():
    # Simulate complete test from TestMain.vue
    session = await create_test_session(project_id=1, station_id=1)
    results = await run_all_tests(session.id)
    assert all(r.result in ['PASS', 'FAIL'] for r in results)
```

---

## 📈 實現進度追蹤

### 當前狀態 (2026-02-04)

```
Progress: [███████████████░░░░░░░] 57.7%

已完成: 15/26
待實現: 11/26
```

### 里程碑

- [x] **M0** - 基礎架構 (BaseInstrument) ✅ 已完成
- [x] **M1** - 電源供應器類 (6/6) ✅ 已完成
- [x] **M2** - 數據採集類 (3/3) ✅ 已完成
- [x] **M3** - 量測儀器類 (2/2) ✅ 已完成
- [ ] **M4** - 通用介面層 (0/4) 🔜 Phase 1
- [x] **M5** - 常用測試儀器 (4/4) ✅ Phase 2 完成
- [ ] **M6** - 特殊應用儀器 (0/5) ⏳ Phase 3

---

## 🔗 相關文件

### WebPDTool 專案文件
- [CLAUDE.md](../../CLAUDE.md) - 專案總覽
- [README.md](../README.md) - 開發指南
- [測試計畫匯入](../../backend/scripts/import_testplan.py) - CSV 匯入工具

### LowSheen Library 文件
- [README.md](./README.md) - 儀器驅動總覽
- [各儀器 API 分析文件](./) - 詳細 API 規格

### 儀器分類索引

#### 已實現
- [Keithley 2260B](./2260B_API_Analysis.md)
- [Agilent 34970A](./34970A_API_Analysis.md)
- [Keithley DAQ6510](./DAQ6510_API_Analysis.md)
- [Keysight DAQ973A](./DAQ973A_test_API_Analysis.md)
- [ITECH IT6723C](./IT6723C_API_Analysis.md)
- [Keithley 2015](./Keithley2015_API_Analysis.md)
- [Tektronix MDO34](./MDO34_API_Analysis.md)
- [Keithley 2303](./2303_API_Analysis.md)
- [Keithley 2306](./2306_API_Analysis.md)
- [GW Instek PSW3072](./PSW3072_API_Analysis.md)

#### 待實現
- [GW Instek APS7050](./APS7050_API_Analysis.md) 🔴
- [Agilent N5182A](./Agilent_N5182A_API_Analysis.md) 🟡
- [Analog Discovery 2](./AnalogDiscovery2_API_Analysis.md) 🟡
- [R&S CMW100](./CMW100_API_Analysis.md) 🟢
- [通用 COM Port](./ComPortCommand_API_Analysis.md) 🔴
- [控制台命令](./ConSoleCommand_API_Analysis.md) 🟡
- [FTM 模式](./FTM_On_API_Analysis.md) 🟡
- [通用 TCP/IP](./TCPIPCommand_API_Analysis.md) 🔴
- [測試延遲](./Wait_test_API_Analysis.md) 🟡
- [L6 MPU 系列](./L6MPU_ssh_cmd_API_Analysis.md) 🟢
- [PEAK CAN](./PEAK_API_Analysis.md) 🟢
- [RF Tool](./RF_Tool_API_Analysis.md) 🟢
- [SMC V100B](./smcv100b_API_Analysis.md) 🟢

---

## 📝 更新記錄

| 版本 | 日期 | 作者 | 變更說明 |
|-----|------|------|---------|
| v1.0 | 2026-02-04 | Claude Code | 初始版本，完整比對 PDTool4 與 WebPDTool 實現狀態 |
| v1.1 | 2026-02-04 | Claude Code | Phase 2 完成: 新增 APS7050, N5182A, AD2, FTM_On 驅動 |

---

## 📧 聯絡資訊

如有疑問或建議，請聯繫開發團隊或在專案 Issue 追蹤系統中提出。

**專案倉庫**: WebPDTool
**文檔位置**: `docs/lowsheen_lib/Instrument_Implementation_Status.md`

---

*本文檔由 Claude Code 自動生成並維護*
