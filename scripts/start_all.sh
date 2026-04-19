#!/usr/bin/env bash
# 一键启动青苗守护者所有服务（Linux / macOS）
# 用法：bash scripts/start_all.sh

set -e
cd "$(dirname "$0")/.."
PROJECT_ROOT="$(pwd)"

# 颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

mkdir -p logs

cleanup() {
  echo -e "\n${YELLOW}正在停止所有服务...${NC}"
  kill $BACKEND_PID $AI_PID $FRONT_PID 2>/dev/null || true
  exit 0
}
trap cleanup INT TERM

echo -e "${GREEN}[1/4]${NC} 启动 AI 推理服务（http://localhost:8000）"
cd "$PROJECT_ROOT/ai_service"
nohup python server.py > "$PROJECT_ROOT/logs/ai.log" 2>&1 &
AI_PID=$!

sleep 2

echo -e "${GREEN}[2/4]${NC} 启动 Flask 后端（http://localhost:5000）"
cd "$PROJECT_ROOT/backend"
nohup python run.py > "$PROJECT_ROOT/logs/backend.log" 2>&1 &
BACKEND_PID=$!

sleep 2

echo -e "${GREEN}[3/4]${NC} 启动前端开发服务器（http://localhost:5173）"
cd "$PROJECT_ROOT/frontend"
nohup npm run dev > "$PROJECT_ROOT/logs/frontend.log" 2>&1 &
FRONT_PID=$!

sleep 4

echo -e "${GREEN}[4/4]${NC} 全部启动完成！日志在 ./logs/"
echo
echo "  📊 数据大屏：     http://localhost:5173/dashboard"
echo "  🏠 工作台：       http://localhost:5173/workbench"
echo "  🔑 默认账号：     admin / admin123"
echo
echo "  按 Ctrl+C 停止所有服务"

wait
