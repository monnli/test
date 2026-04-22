"""把训练好的 YOLOv8 模型一键集成到 AI 服务。

流程：
1. 把 best.pt 复制到 ai_service/models/yolov8_classroom.pt
2. 从数据集 yaml 读出类别，写入 ai_service/models/yolov8_classroom_labels.json
3. 导出 ONNX（可选，供 CPU 部署）

之后 BehaviorPipeline 会自动优先加载自训模型，读取对应标签。

用法：
    python scripts/train/integrate_model.py --weights runs/qingmiao_behavior/scb_v1/weights/best.pt
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MODEL_DIR = PROJECT_ROOT / "ai_service" / "models"


def load_classes_from_yaml(yaml_path: Path) -> list[str]:
    """从 YOLO 数据集 yaml 读出 names。"""
    classes: list[str] = []
    in_names = False
    for line in yaml_path.read_text(encoding="utf-8").splitlines():
        line = line.rstrip()
        if line.startswith("names:"):
            in_names = True
            continue
        if in_names:
            if not line or not line.startswith(" "):
                in_names = False
                continue
            # "  0: person"
            parts = line.strip().split(":", 1)
            if len(parts) == 2:
                try:
                    idx = int(parts[0])
                    name = parts[1].strip()
                    while len(classes) <= idx:
                        classes.append("")
                    classes[idx] = name
                except ValueError:
                    pass
    return [c for c in classes if c]


# 英文标签 → 中文映射
LABEL_CN_MAP = {
    "hand": "手",
    "raise_hand": "举手",
    "read": "阅读",
    "write": "写作",
    "stand": "站立",
    "phone": "玩手机",
    "look_at_screen": "看屏幕",
    "bow_head": "低头",
    "lying": "趴桌",
    "sleeping": "睡觉",
    "using_phone": "玩手机",
    "person": "学生",
    "listening": "听课",
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--weights", required=True)
    parser.add_argument("--data", default=str(PROJECT_ROOT / "data" / "scb" / "scb.yaml"))
    parser.add_argument("--no-onnx", action="store_true", help="跳过 ONNX 导出")
    args = parser.parse_args()

    weights = Path(args.weights)
    if not weights.exists():
        print(f"[ERR] 权重不存在：{weights}")
        sys.exit(1)

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    dst_weights = MODEL_DIR / "yolov8_classroom.pt"
    shutil.copy2(weights, dst_weights)
    print(f"[OK] 权重已复制：{dst_weights}")

    # 从 yaml 读类别
    yaml_path = Path(args.data)
    if yaml_path.exists():
        classes = load_classes_from_yaml(yaml_path)
    else:
        classes = []
    if not classes:
        print("[WARN] 未能从 yaml 读出类别，请手动填入 yolov8_classroom_labels.json")
        classes = ["unknown"]

    labels_file = MODEL_DIR / "yolov8_classroom_labels.json"
    payload = {
        "classes": classes,
        "labels_cn": {c: LABEL_CN_MAP.get(c, c) for c in classes},
    }
    labels_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] 标签映射已写入：{labels_file}")
    print(f"     类别：{classes}")

    # 导出 ONNX
    if not args.no_onnx:
        try:
            from ultralytics import YOLO  # type: ignore

            print("[..] 导出 ONNX（供 CPU 部署）...")
            m = YOLO(str(dst_weights))
            onnx_path = m.export(format="onnx", imgsz=640, simplify=True, dynamic=False)
            print(f"[OK] ONNX：{onnx_path}")
        except Exception as exc:  # noqa: BLE001
            print(f"[WARN] ONNX 导出失败（不影响主功能）：{exc}")

    print()
    print("=" * 60)
    print("✅ 模型集成完成")
    print()
    print("接下来的操作：")
    print("  1. 重启 AI 服务：cd ai_service && python server.py")
    print("  2. BehaviorPipeline 会自动识别并加载自训模型")
    print("  3. 在 /system/ai 监控页点对应流水线「加载」按钮验证")
    print()
    print("答辩时可以说：")
    print("  '我们在 SCB 课堂行为数据集上对 YOLOv8 做了针对性微调，")
    print(f"   共 {len(classes)} 类课堂行为，在验证集上达到 mAP50 = XX.X%。'")
    print("=" * 60)


if __name__ == "__main__":
    main()
