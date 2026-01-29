# WebPDTool Docker 部署指南

本文檔說明如何使用 Docker 和 Docker Compose 部署 WebPDTool 系統。

## 系統需求

- Docker Engine 20.10+
- Docker Compose 2.0+
- 至少 4GB RAM
- 至少 10GB 硬碟空間

## 快速開始

### 1. 準備環境變數

複製環境變數範例檔案：

```bash
cp .env.example .env
```

編輯 `.env` 檔案，設定必要的環境變數：

```bash
# 重要：務必修改以下設定
MYSQL_ROOT_PASSWORD=your-secure-root-password
MYSQL_PASSWORD=your-secure-password
SECRET_KEY=your-secret-key-at-least-32-characters-long
```

### 2. 啟動服務

#### 生產環境部署

```bash
# 建置並啟動所有服務
docker-compose up -d

# 查看服務狀態
docker-compose ps

# 查看日誌
docker-compose logs -f
```

#### 開發環境部署

```bash
# 使用開發配置啟動（支援熱重載）
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# 或在背景執行
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

### 3. 訪問應用

啟動完成後，可通過以下 URL 訪問：

- **前端應用**: http://localhost (或您設定的 FRONTEND_PORT)
- **後端 API**: http://localhost:8000 (或您設定的 BACKEND_PORT)
- **API 文檔**: http://localhost:8000/docs

## 服務說明

### 服務列表

| 服務名稱 | 容器名稱 | 說明 | 端口 |
|---------|---------|------|------|
| db | webpdtool-db | MySQL 8.0 資料庫 | 3306 |
| backend | webpdtool-backend | FastAPI 後端服務 | 8000 |
| frontend | webpdtool-frontend | Vue 3 前端應用 (Nginx) | 80 |

### 資料持久化

使用 Docker Volume 持久化資料庫：

```bash
# 查看 volume
docker volume ls | grep webpdtool

# Volume 位置
mysql_data -> /var/lib/docker/volumes/webpdtool_mysql_data
```

## Docker Compose 常用指令

### 啟動與停止

```bash
# 啟動所有服務
docker-compose up -d

# 停止所有服務
docker-compose down

# 停止並刪除 volumes（注意：會刪除資料庫資料）
docker-compose down -v

# 重啟特定服務
docker-compose restart backend

# 重新建置並啟動
docker-compose up -d --build
```

### 查看狀態與日誌

```bash
# 查看所有服務狀態
docker-compose ps

# 查看所有服務日誌
docker-compose logs

# 查看特定服務日誌
docker-compose logs backend

# 即時跟蹤日誌
docker-compose logs -f backend

# 查看最後 100 行日誌
docker-compose logs --tail=100 backend
```

### 進入容器

```bash
# 進入後端容器
docker-compose exec backend bash

# 進入資料庫容器
docker-compose exec db bash

# 執行 MySQL 指令
docker-compose exec db mysql -u root -p
```

### 資源管理

```bash
# 查看資源使用情況
docker-compose top

# 查看容器統計資訊
docker stats

# 清理未使用的資源
docker system prune -a
```

## 資料庫管理

### 資料庫初始化

資料庫會在首次啟動時自動初始化，執行以下腳本：
1. `database/schema.sql` - 建立資料表
2. `database/seed_data.sql` - 載入種子資料

### 手動執行 SQL

```bash
# 方法 1: 通過容器執行
docker-compose exec db mysql -u pdtool -p webpdtool < your_script.sql

# 方法 2: 進入容器後執行
docker-compose exec db bash
mysql -u pdtool -p webpdtool
```

### 資料庫備份與還原

```bash
# 備份資料庫
docker-compose exec db mysqldump -u root -p webpdtool > backup_$(date +%Y%m%d_%H%M%S).sql

# 還原資料庫
docker-compose exec -T db mysql -u root -p webpdtool < backup_20231217_120000.sql
```

## 開發環境配置

### 使用開發配置

開發配置 (`docker-compose.dev.yml`) 提供：
- 後端熱重載
- 前端開發伺服器 (Vite)
- DEBUG 模式開啟
- 本地代碼掛載

```bash
# 啟動開發環境
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# 停止開發環境
docker-compose -f docker-compose.yml -f docker-compose.dev.yml down
```

### 安裝新的依賴

#### 後端 Python 依賴

```bash
# 進入後端容器
docker-compose exec backend bash

# 安裝套件
uv add package-name

# 或在主機上修改 pyproject.toml 後
docker-compose restart backend
```

#### 前端 npm 依賴

```bash
# 開發模式（使用 frontend-dev）
docker-compose exec frontend-dev sh
npm install package-name

