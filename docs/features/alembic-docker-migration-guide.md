# Alembic Migration 與 Docker 自動化實作指南

> **建立日期:** 2026-03-12
>
> **相關 Issues:** Issue 11.1 (Alembic Migration 建立), Issue 11.2 (Docker 自動化)
>
> **適用場景:** 新增資料庫表/欄位時的標準流程

---

## Overview

本文檔記錄如何為 WebPDTool 專案建立正確的 Alembic migration，並在 Docker 容器中實作自動執行機制。這是從「使用 raw SQL migration」遷移到「標準 Alembic workflow」的完整案例研究。

### 問題背景

原始的 `instruments` 表只有：
- `schema.sql` 中的 DDL 定義
- `database/migrations/add_instruments_table.sql` (raw SQL)
- `seed_instruments.sql` (seed data)

**缺失：**
- ❌ 沒有對應的 Alembic migration
- ❌ `alembic/env.py` 未匯入 `Instrument` 模型
- ❌ 無法透過 `alembic upgrade` 管理版本
- ❌ Docker 容器啟動時不自動執行 migration

---

## Part 1: Alembic Migration 建立

### 步驟 1: 確認專案狀態

首先檢查 Alembic 是否已配置：

```bash
cd /home/ubuntu/python_code/WebPDTool/backend

# 檢查 Alembic 設定
ls -la alembic/
ls -la alembic/versions/

# 預期輸出：
# alembic.ini        ✅
# alembic/env.py     ✅
# versions/          ✅ (包含既有 migrations)
```

### 步驟 2: 檢查 alembic/env.py 的模型匯入

**問題發現：**

```python
# backend/alembic/env.py (原始狀態)
from app.models.user import User
from app.models.project import Project
from app.models.station import Station
from app.models.testplan import TestPlan
from app.models.test_result import TestResult
from app.models.test_session import TestSession
from app.models.sfc_log import SFCLog
# ❌ Instrument 模型未匯入！
```

**為什麼這是問題？**

`alembic revision --autogenerate` 透過 `target_metadata` 來偵測模型變更。如果模型未匯入，Alembic 無法偵測到 `instruments` 表的存在。

**修正：**

```python
# backend/alembic/env.py (修正後)
from app.models.instrument import Instrument  # 新增這行
```

### 步驟 3: 確認 Migration Chain

檢查既有 migrations 的依賴關係：

```bash
grep -E "^(revision|down_revision)" backend/alembic/versions/*.py | sort
```

**輸出範例：**
```
alembic/versions/0232af89acc2_add_new_fields_to_testplan_table.py:revision: str = '0232af89acc2'
alembic/versions/0232af89acc2_add_new_fields_to_testplan_table.py:down_revision: Union[str, Sequence[str], None] = None
alembic/versions/9dd55b733f64_add_test_plan_name_to_test_plans.py:revision: str = '9dd55b733f64'
alembic/versions/9dd55b733f64_add_test_plan_name_to_test_plans.py:down_revision: Union[str, Sequence[str], None] = '0232af89acc2'
alembic/versions/20250109_change_measured_value_to_string.py:revision = '20250109_change_measured_value'
alembic/versions/20250109_change_measured_value_to_string.py:down_revision = '9dd55b733f64'
alembic/versions/a8124fdea538_add_project_id_to_test_plans.py:revision: str = 'a8124fdea538'
alembic/versions/a8124fdea538_add_project_id_to_test_plans.py:down_revision: Union[str, Sequence[str], None] = '20250109_change_measured_value'
```

**Migration Chain:**
```
0232af89acc2 → 9dd55b733f64 → 20250109 → a8124fdea538 (latest)
```

新的 migration 必須連接到 `a8124fdea538`。

### 步驟 4: 建立 Migration 檔案

創建 `backend/alembic/versions/20260312_add_instruments_table.py`：

