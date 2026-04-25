# ======================================================================
# 青苗守护者 · 一体化 Docker 镜像
# 包含：Vue 3 前端（Nginx 托管）+ Flask 后端 + FastAPI AI 推理服务
# 数据库：MySQL 由 docker-compose 单独容器提供
# ======================================================================

# -------- Stage 1: 前端构建 --------
FROM node:20-alpine AS frontend-builder
#FROM docker.mirrors.sjtug.sjtu.edu.cn/library/node:20-alpine AS frontend-builder

WORKDIR /app
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm config set registry https://registry.npmmirror.com && \
    (npm ci --no-audit --no-fund || npm install --no-audit --no-fund)

COPY frontend/ ./
RUN npm run build


# -------- Stage 2: Python 运行时 + Nginx + Supervisor --------
FROM python:3.10-slim
#FROM docker.mirrors.sjtug.sjtu.edu.cn/library/python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    TZ=Asia/Shanghai \
    DEBIAN_FRONTEND=noninteractive

# 系统依赖 + Nginx + Supervisor（同时跑多进程）
# ==================== 替换国内阿里云 apt 源 ====================
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources \
    && sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources

# 系统依赖 + Nginx + Supervisor（同时跑多进程）
RUN apt-get update && apt-get install -y --no-install-recommends \
        nginx \
        supervisor \
        curl \
        default-libmysqlclient-dev \
        pkg-config \
        build-essential \
        libgl1 \
        libglib2.0-0 \
        ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python 依赖
COPY backend/requirements.txt /tmp/backend-requirements.txt
COPY ai_service/requirements.txt /tmp/ai-requirements.txt

RUN pip install --index-url https://pypi.tuna.tsinghua.edu.cn/simple \
        -r /tmp/backend-requirements.txt \
        -r /tmp/ai-requirements.txt && \
    rm /tmp/backend-requirements.txt /tmp/ai-requirements.txt

# 源代码
COPY backend/ /app/backend/
COPY ai_service/ /app/ai_service/
COPY scripts/ /app/scripts/

# 前端构建产物 → Nginx
COPY --from=frontend-builder /app/dist /usr/share/nginx/html

# Nginx 配置
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
RUN rm -f /etc/nginx/sites-enabled/default

# Supervisor 配置
COPY docker/supervisord.conf /etc/supervisor/conf.d/qingmiao.conf

# 启动脚本（首次自动初始化数据库）
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# 日志与存储目录
RUN mkdir -p /app/logs /app/storage && chmod -R 777 /app/logs /app/storage

EXPOSE 80 5000 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD curl -f http://localhost/ || exit 1

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]
