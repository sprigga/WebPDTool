# WebPDTool 開發啟動腳本

本目錄包含用於本地開發和除錯的啟動腳本。

## 腳本說明

### 1. start-backend-dev.sh
啟動 Backend 開發伺服器 (FastAPI + Uvicorn)

**特點:**
- 自動使用 uv 管理 Python 環境
- 啟用熱重載 (修改代碼自動重啟)
- DEBUG 日誌級別
- 自動檢查並安裝依賴
- 自動創建 .env 文件 (如不存在)

**使用方法:**
```bash
# 在專案根目錄執行
./scripts/start-backend-dev.sh
```

**服務地址:**
- API: http://localhost:8765
- API 文檔: http://localhost:8765/docs
- ReDoc: http://localhost:8765/redoc

---

### 2. start-frontend-dev.sh
啟動 Frontend 開發伺服器 (Vue 3 + Vite)

**特點:**
- Vite 快速熱更新 (HMR)
- 自動檢查 Node.js 環境
- 自動安裝 npm 依賴 (如需要)

**使用方法:**
```bash
# 在專案根目錄執行
./scripts/start-frontend-dev.sh
```

**服務地址:**
- Frontend: http://localhost:5678

---

### 3. start-dev.sh
同時啟動 Frontend 和 Backend 開發伺服器

**特點:**
- 支援兩種模式:
  - **tmux 模式** (推薦): 分割視窗,方便查看兩個服務的日誌
  - **背景進程模式**: 如果未安裝 tmux,以背景進程方式啟動
- 自動處理進程清理
- Ctrl+C 可同時停止兩個服務

**使用方法:**
```bash
# 在專案根目錄執行
./scripts/start-dev.sh
```

**tmux 模式操作提示:**
- `Ctrl+B` 然後按方向鍵: 切換窗格
- `Ctrl+B` 然後按 `d`: 離開 tmux (服務繼續運行)
- `Ctrl+B` 然後按 `&`: 關閉整個 session
- `tmux attach -t webpdtool-dev`: 重新連接到 session

---

## 前置需求

### Backend
- Python 3.9+
- uv (Python 套件管理工具)
  ```bash
  pip install uv
  ```

### Frontend
- Node.js 16+
- npm 或 yarn

### 完整開發環境 (推薦安裝 tmux)
```bash
# Ubuntu/Debian
sudo apt-get install tmux

# macOS
brew install tmux
```

---

## 故障排除

### Backend 無法啟動
1. 檢查 Python 版本: `python --version` (需要 >= 3.9)
2. 檢查 uv 是否安裝: `uv --version`
3. 檢查 .env 文件配置
4. 查看 backend/logs/ 目錄下的日誌

### Frontend 無法啟動
1. 檢查 Node.js 版本: `node --version` (需要 >= 16)
2. 刪除 frontend/node_modules 並重新安裝: `cd frontend && rm -rf node_modules && npm install`
3. 檢查端口 5173 是否被占用

### 端口被占用
```bash
# 查找占用端口的進程
lsof -i :8765  # Backend
lsof -i :5678  # Frontend

# 終止進程
kill -9 <PID>
```

**注意:** 本專案使用冷門端口 (Backend: 8765, Frontend: 5678) 以避免與其他容器服務衝突。

---

## 開發工作流程建議

1. **開始開發**: 使用 `./scripts/start-dev.sh` 同時啟動前後端
2. **單獨除錯 Backend**: 使用 `./scripts/start-backend-dev.sh`
3. **單獨除錯 Frontend**: 使用 `./scripts/start-frontend-dev.sh`
4. **修改代碼**: 兩個服務都支援熱重載,保存文件即可看到變更

---

## 注意事項

1. 所有腳本都應在**專案根目錄**執行
2. 確保腳本有執行權限: `chmod +x scripts/*.sh`
3. 首次執行可能需要較長時間安裝依賴
4. 開發時建議使用 tmux 模式,日誌查看更清晰
