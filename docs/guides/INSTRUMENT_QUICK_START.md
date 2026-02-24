# 儀器驅動器快速入門

## 🚀 5 分鐘開始使用

### 1. 安裝依賴 (1 分鐘)

```bash
cd /home/ubuntu/python_code/WebPDTool/backend
uv pip install pydantic pydantic-settings pyvisa pyvisa-py pyserial
```

### 2. 運行測試 (1 分鐘)

```bash
# 模擬模式 - 無需硬體
uv run python scripts/test_instrument_drivers.py
```

**預期輸出**:
```
✓ Configuration loading
✓ DAQ973A: All tests passed
✓ MODEL2303: All tests passed
Test suite completed successfully!
```

### 3. 配置儀器 (2 分鐘)

```bash
# 使用範例配置
cp instruments.example.json instruments.json

# 設定環境變數
export INSTRUMENTS_CONFIG_FILE=./instruments.json

# 或在 .env 文件中
echo "INSTRUMENTS_CONFIG_FILE=./instruments.json" >> .env
```

### 4. 使用驅動器 (1 分鐘)

```python
from app.services.instrument_executor import get_instrument_executor

async def measure():
    executor = get_instrument_executor()

    # 電壓測量
    result = await executor.execute_instrument_command(
        instrument_id="DAQ973A_1",
        params={
            'Item': 'VOLT',
            'Channel': '101',
            'Type': 'DC'
        },
        simulation=True  # 先使用模擬模式
    )
    print(f"Voltage: {result}V")

# 在 async 環境中執行
import asyncio
asyncio.run(measure())
```

---

## 📋 常用指令

### 開發測試

```bash
# 模擬模式測試
uv run python scripts/test_instrument_drivers.py

# 測試特定儀器 (編輯腳本)
uv run python -c "
import asyncio
from app.services.instrument_executor import get_instrument_executor

async def test():
    executor = get_instrument_executor()
    result = await executor.execute_instrument_command(
        'DAQ973A_1',
        {'Item': 'VOLT', 'Channel': '101', 'Type': 'DC'},
        simulation=True
    )
    print(result)

asyncio.run(test())
"
```

### 配置管理

```bash
# 檢查配置
python -c "
from app.core.instrument_config import get_instrument_settings
settings = get_instrument_settings()
for id, cfg in settings.list_instruments().items():
    print(f'{id}: {cfg.type} ({cfg.connection.type})')
"

# 驗證配置文件
python -c "
import json
with open('instruments.json') as f:
    config = json.load(f)
    print(f'Loaded {len(config[\"instruments\"])} instruments')
"
```

---

## 🔧 快速修復

### 問題: ModuleNotFoundError: pydantic

```bash
uv pip install pydantic pydantic-settings
```

### 問題: ModuleNotFoundError: pyvisa

```bash
uv pip install pyvisa pyvisa-py
```

### 問題: Instrument not found

1. 檢查 `instruments.json` 是否存在
2. 檢查環境變數 `INSTRUMENTS_CONFIG_FILE`
3. 檢查儀器 ID 是否正確

```bash
# 列出可用儀器
python -c "
from app.core.instrument_config import get_instrument_settings
print('Available instruments:')
for id in get_instrument_settings().list_instruments():
    print(f'  - {id}')
"
```

### 問題: Connection failed

**開發階段**: 使用模擬模式
```python
simulation=True  # 加入這個參數
```

**生產環境**: 檢查網路連線
```bash
# 測試網路連線
ping 192.168.1.10

# 測試 VISA 資源
python -c "
import pyvisa
rm = pyvisa.ResourceManager()
print(rm.list_resources())
"
```

---

## 📚 範例程式碼

### 範例 1: 電壓測量

```python
from app.services.instrument_executor import get_instrument_executor

async def measure_voltage():
    executor = get_instrument_executor()

    result = await executor.execute_instrument_command(
        instrument_id="DAQ973A_1",
        params={
            'Item': 'VOLT',
            'Channel': '101',
            'Type': 'DC'
        },
        simulation=True
    )

    print(f"Measured voltage: {result}V")
    return float(result)
```

### 範例 2: 電源設定

```python
async def set_power():
    executor = get_instrument_executor()

    result = await executor.execute_instrument_command(
        instrument_id="MODEL2303_1",
        params={
            'SetVolt': '12.0',
            'SetCurr': '2.5'
        },
        simulation=True
    )

    if result == '1':
        print("Power supply configured successfully")
    else:
        print(f"Configuration failed: {result}")
```

### 範例 3: 批次測量

```python
async def batch_measurements():
    executor = get_instrument_executor()

    channels = ['101', '102', '103', '104']
    results = []

    for channel in channels:
        result = await executor.execute_instrument_command(
            instrument_id="DAQ973A_1",
            params={
                'Item': 'VOLT',
                'Channel': channel,
                'Type': 'DC'
            },
            simulation=True
        )
        results.append((channel, float(result)))

    for ch, voltage in results:
        print(f"Channel {ch}: {voltage}V")
```

### 範例 4: 錯誤處理

```python
from app.services.instrument_connection import (
    InstrumentNotFoundError,
    InstrumentConnectionError,
    InstrumentCommandError
)

async def safe_measurement():
    executor = get_instrument_executor()

    try:
        result = await executor.execute_instrument_command(
            instrument_id="DAQ973A_1",
            params={'Item': 'VOLT', 'Channel': '101', 'Type': 'DC'},
            simulation=True
        )
        return float(result)

    except InstrumentNotFoundError as e:
        print(f"儀器未找到: {e}")
        return None

    except InstrumentConnectionError as e:
        print(f"連線失敗: {e}")
        return None

    except InstrumentCommandError as e:
        print(f"命令執行失敗: {e}")
        return None

    except ValueError as e:
        print(f"參數錯誤: {e}")
        return None
```

---

## 🎯 下一步

1. **閱讀完整文檔**: [INSTRUMENT_MIGRATION.md](../lowsheen_lib/INSTRUMENT_MIGRATION.md)
2. **查看範例配置**: [backend/instruments.example.json](../../backend/instruments.example.json)
3. **開發新驅動器**: 參考 `app/services/instruments/daq973a.py`
4. **整合到測試**: 修改 `measurement_service.py`

---

## 📞 支援

- **詳細指南**: [INSTRUMENT_MIGRATION.md](../lowsheen_lib/INSTRUMENT_MIGRATION.md)
- **完整報告**: [MIGRATION_SUMMARY.md](../lowsheen_lib/MIGRATION_SUMMARY.md)
- **測試腳本**: [backend/scripts/test_instrument_drivers.py](../../backend/scripts/test_instrument_drivers.py)

---

**快速檢查清單**:

- [ ] 安裝依賴
- [ ] 運行測試通過
- [ ] 配置儀器文件
- [ ] 理解範例程式碼
- [ ] 閱讀遷移指南

**祝開發順利!** 🎉
