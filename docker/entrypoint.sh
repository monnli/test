#!/usr/bin/env bash
# 青苗守护者 · 容器启动入口脚本
# 1. 等待 MySQL 就绪
# 2. 首次启动自动初始化数据库 + 写入演示数据（幂等）
# 3. 把控制权交给 CMD（supervisord）

set -e

INIT_FLAG=/app/storage/.initialized

echo "================================================================"
echo "  青苗守护者 · 启动中..."
echo "  MySQL: ${MYSQL_HOST:-mysql}:${MYSQL_PORT:-3306}"
echo "  数据库: ${MYSQL_DATABASE:-qingmiao_guardian}"
echo "================================================================"

# 等待 MySQL 可连接（最多 60 秒）
for i in $(seq 1 30); do
    if python -c "
import os, pymysql
try:
    c = pymysql.connect(
        host=os.getenv('MYSQL_HOST', 'mysql'),
        port=int(os.getenv('MYSQL_PORT', 3306)),
        user=os.getenv('MYSQL_USER', 'qingmiao'),
        password=os.getenv('MYSQL_PASSWORD', 'qingmiao123'),
        connect_timeout=2,
    )
    c.close()
" 2>/dev/null; then
        echo "[OK] MySQL 已就绪"
        break
    fi
    echo "  等待 MySQL 就绪... ($i/30)"
    sleep 2
done

cd /app

# 首次启动初始化
if [ ! -f "$INIT_FLAG" ]; then
    echo ""
    echo "[INIT] 首次启动，初始化数据库与演示数据..."
    python scripts/init_db.py || { echo "[ERR] 建表失败"; exit 1; }
    python scripts/seed_demo_data.py || { echo "[ERR] 基础数据失败"; exit 1; }
    python scripts/seed_demo_extras.py || echo "[WARN] 增强数据写入失败（可忽略）"

    mkdir -p "$(dirname $INIT_FLAG)"
    touch "$INIT_FLAG"
    echo "[OK] 初始化完成"
else
    echo "[SKIP] 已初始化过，跳过数据写入"
fi

echo ""
echo "================================================================"
echo "  启动服务中（前端 + 后端 + AI）..."
echo "  访问：http://localhost"
echo "  账号：admin / admin123"
echo "================================================================"
echo ""

exec "$@"
