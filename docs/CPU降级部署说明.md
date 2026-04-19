# CPU 降级部署说明

> 演示机没有 GPU 时的部署方案。

## 1. 基本原则

本项目所有 AI 流水线在加载真实模型失败时**自动降级为 mock 模式**，仍可演示完整功能。
因此即便不安装任何 AI 依赖，整个系统也能正常工作（适合应急/快速演示）。

## 2. 推荐方案：CPU 真实模型 + 通义千问 API

### 2.1 修改 `.env`

```bash
AI_DEVICE=cpu
DASHSCOPE_API_KEY=sk-你的通义千问API_KEY
```

### 2.2 安装 CPU 版 AI 依赖

编辑 `ai_service/requirements.txt`，取消对应注释，并将 GPU 版替换为 CPU 版：

```
opencv-python-headless==4.10.0.84
torch==2.3.1            # 自动安装 CPU 版本
torchvision==0.18.1
ultralytics==8.2.79     # YOLOv8
insightface==0.7.3
onnxruntime==1.18.1     # CPU 版（注释掉 onnxruntime-gpu）
hsemotion==0.3
timm==1.0.8
```

```bash
cd ai_service
pip install -r requirements.txt
```

### 2.3 下载模型

```bash
python scripts/download_models.py
```

### 2.4 启动

```bash
bash scripts/start_all.sh
```

进入 `/system/ai`「AI 服务监控」页，点击各流水线「加载」按钮，等待加载完成。

## 3. 性能参考（典型笔记本 CPU i5-1135G7）

| 流水线 | CPU 耗时 | GPU (P100) |
|---|---|---|
| 人脸检测+识别（单帧） | ~250ms | ~30ms |
| 表情识别（单脸） | ~80ms | ~15ms |
| YOLOv8n 行为检测 | ~200ms | ~25ms |
| 通义千问对话 | 1~3s（API） | 1~3s |

## 4. 演示优化建议

### 4.1 实时摄像头降帧

`/classroom/realtime` 页面默认 1 秒发一帧，CPU 设备建议改为 2~3 秒：
- 在前端「分析频率」输入 2000 或 3000

### 4.2 上传视频抽帧间隔

CPU 处理视频较慢，建议抽帧间隔设为 5~10 秒，减少帧数。

### 4.3 提前生成演示数据

```bash
python scripts/seed_demo_extras.py
```

让大屏、报告中心、关联分析直接展示丰富数据，避免现场跑分析等待。

### 4.4 极端容灾：纯 mock 模式

如果 CPU 实在跑不动，注释掉 `ai_service/requirements.txt` 中的 AI 依赖：

```bash
pip uninstall ultralytics insightface hsemotion onnxruntime
```

所有流水线自动降级为 mock，**不影响演示流程**，只是数字是模拟的。

## 5. 一键启动脚本

| 平台 | 命令 |
|---|---|
| Linux/macOS | `bash scripts/start_all.sh` |
| Windows | 双击 `scripts/start_all.bat` |

启动后访问：
- 数据大屏：http://localhost:5173/dashboard
- 工作台：http://localhost:5173/workbench
- 默认账号：admin / admin123
