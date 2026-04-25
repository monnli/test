"""课堂行为检测流水线（YOLOv8）。

标准课堂 **8 类**（与自训 best.pt 中文类别一致）：
低头写字、低头看书、抬头听课、转头、举手、站立、小组讨论、教师指导。

- 自训模型：直接使用模型 `names`（可为中文），配合 `CLASSROOM_BEHAVIORS_CN` 与 `_GUESS_CN_LABEL`。
- 通用 COCO 回退：将 person / book / laptop / cell phone 等映射到上述八类中最接近的一项。
"""

from __future__ import annotations

import hashlib
from typing import Any

import numpy as np
from loguru import logger

from .base import AI_MODEL_DIR, BasePipeline

# COCO 80 类中我们关注的
COCO_INTEREST = {
    0: "person",
    67: "cell phone",
    63: "laptop",
    64: "mouse",
    66: "keyboard",
    73: "book",
}

# 标准八类中文（训练集可直接用这八个字符串作类别名）
BEHAVIOR_CLASSES_CN: tuple[str, ...] = (
    "低头写字",
    "低头看书",
    "抬头听课",
    "转头",
    "举手",
    "站立",
    "小组讨论",
    "教师指导",
)

CLASSROOM_BEHAVIORS_CN: dict[str, str] = {
    **{cn: cn for cn in BEHAVIOR_CLASSES_CN},
    # 历史 / COCO / 常见英文别名 → 标准八类
    "person": "抬头听课",
    "person_head_up": "抬头听课",
    "person_head_down": "低头看书",
    "student": "抬头听课",
    "hand_up": "举手",
    "raising_hand": "举手",
    "raise_hand": "举手",
    "hand_raise": "举手",
    "standing": "站立",
    "stand": "站立",
    "sitting": "抬头听课",
    "sit": "抬头听课",
    "lying": "低头写字",
    "sleeping": "低头看书",
    "talking": "小组讨论",
    "discussion": "小组讨论",
    "group_discussion": "小组讨论",
    "teacher": "教师指导",
    "using_phone": "低头看书",
    "cell phone": "低头看书",
    "cell_phone": "低头看书",
    "book": "低头看书",
    "laptop": "低头写字",
    "mouse": "低头写字",
    "keyboard": "低头写字",
}


class BehaviorPipeline(BasePipeline):
    name = "behavior"

    def _load(self) -> None:
        from ultralytics import YOLO  # type: ignore

        # 按优先级搜索自训模型路径
        project_root = AI_MODEL_DIR.parent.parent
        candidates = [
            # 用户放在仓库根目录的权重（比赛/本地训练最常见）
            project_root / "best.pt",
            # 兼容历史命名
            AI_MODEL_DIR / "yolov8_classroom.pt",
            AI_MODEL_DIR / "yolov8m_best.pt",
            AI_MODEL_DIR / "yolov8_best.pt",
            project_root / "yolov8m_best.pt",
            project_root / "yolov8_best.pt",
        ]
        for path in candidates:
            if path.exists():
                logger.success(f"🎯 加载自训课堂行为模型：{path}")
                self._model = YOLO(str(path))
                self._auto_register_labels()
                return

        generic_model = AI_MODEL_DIR / "yolov8n.pt"
        if generic_model.exists():
            logger.info(f"加载通用 YOLOv8：{generic_model}")
            self._model = YOLO(str(generic_model))
            return
        logger.info("YOLOv8 权重不在本地，使用 ultralytics 默认缓存或自动下载")
        self._model = YOLO("yolov8n.pt")

    def _auto_register_labels(self) -> None:
        """从加载的自训模型里读出类别名并生成中文映射。

        支持三种来源：
        1. ai_service/models/yolov8_classroom_labels.json（手动维护）
        2. 模型本身的 names 属性（自动）
        3. 内置英文→中文词典（用于标准词汇）
        """
        import json

        # 先尝试读外部映射文件
        labels_file = AI_MODEL_DIR / "yolov8_classroom_labels.json"
        if labels_file.exists():
            try:
                data = json.loads(labels_file.read_text(encoding="utf-8"))
                cn_map = data.get("labels_cn") or {}
                CLASSROOM_BEHAVIORS_CN.update(cn_map)
                logger.info(f"自训模型类别中文映射已合并（来自 JSON）：{list(cn_map.keys())}")
            except Exception as exc:  # noqa: BLE001
                logger.warning(f"加载自训标签 JSON 失败：{exc}")

        # 再自动读模型内的类别
        try:
            names = getattr(self._model, "names", None) or getattr(self._model.model, "names", None)
            if not names:
                return
            auto_map = {}
            for _, name in (names.items() if isinstance(names, dict) else enumerate(names)):
                # 有 JSON 映射就跳过，否则用默认字典或保留原值
                if name in CLASSROOM_BEHAVIORS_CN:
                    continue
                cn = _GUESS_CN_LABEL(name)
                auto_map[name] = cn
            if auto_map:
                CLASSROOM_BEHAVIORS_CN.update(auto_map)
                logger.info(f"自动识别模型类别 → 中文映射：{auto_map}")
        except Exception as exc:  # noqa: BLE001
            logger.debug(f"读取模型类别失败：{exc}")

    def _infer(self, image: np.ndarray, conf: float = 0.35) -> dict[str, Any]:
        """image: RGB ndarray。"""
        # ultralytics 支持 RGB ndarray
        result = self._model.predict(image, conf=conf, verbose=False)[0]
        names = result.names if hasattr(result, "names") else self._model.names
        detections: list[dict[str, Any]] = []
        if result.boxes is None:
            return {"detections": [], "summary": {}}

        # 判断是自训模型还是 COCO 通用模型：
        # 通用模型类别很多（80 类）且包含 person；自训模型类别少（3~10 类）
        is_custom = len(names) < 30 if isinstance(names, dict) else False

        for box in result.boxes:
            cls_id = int(box.cls.item()) if hasattr(box.cls, "item") else int(box.cls)
            label = names.get(cls_id, str(cls_id)) if isinstance(names, dict) else names[cls_id]
            # 通用模型：只保留我们关心的 COCO 类别
            # 自训模型：保留所有类别
            if not is_custom and cls_id not in COCO_INTEREST:
                continue
            xyxy = box.xyxy[0].cpu().numpy().tolist() if hasattr(box.xyxy[0], "cpu") else list(box.xyxy[0])
            cn = CLASSROOM_BEHAVIORS_CN.get(label) or _GUESS_CN_LABEL(label)
            detections.append({
                "label": label,
                "label_cn": cn,
                "confidence": float(box.conf.item()) if hasattr(box.conf, "item") else float(box.conf),
                "bbox": xyxy,
            })
        return {
            "detections": detections,
            "summary": _summarize(detections),
        }

    def _mock(self, image: np.ndarray, conf: float = 0.35) -> dict[str, Any]:
        h, w = image.shape[:2]
        seed = int(hashlib.md5(image.tobytes()).hexdigest()[:8], 16)
        rng = np.random.default_rng(seed)
        n = int(rng.integers(2, 5))
        detections: list[dict[str, Any]] = []
        labels_pool = list(BEHAVIOR_CLASSES_CN)
        for _ in range(n):
            x1 = rng.uniform(0, w * 0.55)
            y1 = rng.uniform(0, h * 0.55)
            x2 = x1 + rng.uniform(60, 160)
            y2 = y1 + rng.uniform(70, 200)
            cn = str(rng.choice(labels_pool))
            detections.append({
                "label": cn,
                "label_cn": cn,
                "confidence": float(rng.uniform(0.62, 0.93)),
                "bbox": [float(x1), float(y1), float(min(x2, w)), float(min(y2, h))],
            })
        return {"detections": detections, "summary": _summarize(detections), "_mock": True}