```python
"""add_instruments_table

Add instruments table for DB-backed instrument configuration.

Revision ID: 20260312_add_instruments_table
Revises: a8124fdea538
Create Date: 2026-03-12
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '20260312_add_instruments_table'
down_revision: Union[str, Sequence[str], None] = 'a8124fdea538'

def upgrade() -> None:
    """建立 instruments 表並插入預設資料"""
    # 使用 raw SQL 以支援 MySQL 特定功能
    op.execute("""
        CREATE TABLE IF NOT EXISTS instruments (
            id              INT AUTO_INCREMENT PRIMARY KEY,
            instrument_id   VARCHAR(64) NOT NULL UNIQUE COMMENT 'Logical ID',
            instrument_type VARCHAR(64) NOT NULL COMMENT 'Driver type',
            name            VARCHAR(128) NOT NULL,
            conn_type       VARCHAR(32) NOT NULL COMMENT 'Connection type',
            conn_params     JSON NOT NULL COMMENT 'Connection parameters',
            enabled         TINYINT(1) NOT NULL DEFAULT 1,
            description     TEXT,
            created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_instruments_type (instrument_type),
            INDEX idx_instruments_enabled (enabled)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)

    # Idempotent seed data
    op.execute("""
        INSERT INTO instruments (instrument_id, instrument_type, name, conn_type, conn_params, enabled, description)
        VALUES
          ('DAQ973A_1', 'DAQ973A', 'Keysight DAQ973A #1',
           'VISA', '{"address":"TCPIP0::192.168.1.10::inst0::INSTR","timeout":5000}',
           0, 'Keysight DAQ973A data acquisition system'),
          ('MODEL2303_1', 'MODEL2303', 'Keysight 2303 Power Supply #1',
           'VISA', '{"address":"TCPIP0::192.168.1.11::inst0::INSTR","timeout":5000}',
           0, 'Keysight 2303 power supply'),
          ('console_1', 'console', 'Console Command (default)',
           'LOCAL', '{"address":"local://console"}', 1, 'Virtual instrument for OS subprocess'),
          ('comport_1', 'comport', 'COM Port Command (default)',
           'LOCAL', '{"address":"local://comport"}', 1, 'Virtual instrument for serial port'),
          ('tcpip_1', 'tcpip', 'TCP/IP Command (default)',
           'LOCAL', '{"address":"local://tcpip"}', 1, 'Virtual instrument for TCP/IP')
        ON DUPLICATE KEY UPDATE
          name        = VALUES(name),
          conn_type   = VALUES(conn_type),
          conn_params = VALUES(conn_params),
          description = VALUES(description);
    """)

def downgrade() -> None:
    """移除 instruments 表"""
    op.execute("DROP TABLE IF EXISTS instruments;")
```

### 設計決策說明

| 決策 | 原因 |
|------|------|
| 使用 `op.execute()` 而非 `op.create_table()` | MySQL 特定功能：JSON、TINYINT(1)、ON DUPLICATE KEY UPDATE |
| `CREATE TABLE IF NOT EXISTS` | 幂等性：可重複執行 |
| `ON DUPLICATE KEY UPDATE` | Seed data 幂等性 |
| `down_revision = 'a8124fdea538'` | 連接到正確的 migration chain |
| 提供 `downgrade()` | 支援完整 rollback |

### 步驟 5: 驗證 Migration

```bash
# 檢查當前版本
uv run alembic current

# 執行 migration
uv run alembic upgrade head

# 驗證表已建立
docker-compose exec db mysql -uroot -prootpassword webpdtool -e "DESCRIBE instruments;"

# 驗證 seed data
docker-compose exec db mysql -uroot -prootpassword webpdtool -e "SELECT instrument_id, name, enabled FROM instruments;"

# 測試 rollback
uv run alembic downgrade -1
uv run alembic upgrade 20260312_add_instruments_table
```

### 常見問題排除

#### 問題 1: Revision Chain 不一致

**症狀：**
```
alembic.util.exc.CommandError: Target database is not up to date.
```

**原因：**
`down_revision` 指向了錯誤的或過舊的 revision。

**解決：**
```bash
# 查看完整 migration chain
uv run alembic history

# 確認最新的 revision ID
# 修正 down_revision 為最新的 revision
```

