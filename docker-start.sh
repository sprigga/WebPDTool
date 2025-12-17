#!/bin/bash
# WebPDTool Docker Quick Start Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== WebPDTool Docker 快速啟動 ===${NC}"

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}未找到 .env 檔案，從 .env.example 複製...${NC}"
    cp .env.example .env
    echo -e "${RED}請編輯 .env 檔案，設定必要的環境變數（特別是密碼和 SECRET_KEY）${NC}"
    echo -e "${YELLOW}編輯完成後請重新執行此腳本${NC}"
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}錯誤: Docker 未運行，請先啟動 Docker${NC}"
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}錯誤: docker-compose 未安裝${NC}"
    exit 1
fi

# Parse command line arguments
MODE=${1:-production}

if [ "$MODE" = "dev" ] || [ "$MODE" = "development" ]; then
    echo -e "${YELLOW}啟動開發環境...${NC}"
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
elif [ "$MODE" = "prod" ] || [ "$MODE" = "production" ]; then
    echo -e "${YELLOW}啟動生產環境...${NC}"
    docker-compose up -d
elif [ "$MODE" = "build" ]; then
    echo -e "${YELLOW}重新建置並啟動...${NC}"
    docker-compose up -d --build
elif [ "$MODE" = "down" ]; then
    echo -e "${YELLOW}停止所有服務...${NC}"
    docker-compose down
elif [ "$MODE" = "logs" ]; then
    echo -e "${YELLOW}查看服務日誌...${NC}"
    docker-compose logs -f
elif [ "$MODE" = "status" ]; then
    echo -e "${YELLOW}查看服務狀態...${NC}"
    docker-compose ps
else
    echo -e "${RED}未知的模式: $MODE${NC}"
    echo "用法: $0 [production|dev|build|down|logs|status]"
    echo "  production (預設) - 啟動生產環境"
    echo "  dev               - 啟動開發環境（支援熱重載）"
    echo "  build             - 重新建置並啟動"
    echo "  down              - 停止所有服務"
    echo "  logs              - 查看服務日誌"
    echo "  status            - 查看服務狀態"
    exit 1
fi

# Wait for services to be ready (only for up commands)
if [ "$MODE" != "down" ] && [ "$MODE" != "logs" ] && [ "$MODE" != "status" ]; then
    echo -e "${YELLOW}等待服務啟動...${NC}"
    sleep 5

    echo -e "${GREEN}檢查服務狀態...${NC}"
    docker-compose ps

    echo ""
    echo -e "${GREEN}=== 服務已啟動 ===${NC}"
    echo -e "前端: ${GREEN}http://localhost${NC} (或 http://localhost:\${FRONTEND_PORT})"
    echo -e "後端 API: ${GREEN}http://localhost:8000${NC} (或 http://localhost:\${BACKEND_PORT})"
    echo -e "API 文檔: ${GREEN}http://localhost:8000/docs${NC}"
    echo ""
    echo -e "預設帳號:"
    echo -e "  管理員: ${YELLOW}admin / admin123${NC}"
    echo -e "  工程師: ${YELLOW}engineer1 / admin123${NC}"
    echo -e "  作業員: ${YELLOW}operator1 / admin123${NC}"
    echo ""
    echo -e "${YELLOW}查看日誌: docker-compose logs -f [service-name]${NC}"
    echo -e "${YELLOW}停止服務: docker-compose down${NC}"
fi
