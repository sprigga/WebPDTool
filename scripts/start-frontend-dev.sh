#!/bin/bash

# Frontend 開發環境啟動腳本
# 用於本地開發和除錯

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}啟動 WebPDTool Frontend 開發伺服器${NC}"
echo -e "${GREEN}========================================${NC}"

# 檢查是否在正確的目錄
if [ ! -d "frontend" ]; then
    echo -e "${RED}錯誤: 請在專案根目錄執行此腳本${NC}"
    exit 1
fi

# 進入 frontend 目錄
cd frontend

# 檢查 Node.js
echo -e "${YELLOW}檢查 Node.js 環境...${NC}"
if ! command -v node &> /dev/null; then
    echo -e "${RED}錯誤: 未安裝 Node.js${NC}"
    exit 1
fi

# 檢查 npm
if ! command -v npm &> /dev/null; then
    echo -e "${RED}錯誤: 未安裝 npm${NC}"
    exit 1
fi

# 檢查 node_modules 是否存在
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}node_modules 不存在,執行 npm install...${NC}"
    npm install
else
    echo -e "${GREEN}node_modules 已存在${NC}"
fi

# 顯示配置資訊
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}配置資訊:${NC}"
echo -e "  應用: WebPDTool Frontend"
echo -e "  框架: Vue 3 + Vite"
echo -e "  環境: 開發模式"
echo -e "  熱重載: 啟用"
echo -e "${GREEN}========================================${NC}"

# 啟動 Vite 開發伺服器
echo -e "${GREEN}啟動開發伺服器...${NC}"
echo -e "${YELLOW}按 Ctrl+C 停止伺服器${NC}"
echo ""

# 執行 npm run dev
npm run dev
