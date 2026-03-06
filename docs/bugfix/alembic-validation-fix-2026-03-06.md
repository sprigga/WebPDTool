# Alembic 可用性驗證與修正紀錄

## 問題背景

使用者要求驗證 `backend` 目錄中的 Alembic 是否可用，若不可用則修正。

驗證日期: 2026-03-06

## 遇到的問題

### 1. `alembic` 指令不存在

在 `backend` 目錄直接執行:

```bash
alembic current
alembic history
alembic check
```

結果:

```text
/bin/bash: line 1: alembic: command not found
```

根因:
- 系統 PATH 未包含 Alembic CLI。
- 專案中可用的 Alembic 位於虛擬環境 `.venv2/bin/alembic`。

### 2. `uv run` 無法直接使用

嘗試改用 `uv run alembic ...` 時，遇到兩類錯誤:

1. uv cache 權限問題:
- `/home/ubuntu/.cache/uv` 無權限寫入。

2. `.venv` 權限問題:
- `backend/.venv` 為 root 擁有，uv 嘗試處理時失敗:
- `failed to remove directory .../.venv/bin: Permission denied`

根因:
- 目前工作環境中存在不可寫的 uv cache 與 root-owned `.venv`。

### 3. Alembic 執行時強制使用不可達資料庫

使用 `.venv2/bin/alembic current/check` 時，連線失敗:

```text
Can't connect to MySQL server on 'host.docker.internal'
```

根因:
- `backend/alembic/env.py` 固定以 `app.core.database.DATABASE_URL` 覆寫 `sqlalchemy.url`。
- 專案 `.env` 的 `DB_HOST=host.docker.internal` 在當前執行環境不可解析或不可達。

### 4. SQLite 驗證不適用此 migration 鏈

改用 SQLite 測試升級流程時，出現:
- `no such index: config_key`
- `No support for ALTER of constraints in SQLite dialect`

根因:
- 現有 migration 含 MySQL 專屬操作與約束調整，不是跨資料庫 migration。

## 修正內容

### 修改檔案

- `backend/alembic/env.py`

### 修正方式

新增資料庫 URL 解析邏輯，支援環境變數覆寫:

優先順序:
1. `ALEMBIC_DATABASE_URL`
2. `DATABASE_URL`
3. 原本 `app.core.database.DATABASE_URL`（fallback）

目的:
- 保留原本行為（不設環境變數時不變）。
- 允許在 CI、本機、不同網路環境下指定 Alembic 目標 DB，避免被 `host.docker.internal` 綁死。

## 驗證結果

### 成功項目

1. Alembic revision 鏈可讀取:

```bash
.venv2/bin/alembic history
.venv2/bin/alembic heads
```

2. 使用 MySQL dialect 離線產生升級 SQL（不需實際連線）可完整跑到 head:

```bash
ALEMBIC_DATABASE_URL='mysql+pymysql://user:pass@localhost/dbname' \
.venv2/bin/alembic upgrade head --sql
```

成功產生完整 SQL，包含從 base 到 `a8124fdea538 (head)` 的所有 upgrade steps。

### 預期限制

- `alembic current`、`alembic check` 仍需要「可連線的實際資料庫」。
- 若資料庫不可達，這兩個指令會失敗，屬正常行為。

## 建議用法

在本機或 CI 執行 Alembic 時，明確指定連線：

```bash
cd backend
ALEMBIC_DATABASE_URL='mysql+pymysql://<user>:<pass>@<host>:<port>/<db>' .venv2/bin/alembic upgrade head
```

若只需驗證 migration 程式碼可生成 SQL:

```bash
cd backend
ALEMBIC_DATABASE_URL='mysql+pymysql://user:pass@localhost/dbname' .venv2/bin/alembic upgrade head --sql
```

## 影響範圍

- 只影響 Alembic 執行時的 DB URL 解析。
- 不影響 FastAPI 應用程式的既有 DB 連線邏輯。
- 不影響既有 migration revision 檔案內容。
