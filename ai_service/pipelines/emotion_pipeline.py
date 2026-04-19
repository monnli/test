"""表情识别流水线（HSEmotion）。

输入：人脸裁剪图（或整张含单人脸的图）
输出：7 类基础情绪 {高兴/悲伤/愤怒/恐惧/中性/厌恶/惊讶} 的概率分布
"""

from __future__ import annotations

import hashlib
from typing import Any

import numpy as np
from loguru import logger

from .base import BasePipeline

EMOTION_LABELS_CN = {
    "Happiness": "高兴",
    "Sadness": "悲伤",
    "Anger": "愤怒",
    "Fear": "恐惧",
    "Neutral": "中性",
    "Disgust": "厌恶",
    "Surprise": "惊讶",
    "Contempt": "蔑视",
}


class EmotionPipeline(BasePipeline):
    name = "emotion"

    def _load(self) -> None:
        from hsemotion.facial_emotions import HSEmotionRecognizer  # type: ignore

        model_name = "enet_b0_8_best_afew"
        self._model = HSEmotionRecognizer(model_name=model_name, device=self.device)

    def _infer(self, face_image: np.ndarray) -> dict[str, Any]:
        """face_image: RGB ndarray。"""
        emotion, scores = self._model.predict_emotions(face_image, logits=False)
        probs: dict[str, float] = {}
        # hsemotion 返回的 scores 顺序与标签对应
        labels = getattr(self._model, "idx_to_class", None)
        if labels:
            for idx, p in enumerate(scores):
                probs[labels[idx]] = float(p)
        else:
            probs[emotion] = 1.0
        return {
            "emotion": emotion,
            "emotion_cn": EMOTION_LABELS_CN.get(emotion, emotion),
            "confidence": float(max(scores)) if hasattr(scores, "__iter__") else 1.0,
            "probs": probs,
            "probs_cn": {EMOTION_LABELS_CN.get(k, k): v for k, v in probs.items()},
        }

    def _mock(self, face_image: np.ndarray) -> dict[str, Any]:
        # 使用像素哈希保证稳定
        seed = int(hashlib.md5(face_image.tobytes()).hexdigest()[:8], 16)
        rng = np.random.default_rng(seed)
        labels = ["Happiness", "Neutral", "Surprise", "Sadness", "Anger", "Fear", "Disgust"]
        weights = rng.dirichlet(np.ones(len(labels)) * 1.5)
        top_idx = int(np.argmax(weights))
        probs = {l: float(w) for l, w in zip(labels, weights)}
        return {
            "emotion": labels[top_idx],
            "emotion_cn": EMOTION_LABELS_CN[labels[top_idx]],
            "confidence": float(weights[top_idx]),
            "probs": probs,
            "probs_cn": {EMOTION_LABELS_CN.get(k, k): v for k, v in probs.items()},
            "_mock": True,
        }


emotion_pipeline = EmotionPipeline()
