#!/usr/bin/env bash
# 一键初始化数据库 + 写入完整演示数据
# 用法：bash scripts/init_demo.sh

set -e
cd "$(dirname "$0")/.."

GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${GREEN}[1/3]${NC} 创建数据库与表..."
python scripts/init_db.py

echo -e "${GREEN}[2/3]${NC} 写入基础数据（学校/班级/学生/教师/账号）..."
python scripts/seed_demo_data.py

echo -e "${GREEN}[3/5]${NC} 写入增强演示数据（量表/文本/对话/成绩/情绪时序/课堂/预警）..."
python scripts/seed_demo_extras.py

echo -e "${GREEN}[4/5]${NC} 合成 5 段演示课堂视频..."
python scripts/generate_demo_videos.py

echo -e "${GREEN}[5/5]${NC} 创建摄像头 + 课表（2026 春季学期）..."
python scripts/seed_cameras_and_schedules.py

echo
echo -e "${GREEN}✅ 初始化完成！${NC}"
echo "现在可以执行：bash scripts/start_all.sh"