#### 問題 2: Autogenerate 無法偵測模型

**症狀：**
```bash
uv run alembic revision --autogenerate -m "add instruments"
# 產生的 migration 檔案是空的
```

**原因：**
模型未在 `alembic/env.py` 中匯入。

**解決：**
```python
# 確保在 alembic/env.py 中匯入所有模型
from app.models.instrument import Instrument  # 加入這行
```

#### 問題 3: MySQL JSON 類型問題

**症狀：**
```
sqlalchemy.exc.CompileError: **etc etc**
```

**原因：**
SQLAlchemy 的 autogenerate 可能產生不兼容 MySQL 的 JSON 類型定義。

**解決：**
使用 `op.execute()` 執行原生 SQL，而不是依賴 autogenerate。

---

## Part 2: Docker 自動化 Migration

### 步驟 1: 建立 Entrypoint 腳本

創建 `backend/docker-entrypoint.sh`：

```bash
#!/bin/bash
set -e

# Configuration
SKIP_MIGRATIONS="${SKIP_MIGRATIONS:-false}"
MIGRATION_TIMEOUT="${MIGRATION_TIMEOUT:-10}"

# Logging functions
log_info() {
    echo -e "\033[0;32m[INFO]\033[0m $1"
}

log_warn() {
    echo -e "\033[1;33m[WARN]\033[0m $1"
}

log_error() {
    echo -e "\033[0;31m[ERROR]\033[0m $1"
}

# Wait for database
wait_for_db() {
    local host="${DB_HOST:-db}"
    local port="${DB_PORT:-3306}"
    local timeout=$MIGRATION_TIMEOUT
    local count=0

    log_info "Waiting for database at ${host}:${port}..."

    while [ $count -lt $timeout ]; do
        if python -c "
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    s.connect(('${host}', ${port}))
    s.close()
    exit(0)
except:
    exit(1)
" 2>/dev/null; then
            log_info "Database is ready!"
            return 0
        fi
        count=$((count + 1))
        sleep 1
    done

    log_error "Database connection timeout after ${timeout}s"
    return 1
}

# Run migrations
run_migrations() {
    if [ "$SKIP_MIGRATIONS" = "true" ]; then
        log_warn "SKIP_MIGRATIONS=true, skipping migrations"
        return 0
    fi

    log_info "Running Alembic migrations..."
    uv run alembic current 2>/dev/null || log_warn "No migration version found"

    if uv run alembic upgrade head; then
        log_info "✅ Migrations completed!"
        uv run alembic current
    else
        log_error "❌ Migration failed! App will start anyway."
        log_error "Run manually: docker-compose exec backend uv run alembic upgrade head"
    fi
}

# Main
main() {
    log_info "WebPDTool Backend Entrypoint"
    wait_for_db || true
    run_migrations
    log_info "Starting FastAPI..."
    exec "$@"
}

main "$@"
```

**關鍵設計：**
1. **優雅降級** - Migration 失敗不阻止應用啟動
2. **可配置** - 透過環境變數控制行為
3. **詳細日誌** - 彩色輸出便於除錯

### 步驟 2: 更新 Dockerfile

```dockerfile
# Backend Dockerfile for WebPDTool
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install --no-cache-dir uv

# Install dependencies
COPY pyproject.toml ./
COPY uv.lock ./
RUN uv sync --frozen

# Copy application code
COPY . .

# Copy entrypoint script
# 注意：sed -i 's/\r//' 修正 Windows CRLF 換行，避免 "no such file or directory" 錯誤
COPY docker-entrypoint.sh /usr/local/bin/
RUN sed -i 's/\r//' /usr/local/bin/docker-entrypoint.sh && \
    chmod +x /usr/local/bin/docker-entrypoint.sh

EXPOSE 9100

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:9100/health')" || exit 1

# Use entrypoint（使用完整絕對路徑）
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9100"]
```

