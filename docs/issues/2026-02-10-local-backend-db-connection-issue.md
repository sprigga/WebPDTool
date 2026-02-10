# 本地後端資料庫連接問題

**日期:** 2026-02-10
**狀態:** ✅ 已解決
**嚴重性:** 高 - 影響本地開發環境

## 問題描述

本地後端 (port 8765) 啟動後，調用 `/api/stations/{station_id}/testplan-map` API 時返回 500 錯誤：

```
Failed to create TestPointMap: (pymysql.err.OperationalError) (1054, "Unknown column 'test_plans.switch_mode' in 'field list'")
```

## 環境

- 本地後端: `uv run uvicorn app.main:app --host 0.0.0.0 --port 8765`
- Docker 資料庫: `webpdtool-db` container, expose port `33306->3306`
- 前端 Vite proxy: 指向 `localhost:8765`

## 已確認的事實

### 1. Docker 後端 (port 9100) 運作正常

```bash
curl "http://localhost:9100/api/stations/1/testplan-map?project_id=1"
# 返回正確的 test_plans 數據，包含 switch_mode 欄位
```

### 2. Docker 內部資料庫結構正確

```sql
-- 從 Docker 內部查詢
mysql> SHOW COLUMNS FROM test_plans LIKE 'switch_mode';
+-------------+-------------+------+-----+---------+-------+
| Field       | Type        | Null | Key | Default | Extra |
+-------------+-------------+------+-----+---------+-------+
| switch_mode | varchar(50) | YES  | MUL | NULL    |       |
+-------------+-------------+------+-----+---------+-------+
-- test_plans count: 6
-- hostname: 8deb33d0d39d
```

### 3. 本地 pymysql 連接到不同的資料庫實例

```python
# 從本地環境透過 127.0.0.1:33306 連接
import pymysql
conn = pymysql.connect(host='127.0.0.1', port=33306, ...)
cursor.execute('SELECT @@hostname')  # 返回: 8f0933ef295c
cursor.execute('SELECT COUNT(*) FROM test_plans')  # 返回: 3
cursor.execute('SHOW COLUMNS FROM test_plans')  # 沒有 switch_mode 欄位
```

### 4. 兩個資料庫實例比較

| 屬性 | Docker 內部 | 本地 pymysql (127.0.0.1:33306) |
|------|-------------|-------------------------------|
| hostname | `8deb33d0d39d` | `8f0933ef295c` |
| test_plans count | 6 | 3 |
| switch_mode 欄位 | 存在 | 不存在 |
| MySQL version | 8.0.45 | 8.0.45 |

### 5. Docker Container 列表

```
CONTAINER ID   NAMES               PORTS
8deb33d0d39d   webpdtool-db        0.0.0.0:33306->3306/tcp
e46b875bfe95   webpdtool-backend   0.0.0.0:9100->9100/tcp
87f965a09ca8   webpdtool-redis     0.0.0.0:6379->6379/tcp
```

- 只有一個 MySQL container (`webpdtool-db`)
- Container ID `8f0933ef295c` 不存在於 Docker 中

### 6. Port 33306 確認

```bash
$ ss -tlnp | grep 33306
LISTEN 0 4096 0.0.0.0:33306 0.0.0.0:*
LISTEN 0 4096 [::]:33306 [::]:*

$ nc -zv 127.0.0.1 33306
Connection to 127.0.0.1 33306 port [tcp/*] succeeded!
```

### 7. SQLAlchemy 配置正確

```python
DATABASE_URL = 'mysql+pymysql://pdtool:pdtool123@127.0.0.1:33306/webpdtool'
# URL 顯示正確的 127.0.0.1:33306
# 但 SELECT @@port 返回 3306
```

## 可能的原因

### 假設 1: WSL2 網路層問題
WSL2 的網路架構可能有 port forwarding 或 proxy 行為，導致連接到不同的實例。

