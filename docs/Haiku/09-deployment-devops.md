# 09 - 部署與維運

## Docker 部署架構

```
Host Machine
├─ Docker Engine
│  ├─ Container: mysql (資料庫)
│  │   ├─ 埠：3306 (內部) → 33306 (host)
│  │   ├─ 卷：database/ → /var/lib/mysql
│  │   └─ Env: MYSQL_ROOT_PASSWORD, MYSQL_DATABASE
│  │
│  ├─ Container: redis (日誌)
│  │   ├─ 埠：6379 (內部) → 6379 (host)
│  │   └─ 用途：日誌流和快取
│  │
│  ├─ Container: backend (FastAPI)
│  │   ├─ 埠：9100 (內部) → 9100 (host)
│  │   ├─ 卷：backend/ → /app
│  │   ├─ 依賴：db, redis
│  │   └─ 命令：uvicorn app.main:app
│  │
│  ├─ Container: frontend (Nginx + Vue SPA)
│  │   ├─ 埠：80/443 → 9080 (host)
│  │   ├─ 卷：frontend/dist → /usr/share/nginx/html
│  │   ├─ Nginx 配置：/etc/nginx/nginx.conf
│  │   └─ 反向代理：/ → frontend, /api → backend
│  │
│  └─ Docker Network
│      └─ 所有容器通過服務名通訊 (db, redis, backend)
│
└─ 埠暴露
   ├─ 9080: 前端 (http://localhost:9080)
   ├─ 9100: 後端 API (http://localhost:9100)
   ├─ 33306: MySQL (localhost:33306)
   └─ 6379: Redis (localhost:6379)
```

## docker-compose.yml 配置

```yaml
version: '3.8'

services:
  # MySQL 8.0 資料庫
  db:
    image: mysql:8.0
    container_name: webpdtool_mysql
    ports:
      - "33306:3306"
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD:-rootpassword}
      MYSQL_DATABASE: ${MYSQL_DATABASE:-webpdtool}
      MYSQL_USER: ${MYSQL_USER:-pdtool}
      MYSQL_PASSWORD: ${MYSQL_PASSWORD:-pdtool123}
    volumes:
      - ./database/schema.sql:/docker-entrypoint-initdb.d/01-schema.sql
      - ./database/seed_data.sql:/docker-entrypoint-initdb.d/02-seed.sql
      - mysql_data:/var/lib/mysql
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - webpdtool_network

  # Redis 日誌和快取
  redis:
    image: redis:7-alpine
    container_name: webpdtool_redis
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    networks:
      - webpdtool_network

  # FastAPI 後端
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: webpdtool_backend
    ports:
      - "9100:9100"
    environment:
      DATABASE_URL: mysql+asyncmy://pdtool:pdtool123@db:3306/webpdtool
      REDIS_URL: redis://redis:6379/0
      SECRET_KEY: ${SECRET_KEY:-change-this-in-production}
      ACCESS_TOKEN_EXPIRE_MINUTES: 480
      DEBUG: ${DEBUG:-false}
      LOG_LEVEL: ${LOG_LEVEL:-INFO}
      REDIS_ENABLED: true
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    volumes:
      - ./backend:/app
      - backend_logs:/app/logs
    command: uvicorn app.main:app --host 0.0.0.0 --port 9100
    networks:
      - webpdtool_network
    restart: unless-stopped

  # Vue 3 前端 + Nginx
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      args:
        VITE_API_BASE_URL: ${VITE_API_BASE_URL:-http://localhost:9100}
    container_name: webpdtool_frontend
    ports:
      - "9080:80"
    depends_on:
      - backend
    volumes:
      - ./frontend/nginx.conf:/etc/nginx/nginx.conf:ro
    networks:
      - webpdtool_network
    restart: unless-stopped

volumes:
  mysql_data:
  redis_data:
  backend_logs:

networks:
  webpdtool_network:
    driver: bridge
```

## 環境變數配置

### .env (專案根目錄)

