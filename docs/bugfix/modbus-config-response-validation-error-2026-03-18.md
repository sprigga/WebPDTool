# Modbus Config Response Validation Error (2026-03-18)

## 問題描述

`GET /api/modbus/stations/{station_id}/config` 回傳 500 Internal Server Error，後端 log 顯示：

```
fastapi.exceptions.ResponseValidationError: 4 validation errors:
  {'type': 'value_error', 'loc': ('response', 'ready_status_address'), 'msg': 'Value error, Hex address must start with 0x or 0X', 'input': '400001', ...}
  {'type': 'value_error', 'loc': ('response', 'read_sn_address'), 'msg': 'Value error, Hex address must start with 0x or 0X', 'input': '400002', ...}
  {'type': 'value_error', 'loc': ('response', 'test_status_address'), 'msg': 'Value error, Hex address must start with 0x or 0X', 'input': '400001', ...}
  {'type': 'value_error', 'loc': ('response', 'test_result_address'), 'msg': 'Value error, Hex address must start with 0x or 0X', 'input': '400002', ...}
```

同時，`POST /api/modbus/configs` 也回傳 422 Unprocessable Entity（建立時也觸發同樣驗證邏輯）。

## 根本原因

**`ModbusConfigResponse` 繼承了 `ModbusConfigBase`，而 `ModbusConfigBase` 的 `field_validator` 強制要求地址欄位必須以 `0x` 開頭。**

```python
# backend/app/schemas/modbus.py
class ModbusConfigBase(BaseModel):
    ready_status_address: str = Field(default="0x0013", ...)
    ...

    @field_validator('ready_status_address', 'read_sn_address', ...)
    @classmethod
    def validate_hex_string(cls, v: str) -> str:
        if not (v.startswith('0x') or v.startswith('0X')):
            raise ValueError('Hex address must start with 0x or 0X')  # ← 問題所在
        ...

class ModbusConfigResponse(ModbusConfigBase):  # ← 繼承了父類別 validator
    id: int
    station_id: int
    model_config = {"from_attributes": True}
```

資料庫中儲存的地址格式為十進位字串（如 `400001`、`400002`），而非 hex 格式（如 `0x61A1`）。

**Pydantic v2 在 ORM → Schema 轉換（`from_attributes=True`）時也會執行 `field_validator`**，導致從資料庫讀取資料後反序列化失敗，丟出 `ResponseValidationError`。

## 除錯過程

1. **看 log** — 錯誤訊息明確指出 `ResponseValidationError`，位置在 `('response', 'ready_status_address')`，輸入值是 `'400001'`
2. **定位 schema** — 追蹤 `backend/app/schemas/modbus.py`，找到 `ModbusConfigBase.validate_hex_string`
3. **確認繼承關係** — `ModbusConfigResponse(ModbusConfigBase)` 繼承了 validator，而 `from_attributes=True` 使 ORM 讀取時也觸發驗證
4. **確認資料格式** — 資料庫中的地址欄位儲存為十進位字串（`400001`），是舊有格式

## 修正方式

修改 `backend/app/schemas/modbus.py` 中的 `validate_hex_string`，讓它同時接受：
- `0x` 或 `0X` 開頭的 hex 字串（新格式）
- 純十進位數字字串（舊格式，資料庫中的既有資料）

```python
# 修改前
@field_validator(...)
@classmethod
def validate_hex_string(cls, v: str) -> str:
    """Validate hex string format"""
    if not (v.startswith('0x') or v.startswith('0X')):
        raise ValueError('Hex address must start with 0x or 0X')
    try:
        int(v, 16)
    except ValueError:
        raise ValueError(f'Invalid hex string: {v}')
    return v

# 修改後
@field_validator(...)
@classmethod
def validate_hex_string(cls, v: str) -> str:
    """Validate hex string format. Accepts 0x-prefixed hex or plain decimal strings."""
    if v.startswith('0x') or v.startswith('0X'):
        try:
            int(v, 16)
        except ValueError:
            raise ValueError(f'Invalid hex string: {v}')
    else:
        # Accept plain decimal strings stored by legacy data (e.g. "400001")
        if not v.isdigit():
            raise ValueError('Hex address must start with 0x or 0X, or be a plain decimal number')
    return v
```

## 修正後驗證

重啟 backend container 後確認：

```bash
docker-compose restart backend
docker-compose logs --tail=5 backend
# → INFO: Application startup complete.
# → INFO: Uvicorn running on http://0.0.0.0:9100
```

`GET /api/modbus/stations/{station_id}/config` 不再回傳 500。

## 影響範圍

- `backend/app/schemas/modbus.py` — `ModbusConfigBase.validate_hex_string`

## 相關端點

- `GET /api/modbus/stations/{station_id}/config` — 原本回傳 500
- `GET /api/modbus/configs` — 同樣受影響（回傳 list 時也會觸發）
- `GET /api/modbus/configs/{config_id}` — 同樣受影響
