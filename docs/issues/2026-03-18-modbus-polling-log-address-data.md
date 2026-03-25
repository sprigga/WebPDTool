# Issue: Modbus 輪詢時 backend log 未顯示 server address 和 register 資料

**日期：** 2026-03-18
**影響範圍：** `backend/app/services/modbus/modbus_listener.py`
**嚴重性：** 可觀察性（不影響功能，但無法從 log 追蹤 Modbus 通訊內容）
**狀態：** ✅ 已修正

---

## 問題描述

Modbus listener 每秒輪詢 Modbus server 的 holding register 以確認 DUT 是否就緒，但 backend log 在正常運作期間**完全沒有輸出**連線位址或 register 資料，只有以下訊息：

```
2026-03-18 16:49:22 - INFO - [modbus_listener:93:start] Modbus listener started for station 3
2026-03-18 16:50:10 - INFO - [modbus_listener:188:_run_async] Listener task for station 3 cancelled gracefully
```

輪詢結果只記錄在 `DEBUG` 等級（`cycle_count`），生產環境無法看到：

```python
logger.debug(f"Device {self.device_id} listening cycle {self.cycle_count}")
```

### 症狀

- 從 backend log 無法確認是否已成功連線到 Modbus server
- 無法確認每次輪詢讀取的 register address 和回傳值
- 必須依賴外部 Modbus tool 的 log（Tx/Rx raw bytes）才能判斷通訊內容
- 當發生問題時（如 register 值異常），難以快速定位是 backend 讀錯 address 還是 device 回傳錯誤值

---

## 除錯過程

### 1. 比對兩邊 log 確認連線正常

從 Modbus tool log 可以看到 raw TCP 封包：

```
'127.0.0.1:34780' Rx: 00 01 00 00 00 06 01 03 00 00 00 01
'127.0.0.1:34780' Tx: 00 01 00 00 00 05 01 03 02 00 00
```

解碼 MBAP Header + PDU：

| 欄位 | Bytes | 值 | 說明 |
|------|-------|----|------|
| Transaction ID | `00 01` | 1 | 請求序號 |
| Protocol ID | `00 00` | 0 | Modbus TCP |
| Length | `00 06` | 6 | 後續 PDU 長度 |
| Unit ID | `01` | 1 | Device ID |
| Function Code | `03` | FC3 | Read Holding Registers |
| Start Address | `00 00` | 0 | Register[0] |
| Quantity | `00 01` | 1 | 讀 1 個 register |

回傳：FC3 + 2 bytes data + `00 00` → register[0] = `0x0000`（DUT 未就緒）

### 2. 確認 backend 讀取的 address 來源

`_read_registers_async()` 透過 `_str2hex()` 將設定檔的 ModbusTools 格式 address（如 `0x400001`）轉換為 pymodbus wire address：

```python
def _str2hex(self, hex_str: str) -> int:
    val = int(hex_str, 16)
    if val >= 0x400001:
        return (val & 0xFFFF) - 1  # 0x400001 -> 0x0000
    return val
```

`0x400001` → wire address `0x0000`，與 Modbus tool log 的 `00 00` 吻合，確認 address 正確。

### 3. 找出 log 缺失的根本原因

`_read_registers_async()` 在成功路徑上只有 return，沒有任何 INFO log：

```python
# 修正前
return rr.registers[0] if rr.registers else None
```

每秒一次的輪詢結果在 INFO 等級完全無聲，只能靠外部工具確認通訊狀態。

---

## 修正方式

在 `_read_registers_async()` 的成功路徑加入 `INFO` 等級 log，輸出 server 位址、register address（十六進位）和回傳值（十六進位 + 十進位）：

**檔案：** `backend/app/services/modbus/modbus_listener.py`，`_read_registers_async()` 方法

```python
# 修正前
return rr.registers[0] if rr.registers else None

# 修正後
value = rr.registers[0] if rr.registers else None
if value is not None:
    logger.info(
        f"[Modbus] {self.server_host}:{self.server_port} "
        f"ReadHoldingReg addr=0x{address:04X} count={count} "
        f"-> 0x{value:04X} ({value})"
    )
else:
    logger.info(
        f"[Modbus] {self.server_host}:{self.server_port} "
        f"ReadHoldingReg addr=0x{address:04X} count={count} -> (no data)"
    )
return value
```

---

## 修正後 Log 輸出範例

**DUT 未就緒（register = 0）：**
```
2026-03-18 16:55:01 - INFO - [modbus_listener] [Modbus] 127.0.0.1:502 ReadHoldingReg addr=0x0000 count=1 -> 0x0000 (0)
```

**DUT 就緒（register = 1），觸發讀取 SN：**
```
2026-03-18 16:55:02 - INFO - [modbus_listener] [Modbus] 127.0.0.1:502 ReadHoldingReg addr=0x0000 count=1 -> 0x0001 (1)
2026-03-18 16:55:02 - INFO - [modbus_listener] SN Register values = [...]
2026-03-18 16:55:02 - INFO - [modbus_listener] SN value = XXXXXXXXXX
```

**連線失敗：**
```
2026-03-18 16:55:01 - ERROR - [modbus_listener] Cannot connect to Modbus server 127.0.0.1:502
```

---

## 對照 Modbus Tool Log 的讀法

| Modbus Tool | Backend Log | 說明 |
|-------------|-------------|------|
| `Rx: ... 01 03 00 00 00 01` | `addr=0x0000 count=1` | FC3 請求，address 0，讀 1 個 |
| `Tx: ... 01 03 02 00 00` | `-> 0x0000 (0)` | 回傳 2 bytes，值為 0 |
| `Tx: ... 01 03 02 00 01` | `-> 0x0001 (1)` | 回傳值為 1，DUT 就緒 |

---

## 部署步驟

```bash
docker-compose build --no-cache backend
docker-compose up -d backend
```

---

## 注意事項

- 每秒輪詢一次，`INFO` 等級 log 量較大，若 log 量造成問題可將此行改為 `DEBUG` 並在需要時臨時調整 log level
- 僅修改 `_read_registers_async()` 的成功路徑；錯誤路徑（`isError()`、`ModbusException`）已有對應的 `WARNING`/`ERROR` log
- `write_test_result()` 和 `_read_sn_async()` 已有足夠的 log，本次未修改