```bash
# ============== 資料庫 ==============
MYSQL_ROOT_PASSWORD=rootpassword
MYSQL_PASSWORD=pdtool123
MYSQL_USER=pdtool
MYSQL_DATABASE=webpdtool

# ============== 後端 ==============
SECRET_KEY=your-secret-key-must-be-32-chars-or-longer-change-in-production
DATABASE_URL=mysql+asyncmy://pdtool:pdtool123@db:3306/webpdtool
REDIS_URL=redis://redis:6379/0

# Token 過期時間 (分鐘)
ACCESS_TOKEN_EXPIRE_MINUTES=480  # 8 小時

# 日誌配置
LOG_LEVEL=INFO
REDIS_ENABLED=true
ENABLE_JSON_LOGS=false

# 應用配置
DEBUG=false
APP_NAME=WebPDTool
APP_VERSION=0.1.0

# CORS 配置 (逗號分隔)
CORS_ORIGINS=http://localhost:9080,http://localhost:3000

# ============== 前端 ==============
VITE_API_BASE_URL=http://localhost:9100

# ============== 埠 ==============
FRONTEND_PORT=9080
BACKEND_PORT=9100
MYSQL_PORT=33306
```

## Docker 常用命令

### 啟動和停止

```bash
# 啟動所有服務
docker-compose up -d

# 檢視執行狀態
docker-compose ps

# 檢視日誌
docker-compose logs -f backend      # 實時檢視後端日誌
docker-compose logs -f mysql        # 資料庫日誌

# 停止服務
docker-compose stop

# 停止並刪除容器 (保留卷)
docker-compose down

# 停止並刪除容器和卷 (完全清理)
docker-compose down -v

# 重啟服務
docker-compose restart backend
```

### 執行命令

```bash
# 在後端容器內執行 Python 命令
docker-compose exec backend python -c "import app"

# 執行資料庫遷移
docker-compose exec backend alembic upgrade head

# 執行測試
docker-compose exec backend pytest

# 進入後端容器 shell
docker-compose exec backend bash

# 進入資料庫
docker-compose exec db mysql -uroot -p${MYSQL_ROOT_PASSWORD} webpdtool

# 執行 SQL 語句
docker-compose exec db mysql -uroot -p${MYSQL_ROOT_PASSWORD} webpdtool \
  -e "SELECT COUNT(*) FROM test_sessions;"
```

### 構建和推送

```bash
# 重新構建映象 (程式碼改變後)
docker-compose build --no-cache

# 推送映象到倉庫 (如 Docker Hub、私有倉庫)
docker tag webpdtool_backend:latest myregistry.com/webpdtool-backend:latest
docker push myregistry.com/webpdtool-backend:latest
```

## 本地開發環境

### 後端開發 (熱載入)

```bash
cd backend

# 建立虛擬環境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安裝依賴
pip install -e ".[dev]"

# 執行開發伺服器 (自動重載)
uvicorn app.main:app --reload --host 0.0.0.0 --port 9100

# 需要有效的.env 檔案或環境變數:
export DATABASE_URL=mysql+pymysql://pdtool:pdtool123@localhost:33306/webpdtool
export SECRET_KEY=dev-secret-key
```

### 前端開發 (熱重載)

```bash
cd frontend

# 安裝依賴
npm install

# 開發伺服器 (Vite 熱更新)
npm run dev

# 生產構建
npm run build

# 預覽生產構建
npm run preview
```

### 資料庫初始化

```bash
# Docker 啟動後初始化資料庫
docker-compose exec db mysql -uroot -p${MYSQL_ROOT_PASSWORD} webpdtool \
  < database/schema.sql

# 匯入示例資料
docker-compose exec db mysql -uroot -p${MYSQL_ROOT_PASSWORD} webpdtool \
  < database/seed_data.sql

# 驗證資料
docker-compose exec db mysql -uroot -p${MYSQL_ROOT_PASSWORD} webpdtool \
  -e "SELECT * FROM users; SELECT COUNT(*) FROM test_plans;"
```

## 生產部署

### 前置條件

