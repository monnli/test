# 青苗守护者 · AI 中小学生课堂行为与心理健康综合分析平台

> 全国大学生计算机设计大赛 · 人工智能应用赛道参赛作品

「用一双 AI 慧眼，守护每一株青苗的成长状态」—— 通过课堂视频、心理量表、文本表达等多模态数据的融合分析，为学校提供从「群体行为洞察」到「个体心理预警」的一站式智能辅助决策平台。

---

## ✨ 核心亮点

- **多模态融合**：视频行为 + 面部情绪 + 文本（周记/作文）+ 心理量表 + 学业成绩
- **课堂↔心理双向关联**：业内多数产品只做单一维度，本项目深度做关联因果分析
- **四级风险预警机制**：绿/黄/橙/红 自动分级，红色预警直达心理老师
- **负责任 AI 设计**：本地化推理、人脸哈希匿名、数据最小化、人工最终决策
- **大模型 + 标准化量表融合**：通义千问 + MHT + PHQ-9 + GAD-7 + SCARED + CES-DC
- **可视化大屏**：DataV 风格深色科技风

---

## 🏗️ 系统架构

```
浏览器 (Vue 3 SPA)
    ↓ HTTPS / WebSocket
Flask 后端 (REST + Socket.IO + 内置异步任务)
    ↓
MySQL (本地)  ← →  本地文件存储 / MinIO  ← →  AI 推理服务 (FastAPI)
                                                       ↓
                                       本地模型 + 通义千问 API
```

> 项目**不依赖 Docker / Redis**，MySQL 使用本机已安装版本，文件存储默认走本地磁盘，部署轻量、零外部基础设施。

---

## 🛠️ 技术栈

| 层 | 技术 |
|---|---|
| 前端 | Vue 3 + TypeScript + Vite + Element Plus + ECharts + DataV-Vue + Pinia |
| 后端 | Python 3.10 + Flask + Flask-SocketIO + Flask-JWT-Extended + SQLAlchemy |
| 数据库 | MySQL 8.0（本机已安装） |
| 文件存储 | 本地磁盘（默认）/ MinIO（可选） |
| AI | PyTorch + ONNXRuntime + OpenCV + ultralytics + insightface + hsemotion + dashscope |
| 实时通信 | WebRTC + WebSocket（Flask-SocketIO） |

---

## 📁 目录结构

```
qingmiao-guardian/
├── backend/              # Flask 后端
│   ├── app/
│   │   ├── api/          # REST 蓝图
│   │   ├── models/       # SQLAlchemy 模型
│   │   ├── schemas/      # Marshmallow 序列化
│   │   ├── services/     # 业务逻辑
│   │   ├── ai/           # AI 客户端封装
│   │   ├── tasks/        # 异步任务
│   │   ├── sockets/      # WebSocket 事件
│   │   └── utils/        # 工具（含本地存储抽象）
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
├── ai_service/           # 独立 AI 推理微服务（FastAPI）
├── scripts/              # 数据库初始化、演示数据生成
├── storage/              # 本地文件存储目录（自动创建，已 gitignore）
├── docs/                 # 项目报告、架构、API 文档
├── .env.example
└── README.md
```

---

## 🚀 快速开始

> 假设你已经在本机安装了 MySQL 8.x 和 Python 3.10（或更新版本），并激活了 conda 环境 `kt_cursor`。

### 1. 准备 MySQL

```sql
-- 在 MySQL 中执行（或用任意可视化工具）
CREATE USER 'qingmiao'@'localhost' IDENTIFIED BY 'qingmiao123';
GRANT ALL PRIVILEGES ON *.* TO 'qingmiao'@'localhost';
FLUSH PRIVILEGES;
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 按需修改 .env 中的 MYSQL_USER / MYSQL_PASSWORD 等
```

### 3. 安装后端依赖

```bash
conda activate kt_cursor
cd backend && pip install -r requirements.txt && cd ..
```

### 4. 初始化数据库 + 演示数据

```bash
python scripts/init_db.py              # 创建数据库与所有表
python scripts/seed_demo_data.py       # 生成 1 校 / 6 班 / 180 学生 / 14 教师账号
```

### 5. 启动后端

```bash
cd backend && python run.py
# 后端运行在 http://localhost:5000
```

### 6. 启动 AI 服务（可选，M2 起需要）

```bash
cd ai_service && pip install -r requirements.txt && python server.py
# AI 服务运行在 http://localhost:8000
```

### 7. 启动前端

```bash
cd frontend && npm install && npm run dev
# 浏览器访问 http://localhost:5173
```

---

## 🔑 演示账号（M1 起可用）

登录页提供「演示账号一键填充」按钮。

| 角色 | 账号 | 密码 |
|---|---|---|
| 学校管理员 | `admin` | `admin123` |
| 心理学老师 | `psy` | `psy12345` |
| 年级组长（七）| `grade_head_7` | `grade123` |
| 班主任（七1班）| `head_7_1b` | `head1234` |
| 科任老师（物理）| `sub_physics` | `sub12345` |

完整 16 个账号详见 [docs/M1-完成清单.md](docs/M1-完成清单.md)。

---

## 📦 开发里程碑

- [x] **M0 · 基础设施**：仓库骨架、最小可运行链路
- [x] **M1 · 用户与权限**：5 级 RBAC + 组织架构 CRUD + 演示数据
- [x] **M2 · AI 推理服务**：人脸库、行为检测、表情识别、文本情绪、AI 对话
- [ ] **M3 · 课堂视频分析**：上传分析 + 实时摄像头
- [ ] **M4 · 心理健康**：5 套量表、文本分析、AI 对话
- [ ] **M5 · 关联分析与预警**：多维关联、四级预警
- [ ] **M6 · 数据大屏**：DataV 风格可视化大屏
- [ ] **M7 · 报告中心**：AI 报告生成、PDF 导出
- [ ] **M8 · 演示打磨**：演示数据、CPU 降级、报告定稿

---

## 🛡️ 负责任 AI 设计

本项目严格遵循以下原则：

1. **辅助而非替代**：所有分析仅做辅助筛查，最终判断由专业心理咨询师/医生
2. **隐私最小化**：人脸哈希存储、数据本地化推理、敏感字段脱敏
3. **学生主体性**：避免标签化、提供数据知情权与删除权
4. **预警优于评价**：发现需要帮助的孩子，而非打分排名
5. **人工介入闭环**：所有红色预警必须由真人处理，AI 不做最终决定

详见 [docs/伦理设计说明.md](docs/伦理设计说明.md)

---

## 📄 许可

仅供学术研究与比赛展示使用。
