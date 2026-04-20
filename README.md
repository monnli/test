<p align="center">
  <img src="frontend/public/favicon.svg" width="80" alt="青苗守护者" />
</p>

<h1 align="center">青苗守护者</h1>
<h3 align="center">AI 中小学生课堂行为与心理健康综合分析平台</h3>

<p align="center">
  <img src="https://img.shields.io/badge/%E5%9B%BD%E8%B5%9B-%E4%BA%BA%E5%B7%A5%E6%99%BA%E8%83%BD%E5%BA%94%E7%94%A8%E8%B5%9B%E9%81%93-22c55e?style=flat-square" />
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Vue-3.4-4FC08D?style=flat-square&logo=vue.js&logoColor=white" />
  <img src="https://img.shields.io/badge/Flask-3.0-000000?style=flat-square&logo=flask&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/MySQL-8.0-4479A1?style=flat-square&logo=mysql&logoColor=white" />
  <img src="https://img.shields.io/badge/License-Academic-orange?style=flat-square" />
</p>

<p align="center">
  <strong>「用一双 AI 慧眼 · 守护每一株青苗」</strong>
</p>

<p align="center">
  通过课堂视频、心理量表、文本表达等多模态数据的融合分析<br/>
  为学校提供从「群体行为洞察」到「个体心理预警」的一站式智能辅助决策平台
</p>

<p align="center">
  <a href="docs/演示视频脚本.md">📹 演示视频</a> ·
  <a href="docs/项目报告大纲.md">📄 项目报告</a> ·
  <a href="docs/答辩PPT大纲.md">🎤 答辩资料</a> ·
  <a href="docs/%E4%BC%A6%E7%90%86%E8%AE%BE%E8%AE%A1%E8%AF%B4%E6%98%8E.md">🛡️ 伦理设计</a>
</p>

---

---

## ✨ 核心亮点

- **多模态融合**：视频行为 + 面部情绪 + 文本（周记/作文）+ 心理量表 + 学业成绩，5 维数据交叉
- **课堂↔心理双向关联**：业内多数产品只做单一维度，本项目深度做关联因果分析
- **四级风险预警机制**：绿/黄/橙/红 自动分级 + 工单流转 + 干预记录
- **「可真可假」的 AI**：所有流水线支持加载失败自动降级 mock，**任何机器都能跑通**
- **5 套标准化心理量表**：PHQ-9 + GAD-7 + SCARED + CES-DC + MHT
- **DataV 风格数据大屏**：深色科技风 + 6 张图表 + 实时刷新
- **AI 报告生成 + PDF 导出**：通义千问 + reportlab 中文 PDF
- **负责任 AI 设计**：本地化推理、人脸哈希匿名、数据最小化、人工最终决策

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
| 前端 | Vue 3 + TypeScript + Vite + Element Plus + ECharts + Pinia + Socket.IO Client |
| 后端 | Python 3.10 + Flask + Flask-SocketIO + Flask-JWT-Extended + SQLAlchemy + reportlab |
| 数据库 | MySQL 8.0（本机已安装） |
| 文件存储 | 本地磁盘（默认）/ MinIO（可选） |
| AI | PyTorch + ONNXRuntime + OpenCV + ultralytics(YOLOv8) + insightface + hsemotion + dashscope（通义千问） |
| 实时通信 | WebRTC + WebSocket（Flask-SocketIO） |

---

## 📁 目录结构

```
qingmiao-guardian/
├── backend/              # Flask 后端
│   └── app/
│       ├── api/          # REST 蓝图（auth/users/orgs/faces/ai/classroom/psychology/alerts/dashboard/reports）
│       ├── models/       # 30+ 张 SQLAlchemy 模型
│       ├── services/     # 业务逻辑层
│       ├── ai/           # AI 客户端封装
│       ├── tasks/        # 异步任务（Python threading）
│       ├── sockets/      # WebSocket 事件
│       └── utils/        # 权限、存储、安全等工具
├── frontend/             # Vue 3 前端（30+ 页面）
├── ai_service/           # FastAPI AI 推理微服务
│   └── pipelines/        # 4 条流水线（face/emotion/behavior/text）
├── scripts/              # 数据库/演示数据/模型下载/一键启动
├── storage/              # 本地文件存储（自动创建）
├── docs/                 # 报告大纲、伦理、架构、M0~M8 完成清单
└── README.md
```

---

## 🚀 快速开始

