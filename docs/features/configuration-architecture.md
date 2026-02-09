# Configuration Architecture

## Overview

WebPDTool uses a layered configuration system that separates concerns between environment-specific values, type-safe settings, and runtime behavior. This architecture enables flexible deployment across Docker containers and local development environments without code changes.

## Architecture Layers

```
┌─────────────────────────────────────────────────────────┐
│                  Configuration Layer                     │
├─────────────────────────────────────────────────────────┤
│  .env (User Editable)                                    │
│  └─ SCRIPTS_DIR=./scripts  ← Developer sets this        │
│                                                          │
│         ↓                                               │
│  config.py (Type-Safe Settings)                          │
│  └─ settings.SCRIPTS_DIR  ← Pydantic validates & loads  │
│                                                          │
│         ↓                                               │
│  implementations.py (Consumer)                           │
│  └─ OtherMeasurement.execute()  ← Uses resolved path    │
│     ├─ Reads settings.SCRIPTS_DIR                       │
│     ├─ Converts to absolute if needed                   │
│     ├─ Validates script exists (os.path.exists)         │
│     └─ Executes python3 script_path                     │
│                                                          │
│         ↓                                               │
│  Runtime Execution                                       │
│  └─ subprocess runs: python3 backend/scripts/test.py   │
└─────────────────────────────────────────────────────────┘
```

## Configuration Flow Chain

```
.env (user-defined values)
    ↓
backend/app/config.py (Pydantic BaseSettings)
    ↓
backend/app/measurements/implementations.py (consumes settings)
    ↓
Runtime behavior (script execution paths)
```

## Core Components

### 1. Environment Configuration (.env)

Located at `backend/.env`, this file contains user-defined environment variables:

```bash
# Scripts Directory Configuration
# 本地環境: ./scripts (相對於 backend 目錄)
# 容器環境: /app/scripts (Docker 內部路徑)
SCRIPTS_DIR=./scripts
```

### 2. Settings Module (backend/app/config.py)

Uses Pydantic's `BaseSettings` for type-safe configuration loading:

```python
class Settings(BaseSettings):
    # ✅ Added: Scripts Directory Configuration
    # 容器環境: /app/scripts (Docker 內部路徑)
    # 本地環境: ./scripts 或絕對路徑
    SCRIPTS_DIR: str = "./scripts"

    # Model config for Pydantic v2
    model_config = {"env_file": ".env", "case_sensitive": True, "extra": "ignore"}

# Global settings instance
settings = Settings()
```

#### Pydantic BaseSettings 自動載入機制

**是的，`.env` 檔案中的 `SCRIPTS_DIR` 可以自動被 `config.py` 讀取和代入。**

**工作原理：**

```python
# config.py Line 69: 關鍵配置
model_config = {"env_file": ".env", "case_sensitive": True, "extra": "ignore"}
```

這個配置告訴 Pydantic `BaseSettings`：

| 設定 | 說明 |
|------|------|
| `env_file: ".env"` | 從 `backend/.env` 檔案載入環境變數 |
| `case_sensitive: True` | 變數名稱區分大小寫 |
| `extra: "ignore"` | 忽略 .env 中未定義的變數 |

**載入順序（優先級）：**

```
優先級 1 (最高): 系統環境變數 (export SCRIPTS_DIR=/custom/path)
      ↓
優先級 2: .env 檔案中的值 (SCRIPTS_DIR=./scripts)
      ↓
優先級 3 (最低): config.py 中的預設值 (SCRIPTS_DIR: str = "./scripts")
```

**實際驗證：**

建立測試腳本驗證載入結果：

```python
# test_config_load.py
from app.config import settings

print(f"SCRIPTS_DIR from config: {settings.SCRIPTS_DIR}")
print(f"Type: {type(settings.SCRIPTS_DIR)}")
```

執行結果：
```
SCRIPTS_DIR from config: ./scripts
Type: <class 'str'>
```

**檔案對應關係：**

| 來源 | 變數名稱 | 實際值 |
|------|---------|--------|
| `.env` Line 50 | `SCRIPTS_DIR=./scripts` | `"./scripts"` |
| `config.py` Line 66 | `SCRIPTS_DIR: str = "./scripts"` | **被 .env 覆蓋** |
| `implementations.py` Line 113 | `settings.SCRIPTS_DIR` | `"./scripts"` (從 .env 讀取) |

### 3. Configuration Consumer (backend/app/measurements/implementations.py)

The `OtherMeasurement` class uses configuration for script execution:

```python
# Lines 113-122: Environment-aware path resolution
scripts_dir = settings.SCRIPTS_DIR

# If relative path, convert to absolute (relative to backend directory)
if not os.path.isabs(scripts_dir):
    # __file__ = backend/app/measurements/implementations.py
    # Need to go back to backend dir (up 3 levels)
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    scripts_dir = os.path.join(backend_dir, scripts_dir)

script_path = os.path.join(scripts_dir, f"{script_name}.py")
```

## Key Configuration Variables

| Variable | `.env` Value | `config.py` Default | Usage in `implementations.py` |
|----------|-------------|---------------------|-------------------------------|
| `SCRIPTS_DIR` | `./scripts` | `"./scripts"` | Lines 113-122: Resolves script paths |
| `REDIS_ENABLED` | `false` | `False` | Real-time log streaming (planned) |
| `LOG_LEVEL` | `INFO` | `"INFO"` | Logger configuration |

## Environment-Specific Behaviors

| Environment | `.env` SCRIPTS_DIR | Resolved Path Example | Use Case |
|-------------|-------------------|----------------------|----------|
| **Docker** | `/app/scripts` | `/app/scripts/test.py` | Container deployment |
| **Local Dev** | `./scripts` | `/home/ubuntu/python_code/WebPDTool/backend/scripts/test.py` | Development |
| **Custom** | `/opt/custom/scripts` | `/opt/custom/scripts/test.py` | Custom deployment |

## Path Resolution Strategy

### Three-Level Directory Traversal

The path resolution algorithm uses `os.path.dirname()` three times to navigate from:

```
implementations.py → measurements → app → backend
```

### Code Implementation

```python
# Line 119: Calculate backend directory
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

### Cross-Platform Compatibility

- Uses `os.path.isabs()` to detect absolute vs relative paths
- Uses `os.path.join()` for Windows/Linux path separator compatibility
- Supports both forward slashes and backslashes

## Error Handling Chain

### Fail-Fast Validation Pattern

Lines 128-134 implement early validation:

```python
# Check if script file exists
if not os.path.exists(script_path):
    error_msg = f"Script not found: {script_path} (scripts_dir: {scripts_dir})"
    self.logger.error(error_msg)
    return self.create_result(
        result="ERROR",
        error_message=error_msg
    )
```

### Validation Benefits

1. **Early Validation** - Checks file existence before subprocess creation
2. **Detailed Error Messages** - Includes both resolved path and original `scripts_dir`
3. **Graceful Degradation** - Returns `MeasurementResult` instead of raising exceptions

## Configuration Dependencies

```
implementations.py imports:
├─ from app.config import settings (line 16)
├─ from decimal import Decimal (line 5)
├─ from typing import Dict, Any, Optional (line 6)
├─ import asyncio (line 7)
├─ import random (line 8)
└─ import os (line 9) ← Used for path resolution
```

## Design Patterns

### 1. Dependency Injection Pattern

`implementations.py` injects `settings` as a dependency rather than hardcoding values:

```python
from app.config import settings

scripts_dir = settings.SCRIPTS_DIR
```

### 2. Environment-Aware Configuration

The system automatically adapts to deployment environment:

- **Docker**: Uses absolute paths like `/app/scripts`
- **Local**: Uses relative paths resolved from `__file__` location
- **No code changes required**: Configuration drives behavior

### 3. Pydantic Settings Pattern

`config.py` uses `BaseSettings` for:
- Type-safe configuration loading
- Environment variable validation
- Default value management
- Case-sensitive option handling

**Pydantic BaseSettings 核心特性：**

1. **自動環境變數對應**
   - Pydantic 會自動將 `SCRIPTS_DIR` 環境變數對應到 `Settings.SCRIPTS_DIR` 屬性
   - 無需手動編寫讀取程式碼，Pydantic 自動處理

2. **型別驗證**
   - 自動驗證環境變數型別是否符合定義
   - 型別錯誤會在啟動時立即報錯

3. **優先級管理**
   - 系統環境變數 > .env 檔案 > 預設值
   - 提供靈活的配置覆蓋機制

## Best Practices

### Adding New Configuration Variables

1. **Add to `.env`:**
   ```bash
   NEW_CONFIG=default_value
   ```

2. **Add to `config.py`:**
   ```python
   class Settings(BaseSettings):
       NEW_CONFIG: str = "default_value"
   ```

3. **Use in implementation:**
   ```python
   from app.config import settings
   value = settings.NEW_CONFIG
   ```

### 如何修改 SCRIPTS_DIR 設定

**方法 1：修改 .env 檔案（推薦）**
```bash
# backend/.env
SCRIPTS_DIR=/app/scripts  # Docker 環境
# 或
SCRIPTS_DIR=./scripts     # 本地開發
```

**方法 2：設定系統環境變數**
```bash
export SCRIPTS_DIR=/custom/path
python app/main.py
```

**方法 3：修改預設值（不推薦）**
```python
# config.py Line 66
SCRIPTS_DIR: str = "/app/scripts"  # 這是預設值，會被 .env 覆蓋
```

### 實際應用範例

**場景 1: 本地開發使用相對路徑**
```bash
# backend/.env
SCRIPTS_DIR=./scripts
```

**場景 2: Docker 容器使用絕對路徑**
```bash
# backend/.env
SCRIPTS_DIR=/app/scripts
```

**場景 3: 自訂腳本目錄**
```bash
# backend/.env
SCRIPTS_DIR=/opt/custom/scripts
```

### 驗證設定是否生效

在 `implementations.py` 中，腳本會記錄實際使用的路徑：

```python
# Line 124-125
self.logger.info(f"Executing Other script: {script_path}")
self.logger.info(f"Scripts directory: {scripts_dir}")
```

查看後端日誌可以看到：
```
INFO: Executing Other script: /home/ubuntu/python_code/WebPDTool/backend/scripts/test123.py
INFO: Scripts directory: /home/ubuntu/python_code/WebPDTool/backend/scripts
```

### Configuration Validation

Pydantic automatically validates types:
- Integer values: `int`
- String values: `str`
- Boolean values: `bool`
- List values: `List[str]`

### Custom Validators

Example from `config.py` (lines 40-46):

```python
@field_validator('CORS_ORIGINS', mode='before')
@classmethod
def parse_cors_origins(cls, v):
    """解析 CORS_ORIGINS 環境變數 (支援逗號分隔的字串)"""
    if isinstance(v, str):
        return [origin.strip() for origin in v.split(',')]
    return v
