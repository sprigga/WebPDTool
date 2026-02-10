# Docker Desktop WSL2 資料庫連接問題修復

**日期:** 2026-02-10
**問題類型:** 環境配置 / 網路連接
**影響範圍:** WSL2 + Docker Desktop 本地開發環境
**嚴重性:** 高 - 導致本地後端無法連接到正確的資料庫

---

## 問題摘要

本地後端 (port 8765) 啟動後，調用 `/api/stations/{station_id}/testplan-map` API 時返回 500 錯誤：

```
Failed to create TestPointMap: (pymysql.err.OperationalError)
(1054, "Unknown column 'test_plans.switch_mode' in 'field list'")
```

## 根本原因分析

### 問題現象

1. **Docker 後端正常運行** (port 9100)
   - 可正確訪問資料庫
   - `switch_mode` 欄位存在
   - test_plans 表有 6 筆記錄

2. **本地後端連接錯誤** (port 8765)
   - 連接到不同的 MySQL 實例
   - `switch_mode` 欄位不存在
   - test_plans 表只有 3 筆記錄

### 技術深入調查

使用 `pymysql` 測試連接到 `127.0.0.1:33306`：

```python
conn = pymysql.connect(host='127.0.0.1', port=33306, ...)
cursor.execute('SELECT @@hostname')
# 返回: 8f0933ef295c (ghost container)

cursor.execute('SELECT COUNT(*) FROM test_plans')
# 返回: 3

cursor.execute("SHOW COLUMNS FROM test_plans LIKE 'switch_mode'")
# 返回: 空 (欄位不存在)
```

使用 `docker exec` 直接查詢容器內部：

```bash
docker exec webpdtool-db mysql -e "SELECT @@hostname"
# 返回: 902dd88e6467 (正確的 container)

docker exec webpdtool-db mysql -e "SELECT COUNT(*) FROM test_plans"
# 返回: 6

docker exec webpdtool-db mysql -e "SHOW COLUMNS FROM test_plans LIKE 'switch_mode'"
# 返回: switch_mode 欄位存在
```

### 發現關鍵證據

| 連接方式 | MySQL Hostname | test_plans 數量 | switch_mode 欄位 |
|---------|----------------|----------------|-----------------|
| localhost:33306 | `8f0933ef295c` | 3 | ❌ 不存在 |
| 127.0.0.1:33306 | `8f0933ef295c` | 3 | ❌ 不存在 |
| **host.docker.internal:33306** | `902dd88e6467` | 6 | ✅ 存在 |
| docker exec (內部) | `902dd88e6467` | 6 | ✅ 存在 |

**關鍵發現:**
- Container ID `8f0933ef295c` **不存在於** `docker ps -a` 輸出中
- 這是一個 **phantom/ghost container**，可能是 Docker Desktop 代理層的緩存

### 根本原因

**Docker Desktop 在 WSL2 環境中的端口轉發機制:**

Docker Desktop 使用內部代理層處理從 WSL2 主機到容器的端口映射。當容器被重建或資料庫 schema 更新時，代理層可能會：

1. 緩存舊的連接路由
2. 將 `localhost/127.0.0.1` 的連接轉發到已刪除容器的殘留資料卷
3. 保持過時的資料庫狀態

這導致本地應用程式連接到舊的資料庫實例，而 Docker 內部網路仍然正確。

---

## 解決方案

### 修改資料庫主機配置

編輯 `backend/.env`：

```bash
# ❌ 原本 (錯誤) - 會連接到 Docker Desktop 代理緩存
DB_HOST=localhost
DB_PORT=33306

# ✅ 修正後 (正確) - 直接連接到 Docker 容器
DB_HOST=host.docker.internal
DB_PORT=33306
```

### 為什麼 `host.docker.internal` 有效？

- **`localhost` / `127.0.0.1`**:
  - WSL2 網路介面 → Docker Desktop 代理層 → **可能路由到錯誤的容器**

- **`host.docker.internal`**:
  - Docker 提供的特殊 DNS 名稱
  - 直接解析到當前運行的 Docker 容器 IP
  - 繞過代理層，保證連接到正確的容器

### 驗證修復

1. **測試資料庫連接:**

```bash
# 使用修正後的配置
cd backend
uv run python << EOF
import pymysql
conn = pymysql.connect(
    host='host.docker.internal',
    port=33306,
    user='pdtool',
    password='pdtool123',
    database='webpdtool'
)
cursor = conn.cursor()
cursor.execute('SELECT @@hostname')
print(f"Hostname: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM test_plans")
print(f"test_plans count: {cursor.fetchone()[0]}")

cursor.execute("SHOW COLUMNS FROM test_plans LIKE 'switch_mode'")
print(f"switch_mode exists: {len(cursor.fetchall()) > 0}")
EOF
```