**關鍵變更：**
1. `COPY docker-entrypoint.sh /usr/local/bin/` - 複製到標準位置
2. `sed -i 's/\r//'` - 移除 Windows CRLF，防止 shebang 解析錯誤
3. `RUN chmod +x` - 確保可執行
4. `ENTRYPOINT ["/usr/local/bin/..."]` - 使用完整絕對路徑

### 步驟 3: 更新 docker-compose.yml

```yaml
services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    environment:
      # ... 其他環境變數 ...

      # Alembic migration automation
      SKIP_MIGRATIONS: ${SKIP_MIGRATIONS:-false}
      MIGRATION_TIMEOUT: ${MIGRATION_TIMEOUT:-10}
      ALEMBIC_ARGS: ${ALEMBIC_ARGS:-}
```

### 步驟 4: 測試 Docker 自動化

```bash
# 重建容器（Dockerfile 有變更）
docker-compose build backend

# 啟動並查看日誌
docker-compose up -d backend
docker-compose logs -f backend | grep -E "(INFO|Migration|Database)"

# 預期輸出：
# [INFO] Waiting for database at db:3306...
# [INFO] Database is ready!
# [INFO] Running Alembic migrations...
# [INFO] ✅ Migrations completed!
# [INFO] Starting FastAPI...
```

### Docker 故障排除

#### 問題 0: Entrypoint 找不到檔案（CRLF 換行問題）⭐ 重要

**症狀：**
```
exec /usr/local/bin/docker-entrypoint.sh: no such file or directory
```

**發生情境：**
在 Windows 環境（或 WSL）建立的 shell 腳本，使用 Windows 的 `\r\n`（CRLF）換行。
Linux kernel 在解析 shebang 行 `#!/bin/bash` 時，會把 `\r` 當作路徑的一部分，
實際上去尋找 `/bin/bash\r`，這個路徑不存在，因此報錯。

**根本原因分析：**

```bash
# 用 hexdump 可以看到 CRLF 問題（容器外執行）
hexdump -C docker-entrypoint.sh | head -3
# 如果看到 0d 0a，代表有 CRLF 換行
# 00000000  23 21 2f 62 69 6e 2f 62  61 73 68 0d 0a 73 65 74  |#!/bin/bash..set|
#                                            ^^^^
#                                           \r\n (CRLF)

# 正常應該只有 LF
# 00000000  23 21 2f 62 69 6e 2f 62  61 73 68 0a 73 65 74 20  |#!/bin/bash.set |
#                                            ^^
#                                           \n (LF only)
```

**修正方法（Dockerfile）：**

在 `chmod` 之前加入 `sed` 移除 `\r`：

```dockerfile
# ❌ 原始（有問題）
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# ✅ 修正後
COPY docker-entrypoint.sh /usr/local/bin/
RUN sed -i 's/\r//' /usr/local/bin/docker-entrypoint.sh && \
    chmod +x /usr/local/bin/docker-entrypoint.sh
```

同時確保 `ENTRYPOINT` 使用完整絕對路徑：

```dockerfile
# ❌ 原始（有時會找不到）
ENTRYPOINT ["docker-entrypoint.sh"]

# ✅ 修正後（明確指定完整路徑）
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
```

**替代方案（治本）：**

在 Git repository 設定 `.gitattributes`，強制以 LF 儲存 shell 腳本：

```ini
# .gitattributes
*.sh text eol=lf
```

或在本地用 `dos2unix` 轉換：

```bash
dos2unix backend/docker-entrypoint.sh
```

**除錯流程摘要：**

```
症狀：exec /usr/local/bin/docker-entrypoint.sh: no such file or directory
  ↓
懷疑：CRLF 換行問題（在 Windows/WSL 環境常見）
  ↓
確認：hexdump -C docker-entrypoint.sh | head -3 → 是否有 0d 0a
  ↓
修正：Dockerfile 加入 sed -i 's/\r//' + 使用完整絕對路徑 ENTRYPOINT
  ↓
重建：docker-compose build --no-cache backend
  ↓
驗證：docker-compose up -d backend && docker-compose logs -f backend
```

---

#### 問題 1: Entrypoint 權限錯誤

