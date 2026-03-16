# Alembic Migration asyncmy ImportError

**日期:** 2026-03-13
**狀態:** ✅ 已解決
**嚴重性:** 高 - 影響 Docker 容器啟動時的自動資料庫遷移

## 問題描述

後端 Docker 容器啟動時，自動執行的 Alembic 資料庫遷移失敗，出現以下錯誤：

```
ImportError: cannot import name 'DATABASE_URL' from 'app.core.database' (/app/app/core/database.py)
```

隨後，在修正此問題後又出現：

```
ModuleNotFoundError: No module named 'pymysql'
```

### 完整錯誤日誌

```
2026-03-13 16:50:18.250 | Traceback (most recent call last):
2026-03-13 16:50:18.250 |   File "/app/.venv/bin/alembic", line 10, in <module>
2026-03-13 16:50:18.250 |     sys.exit(main())
2026-03-13 16:50:18.250 |              ^^^^^^
2026-03-13 16:50:18.250 |   File "/app/.venv/lib/python3.11/site-packages/alembic/config.py", line 1033, in main
2026-03-13 16:50:18.250 |     CommandLine(prog=prog).main(argv=argv)
2026-03-13 16:50:18.250 |   File "/app/.venv/lib/python3.11/site-packages/alembic/config.py", line 1023, in main
2026-03-13 16:50:18.250 |     self.run_cmd(cfg, options)
2026-03-13 16:50:18.250 |   File "/app/.venv/lib/python3.11/site-packages/alembic/config.py", line 957, in run_cmd
2026-03-13 16:50:18.250 |     fn(
2026-03-13 16:50:18.250 |   File "/app/.venv/lib/python3.11/site-packages/alembic/command.py", line 483, in upgrade
2026-03-13 16:50:18.250 |     script.run_env()
2026-03-13 16:50:18.251 |   File "/app/.venv/lib/python3.11/site-packages/alembic/script/base.py", line 545, in run_env
2026-03-13 16:50:18.251 |     util.load_python_file(self.dir, "env.py")
2026-03-13 16:50:18.251 |   File "/app/.venv/lib/python3.11/site-packages/alembic/util/pyfiles.py", line 116, in load_python_file
2026-03-13 16:50:18.251 |     module = load_module_py(module_id, path)
2026-03-13 16:50:18.251 |   File "/app/.venv/lib/python3.11/site-packages/alembic/util/pyfiles.py", line 136, in load_module_py
2026-03-13 16:50:18.251 |     spec.loader.exec_module(module)  # type: ignore
2026-03-13 16:50:18.251 |   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2026-03-13 16:50:18.251 |   File "<frozen importlib._bootstrap_external>", line 940, in exec_module
2026-03-13 16:50:18.251 |   File "<frozen importlib._bootstrap>", line 241, in _call_with_frames1
2026-03-13 16:50:18.251 |   File "/app/alembic/env.py", line 14, in <module>
2026-03-13 16:50:18.251 |     from app.core.database import Base, DATABASE_URL
2026-03-13 16:50:18.251 | ImportError: cannot import name 'DATABASE_URL' from 'app.core.database' (/app/app/core/database.py)
```

## 環境

- 後端: Docker 容器 `webpdtool-backend`
- Python: 3.11
- SQLAlchemy: 2.0+ (async only)
- Alembic: 1.12+
- 資料庫驅動: asyncmy (async), pymysql (sync, 用於遷移)

## 根本原因分析

### 問題 1: DATABASE_URL 不存在

**原因:**

專案在 Wave 6 重構中從同步資料庫驅動 (`pymysql`) 遷移到完全非同步架構 (`asyncmy`)。`app/core/database.py` 中只導出 `ASYNC_DATABASE_URL`，但 `alembic/env.py` 仍然嘗試導入 `DATABASE_URL`。

**程式碼對比:**

```python
# backend/app/core/database.py (當前狀態)
ASYNC_DATABASE_URL = f"mysql+asyncmy://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
# DATABASE_URL 不存在

# backend/alembic/env.py (修正前)
from app.core.database import Base, DATABASE_URL  # ❌ ImportError
```

### 問題 2: asyncmy 與 Alembic 同步引擎不相容

**原因:**

Alembic 的 `run_migrations_online()` 函數使用 `engine_from_config()` 創建**同步**引擎，但 `mysql+asyncmy://` URL 只能與 SQLAlchemy 的異步引擎 (`create_async_engine`) 一起使用。

**技術細節:**

| 元件 | 引擎類型 | URL 協議 | 驅動 |
|------|----------|----------|------|
| FastAPI 運行時 | 異步 (`AsyncEngine`) | `mysql+asyncmy://` | asyncmy |
| Alembic 遷移 | 同步 (`Engine`) | `mysql+pymysql://` | pymysql |

### 問題 3: pymysql 依賴缺失

**原因:**

專案依賴 `pyproject.toml` 中只有 `asyncmy`，沒有 `pymysql`。當 Alembic 嘗試使用 `mysql+pymysql://` URL 時，無法找到該模組。

## 解決方案

### 修正 1: 更新 alembic/env.py 導入

**檔案:** `backend/alembic/env.py`

```python
# 修正前
from app.core.database import Base, DATABASE_URL  # ❌ DATABASE_URL 不存在

# 修正後
from app.core.database import Base, ASYNC_DATABASE_URL

# 為了向後相容性
DATABASE_URL = ASYNC_DATABASE_URL
```

### 修正 2: 添加 URL 協議轉換

**檔案:** `backend/alembic/env.py`