```

## Migration Notes

### From Hardcoded Paths to Configuration

**Before (hardcoded):**
```python
script_path = "/app/scripts/test.py"  # Docker-specific
```

**After (configurable):**
```python
scripts_dir = settings.SCRIPTS_DIR
if not os.path.isabs(scripts_dir):
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    scripts_dir = os.path.join(backend_dir, scripts_dir)
script_path = os.path.join(scripts_dir, f"{script_name}.py")
```

## Troubleshooting

### Script Not Found Errors

If you see "Script not found" errors:

1. Check `backend/.env` SCRIPTS_DIR value
2. Verify script files exist in the directory
3. Check logs for resolved path: `(scripts_dir: /path/to/scripts)`
4. Ensure relative paths are relative to `backend/` directory

### Docker vs Local Path Issues

**Docker containers:**
```bash
SCRIPTS_DIR=/app/scripts  # Absolute path inside container
```

**Local development:**
```bash
SCRIPTS_DIR=./scripts  # Relative to backend directory
```

### Permission Issues

Ensure script files are executable:
```bash
chmod +x backend/scripts/*.py
```

## Related Documentation

- [Measurement Implementation](./measurement-implementations.md) - How measurements use configuration
- [Environment Setup](../setup/environment-setup.md) - Complete environment configuration guide
- [Docker Deployment](../deployment/docker.md) - Docker-specific configuration

## Summary

The configuration architecture provides:

1. **Separation of Concerns**
   - Configuration logic in `config.py`
   - Business logic in `implementations.py`
   - Environment values in `.env`

2. **Flexibility**
   - Supports multiple deployment environments
   - No code changes needed for different paths
   - Easy to add new configuration variables

3. **Type Safety**
   - Pydantic validates configuration at startup
   - Type hints catch errors early
   - Custom validators for complex types

4. **Developer Experience**
   - Simple environment variable management
   - Clear error messages
   - Cross-platform compatibility

## Pydantic BaseSettings 自動載入總結

**✅ 是的，`.env` 檔案中的 `SCRIPTS_DIR` 會自動代入到 `config.py`**

**關鍵要點：**
1. Pydantic 的 `BaseSettings` 自動處理環境變數載入
2. `model_config = {"env_file": ".env"}` 啟用 .env 檔案讀取
3. 環境變數優先級高於預設值
4. 無需手動編寫讀取程式碼，Pydantic 自動處理

**載入機制：**
```
.env 檔案 (SCRIPTS_DIR=./scripts)
    ↓
Pydantic BaseSettings 自動載入
    ↓
Settings 物件 (settings.SCRIPTS_DIR)
    ↓
應用程式使用 (implementations.py)
```

**檔案位置對應：**
- `.env` 檔案: `backend/.env`
- `config.py`: `backend/app/config.py`
- 預設工作目錄: `backend/` 目錄

因此 Pydantic 會正確找到 `backend/.env` 檔案並載入其中的 `SCRIPTS_DIR` 設定。