**症狀：**
```
ERROR: for webpdtool-backend  Cannot start service backend:
OCI runtime create failed: container_linux.go:370: starting container process caused: exec: "docker-entrypoint.sh": permission denied
```

**原因：**
Entrypoint 腳本沒有執行權限。

**解決：**
```dockerfile
# 確保 Dockerfile 包含此行
RUN chmod +x /usr/local/bin/docker-entrypoint.sh
```

#### 問題 2: 資料庫連線超時

**症狀：**
```
[ERROR] Database connection timeout after 60s
```

**解決方案：**

1. 檢查資料庫是否正常運行：
```bash
docker-compose ps db
docker-compose logs db | tail -n 20
```

2. 增加超時時間：
```yaml
environment:
  MIGRATION_TIMEOUT: 30  # 30 秒
```

3. 手動測試連線：
```bash
docker-compose exec backend python -c "
import pymysql
pymysql.connect(host='db', user='pdtool', password='pdtool123', database='webpdtool')
print('Connection OK')
"
```

#### 問題 3: Migration 失敗但需手動修復

**情境：**
Migration 有錯誤，但應用程式已啟動。

**步驟：**

1. 查看完整錯誤日誌：
```bash
docker-compose logs backend | grep -A 10 "Migration failed"
```

2. 進入容器手動執行：
```bash
docker-compose exec backend bash

# 在容器內
uv run alembic history
uv run alembic current
uv run alembic upgrade head  # 查看詳細錯誤
```

3. 修正 migration 後重新執行：
```bash
# 重新構建並啟動
docker-compose up -d --build backend
```

#### 問題 4: 需要跳過 Migrations（開發環境）

**方法 1：環境變數**
```bash
docker-compose run -e SKIP_MIGRATIONS=true backend
```

**方法 2：.env 檔案**
```bash
echo "SKIP_MIGRATIONS=true" >> .env
docker-compose up backend
```

**方法 3：繞過 Entrypoint**
```bash
# 直接執行命令（繞過 entrypoint 腳本）
docker-compose exec backend uv run uvicorn app.main:app --host 0.0.0.0 --port 9100
```

---

## Part 3: 標準工作流程

### 新增資料庫表/欄位的完整流程

```bash
# 1. 建立/修改 ORM 模型
# backend/app/models/new_model.py

# 2. 更新 alembic/env.py 匯入
# backend/alembic/env.py
from app.models.new_model import NewModel

# 3. 生成 migration（選擇其中一種方法）

# 方法 A: 使用 autogenerate（適用簡單變更）
uv run alembic revision --autogenerate -m "add new table"

# 方法 B: 手動建立 migration 檔案（適用複雜變更）
uv run alembic revision -m "add new table"
# 然後編輯生成的檔案

# 4. 檢查生成的 migration
cat backend/alembic/versions/xxxxx_add_new_table.py

# 5. 測試 migration
uv run alembic upgrade head
uv run alembic current

# 6. 測試 rollback
uv run alembic downgrade -1
uv run alembic upgrade head

# 7. 建立/更新 Docker
docker-compose build backend

# 8. 部署測試
docker-compose up -d backend
docker-compose logs backend | grep Migration

# 9. 更新文件
# 記錄變更到相關的 feature document
```

### Alembic 常用指令

```bash
# 查看當前版本
uv run alembic current

# 查看所有歷史
uv run alembic history

# 升級到最新
uv run alembic upgrade head

# 升級到特定版本
uv run alembic upgrade <revision_id>

# 降級一個版本
uv run alembic downgrade -1

# 降級到特定版本
uv run alembic downgrade <revision_id>

# 生成空白 migration
uv run alembic revision -m "description"

# 生成 autogenerate migration
uv run alembic revision --autogenerate -m "description"

# 顯示 SQL（不執行）
uv run alembic upgrade head --sql

# 驗證 migration（檢查問題）
uv run alembic check
```

---

## Part 4: 檔案結構總覽

