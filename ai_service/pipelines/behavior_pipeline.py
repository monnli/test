"""课堂行为检测流水线（YOLOv8）。

检测类别（基于 COCO + 自定义映射）：
- 人（person）
- 举手（hand_up）← 通过姿态关键点派生
- 趴桌（lying）← 通过姿态+位置派生
- 坐立（sitting / standing）← 姿态派生
- 玩手机（using_phone）← COCO: cell phone + 人重合判定
- 睡觉（sleeping）← 姿态派生

M2 阶段实现简单版：只做 person + cell phone 检测；复杂行为的分类放 M3 阶段。
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

CLASSROOM_BEHAVIORS_CN = {
    "person": "学生",
    "person_head_up": "抬头",
    "person_head_down": "低头",
    "hand_up": "举手",
    "lying": "趴桌",
    "sitting": "坐姿",
    "standing": "站立",
    "using_phone": "玩手机",
    "sleeping": "睡觉",
    "talking": "交头接耳",
    "cell phone": "手机",
    "book": "书本",
    "laptop": "笔记本",
}


class BehaviorPipeline(BasePipeline):
    name = "behavior"

    def _load(self) -> None:
        from ultralytics import YOLO  # type: ignore

        # 优先级：
        # 1. 自训课堂行为模型（yolov8_classroom.pt）
        # 2. 通用 yolov8n.pt（本地）
        # 3. ultralytics 默认缓存/自动下载
        classroom_model = AI_MODEL_DIR / "yolov8_classroom.pt"
        generic_model = AI_MODEL_DIR / "yolov8n.pt"

        if classroom_model.exists():
            logger.success(f"🎯 加载自训课堂行为模型：{classroom_model}")
            self._model = YOLO(str(classroom_model))
            self._load_custom_labels()
            return
        if generic_model.exists():
            logger.info(f"加载通用 YOLOv8：{generic_model}")
            self._model = YOLO(str(generic_model))
            return
        logger.info("YOLOv8 权重不在本地，使用 ultralytics 默认缓存或自动下载")
        self._model = YOLO("yolov8n.pt")

    def _load_custom_labels(self) -> None:
        """加载自训模型的中文标签映射。"""
        import json

        labels_file = AI_MODEL_DIR / "yolov8_classroom_labels.json"
        if not labels_file.exists():
            return
        try:
            data = json.loads(labels_file.read_text(encoding="utf-8"))
            cn_map = data.get("labels_cn") or {}
            # 合并到全局映射
            CLASSROOM_BEHAVIORS_CN.update(cn_map)
            logger.info(f"自训模型类别中文映射已合并：{list(cn_map.keys())}")
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"加载自训标签失败：{exc}")

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
            detections.append({
                "label": label,
                "label_cn": CLASSROOM_BEHAVIORS_CN.get(label, label),
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
        n = int(rng.integers(2, 6))
        detections: list[dict[str, Any]] = []
        for _ in range(n):
            x1 = rng.uniform(0, w * 0.6)
            y1 = rng.uniform(0, h * 0.6)
            x2 = x1 + rng.uniform(60, 150)
            y2 = y1 + rng.uniform(80, 200)
            detections.append({
                "label": "person",
                "label_cn": "学生",
                "confidence": float(rng.uniform(0.6, 0.95)),
                "bbox": [float(x1), float(y1), float(min(x2, w)), float(min(y2, h))],
            })
        if rng.random() < 0.3:
            detections.append({
                "label": "cell phone",
                "label_cn": "手机",
                "confidence": 0.72,
                "bbox": [w * 0.2, h * 0.5, w * 0.25, h * 0.55],
            })
        return {"detections": detections, "summary": _summarize(detections), "_mock": True}


def _summarize(detections: list[dict[str, Any]]) -> dict[str, int]:
    summary: dict[str, int] = {}
    for d in detections:
        key = d["label_cn"] or d["label"]
        summary[key] = summary.get(key, 0) + 1
    return summary


behavior_pipeline = BehaviorPipeline()
