"""YOLOv8 课堂行为检测训练脚本（P100 16GB 调优）。

默认配置针对 P100 16GB：
- 基座：yolov8n.pt（快速收敛，约 8 小时）
- 图像尺寸：640
- batch：16（P100 16GB 跑 n 版本 batch 16 稳定）
  * 如需更大模型 yolov8m.pt，batch 调到 8

用法：
    # 标准训练（推荐）
    python scripts/train/train_yolov8_behavior.py

    # 快速验证（5 epoch，用来验证流程是否通）
    python scripts/train/train_yolov8_behavior.py --epochs 5 --name smoke_test

    # 使用更大的 m 模型
    python scripts/train/train_yolov8_behavior.py --base yolov8m.pt --batch 8

训练输出：
    runs/qingmiao_behavior/<name>/
        weights/best.pt    ← 验证集最优权重
        weights/last.pt    ← 最后一个 epoch
        results.png        ← 训练曲线
        val_batch0_pred.jpg ← 验证预测可视化
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default=str(PROJECT_ROOT / "data" / "scb" / "scb.yaml"),
                        help="数据集 yaml 路径")
    parser.add_argument("--base", default="yolov8n.pt",
                        help="基座模型（yolov8n.pt / yolov8s.pt / yolov8m.pt）")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument("--device", default="0", help="GPU 索引，cpu 强制用 CPU")
    parser.add_argument("--name", default="scb_v1", help="本次实验名称")
    parser.add_argument("--project", default=str(PROJECT_ROOT / "runs" / "qingmiao_behavior"))
    parser.add_argument("--patience", type=int, default=20, help="early stopping")
    parser.add_argument("--resume", action="store_true", help="从上次中断处恢复")
    args = parser.parse_args()

    if not Path(args.data).exists():
        print(f"[ERR] 数据集配置不存在：{args.data}")
        print("请先运行：python scripts/train/prepare_scb_dataset.py")
        sys.exit(1)

    try:
        from ultralytics import YOLO  # type: ignore
    except ImportError:
        print("[ERR] 请安装 ultralytics：pip install ultralytics")
        sys.exit(1)

    print("=" * 60)
    print("青苗守护者 · YOLOv8 课堂行为模型训练")
    print("=" * 60)
    print(f"基座模型：{args.base}")
    print(f"数据集：{args.data}")
    print(f"图像尺寸：{args.imgsz}")
    print(f"Batch：{args.batch}")
    print(f"Epochs：{args.epochs}")
    print(f"设备：{args.device}")
    print(f"实验名：{args.name}")
    print("=" * 60)

    model = YOLO(args.base)

    # 训练（所有参数针对 P100 16GB + 中小数据量调优）
    results = model.train(
        data=args.data,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        project=args.project,
        name=args.name,
        patience=args.patience,
        save=True,
        save_period=10,
        cache=True,             # 缓存图像到内存/磁盘，加速
        workers=4,
        # —— 数据增强（课堂场景比较单调，不要过度增强）——
        hsv_h=0.015,
        hsv_s=0.4,
        hsv_v=0.4,
        degrees=5.0,            # 轻微旋转（课堂摄像头不怎么旋转）
        translate=0.1,
        scale=0.5,
        fliplr=0.5,
        mosaic=0.5,             # 小数据场景不要开太猛
        mixup=0.0,
        # —— 优化器 ——
        optimizer="AdamW",
        lr0=0.001,              # AdamW 的合适起始学习率
        lrf=0.01,
        momentum=0.937,
        weight_decay=0.0005,
        warmup_epochs=3,
        # —— Loss 权重（检测任务默认即可）——
        box=7.5,
        cls=0.5,
        dfl=1.5,
        # —— 其他 ——
        verbose=True,
        plots=True,             # 生成训练曲线 PNG
        resume=args.resume,
    )

    print()
    print("=" * 60)
    print("✅ 训练完成")
    weights_dir = Path(args.project) / args.name / "weights"
    print(f"   权重目录：{weights_dir}")
    print(f"   最佳权重：{weights_dir / 'best.pt'}")
    print()
    print("下一步：")
    print(f"   1. 评估：python scripts/train/evaluate_model.py --weights \"{weights_dir / 'best.pt'}\"")
    print(f"   2. 替换到项目：python scripts/train/integrate_model.py --weights \"{weights_dir / 'best.pt'}\"")
    print("=" * 60)


if __name__ == "__main__":
    main()