預期輸出:
```
Hostname: 902dd88e6467
test_plans count: 6
switch_mode exists: True
```

2. **啟動本地後端並測試 API:**

```bash
# 啟動後端
cd backend
uv run uvicorn app.main:app --host 0.0.0.0 --port 8765

# 在另一個終端測試 API
TOKEN=$(curl -s -X POST "http://localhost:8765/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}' | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

curl -s "http://localhost:8765/api/stations/1/testplan-map?project_id=1" \
  -H "Authorization: Bearer $TOKEN"
```

預期結果: ✅ 返回正常的 test_plans 資料，無 `switch_mode` 欄位錯誤

---

## 影響範圍

### ✅ 受影響的環境
- **WSL2 + Docker Desktop for Windows**
- 本地開發環境使用 `localhost` 或 `127.0.0.1` 連接 Docker 容器

### ❌ 不受影響的環境
- Docker Compose 內部容器間通訊 (使用服務名稱 `db:3306`)
- 純 Linux 環境的 Docker 部署
- 生產環境 (通常使用專用資料庫伺服器)

---

## 預防措施

### 1. 統一使用 `host.docker.internal`

在本地開發的 `.env` 中，始終使用 `host.docker.internal` 而非 `localhost`：

```bash
# backend/.env (本地開發)
DB_HOST=host.docker.internal
DB_PORT=33306
```

### 2. 文件化環境差異

在 `backend/.env.example` 中添加註釋：

```bash
# Database Host
# 本地開發 (WSL2 + Docker Desktop): 使用 host.docker.internal
# Docker Compose 容器內: 使用 db
# 生產環境: 使用實際資料庫主機 IP/域名
DB_HOST=host.docker.internal
```

### 3. 重建容器後的檢查清單

當重建 MySQL 容器或執行 schema 遷移後：

```bash
# 1. 確認容器 ID
docker ps | grep webpdtool-db

# 2. 測試連接到正確的容器
docker exec webpdtool-db mysql -uroot -prootpassword \
  -e "SELECT @@hostname, COUNT(*) FROM webpdtool.test_plans"

# 3. 從本地測試連接
cd backend
uv run python -c "
import pymysql
conn = pymysql.connect(
    host='host.docker.internal', port=33306,
    user='pdtool', password='pdtool123', database='webpdtool'
)
cursor = conn.cursor()
cursor.execute('SELECT @@hostname')
print(f'Connected to: {cursor.fetchone()[0]}')
"
```

---

## 相關檔案

- `backend/.env` - 資料庫連接配置 (已修正)
- `backend/app/config.py` - Settings 類別，載入環境變數
- `backend/app/core/database.py` - SQLAlchemy 資料庫引擎配置
- `docker-compose.yml` - Docker 服務編排配置

---

## 參考資源

- [Docker Desktop for Windows - Networking features](https://docs.docker.com/desktop/networking/)
- [WSL2 Networking - Docker Documentation](https://docs.docker.com/desktop/wsl/)
- [host.docker.internal - Special DNS name](https://docs.docker.com/desktop/networking/#i-want-to-connect-from-a-container-to-a-service-on-the-host)

---

## 經驗總結

### 問題診斷關鍵步驟

1. **比較不同連接方式的結果**
   - Docker 內部 vs 外部連接
   - 不同的主機名稱 (localhost vs host.docker.internal)

2. **查詢資料庫元數據**
   - `SELECT @@hostname` - 確認連接到哪個實例
   - `SHOW COLUMNS` - 驗證 schema 版本
   - `SELECT COUNT(*)` - 比較資料數量

3. **檢查 Docker 網路狀態**
   - `docker ps` - 確認容器 ID
   - `docker inspect` - 查看網路配置
   - `docker logs` - 檢查容器日誌

### 學到的教訓

1. **避免使用 `localhost` 在 WSL2 + Docker Desktop 環境**
   - Docker Desktop 的代理層可能產生意外行為
   - 使用 `host.docker.internal` 更可靠

2. **容器重建後驗證連接**
   - 不要假設端口映射總是指向正確的容器
   - 重建容器後明確測試資料庫連接

3. **環境特定的配置需要文件化**
   - 不同環境 (本地/Docker/生產) 可能需要不同的配置
   - 在 `.env.example` 中提供清晰的指引
