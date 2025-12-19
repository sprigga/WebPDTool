#!/bin/bash

# 同時啟動 Frontend 和 Backend 開發伺服器
# 用於本地全棧開發和除錯

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}啟動 WebPDTool 全棧開發環境${NC}"
echo -e "${GREEN}========================================${NC}"

# 檢查是否在正確的目錄
if [ ! -d "frontend" ] || [ ! -d "backend" ]; then
    echo -e "${RED}錯誤: 請在專案根目錄執行此腳本${NC}"
    exit 1
fi

# 檢查是否已安裝 tmux 或 screen (可選,用於分割終端)
USE_TMUX=false
if command -v tmux &> /dev/null; then
    USE_TMUX=true
    echo -e "${GREEN}檢測到 tmux,將使用分割視窗模式${NC}"
fi

# 清理函數 - 確保退出時停止所有子進程
cleanup() {
    echo -e "\n${YELLOW}停止所有開發伺服器...${NC}"
    # 終止所有子進程
    jobs -p | xargs -r kill 2>/dev/null || true
    wait
    echo -e "${GREEN}所有服務已停止${NC}"
    exit 0
}

# 設置 trap 捕獲中斷信號
trap cleanup SIGINT SIGTERM

# 獲取腳本所在目錄
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

if [ "$USE_TMUX" = true ]; then
    # 使用 tmux 分割視窗模式
    echo -e "${BLUE}使用 tmux 模式啟動...${NC}"
    echo -e "${YELLOW}tmux 操作提示:${NC}"
    echo -e "  - Ctrl+B 然後按方向鍵: 切換窗格"
    echo -e "  - Ctrl+B 然後按 d: 離開 tmux (服務繼續運行)"
    echo -e "  - Ctrl+B 然後按 &: 關閉整個 session"
    echo -e "  - tmux attach -t webpdtool-dev: 重新連接"
    echo ""
    sleep 2

    # 檢查是否已存在同名 session
    if tmux has-session -t webpdtool-dev 2>/dev/null; then
        echo -e "${YELLOW}檢測到已存在的 session,將先關閉...${NC}"
        tmux kill-session -t webpdtool-dev
    fi

    # 創建新的 tmux session
    tmux new-session -d -s webpdtool-dev -n WebPDTool

    # 分割視窗為左右兩部分
    tmux split-window -h -t webpdtool-dev:0

    # 左側窗格運行 backend
    tmux send-keys -t webpdtool-dev:0.0 "cd $PROJECT_DIR" C-m
    tmux send-keys -t webpdtool-dev:0.0 "echo -e '${BLUE}Backend 開發伺服器${NC}'" C-m
    tmux send-keys -t webpdtool-dev:0.0 "./scripts/start-backend-dev.sh" C-m

    # 右側窗格運行 frontend
    tmux send-keys -t webpdtool-dev:0.1 "cd $PROJECT_DIR" C-m
    tmux send-keys -t webpdtool-dev:0.1 "echo -e '${BLUE}Frontend 開發伺服器${NC}'" C-m
    tmux send-keys -t webpdtool-dev:0.1 "./scripts/start-frontend-dev.sh" C-m

    # 附加到 session
    echo -e "${GREEN}正在附加到 tmux session...${NC}"
    tmux attach-session -t webpdtool-dev

else
    # 不使用 tmux,以背景進程方式啟動
    echo -e "${BLUE}以背景進程模式啟動...${NC}"
    echo -e "${YELLOW}注意: 日誌將交錯顯示${NC}"
    echo ""

    # 啟動 backend (背景)
    echo -e "${GREEN}[1/2] 啟動 Backend...${NC}"
    (
        cd "$PROJECT_DIR"
        ./scripts/start-backend-dev.sh 2>&1 | sed "s/^/[BACKEND] /"
    ) &
    BACKEND_PID=$!

    # 等待一下讓 backend 先啟動
    sleep 3

    # 啟動 frontend (背景)
    echo -e "${GREEN}[2/2] 啟動 Frontend...${NC}"
    (
        cd "$PROJECT_DIR"
        ./scripts/start-frontend-dev.sh 2>&1 | sed "s/^/[FRONTEND] /"
    ) &
    FRONTEND_PID=$!

    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}開發伺服器已啟動${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo -e "  Backend PID:  ${BACKEND_PID}"
    echo -e "  Frontend PID: ${FRONTEND_PID}"
    echo -e ""
    echo -e "  Backend URL:  ${BLUE}http://localhost:8765${NC}"
    echo -e "  Frontend URL: ${BLUE}http://localhost:5678${NC}"
    echo -e "  API Docs:     ${BLUE}http://localhost:8765/docs${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo -e "${YELLOW}按 Ctrl+C 停止所有服務${NC}"
    echo ""

    # 等待所有背景進程
    wait
fi
