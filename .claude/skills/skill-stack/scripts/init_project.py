#!/usr/bin/env python3
"""
初始化 Vue 3 + FastAPI 全端專案結構
"""
import os
import sys
from pathlib import Path


def create_directory(path: Path):
    """創建目錄"""
    path.mkdir(parents=True, exist_ok=True)
    print(f"✓ Created: {path}")


def create_file(path: Path, content: str = ""):
    """創建檔案"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    print(f"✓ Created: {path}")


def init_backend_structure(base_dir: Path):
    """初始化後端專案結構"""
    backend_dir = base_dir / "backend"

    # 創建目錄結構
    directories = [
        backend_dir / "app",
        backend_dir / "app" / "api",
        backend_dir / "app" / "core",
        backend_dir / "app" / "models",
        backend_dir / "app" / "schemas",
        backend_dir / "app" / "services",
        backend_dir / "app" / "db",
        backend_dir / "tests",
    ]

    for directory in directories:
        create_directory(directory)

    # 創建基本檔案
    files = {
        backend_dir / "main.py": '''"""
FastAPI 應用程式進入點
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Welcome to FastAPI"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
''',
        backend_dir / "app" / "__init__.py": "",
        backend_dir / "app" / "core" / "__init__.py": "",
        backend_dir / "app" / "core" / "config.py": '''"""
應用程式配置
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    PROJECT_NAME: str = "My API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "API for My Application"

    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:9080"]

    # Database
    DATABASE_URL: str = "mysql+asyncmy://user:password@localhost:33306/mydb"

    # JWT
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"


settings = Settings()
''',
        backend_dir / "app" / "db" / "__init__.py": "",
        backend_dir / "app" / "db" / "session.py": '''"""
資料庫連線配置
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,
    pool_pre_ping=True,
)

AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncSession:
    """獲取資料庫會話"""
    async with AsyncSessionLocal() as session:
        yield session
''',
        backend_dir / "requirements.txt": '''fastapi==0.115.6
uvicorn[standard]==0.34.0
sqlalchemy==2.0.36
asyncmy==0.2.9
pydantic==2.10.5
pydantic-settings==2.7.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.20
''',
        backend_dir / ".env.example": '''PROJECT_NAME=My API
VERSION=1.0.0
DATABASE_URL=mysql+asyncmy://user:password@localhost:33306/mydb
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30
''',
        backend_dir / "Dockerfile": '''FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
''',
    }

    for file_path, content in files.items():
        create_file(file_path, content)


def init_frontend_structure(base_dir: Path):
    """初始化前端專案結構"""
    frontend_dir = base_dir / "frontend"

    # 創建目錄結構
    directories = [
        frontend_dir / "src",
        frontend_dir / "src" / "api",
        frontend_dir / "src" / "assets",
        frontend_dir / "src" / "components",
        frontend_dir / "src" / "router",
        frontend_dir / "src" / "stores",
        frontend_dir / "src" / "utils",
        frontend_dir / "src" / "views",
        frontend_dir / "public",
    ]

    for directory in directories:
        create_directory(directory)

    # 創建基本檔案
    files = {
        frontend_dir / "package.json": '''{
  "name": "frontend",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "vue": "^3.5.13",
    "vue-router": "^4.5.0",
    "pinia": "^2.3.0",
    "element-plus": "^2.9.1",
    "axios": "^1.7.9"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.2.1",
    "vite": "^6.0.7"
  }
}
''',
        frontend_dir / "vite.config.js": '''import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    port: 9080,
    proxy: {
      '/api': {
        target: 'http://localhost:9100',
        changeOrigin: true,
      }
    }
  }
})
''',
        frontend_dir / "index.html": '''<!DOCTYPE html>
<html lang="zh-TW">
  <head>
    <meta charset="UTF-8">
    <link rel="icon" href="/favicon.ico">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>My App</title>
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="/src/main.js"></script>
  </body>
</html>
''',
        frontend_dir / "src" / "main.js": '''import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import router from './router'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(ElementPlus)

app.mount('#app')
''',
        frontend_dir / "src" / "App.vue": '''<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script setup>
</script>

