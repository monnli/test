"""把项目根目录的 best.pt 注册为课堂行为模型（YOLOv8）。

用途：
- 你训练好的权重放在仓库根目录 `best.pt`
- 本脚本会复制到 `ai_service/models/yolov8_classroom.pt`
- 并从模型读取类别名，生成 `ai_service/models/yolov8_classroom_labels.json`

用法（在项目根目录执行）：
    python scripts/register_root_best_pt.py
    python scripts/register_root_best_pt.py --weights path/to/best.pt

然后：
1) `.env` 设置 `FORCE_MOCK=false`、`AI_DEVICE=cpu`（无 GPU）
2) 重新安装依赖：`pip install -r ai_service/requirements.txt`（含 ultralytics/torch）
3) 重启 `ai_service` 与 `backend`
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
AI_MODEL_DIR = PROJECT_ROOT / "ai_service" / "models"


def _guess_cn(name: str) -> str:
    """与 ai_service/pipelines/behavior_pipeline.py::_GUESS_CN_LABEL 保持同口径（简化版）。"""
    raw = str(name).strip()
    # 你的 best.pt 类别名本身就是中文：直接原样返回（label_cn == 中文类别）
    if any("\u4e00" <= ch <= "\u9fff" for ch in raw):
        return raw
    key = raw.lower().replace("-", "_").replace(" ", "_")
    alias = {
        "raising_hand": "举手",
        "raise_hand": "举手",
        "handup": "举手",
        "hand_up": "举手",
        "hand_raising": "举手",
        "writing": "写作",
        "write": "写作",
        "reading": "阅读",
        "read": "阅读",
        "listening": "听课",
        "listen": "听课",
        "standing": "站立",
        "stand": "站立",
        "sitting": "坐姿",
        "sit": "坐姿",
        "talking": "交头接耳",
        "talk": "交头接耳",
        "sleeping": "睡觉",
        "sleep": "睡觉",
        "bowing_head": "低头",
        "bow_head": "低头",
        "bow": "低头",
        "head_down": "低头",
        "head_up": "抬头",
        "lying": "趴桌",
        "lean": "趴桌",
        "phone": "玩手机",
        "using_phone": "玩手机",
        "use_phone": "玩手机",
        "cell_phone": "玩手机",
        "look_at_screen": "看屏幕",
        "look_screen": "看屏幕",
        "person": "学生",
        "student": "学生",
        "teacher": "教师",
        "book": "书本",
        "laptop": "笔记本",
        # 课堂 8 行为（常见英文别名）
        "head_down_writing": "低头写字",
        "writing_head_down": "低头写字",
        "write_head_down": "低头写字",
        "head_down_reading": "低头看书",
        "reading_head_down": "低头看书",
        "read_head_down": "低头看书",
        "head_up_listening": "抬头听课",
        "listen_head_up": "抬头听课",
        "listening_head_up": "抬头听课",
        "turn_head": "转头",
        "turning_head": "转头",
        "look_around": "转头",
        "group_discussion": "小组讨论",
        "discussion": "小组讨论",
        "group_talk": "小组讨论",
        "teacher_guidance": "教师指导",
        "teacher_guide": "教师指导",
        "teacher_instruction": "教师指导",
    }
    return alias.get(key, raw)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--weights",
        default=str(PROJECT_ROOT / "best.pt"),
        help="YOLOv8 权重路径（默认：项目根目录 best.pt）",
    )
    args = parser.parse_args()

    src = Path(args.weights)
    if not src.is_absolute():
        src = PROJECT_ROOT / src
    if not src.exists():
        print(f"[ERR] 找不到权重文件：{src}")
        sys.exit(1)

    AI_MODEL_DIR.mkdir(parents=True, exist_ok=True)
    dst = AI_MODEL_DIR / "yolov8_classroom.pt"
    shutil.copy2(src, dst)
    print(f"[OK] 已复制权重：{src} -> {dst}")

    try:
        from ultralytics import YOLO  # type: ignore
    except ImportError as exc:  # pragma: no cover
        print(f"[ERR] ultralytics 未安装：{exc}")
        print("      请先执行：pip install -r ai_service/requirements.txt")
        sys.exit(1)

    model = YOLO(str(dst))
    names_attr = getattr(model, "names", None) or getattr(model.model, "names", None)
    if not names_attr:
        print("[ERR] 无法从模型读取类别 names")
        sys.exit(1)
    if isinstance(names_attr, dict):
        names = [names_attr[i] for i in sorted(names_attr.keys())]
    else:
        names = list(names_attr)

    labels_cn = {n: _guess_cn(n) for n in names}
    out = AI_MODEL_DIR / "yolov8_classroom_labels.json"
    payload = {"model_path": str(dst.name), "classes": names, "labels_cn": labels_cn}
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] 已生成类别映射：{out}")
    print(f"     共 {len(names)} 类：{names}")
    print()
    print("下一步：")
    print("  1) 编辑 `.env`：FORCE_MOCK=false，AI_DEVICE=cpu")
    print("  2) pip install -r ai_service/requirements.txt && pip install -r backend/requirements.txt")
    print("  3) 重启 ai_service 与 backend（或 scripts/start_all.bat）")
    print("  4) 若中文映射不准：直接编辑 yolov8_classroom_labels.json 的 labels_cn")


if __name__ == "__main__":
    main()
