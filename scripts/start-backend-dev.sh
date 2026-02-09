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

# 清除可能干擾的 VIRTUAL_ENV 環境變數
# 確保使用 backend/.venv 而非根目錄的 .venv
if [ ! -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}偵測到 VIRTUAL_ENV 環境變數: ${VIRTUAL_ENV}${NC}"
    echo -e "${YELLOW}將使用 backend 專屬虛擬環境 (.venv)${NC}"
    unset VIRTUAL_ENV
fi

# 預防性檢查：拒絕以 sudo/root 執行，避免虛擬環境權限問題
if [ "$EUID" -eq 0 ]; then
    echo -e "${RED}錯誤: 請不要以 root 身份執行此腳本${NC}"
    echo -e "${YELLOW}這會導致虛擬環境權限問題。請以普通用戶身份執行：${NC}"
    echo -e "${YELLOW}  ./scripts/start-backend-dev.sh${NC}"
    exit 1
fi

# 預防性檢查：拒絕以 sudo/root 執行，避免虛擬環境權限問題
if [ "$EUID" -eq 0 ]; then
    echo -e "${RED}錯誤: 請不要以 root 身份執行此腳本${NC}"
    echo -e "${YELLOW}這會導致虛擬環境權限問題。請以普通用戶身份執行：${NC}"
    echo -e "${YELLOW}  ./scripts/start-backend-dev.sh${NC}"
    exit 1
fi

# 檢查虛擬環境權限，採用實用性策略
# 策略：先測試實際可寫性，失敗則嘗試 sudo chown 修復，最後無法修復時明確提示
VENV_PATH="./.venv"
if [ -d "$VENV_PATH" ]; then
    # 測試虛擬環境是否可寫（創建測試檔案）
    TEST_FILE="$VENV_PATH/.write_test_$$"
    if touch "$TEST_FILE" 2>/dev/null; then
        rm -f "$TEST_FILE"
        # 可寫，檢查所有者是否匹配（僅警告，不強制修復）
        VENV_OWNER=$(stat -c "%U" "$VENV_PATH" 2>/dev/null || stat -f "%Su" "$VENV_PATH" 2>/dev/null || echo "unknown")
        if [ "$VENV_OWNER" != "$(whoami)" ]; then
            echo -e "${YELLOW}注意: 虛擬環境所有者為 ${VENV_OWNER}（可寫，但不建議）${NC}"
        fi
    else
        # 不可寫，嘗試修復
        echo -e "${YELLOW}偵測到虛擬環境無法寫入${NC}"
        echo -e "${GREEN}正在嘗試修復權限...${NC}"

        # 嘗試使用 sudo 修復權限
        if sudo chown -R "$(whoami):$(whoami)" "$VENV_PATH" 2>/dev/null; then
            echo -e "${GREEN}✓ 權限修復成功${NC}"
        else
            echo -e "${RED}錯誤: 無法自動修復虛擬環境權限${NC}"
            echo -e "${YELLOW}請手動執行以下命令後重試:${NC}"
            echo -e "  ${YELLOW}sudo chown -R $(whoami): $(whoami) ${VENV_PATH}${NC}"
            echo -e "  ${YELLOW}或刪除重建: sudo rm -rf ${VENV_PATH}${NC}"
            exit 1
        fi
    fi
fi

# 安裝/更新依賴
echo -e "${YELLOW}檢查並安裝依賴...${NC}"
uv sync

# 驗證虛擬環境位置
if [ ! -d "$VENV_PATH" ]; then
    echo -e "${RED}錯誤: 虛擬環境未建立於 ${VENV_PATH}${NC}"
    exit 1
fi

echo -e "${GREEN}使用虛擬環境: ${VENV_PATH}${NC}"

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