def _summarize(detections: list[dict[str, Any]]) -> dict[str, int]:
    summary: dict[str, int] = {}
    for d in detections:
        key = d["label_cn"] or d["label"]
        summary[key] = summary.get(key, 0) + 1
    return summary


def _GUESS_CN_LABEL(en_name: str) -> str:
    """尝试把英文类别名翻成标准八类中文，失败则返回原名。"""
    raw = str(en_name).strip()
    if any("\u4e00" <= ch <= "\u9fff" for ch in raw):
        return raw

    key = raw.lower().replace("-", "_").replace(" ", "_")
    alias = {
        "head_down_writing": "低头写字",
        "writing_head_down": "低头写字",
        "write_head_down": "低头写字",
        "writing": "低头写字",
        "write": "低头写字",
        "head_down_reading": "低头看书",
        "reading_head_down": "低头看书",
        "read_head_down": "低头看书",
        "reading": "低头看书",
        "read": "低头看书",
        "head_up_listening": "抬头听课",
        "listen_head_up": "抬头听课",
        "listening_head_up": "抬头听课",
        "listening": "抬头听课",
        "listen": "抬头听课",
        "turn_head": "转头",
        "turning_head": "转头",
        "look_around": "转头",
        "raising_hand": "举手",
        "raise_hand": "举手",
        "handup": "举手",
        "hand_up": "举手",
        "hand_raising": "举手",
        "hand_raise": "举手",
        "standing": "站立",
        "stand": "站立",
        "group_discussion": "小组讨论",
        "discussion": "小组讨论",
        "group_talk": "小组讨论",
        "talking": "小组讨论",
        "talk": "小组讨论",
        "teacher_guidance": "教师指导",
        "teacher_guide": "教师指导",
        "teacher_instruction": "教师指导",
        "teacher": "教师指导",
        # COCO / 旧版兼容 → 八类
        "person": "抬头听课",
        "student": "抬头听课",
        "sitting": "抬头听课",
        "sit": "抬头听课",
        "lying": "低头写字",
        "lean": "低头写字",
        "sleeping": "低头看书",
        "sleep": "低头看书",
        "bowing_head": "低头看书",
        "bow_head": "低头看书",
        "bow": "低头看书",
        "head_down": "低头看书",
        "head_up": "抬头听课",
        "phone": "低头看书",
        "using_phone": "低头看书",
        "use_phone": "低头看书",
        "cell_phone": "低头看书",
        "book": "低头看书",
        "laptop": "低头写字",
    }
    return alias.get(key, en_name)


behavior_pipeline = BehaviorPipeline()
