# 青苗守护者 · AI 中小学生课堂行为与心理健康综合分析平台

> 全国大学生计算机设计大赛 · 人工智能应用赛道参赛作品

「用一双 AI 慧眼，守护每一株青苗的成长状态」—— 通过课堂视频、心理量表、文本表达等多模态数据的融合分析，为学校提供从「群体行为洞察」到「个体心理预警」的一站式智能辅助决策平台。

---

## ✨ 核心亮点

- **多模态融合**：视频行为 + 面部情绪 + 文本（周记/作文）+ 心理量表 + 学业成绩，五维数据交叉分析
- **课堂↔心理双向关联**：业内多数产品只做单一维度，本项目深度做关联因果分析
- **四级风险预警机制**：绿/黄/橙/红 自动分级，红色预警直达心理老师
- **负责任 AI 设计**：本地化推理、人脸哈希匿名、学生数据最小化、人工最终决策
- **大模型 + 标准化量表融合**：通义千问 + MHT + PHQ-9 + GAD-7 + SCARED + CES-DC
- **可视化大屏**：DataV 风格深色科技风，演示视觉冲击力拉满

---

## 🏗️ 系统架构

```
浏览器 (Vue 3 SPA)
    ↓ HTTPS / WebSocket
Flask 后端 (REST + Socket.IO + Celery)
    ↓
MySQL ← → Redis ← → MinIO ← → AI 推理服务 (FastAPI)
                                     ↓
                       本地模型 (YOLOv8 / InsightFace / HSEmotion)
                                  + 通义千问 API
```

---

## 🛠️ 技术栈

| 层 | 技术 |
|---|---|
| 前端 | Vue 3 + TypeScript + Vite + Element Plus + ECharts + DataV-Vue + Pinia + Vue Router |
| 后端 | Python 3.10 + Flask + Flask-SocketIO + Flask-JWT-Extended + SQLAlchemy + Marshmallow + Celery |
| 数据库 | MySQL 8.0 + Redis 7 + MinIO |
| AI | PyTorch + ONNXRuntime + OpenCV + MediaPipe + ultralytics + insightface + hsemotion + dashscope |
| 实时通信 | WebRTC + WebSocket (Flask-SocketIO) |
| 部署 | Docker Compose（一键启动） |

---

## 📁 目录结构

```
qingmiao-guardian/
├── backend/              # Flask 后端
│   ├── app/
│   │   ├── api/          # REST 蓝图
│   │   ├── models/       # SQLAlchemy 模型
│   │   ├── schemas/      # Marshmallow 序列化
│   │   ├── services/     # 业务逻辑层
│   │   ├── ai/           # AI 推理客户端封装
│   │   ├── tasks/        # Celery 任务
│   │   ├── sockets/      # WebSocket 事件
│   │   └── utils/
│   ├── migrations/       # Alembic 数据库迁移
│   ├── requirements.txt
│   ├── config.py
│   └── run.py
├── frontend/             # Vue 3 前端
│   └── src/
│       ├── api/
│       ├── views/
│       ├── components/
│       ├── stores/
│       └── router/
├── ai_service/           # 独立 AI 推理微服务
│   ├── pipelines/        # 各类 AI 流水线
│   ├── models/           # 模型权重（.gitignore）
│   └── server.py         # FastAPI 入口
├── scripts/              # 数据库初始化、mock 数据生成等脚本
├── docker/               # Dockerfile 与配置
├── docs/                 # 项目报告、架构、API 文档
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 🚀 快速开始

### 方式一：Docker Compose（推荐）

```bash
cp .env.example .env
docker compose up -d
```

启动后访问：
- 前端：http://localhost:5173
- 后端 API：http://localhost:5000
- AI 服务：http://localhost:8000
- MinIO 控制台：http://localhost:9001
- MySQL：localhost:3306

### 方式二：本地开发（已激活 conda 环境 `kt_cursor`）

#### 1. 后端

```bash
conda activate kt_cursor
cd backend
pip install -r requirements.txt
cp ../.env.example ../.env
# 启动 MySQL/Redis/MinIO（可用 docker compose up -d mysql redis minio）
python run.py
```

#### 2. AI 服务

```bash
conda activate kt_cursor
cd ai_service
pip install -r requirements.txt
python server.py
```

#### 3. 前端

```bash
cd frontend
npm install
npm run dev
```

---

## 📦 开发里程碑

- [x] **M0 · 基础设施**：仓库骨架、Docker Compose、最小可运行链路
- [ ] **M1 · 用户与权限**：5 级 RBAC、组织架构、演示数据
- [ ] **M2 · AI 推理服务**：人脸库、行为检测、表情识别
- [ ] **M3 · 课堂视频分析**：上传分析 + 实时摄像头
- [ ] **M4 · 心理健康**：5 套量表、文本分析、AI 对话
- [ ] **M5 · 关联分析与预警**：多维关联、四级预警
- [ ] **M6 · 数据大屏**：DataV 风格可视化大屏
- [ ] **M7 · 报告中心**：AI 报告生成、PDF 导出
- [ ] **M8 · 演示打磨**：演示数据、CPU 降级、报告定稿

---

## 🛡️ 负责任 AI 设计

本项目严格遵循以下原则：

1. **辅助而非替代**：所有分析结果仅作为辅助参考，最终判断由专业心理咨询师/医生做出
2. **隐私最小化**：人脸图像哈希存储、数据本地化推理、敏感字段脱敏
3. **学生主体性**：避免标签化、提供数据知情权与删除权
4. **预警优于评价**：系统目标是「发现需要帮助的孩子」而非「打分排名」
5. **人工介入闭环**：所有红色预警必须由真人处理，AI 不做最终决定

详见 [docs/伦理设计说明.md](docs/伦理设计说明.md)

---

## 📄 许可

仅供学术研究与比赛展示使用。