```bash
# 伺服器要求
- OS: Ubuntu 20.04+ 或 CentOS 8+
- Docker: 20.10+
- Docker Compose: 2.0+
- 最小配置：2 核 CPU, 4GB 記憶體，50GB 硬碟
```

### 部署步驟

#### 1. 伺服器準備

```bash
# 克隆程式碼
git clone https://github.com/company/webpdtool.git
cd webpdtool

# 安裝 Docker 和 Compose
curl -sSL https://get.docker.com/ | sh
sudo usermod -aG docker $USER

# 版本檢查
docker --version
docker-compose --version
```

#### 2. 環境配置

```bash
# 複製環境模板
cp .env.example .env

# 編輯.env，更改為生產值
nano .env

# 關鍵變數必須改:
# - SECRET_KEY (生成 32 字元隨機值)
# - MYSQL_ROOT_PASSWORD
# - CORS_ORIGINS (改為實際域名)
# - DEBUG=false
# - HTTPS 配置

# 生成強 SECRET_KEY
openssl rand -base64 32
```

#### 3. HTTPS 配置 (Let's Encrypt)

```bash
# 安裝 Certbot
sudo apt install certbot python3-certbot-nginx -y

# 獲取證書
sudo certbot certonly --standalone \
  -d webpdtool.example.com \
  -m admin@example.com \
  --agree-tos

# 驗證證書位置
ls /etc/letsencrypt/live/webpdtool.example.com/

# 更新 Nginx 配置使用證書
# 在 nginx.conf 中配置:
# ssl_certificate /etc/letsencrypt/live/webpdtool.example.com/fullchain.pem;
# ssl_certificate_key /etc/letsencrypt/live/webpdtool.example.com/privkey.pem;

# 自動續期
sudo systemctl enable certbot.timer
```

#### 4. 啟動和驗證

```bash
# 構建映象 (首次)
docker-compose build

# 啟動所有服務
docker-compose up -d

# 驗證健康狀態
docker-compose ps
# 全部狀態應為 "Up"

# 檢查 API
curl http://localhost:9100/docs

# 資料庫健康檢查
docker-compose exec db mysqladmin ping

# 日誌檢查
docker-compose logs --tail=50
```

#### 5. 資料庫準備

```bash
# 匯入 schema
docker-compose exec db mysql -uroot -p${MYSQL_ROOT_PASSWORD} webpdtool \
  < database/schema.sql

# 匯入資料
docker-compose exec db mysql -uroot -p${MYSQL_ROOT_PASSWORD} webpdtool \
  < database/seed_data.sql

# 修改預設密碼
docker-compose exec backend python -c "
from app.services.auth import hash_password
from app.models.user import User
# 更新 admin 密碼
"
```

## 監控和維護

### 日誌管理

```bash
# 設定日誌級別
docker-compose exec backend grep LOG_LEVEL /app/.env

# 檢視實時日誌
docker-compose logs -f --tail=100 backend

# 日誌檔案位置
docker-compose exec backend ls -la logs/

# Redis 日誌檢視
redis-cli -h localhost -p 6379 MONITOR
```

### 效能監控

```bash
# CPU 和記憶體使用
docker stats

# 資料庫連線數
docker-compose exec db mysql -uroot -p${MYSQL_ROOT_PASSWORD} \
  -e "SHOW PROCESSLIST;"

# 快取使用情況
redis-cli INFO memory
```

### 備份策略

```bash
# 日常備份指令碼 (backup.sh)
#!/bin/bash

BACKUP_DIR="/backup/webpdtool"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 資料庫備份
docker-compose exec -T db mysqldump \
  -uroot -p${MYSQL_ROOT_PASSWORD} webpdtool \
  > ${BACKUP_DIR}/db_${TIMESTAMP}.sql

# 壓縮備份
gzip ${BACKUP_DIR}/db_${TIMESTAMP}.sql

# 清理 7 天前的備份
find ${BACKUP_DIR} -name "*.sql.gz" -mtime +7 -delete

echo "備份完成：${BACKUP_DIR}/db_${TIMESTAMP}.sql.gz"

# 設定定時任務 (crontab -e)
# 0 2 * * * /path/to/backup.sh  # 每天 02:00 執行
```