```python
def _resolve_alembic_database_url() -> str:
    """
    解析 Alembic 使用的資料庫 URL。
    將 asyncmy 轉換為 pymysql 以支援同步遷移引擎。
    """
    env_database_url = os.getenv("ALEMBIC_DATABASE_URL") or os.getenv("DATABASE_URL")
    if env_database_url:
        url = env_database_url
    else:
        url = DATABASE_URL

    # 將 mysql+asyncmy:// 轉換為 mysql+pymysql:// 用於同步遷移
    # Alembic 的 run_migrations_online() 使用同步引擎
    if url.startswith("mysql+asyncmy://"):
        return url.replace("mysql+asyncmy://", "mysql+pymysql://")
    return url
```

### 修正 3: 添加 pymysql 依賴

**檔案:** `backend/pyproject.toml`

```toml
dependencies = [
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
    "sqlalchemy>=2.0.0",
    "asyncmy>=0.2.7",
    "pymysql>=1.0.0",  # ✅ 新增: 用於 Alembic 遷移 (同步驅動)
    # ... 其他依賴
]
```

## 除錯過程

### 步驟 1: 確認錯誤位置

```bash
# 查看 Docker 容器日誌
docker-compose logs -f backend
```

確認錯誤發生在 Alembic 執行階段：
```
File "/app/alembic/env.py", line 14, in <module>
    from app.core.database import Base, DATABASE_URL
ImportError: cannot import name 'DATABASE_URL'
```

### 步驟 2: 檢查 database.py

```bash
# 查看實際導出的內容
grep -n "DATABASE_URL\|ASYNC_DATABASE_URL" backend/app/core/database.py
```

結果：只有 `ASYNC_DATABASE_URL`，沒有 `DATABASE_URL`。

### 步驟 3: 修正導入並重建容器

```bash
# 修正後重建
docker-compose build --no-cache backend
docker-compose up -d backend
```

### 步驟 4: 發現第二個錯誤

重建後出現新錯誤：
```
ModuleNotFoundError: No module named 'pymysql'
```

這是因為 URL 被轉換為 `mysql+pymysql://`，但依賴不存在。

### 步驟 5: 添加依賴並重建

```bash
# 在 pyproject.toml 中添加 pymysql
# 重新構建
docker-compose build --no-cache backend
docker-compose up -d backend
```

### 步驟 6: 驗證修正

```bash
# 查看遷移日誌
docker-compose logs backend | grep -E "(Migration|Alembic|ERROR)"
```

成功輸出：
```
[INFO] Running 'alembic upgrade head'...
INFO  [alembic.runtime.migration] Context impl MySQLImpl.
INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
[INFO] ✅ Migrations completed successfully!
20260312_add_instruments_table (head)
```

## 驗證結果

```bash
$ docker-compose logs backend 2>&1 | tail -20

webpdtool-backend  | [INFO] Running 'alembic upgrade head'...
webpdtool-backend  | INFO  [alembic.runtime.migration] Context impl MySQLImpl.
webpdtool-backend  | INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
webpdtool-backend  | 20260312_add_instruments_table (head)
webpdtool-backend  | [INFO] ✅ Migrations completed successfully!
webpdtool-backend  | [INFO] Current migration version:
webpdtool-backend  | 20260312_add_instruments_table (head)
webpdtool-backend  | [INFO] Starting FastAPI application...
webpdtool-backend  | INFO:     Started server process [118]
webpdtool-backend  | INFO:     Uvicorn running on http://0.0.0.0:9100 (Press CTRL+C to quit)
```

## 技術背景

### SQLAlchemy 2.0 異步架構

SQLAlchemy 2.0 引入了完全的異步支援，但需要使用特定的驅動和 URL 協議：

```python
# 異步引擎 (FastAPI 運行時)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
async_engine = create_async_engine("mysql+asyncmy://...")
# 使用: AsyncSession, async_sessionmaker

# 同步引擎 (Alembic 遷移)
from sqlalchemy import create_engine
sync_engine = create_engine("mysql+pymysql://...")
# 使用: Session, sessionmaker
```

### 為什麼需要兩個驅動？

1. **asyncmy**: 提供非同步 MySQL 連接，用於 FastAPI 的異步路由
2. **pymysql**: 提供同步 MySQL 連接，用於 Alembic 的遷移腳本

Alembic 的遷移腳本在執行 DDL (CREATE TABLE, ALTER COLUMN 等) 時需要同步連接，因為:
- 遷移過程需要確保操作的順序性
- DDL 操作通常不支持異步執行
- Alembic 的 `run_migrations_online()` 使用同步 API

## 相關檔案

- `backend/alembic/env.py` - Alembic 環境配置 (已修正)
- `backend/app/core/database.py` - 資料庫連接配置
- `backend/pyproject.toml` - 專案依賴 (已新增 pymysql)
- `backend/docker-entrypoint.sh` - 容器啟動腳本，執行遷移

## 預防措施

為了避免類似問題，建議：

1. **Code Review 檢查清單**: 確認 Alembic 相關檔案與 `app/core/database.py` 的同步
2. **依賴審查**: 當使用異步資料庫驅動時，同時添加同步驅動用於遷移
3. **測試**: 在本地環境執行 `alembic upgrade head` 確認遷移正常

## 參考資料

- [SQLAlchemy 2.0 Async Documentation](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Alembic Documentation](https://alembic.sqlalchemy.org/en/latest/)
- [asyncmy GitHub](https://github.com/long2ice/asyncmy)