### 假設 2: 舊的 Docker container 殘留
可能有一個已停止或殘留的 container 仍在某種方式影響網路。

### 假設 3: Docker Desktop/WSL2 整合問題
Docker Desktop 與 WSL2 的整合可能有緩存或網路映射問題。

## 已嘗試的解決方案

### 1. 修正 .env 路徑解析
- 修改 `app/config.py` 使用 `Path(__file__).resolve().parent.parent / ".env"`
- 修改 `app/config/__init__.py` 使用相同的路徑計算方式
- 結果: Settings 正確載入 DB_PORT=33306，但連接仍然有問題

### 2. 重建本地 venv
- 刪除由 Docker 創建的 `.venv` (root 擁有)
- 使用 `uv venv .venv` 重新創建
- 使用 `uv pip install -e .` 安裝依賴
- 結果: venv 正常，但資料庫連接問題仍存在

## 待調查事項

1. [ ] 確認 WSL2 網路配置
2. [ ] 檢查是否有其他 MySQL/MariaDB 服務在 WSL2 中運行
3. [ ] 嘗試重啟 Docker 服務
4. [ ] 檢查 Docker Desktop 設定 (如果有使用)
5. [ ] 嘗試使用 Docker network 內部 IP 連接 (如 172.18.0.3:3306)

## 臨時解決方案

目前可以使用 Docker 後端 (port 9100) 進行開發：
- 修改 `frontend/vite.config.js` 將 proxy target 改為 `http://localhost:9100`

```javascript
proxy: {
  '/api': {
    target: 'http://localhost:9100',  // 使用 Docker 後端
    changeOrigin: true
  }
}
```

## ✅ 解決方案

### 根本原因

Docker Desktop 在 WSL2 環境中使用內部代理層進行端口轉發。當使用 `localhost` 或 `127.0.0.1` 連接暴露的端口時，Docker Desktop 會通過一個代理容器轉發連接，而這個代理可能會緩存舊的資料庫狀態。

**證據:**
- Docker 容器 ID: `902dd88e6467` (當前運行的 webpdtool-db)
- 代理容器 ID: `8f0933ef295c` (不存在於 `docker ps -a` 中，但仍在處理連接)
- 使用 `localhost:33306` 連接到 `8f0933ef295c` (舊資料庫，無 switch_mode)
- 使用 `host.docker.internal:33306` 連接到 `902dd88e6467` (正確的資料庫，有 switch_mode)

### 修正方法

修改 `backend/.env` 中的資料庫主機設定：

```bash
# 原本 (錯誤)
DB_HOST=localhost

# 修正後 (正確)
DB_HOST=host.docker.internal
```

這個修改使本地後端繞過 Docker Desktop 的代理層，直接連接到正確的資料庫容器。

### 驗證結果

```bash
# 使用 host.docker.internal
$ curl "http://localhost:8765/api/stations/1/testplan-map?project_id=1"
# ✓ 返回正確數據，無 switch_mode 錯誤

# 資料庫連接測試
$ python test_connection.py
Connected to MySQL hostname: 902dd88e6467
test_plans count: 6
switch_mode column: EXISTS
✓ SUCCESS: Connected to the CORRECT database!
```

### 技術細節

**Docker Desktop WSL2 網路架構:**
- `localhost` / `127.0.0.1` → Docker Desktop 代理 → 可能路由到錯誤的容器
- `host.docker.internal` → 直接解析到 Docker 容器 IP → 保證正確連接

**影響範圍:**
- 僅影響 WSL2 + Docker Desktop 環境的本地開發
- 不影響 Docker Compose 內部容器間通訊 (使用 `db:3306`)
- 不影響純 Linux 環境的 Docker 部署

## 相關文件

- `backend/.env` - 資料庫連接配置 (已修正)
- `backend/app/config.py` - 應用配置
- `backend/app/config/__init__.py` - 配置模組載入
- `backend/app/core/database.py` - 資料庫連接
- `frontend/vite.config.js` - 前端代理配置