### 恢復和遷移

```bash
# 恢復資料庫
docker-compose exec -T db mysql \
  -uroot -p${MYSQL_ROOT_PASSWORD} webpdtool \
  < backup/db_20260311_020000.sql

# 遷移到新伺服器
# 1. 匯出資料
docker-compose exec -T db mysqldump \
  -uroot -p${MYSQL_ROOT_PASSWORD} webpdtool \
  > full_backup.sql

# 2. 匯出卷
docker run --rm -v webpdtool_mysql_data:/source \
  -v /tmp:/backup alpine tar czf /backup/mysql_volume.tar.gz -C /source .

# 3. 在新伺服器匯入
docker run --rm -v webnewpdtool_mysql_data:/target \
  -v /tmp:/backup alpine tar xzf /backup/mysql_volume.tar.gz -C /target
```

## 安全加固

### 防火牆配置

```bash
# UFW (Ubuntu)
sudo ufw default deny incoming
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 9080/tcp    # 前端 HTTP
sudo ufw allow 443/tcp     # HTTPS
sudo ufw enable

# iptables (CentOS)
sudo firewall-cmd --add-port=9080/tcp --permanent
sudo firewall-cmd --add-port=443/tcp --permanent
sudo firewall-cmd --reload
```

### Docker 網路隔離

```bash
# 不暴露 MySQL 和 Redis 到外網
# docker-compose.yml 中移除 ports 配置，僅保留 networks

db:
  # ports: 不配置 (移除外網訪問)
  networks:
    - webpdtool_network  # 僅內部訪問

backend:
  # 僅暴露 9100 給前端
  ports:
    - "127.0.0.1:9100:9100"  # 僅 localhost 可訪問
```

### Nginx 反向代理配置

```nginx
# frontend/nginx.conf

server {
    listen 80;
    server_name webpdtool.example.com;

    # 重定向到 HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name webpdtool.example.com;

    # SSL 證書
    ssl_certificate /etc/letsencrypt/live/webpdtool.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/webpdtool.example.com/privkey.pem;

    # 安全頭
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # 前端路由
    root /usr/share/nginx/html;

    location / {
        try_files $uri /index.html;
    }

    # API 反向代理
    location /api {
        proxy_pass http://backend:9100;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket 支援 (未來)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## 更新和升級

### 應用更新流程

```bash
# 1. 拉取最新程式碼
git pull origin main

# 2. 檢查依賴變化
git diff HEAD~1 backend/pyproject.toml
git diff HEAD~1 frontend/package.json

# 3. 重建映象
docker-compose build --no-cache

# 4. 備份當前資料
./backup.sh

# 5. 執行資料庫遷移 (如果有)
docker-compose exec backend alembic upgrade head

# 6. 重啟服務
docker-compose down
docker-compose up -d

# 7. 驗證
docker-compose ps
curl http://localhost:9100/docs
```

## 故障排查

### 常見問題

**問題：容器無法啟動**
```bash
# 檢視日誌
docker-compose logs backend

# 檢查配置
docker-compose config

# 驗證映象
docker images | grep webpdtool
```

**問題：資料庫連線失敗**
```bash
# 檢查健康
docker-compose ps

# 測試連線
docker-compose exec backend python -c \
  "from app.core.database import engine; print('OK')"
```

**問題：API 超時**
```bash
# 檢查資源使用
docker stats

# 檢視日誌
docker-compose logs --tail=100 backend

# 增加超時時間
# docker-compose.yml 中新增:
# deploy:
#   resources:
#     limits:
#       memory: 2G
```

## 下一步

- **開發指南**: [10-development-guide.md](10-development-guide.md)
- **安全配置**: [08-authentication-security.md](08-authentication-security.md)
- **API 參考**: [06-api-endpoints.md](06-api-endpoints.md)
