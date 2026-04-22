# 青苗守护者 · 模型训练脚本

> 为 YOLOv8 课堂行为检测模型准备的完整训练流水线。
> 详细计划参见 [`docs/模型训练3天冲刺方案.md`](../../docs/模型训练3天冲刺方案.md)

## 快速开始（3 条命令完成训练与集成）

```bash
# 1. 准备数据集（自动下载 SCB + 划分 train/val）
python scripts/train/prepare_scb_dataset.py

# 2. 训练（P100 约 8 小时）
python scripts/train/train_yolov8_behavior.py --epochs 100 --name scb_v1

# 3. 评估 + 集成到系统
python scripts/train/evaluate_model.py \
    --weights runs/qingmiao_behavior/scb_v1/weights/best.pt \
    --compare

python scripts/train/integrate_model.py \
    --weights runs/qingmiao_behavior/scb_v1/weights/best.pt
```

集成后重启 AI 服务（`cd ai_service && python server.py`），`BehaviorPipeline` 会自动加载自训模型。

## 脚本说明

| 脚本 | 用途 |
|---|---|
| `prepare_scb_dataset.py` | 下载 SCB 课堂行为数据集，划分 train/val，生成 yaml |
| `train_yolov8_behavior.py` | YOLOv8 训练主脚本（已针对 P100 16GB 调优） |
| `evaluate_model.py` | 评估模型：mAP / 推理速度 / 对比官方模型 |
| `integrate_model.py` | 一键集成训练好的模型到 AI 服务 |

## 目录结构

```
项目根/
├── data/
│   ├── .cache/SCB-dataset/      ← 克隆的原始数据（git 忽略）
│   └── scb/
│       ├── images/
│       │   ├── train/           ← 划分后的训练集
│       │   └── val/             ← 划分后的验证集
│       ├── labels/
│       │   ├── train/
│       │   └── val/
│       └── scb.yaml             ← 数据集配置
├── runs/qingmiao_behavior/      ← 训练输出（git 忽略）
│   └── scb_v1/
│       ├── weights/best.pt      ← 最优模型
│       ├── results.png          ← 训练曲线
│       └── val_batch0_pred.jpg  ← 验证预测可视化
└── ai_service/models/
    ├── yolov8_classroom.pt      ← 集成后的自训模型
    └── yolov8_classroom_labels.json  ← 中文标签映射
```

## 常见问题

### Q: clone SCB 仓库太慢
手动下载：
```
https://github.com/Whiffe/SCB-dataset → Download ZIP
解压到 data/.cache/SCB-dataset/
```

### Q: 训练 OOM
```bash
# P100 16GB 的底线配置
python scripts/train/train_yolov8_behavior.py --batch 8 --imgsz 512
```

### Q: 如何在不重新训练的情况下调整类别映射
直接编辑 `ai_service/models/yolov8_classroom_labels.json`，重启 AI 服务。

### Q: 自训模型效果不好，想回退
```bash
# 删掉自训模型，BehaviorPipeline 会回退到官方通用 yolov8n
rm ai_service/models/yolov8_classroom.pt
# 重启 AI 服务
```