# 生產模式（需要重新建置）
cd frontend
npm install package-name
docker-compose up -d --build frontend
```

## 生產環境部署

### 1. 安全性配置

編輯 `.env` 檔案：

```bash
# 使用強密碼
MYSQL_ROOT_PASSWORD=<strong-random-password>
MYSQL_PASSWORD=<strong-random-password>

# 使用安全的 SECRET_KEY（至少 32 字元）
SECRET_KEY=<random-32-chars-or-more>

# 關閉 DEBUG
DEBUG=false

# 設定正確的 CORS 來源
CORS_ORIGINS=https://yourdomain.com
```

### 2. 使用 HTTPS

建議在前端使用 Nginx 反向代理配置 SSL：

```bash
# 修改 frontend/nginx.conf 添加 SSL 配置
# 或使用外部反向代理 (如 Nginx Proxy Manager, Traefik)
```

### 3. 資源限制

編輯 `docker-compose.yml` 添加資源限制：

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

### 4. 定期備份

設定 cron job 定期備份資料庫：

```bash
# 編輯 crontab
crontab -e

# 每天凌晨 2 點備份
0 2 * * * cd /path/to/WebPDTool && docker-compose exec -T db mysqldump -u root -p${MYSQL_ROOT_PASSWORD} webpdtool > backups/backup_$(date +\%Y\%m\%d).sql
```

## 監控與健康檢查

### 健康檢查狀態

```bash
# 查看健康狀態
docker-compose ps

# 所有服務都應顯示 "healthy" 或 "Up"
```

### 服務監控

```bash
# 查看資源使用
docker stats webpdtool-backend webpdtool-frontend webpdtool-db

# 查看特定容器詳細資訊
docker inspect webpdtool-backend
```

## 故障排除

### 常見問題

#### 1. 資料庫連線失敗

```bash
# 檢查資料庫是否啟動
docker-compose ps db

# 檢查資料庫日誌
docker-compose logs db

# 確認網路連通性
docker-compose exec backend ping db
```

#### 2. 前端無法連接後端

- 檢查 CORS 設定是否正確
- 確認前端 API Base URL 配置
- 查看後端日誌

```bash
docker-compose logs backend
```

#### 3. 容器重複重啟

```bash
# 查看容器日誌尋找錯誤
docker-compose logs <service-name>

# 檢查健康檢查狀態
docker inspect <container-name> | grep -A 10 Health
```

#### 4. 磁碟空間不足

```bash
# 清理未使用的 Docker 資源
docker system prune -a

# 清理未使用的 volumes
docker volume prune
```

### 重置環境

完全重置開發環境：

```bash
# 停止並刪除所有容器、網路、volumes
docker-compose down -v

# 刪除所有 images
docker-compose down --rmi all

# 重新建置並啟動
docker-compose up -d --build
```

## 升級與更新

### 更新應用程式碼

```bash
# 拉取最新程式碼
git pull

# 重新建置並啟動
docker-compose up -d --build

# 或分別重新建置
docker-compose build backend
docker-compose up -d backend
```

### 更新資料庫 Schema

```bash
# 1. 備份當前資料庫
docker-compose exec db mysqldump -u root -p webpdtool > backup_before_migration.sql

# 2. 執行遷移腳本
docker-compose exec -T db mysql -u root -p webpdtool < database/migrations/001_update.sql

# 3. 驗證更新
docker-compose exec db mysql -u root -p -e "USE webpdtool; SHOW TABLES;"
```

## 效能優化

### 1. 資料庫優化

編輯 `docker-compose.yml` 添加 MySQL 配置：

```yaml
services:
  db:
    command:
      - --default-authentication-plugin=mysql_native_password
      - --max_connections=200
      - --innodb_buffer_pool_size=1G
```

### 2. 應用程式快取

考慮添加 Redis 快取服務：

```yaml
services:
  redis:
    image: redis:7-alpine
    container_name: webpdtool-redis
    networks:
      - webpdtool-network
```

### 3. 水平擴展

使用 Docker Compose scale 擴展後端服務：

```bash
docker-compose up -d --scale backend=3
```

## 參考資料

- [Docker 官方文檔](https://docs.docker.com/)
- [Docker Compose 文檔](https://docs.docker.com/compose/)
- [FastAPI Docker 部署](https://fastapi.tiangolo.com/deployment/docker/)
- [Vue.js Docker 部署](https://vuejs.org/guide/best-practices/production-deployment.html)

## 支援與協助

如遇到問題，請：
1. 查看服務日誌
2. 檢查環境變數配置
3. 參考故障排除章節
4. 查閱專案 README 和相關文檔
