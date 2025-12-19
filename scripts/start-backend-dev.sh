#!/bin/bash

# Backend 開發環境啟動腳本
# 用於本地開發和除錯

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}啟動 WebPDTool Backend 開發伺服器${NC}"
echo -e "${GREEN}========================================${NC}"

# 檢查是否在正確的目錄
if [ ! -d "backend" ]; then
    echo -e "${RED}錯誤: 請在專案根目錄執行此腳本${NC}"
    exit 1
fi

# 進入 backend 目錄
cd backend

# 檢查 .env 文件
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}警告: .env 文件不存在,從 .env.example 複製...${NC}"
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}.env 文件已創建,請根據需要修改配置${NC}"
    else
        echo -e "${RED}錯誤: .env.example 也不存在${NC}"
        exit 1
    fi
fi

# 檢查 Python 環境
echo -e "${YELLOW}檢查 Python 環境...${NC}"
if ! command -v uv &> /dev/null; then
    echo -e "${RED}錯誤: 未安裝 uv,請先安裝: pip install uv${NC}"
    exit 1
fi

# 安裝/更新依賴
echo -e "${YELLOW}檢查並安裝依賴...${NC}"
uv sync

# 檢查資料庫連線 (可選)
echo -e "${YELLOW}準備啟動 FastAPI 開發伺服器...${NC}"

# 檢查端口是否已被佔用，如果是則終止佔用的程序
PORT=8765
echo -e "${YELLOW}檢查端口 ${PORT} 是否可用...${NC}"

# # 檢查該端口是否有程序在運行
# PID=$(lsof -t -i:${PORT})
# if [ ! -z "$PID" ]; then
#     echo -e "${YELLOW}端口 ${PORT} 已被佔用，PID: ${PID}，正在停止相關程序...${NC}"
#     kill -9 $PID
#     sleep 2  # 等待端口釋放
# else
#     echo -e "${GREEN}端口 ${PORT} 可用${NC}"
# fi

# 顯示配置資訊
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}配置資訊:${NC}"
echo -e "  應用: WebPDTool Backend"
echo -e "  環境: 開發模式"
echo -e "  熱重載: 啟用"
echo -e "  日誌級別: DEBUG"
echo -e "  端口: ${PORT}"
echo -e "${GREEN}========================================${NC}"

# 啟動 uvicorn 開發伺服器 (啟用熱重載)
echo -e "${GREEN}啟動伺服器...${NC}"
echo -e "${YELLOW}按 Ctrl+C 停止伺服器${NC}"
echo ""

# 使用 uv run 執行,啟用熱重載和詳細日誌
# 使用冷門 port 8765 避免與其他容器衝突
uv run uvicorn app.main:app \
    --host 0.0.0.0 \
    --port ${PORT} \
    --reload \
    --reload-dir app \
    --log-level debug \
    --access-log