```
WebPDTool/
├── backend/
│   ├── alembic/
│   │   ├── env.py                          # ✅ 已修正：新增 Instrument 匯入
│   │   ├── versions/
│   │   │   ├── 0232af89acc2_*.py           # 既有 migrations
│   │   │   ├── 9dd55b733f64_*.py
│   │   │   ├── 20250109_change_*.py
│   │   │   ├── a8124fdea538_*.py           # 最新既有 migration
│   │   │   └── 20260312_add_instruments_table.py  # ✅ 新增
│   │   └── script.py.mako
│   ├── app/
│   │   └── models/
│   │       └── instrument.py               # ORM 模型
│   ├── docker-entrypoint.sh                # ✅ 新增：容器啟動腳本
│   └── Dockerfile                          # ✅ 已修改：使用 ENTRYPOINT
├── docker-compose.yml                      # ✅ 已修改：新增環境變數
├── database/
│   ├── schema.sql                          # 包含 instruments DDL
│   ├── seed_instruments.sql                # Seed data
│   └── migrations/
│       └── add_instruments_table.sql       # 備用：raw SQL migration
└── docs/
    └── features/
        ├── instrument-config-database-migration.md  # ✅ 已更新
        └── alembic-docker-migration-guide.md       # ✅ 新增：本文件
```

---

## Part 5: 經驗總結

### 學到的教訓

1. **Alembic env.py 必須匯入所有模型**
   - 否則 `autogenerate` 無法偵測變更
   - 這是最常見的問題根源

2. **MySQL 特定功能需要 raw SQL**
   - JSON 類型、TINYINT(1) 等
   - `op.execute()` 比 autogenerate 更可靠

3. **Idempotent Migration 設計**
   - `CREATE TABLE IF NOT EXISTS`
   - `ON DUPLICATE KEY UPDATE`
   - 允許 migration 重複執行

4. **正確的 Revision Chain**
   - 必須連接到最新的 migration
   - 使用 `alembic history` 驗證

5. **Docker Entrypoint 最佳實踐**
   - 優雅降級（失敗不阻止啟動）
   - 詳細日誌（彩色輸出）
   - 可配置行為（環境變數）

### 最佳實踐檢查清單

建立新 migration 前，確認：

- [ ] ORM 模型已建立並測試
- [ ] `alembic/env.py` 已匯入新模型
- [ ] 了解最新的 revision ID（`alembic history`）
- [ ] Migration 使用 `IF NOT EXISTS` 或類似冪等機制
- [ ] 提供完整的 `downgrade()` 函式
- [ ] 本地測試過 `upgrade` 和 `downgrade`
- [ ] Seed data（如有）使用 `ON DUPLICATE KEY UPDATE`
- [ ] 更新相關文件

### 相關資源

| 資源 | 連結 |
|------|------|
| Alembic 官方文件 | https://alembic.sqlalchemy.org/ |
| Alembic Cookbook | https://alembic.sqlalchemy.org/en/latest/cookbook.html |
| MySQL JSON 類型 | https://dev.mysql.com/doc/refman/8.0/en/json.html |
| Docker Entrypoint | https://docs.docker.com/engine/reference/builder/#entrypoint |

---

## 快速參考

### 環境變數

| 變數 | 預設值 | 說明 |
|------|--------|------|
| `SKIP_MIGRATIONS` | `false` | 跳過自動 migration |
| `MIGRATION_TIMEOUT` | `10` | DB 等待秒數 |
| `ALEMBIC_ARGS` | `""` | 額外 alembic 參數 |

### 常用指令

```bash
# 本地開發
uv run alembic upgrade head
uv run alembic current
uv run alembic history

# Docker 操作
docker-compose exec backend uv run alembic upgrade head
docker-compose logs backend | grep Migration
docker-compose up -d --build backend

# 除錯
docker-compose exec backend bash
uv run alembic downgrade -1
uv run alembic upgrade head
```

### Migration Chain

```
0232af89acc2 (base)
    ↓
9dd55b733f64 (add test_plan_name)
    ↓
20250109_change_measured_value (change type to string)
    ↓
a8124fdea538 (add project_id)
    ↓
20260312_add_instruments_table (add instruments table) ← 當前最新
```
