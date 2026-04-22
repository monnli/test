"""YOLOv8 训练后评估：mAP + 混淆矩阵 + 推理速度 + 演示视频推理对比。

产出：
- 数值报告（mAP50 / mAP50-95 / precision / recall / 每类 AP）
- 单张图像与视频的推理耗时
- 一张"自训模型 vs 官方 YOLOv8n"对比图（可选）

用法：
    python scripts/train/evaluate_model.py --weights runs/qingmiao_behavior/scb_v1/weights/best.pt
    python scripts/train/evaluate_model.py --weights <path> --video storage/demo_videos/class_7_1.mp4
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--weights", required=True, help="训练好的 best.pt 路径")
    parser.add_argument("--data", default=str(PROJECT_ROOT / "data" / "scb" / "scb.yaml"))
    parser.add_argument("--device", default="0")
    parser.add_argument("--video", help="额外：在一段视频上跑推理，输出每帧耗时")
    parser.add_argument("--compare", action="store_true", help="与官方 yolov8n 对比")
    args = parser.parse_args()

    weights = Path(args.weights)
    if not weights.exists():
        print(f"[ERR] 权重不存在：{weights}")
        sys.exit(1)

    try:
        from ultralytics import YOLO  # type: ignore
    except ImportError:
        print("[ERR] 请安装 ultralytics：pip install ultralytics")
        sys.exit(1)

    print("=" * 60)
    print(f"评估模型：{weights}")
    print("=" * 60)

    model = YOLO(str(weights))

    # 1. 验证集指标
    print("\n[1/3] 验证集指标...")
    metrics = model.val(data=args.data, device=args.device, verbose=False)
    print(f"  mAP50      ：{metrics.box.map50:.3f}")
    print(f"  mAP50-95   ：{metrics.box.map:.3f}")
    print(f"  Precision  ：{metrics.box.mp:.3f}")
    print(f"  Recall     ：{metrics.box.mr:.3f}")
    if hasattr(metrics.box, "ap_class_index") and hasattr(metrics.box, "ap"):
        class_names = metrics.names if hasattr(metrics, "names") else {}
        print("\n  每类 AP50：")
        for i, cls_idx in enumerate(metrics.box.ap_class_index):
            name = class_names.get(int(cls_idx), str(cls_idx))
            print(f"    {name:20s}  AP50={metrics.box.ap50[i]:.3f}")

    # 2. 推理速度
    print("\n[2/3] 推理速度测试（640x640，100 次）...")
    try:
        import numpy as np

        dummy = np.random.randint(0, 255, (640, 640, 3), dtype="uint8")
        # 预热
        for _ in range(5):
            model.predict(dummy, device=args.device, verbose=False)
        start = time.time()
        for _ in range(100):
            model.predict(dummy, device=args.device, verbose=False)
        elapsed = time.time() - start
        fps = 100 / elapsed
        print(f"  平均耗时：{elapsed * 10:.2f} ms/帧  ·  约 {fps:.1f} FPS")
    except Exception as exc:  # noqa: BLE001
        print(f"  [WARN] 速度测试失败：{exc}")

    # 3. 视频推理
    if args.video and Path(args.video).exists():
        print(f"\n[3/3] 视频推理：{args.video}")
        try:
            import cv2  # type: ignore

            cap = cv2.VideoCapture(args.video)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps_in = cap.get(cv2.CAP_PROP_FPS) or 25
            duration = total_frames / fps_in
            print(f"  总帧数：{total_frames}  时长：{duration:.1f}s")

            n_sample = min(30, total_frames)
            step = max(1, total_frames // n_sample)
            times = []
            for i in range(0, total_frames, step):
                cap.set(cv2.CAP_PROP_POS_FRAMES, i)
                ok, frame = cap.read()
                if not ok:
                    continue
                t0 = time.time()
                model.predict(frame, device=args.device, verbose=False)
                times.append(time.time() - t0)
            cap.release()
            if times:
                avg = sum(times) / len(times) * 1000
                print(f"  采样 {len(times)} 帧  ·  平均推理耗时 {avg:.1f} ms/帧")
        except Exception as exc:  # noqa: BLE001
            print(f"  [WARN] 视频推理失败：{exc}")

    # 4. 对比官方模型
    if args.compare:
        print("\n[对比] 官方 yolov8n.pt 验证集指标...")
        try:
            baseline = YOLO("yolov8n.pt")
            base_metrics = baseline.val(data=args.data, device=args.device, verbose=False)
            print(f"  官方 yolov8n mAP50    ：{base_metrics.box.map50:.3f}")
            print(f"  官方 yolov8n mAP50-95 ：{base_metrics.box.map:.3f}")
            delta50 = metrics.box.map50 - base_metrics.box.map50
            delta = metrics.box.map - base_metrics.box.map
            print(f"  提升 mAP50    ：{delta50:+.3f}")
            print(f"  提升 mAP50-95 ：{delta:+.3f}")
        except Exception as exc:  # noqa: BLE001
            print(f"  [WARN] 对比失败：{exc}")

    print()
    print("=" * 60)
    print("✅ 评估完成")
    print()
    print("把上面的 mAP50 数字填进 PPT 作为训练效果证据")
    print("=" * 60)


if __name__ == "__main__":
    main()