<style scoped>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
</style>
''',
        frontend_dir / "Dockerfile": '''FROM node:20-alpine as build

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
''',
        frontend_dir / "nginx.conf": '''server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
''',
    }

    for file_path, content in files.items():
        create_file(file_path, content)


def init_docker_compose(base_dir: Path):
    """創建 docker-compose.yml"""
    content = '''version: '3.8'

services:
  mysql:
    image: mysql:8.0
    container_name: myapp-mysql
    environment:
      MYSQL_ROOT_PASSWORD: rootpassword
      MYSQL_DATABASE: mydb
      MYSQL_USER: user
      MYSQL_PASSWORD: password
    ports:
      - "33306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build: ./backend
    container_name: myapp-backend
    ports:
      - "9100:8000"
    environment:
      DATABASE_URL: mysql+asyncmy://user:password@mysql:3306/mydb
    depends_on:
      mysql:
        condition: service_healthy
    volumes:
      - ./backend:/app
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build: ./frontend
    container_name: myapp-frontend
    ports:
      - "9080:80"
    depends_on:
      - backend

volumes:
  mysql_data:
'''
    create_file(base_dir / "docker-compose.yml", content)


def init_readme(base_dir: Path):
    """創建 README.md"""
    content = '''# 全端專案

Vue 3 + FastAPI 全端應用程式

## 技術堆疊

### 前端
- Vue 3
- Element Plus
- Pinia
- Vue Router
- Axios
- Vite

### 後端
- FastAPI
- SQLAlchemy 2.0
- Pydantic v2
- MySQL 8.0+

## 快速開始

### 使用 Docker Compose (推薦)

```bash
# 啟動所有服務
docker-compose up -d

# 查看日誌
docker-compose logs -f

# 停止服務
docker-compose down
```

訪問:
- 前端: http://localhost:9080
- 後端 API 文件: http://localhost:9100/docs
- MySQL: localhost:33306

### 本地開發

#### 後端

```bash
cd backend
uv venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
uv pip install -r requirements.txt
cp .env.example .env
# 編輯 .env 設定資料庫連線
uvicorn main:app --reload --port 9100
```

#### 前端

```bash
cd frontend
npm install
npm run dev
```

#### 資料庫

```bash
docker-compose up -d mysql
```

## 專案結構

```
.
├── backend/
│   ├── app/
│   │   ├── api/          # API 路由
│   │   ├── core/         # 核心配置
│   │   ├── db/           # 資料庫配置
│   │   ├── models/       # 資料模型
│   │   ├── schemas/      # Pydantic schemas
│   │   └── services/     # 業務邏輯
│   ├── tests/            # 測試
│   ├── main.py           # 應用程式進入點
│   └── requirements.txt  # Python 依賴
├── frontend/
│   ├── src/
│   │   ├── api/          # API 服務
│   │   ├── assets/       # 靜態資源
│   │   ├── components/   # Vue 組件
│   │   ├── router/       # 路由配置
│   │   ├── stores/       # Pinia stores
│   │   ├── utils/        # 工具函數
│   │   └── views/        # 頁面組件
│   └── package.json      # NPM 依賴
└── docker-compose.yml    # Docker 編排
```
'''
    create_file(base_dir / "README.md", content)


def main():
    """主函數"""
    if len(sys.argv) > 1:
        project_name = sys.argv[1]
    else:
        project_name = input("請輸入專案名稱: ").strip() or "my-fullstack-app"

    base_dir = Path.cwd() / project_name

    if base_dir.exists():
        print(f"錯誤: 目錄 {base_dir} 已存在")
        sys.exit(1)

    print(f"\n開始初始化專案: {project_name}\n")

    # 創建專案根目錄
    create_directory(base_dir)

    # 初始化各部分
    init_backend_structure(base_dir)
    init_frontend_structure(base_dir)
    init_docker_compose(base_dir)
    init_readme(base_dir)

    print(f"\n✓ 專案初始化完成!")
    print(f"\n下一步:")
    print(f"  cd {project_name}")
    print(f"  docker-compose up -d")
    print(f"\n或本地開發:")
    print(f"  cd {project_name}/backend && uv pip install -r requirements.txt")
    print(f"  cd {project_name}/frontend && npm install")


if __name__ == "__main__":
    main()
