# 青苗守护者 · Docker 部署指南

> 一条命令把整个系统（前端 + 后端 + AI + MySQL）跑起来，无需手动装 Python / Node / MySQL。

---

## 🎯 前置要求

任何一台装了 **Docker Desktop** 的电脑（Windows 10+ / macOS / Linux），无需装 Python、Node、MySQL。

- Docker Desktop 下载：https://www.docker.com/products/docker-desktop/
- Windows 装好后需要**重启电脑**，并勾选 Docker 设置中的 "Use WSL 2" 或 "Use Hyper-V"

验证安装：
```bash
docker --version
docker compose version
```

---

## 🚀 方案 A：从源码构建（推荐给自己使用）

### 1. 克隆仓库
```bash
git clone https://github.com/monnli/qingmiao-guardian.git
cd qingmiao-guardian
```

### 2. 一键启动
```bash
docker compose up -d --build
```

第一次构建约 5~10 分钟（下载 Python / Node 镜像 + 装依赖）。之后启动只需要几秒。

### 3. 查看启动进度
```bash
docker compose logs -f qingmiao
```

看到 `启动服务中（前端 + 后端 + AI）...` 说明就绪。第一次会自动初始化数据库 + 写入完整演示数据（量表 / 学生 / 教师 / 预警等），约 1~2 分钟。

### 4. 访问系统

| 地址 | 说明 |
|---|---|
| **http://localhost** | 前端主入口 |
| http://localhost/dashboard | 数据大屏 |
| http://localhost:5000/api/health | 后端 API 探活（调试用） |
| http://localhost:8000/health | AI 服务探活（调试用） |

**默认账号**：
- 学校管理员：`admin / admin123`
- 心理学老师：`psy / psy12345`
- 班主任（七1班）：`head_7_1b / head1234`

完整 16 个演示账号见 [M1-完成清单.md](M1-完成清单.md)。

### 5. 停止 / 重启
```bash
# 停止
docker compose down

# 重启
docker compose restart

# 彻底清理（删除数据！谨慎）
docker compose down -v
```

---

## 🚀 方案 B：导出镜像给别人使用（适合答辩带 U 盘）

### 1. 本地构建并导出
```bash
# 先构建镜像
docker compose build

# 导出为 tar 文件（约 2 GB）
docker save -o qingmiao-guardian.tar qingmiao-guardian:latest mysql:8.0
```

### 2. 在目标机器上加载
把 `qingmiao-guardian.tar`、`docker-compose.yml`、`docker/` 目录拷贝到目标机器，然后：

```bash
# 加载镜像
docker load -i qingmiao-guardian.tar

# 启动
docker compose up -d
```

**无需联网**，演示机不用下载任何东西。

---

## ⚙️ 高级配置

### 修改 MySQL 密码 / 端口
编辑 `docker-compose.yml` 或新建 `.env` 文件：

```bash
# .env
MYSQL_ROOT_PASSWORD=your-strong-password
MYSQL_PASSWORD=your-password
SECRET_KEY=your-random-secret
JWT_SECRET_KEY=your-jwt-secret
```

### 启用通义千问 API（让 AI 对话更真）
在 `.env` 加：
```bash
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxx
```

不填默认走 mock 模式，功能演示不受影响。

### GPU 加速（如果服务器有 CUDA）
修改 `docker-compose.yml` 的 `qingmiao` 服务，加：
```yaml
    environment:
      AI_DEVICE: cuda
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
```

---

## 🐛 故障排查

### 前端打不开
```bash
docker compose logs qingmiao | grep -E "nginx|error"
docker compose exec qingmiao curl http://127.0.0.1:5000/api/health
```

### 数据库连不上
```bash
docker compose logs mysql | tail -30
docker compose exec mysql mysql -uroot -proot123 -e "SHOW DATABASES;"
```

### 演示数据没写入
```bash
# 进入容器
docker compose exec qingmiao bash

# 手动重跑
cd /app
python scripts/seed_demo_data.py
python scripts/seed_demo_extras.py
```

### 端口冲突
如果 80 / 3306 / 5000 / 8000 被占用，修改 `docker-compose.yml` 的 `ports`：
```yaml
    ports:
      - "8080:80"     # 前端改成 8080
      - "3307:3306"   # MySQL 改成 3307
```

### 重新初始化数据
```bash
# 删除初始化标记，重启即可再次写入
docker compose exec qingmiao rm -f /app/storage/.initialized
docker compose restart qingmiao
```

### 彻底清空重来
```bash
docker compose down -v   # 删除所有数据卷
docker compose up -d     # 重新启动并初始化
```

---

## 📊 资源占用参考

| 组件 | CPU | 内存 | 磁盘 |
|---|---|---|---|
| mysql 容器 | < 5% | 300 MB | 100 MB（初始） |
| qingmiao 容器（CPU 模式） | 10~20% | 500 MB | 2 GB（镜像） |
| qingmiao 容器（GPU 模式）| 取决于 AI 任务 | 1~3 GB | 4~6 GB |

一台 8GB 内存的普通笔记本就能流畅演示。

---

## 🎬 演示前的最后检查

- [ ] `docker compose ps` 显示两个容器都是 `Up` 状态
- [ ] 浏览器访问 http://localhost 能看到登录页
- [ ] 用 `admin / admin123` 能登录
- [ ] 进入 http://localhost/dashboard 有数据
- [ ] 进入 http://localhost/enhance/cluster 能看到聚类散点图
- [ ] 进入 http://localhost/ethics 能看到负责任 AI 仪表盘
- [ ] 按 **F9** 能启动 Demo Mode

如果某项失败，查看 `docker compose logs -f qingmiao` 排查。

---

## 📦 镜像发布（可选）

如果想把镜像推到 Docker Hub 让全世界能用：

```bash
docker tag qingmiao-guardian:latest yourname/qingmiao-guardian:latest
docker push yourname/qingmiao-guardian:latest
```

别人就可以直接：
```bash
docker pull yourname/qingmiao-guardian:latest
docker compose up -d    # 使用你的 docker-compose.yml
```
