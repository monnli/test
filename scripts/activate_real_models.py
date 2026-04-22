"""一键将 5 个真实模型接入系统。

做的事：
1. 自动把 yolov8m_best.pt 复制/软链接到 ai_service/models/yolov8_classroom.pt
2. 读取模型内置类别，生成 ai_service/models/yolov8_classroom_labels.json
3. 把通义千问 API key 写入 .env（若存在则覆盖 DASHSCOPE_API_KEY 那一行）
4. 检查 mediapipe / hsemotion / insightface 是否可导入
5. 输出各流水线状态建议

用法：
    python scripts/activate_real_models.py
    python scripts/activate_real_models.py --api-key sk-xxxx --yolo-weights yolov8m_best.pt
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
AI_MODEL_DIR = PROJECT_ROOT / "ai_service" / "models"
ENV_FILE = PROJECT_ROOT / ".env"

DEFAULT_API_KEY = "sk-145a1165628741f686970c2922119f7d"
DEFAULT_WEIGHTS_CANDIDATES = [
    PROJECT_ROOT / "yolov8m_best.pt",
    PROJECT_ROOT / "yolov8_best.pt",
    PROJECT_ROOT / "yolov8n_best.pt",
]


def copy_weights(src_path: Path) -> Path:
    """把 YOLO 权重部署到 ai_service/models/yolov8_classroom.pt"""
    AI_MODEL_DIR.mkdir(parents=True, exist_ok=True)
    dst = AI_MODEL_DIR / "yolov8_classroom.pt"
    if dst.exists():
        dst.unlink()
    shutil.copy2(src_path, dst)
    print(f"[OK] 权重已部署：{dst}  （{dst.stat().st_size / 1024 / 1024:.1f} MB）")
    return dst


def generate_labels_json(weights: Path) -> None:
    """加载模型读类别，生成 labels JSON。"""
    try:
        from ultralytics import YOLO  # type: ignore
    except ImportError:
        print("[WARN] ultralytics 未安装，跳过自动生成标签")
        return

    model = YOLO(str(weights))
    names_attr = getattr(model, "names", None) or getattr(model.model, "names", None)
    if not names_attr:
        print("[WARN] 无法从模型读出类别")
        return
    if isinstance(names_attr, dict):
        names = [names_attr[i] for i in sorted(names_attr.keys())]
    else:
        names = list(names_attr)

    # 英文 → 中文词典
    cn_alias = {
        "raising_hand": "举手", "raise_hand": "举手", "handup": "举手",
        "hand_up": "举手", "hand_raising": "举手",
        "writing": "写作", "write": "写作",
        "reading": "阅读", "read": "阅读",
        "listening": "听课", "listen": "听课",
        "standing": "站立", "stand": "站立",
        "sitting": "坐姿", "sit": "坐姿",
        "talking": "交头接耳", "talk": "交头接耳",
        "sleeping": "睡觉", "sleep": "睡觉",
        "bowing_head": "低头", "bow_head": "低头", "bow": "低头", "head_down": "低头",
        "head_up": "抬头",
        "lying": "趴桌", "lean": "趴桌",
        "phone": "玩手机", "using_phone": "玩手机", "use_phone": "玩手机",
        "cell_phone": "玩手机",
        "look_at_screen": "看屏幕", "look_screen": "看屏幕",
        "person": "学生", "student": "学生",
        "teacher": "教师",
        "book": "书本", "laptop": "笔记本",
    }
    labels_cn = {}
    for name in names:
        key = str(name).lower().replace("-", "_").replace(" ", "_")
        labels_cn[name] = cn_alias.get(key, name)

    payload = {
        "model_path": str(weights.name),
        "classes": names,
        "labels_cn": labels_cn,
    }
    out = AI_MODEL_DIR / "yolov8_classroom_labels.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] 类别映射已生成：{out}")
    print(f"     模型共 {len(names)} 类：{names}")
    print(f"     中文映射：{labels_cn}")


def update_env_api_key(api_key: str) -> None:
    """把 API key 写入 .env 的 DASHSCOPE_API_KEY。"""
    if not api_key:
        print("[SKIP] 未提供 API key")
        return
    if not ENV_FILE.exists():
        print(f"[WARN] 未找到 {ENV_FILE}，请先 cp .env.example .env")
        return
    lines = ENV_FILE.read_text(encoding="utf-8").splitlines()
    new_lines = []
    replaced = False
    for line in lines:
        if line.strip().startswith("DASHSCOPE_API_KEY="):
            new_lines.append(f"DASHSCOPE_API_KEY={api_key}")
            replaced = True
        else:
            new_lines.append(line)
    if not replaced:
        new_lines.append(f"DASHSCOPE_API_KEY={api_key}")
    ENV_FILE.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    print(f"[OK] DashScope API Key 已写入 .env")


def check_imports() -> None:
    print()
    print("=" * 60)
    print("依赖检查")
    print("=" * 60)
    checks = [
        ("ultralytics", "YOLOv8"),
        ("insightface", "InsightFace"),
        ("hsemotion_onnx", "HSEmotion ONNX"),
        ("hsemotion", "HSEmotion PyTorch"),
        ("mediapipe", "MediaPipe"),
        ("dashscope", "通义千问 SDK"),
        ("cv2", "OpenCV"),
    ]
    for mod, display in checks:
        try:
            __import__(mod)
            print(f"  [OK] {display} ({mod})")
        except ImportError:
            print(f"  [MISS] {display} ({mod}) 未安装")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--yolo-weights", default=None, help="YOLO 权重路径（默认扫描项目根目录）")
    parser.add_argument("--api-key", default=DEFAULT_API_KEY)
    args = parser.parse_args()

    print("=" * 60)
    print("青苗守护者 · 一键激活 5 个真实模型")
    print("=" * 60)

    # 1. 找 YOLO 权重
    weights: Path | None = None
    if args.yolo_weights:
        cand = Path(args.yolo_weights)
        if not cand.is_absolute():
            cand = PROJECT_ROOT / cand
        weights = cand if cand.exists() else None
    else:
        for cand in DEFAULT_WEIGHTS_CANDIDATES:
            if cand.exists():
                weights = cand
                break

    if weights is None:
        print("[ERR] 未找到 YOLO 权重，请用 --yolo-weights 指定路径，或放到项目根目录")
        print(f"      搜索位置：{[str(p) for p in DEFAULT_WEIGHTS_CANDIDATES]}")
        sys.exit(1)

    print(f"[使用权重] {weights}")
    dst = copy_weights(weights)
    generate_labels_json(dst)

    # 2. 写 API key
    print()
    update_env_api_key(args.api_key)

    # 3. 依赖检查
    check_imports()

    # 4. 提示
    print()
    print("=" * 60)
    print("✅ 全部完成")
    print()
    print("下一步：")
    print("  1. 重启 AI 服务：")
    print("       cd ai_service && python server.py")
    print("     成功时应看到：")
    print("       🎯 加载自训课堂行为模型：.../yolov8_classroom.pt")
    print("       加载 hsemotion-onnx 版 (enet_b0_8_best_afew)")
    print()
    print("  2. 重启后端（读取新 API key）：")
    print("       cd backend && python run.py")
    print()
    print("  3. 浏览器打开 /system/ai 监控页，点每个流水线「加载」按钮")
    print("     流水线状态应变成 ready（而非 mock）")
    print()
    print("  4. 用 /classroom/cameras 或 /enhance/story 做现场演示")
    print("=" * 60)


if __name__ == "__main__":
    main()