### 方式一：Docker 一键启动（推荐 · 最简单）

**任何装了 Docker Desktop 的电脑**（无需 Python / Node / MySQL）：

```bash
git clone https://github.com/monnli/qingmiao-guardian.git
cd qingmiao-guardian
docker compose up -d --build
```

约 5~10 分钟首次构建 + 1 分钟首次数据库初始化，然后浏览器打开 **http://localhost** 即可。默认账号 `admin / admin123`。

详见 [docs/Docker部署指南.md](docs/Docker部署指南.md)。

---

### 方式二：本地开发（开发者）

> 假设你已经在本机安装了 MySQL 8.x、Python 3.10+、Node 18+，并激活 conda 环境 `kt_env`。

### 一键初始化（推荐）

```bash
# 1. 在 MySQL 中创建用户
#    CREATE USER 'qingmiao'@'localhost' IDENTIFIED BY 'qingmiao123';
#    GRANT ALL PRIVILEGES ON *.* TO 'qingmiao'@'localhost';

cp .env.example .env
conda activate kt_env

cd backend && pip install -r requirements.txt && cd ..
cd ai_service && pip install -r requirements.txt && cd ..
cd frontend && npm install && cd ..

# 一键初始化数据库 + 完整演示数据
bash scripts/init_demo.sh

# 一键启动所有服务（前端 + 后端 + AI）
bash scripts/start_all.sh
```

打开浏览器访问：
- **数据大屏**：http://localhost:5173/dashboard
- **工作台**：http://localhost:5173/workbench

### Windows 用户（无需 WSL，纯原生）

```cmd
REM 1. 一键初始化数据库 + 演示数据
scripts\init_demo.bat

REM 2. 一键启动所有服务
scripts\start_all.bat
```

> Windows 上不要用 `bash scripts/init_demo.sh`，那是 Linux/macOS 脚本。

### 手动启动

```bash
# 后端
cd backend && python run.py

# AI 服务（新终端）
cd ai_service && python server.py

# 前端（新终端）
cd frontend && npm run dev
```

---

## 🔑 演示账号

登录页提供「演示账号一键填充」按钮。

| 角色 | 账号 | 密码 | 数据范围 |
|---|---|---|---|
| 学校管理员 | `admin` | `admin123` | 本校全部 |
| 心理学老师 | `psy` | `psy12345` | 本校全部 |
| 年级组长（七）| `grade_head_7` | `grade123` | 七年级 |
| 班主任（七1班）| `head_7_1b` | `head1234` | 本班 |
| 科任老师（物理）| `sub_physics` | `sub12345` | 6 班物理课 |

完整 16 个账号详见 [docs/M1-完成清单.md](docs/M1-完成清单.md)。

---

## ✅ 开发里程碑（已全部完成）

| 里程碑 | 内容 | 文档 |
|---|---|---|
| **M0** | 仓库骨架、Flask + Vue + FastAPI 最小可运行 | [文档](docs/M0-完成清单.md) |
| **M1** | 5 级 RBAC + 30 张表 + 16 个演示账号 | [文档](docs/M1-完成清单.md) |
| **M2** | 4 条 AI 流水线（人脸/表情/行为/文本）+ Mock 降级 | [文档](docs/M2-完成清单.md) |
| **M3** | 视频上传 + 异步分析 + 报告 + 实时摄像头 | [文档](docs/M3-完成清单.md) |
| **M4** | 5 套标准心理量表 + 文本分析 + AI 对话档案 | [文档](docs/M4-完成清单.md) |
| **M5** | 多维关联 + 4 级预警工单 + 干预记录 | [文档](docs/M5-完成清单.md) |
| **M6** | DataV 风格数据大屏 | [文档](docs/M6-完成清单.md) |
| **M7** | AI 自动报告 + PDF 导出 | [文档](docs/M7-完成清单.md) |
| **M8** | 演示打磨 + 一键启动 + 报告大纲 | [文档](docs/M8-完成清单.md) |

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

## 📚 文档索引

- [项目报告大纲](docs/项目报告大纲.md)
- [演示视频脚本](docs/演示视频脚本.md)
- [架构设计](docs/架构设计.md)
- [伦理设计说明](docs/伦理设计说明.md)
- [CPU 降级部署说明](docs/CPU降级部署说明.md)
- M0~M8 完成清单

---

## 📄 许可

仅供学术研究与比赛展示使用。
