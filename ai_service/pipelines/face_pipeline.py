"""人脸检测 + 识别流水线（InsightFace）。

功能：
- 检测：输入图像 → 返回 [{bbox, confidence, embedding, landmark}, ...]
- 识别：输入 embedding + 人脸库 → 返回最相似的 person_id
"""

from __future__ import annotations

import hashlib
from typing import Any

import numpy as np
from loguru import logger

from .base import AI_MODEL_DIR, BasePipeline


class FacePipeline(BasePipeline):
    name = "face"

    def _load(self) -> None:
        from insightface.app import FaceAnalysis  # type: ignore

        root_dir = AI_MODEL_DIR / "insightface"
        root_dir.mkdir(parents=True, exist_ok=True)
        ctx_id = 0 if self.device == "cuda" else -1
        app = FaceAnalysis(
            name="buffalo_l",
            root=str(root_dir),
            providers=["CUDAExecutionProvider", "CPUExecutionProvider"]
            if self.device == "cuda"
            else ["CPUExecutionProvider"],
        )
        app.prepare(ctx_id=ctx_id, det_size=(640, 640))
        self._model = app

    def _infer(self, image: np.ndarray) -> list[dict[str, Any]]:
        """image: RGB ndarray(H,W,3)。"""
        # insightface 期望 BGR
        bgr = image[:, :, ::-1].copy()
        faces = self._model.get(bgr)
        results: list[dict[str, Any]] = []
        for f in faces:
            bbox = f.bbox.astype(float).tolist()
            results.append({
                "bbox": bbox,
                "confidence": float(f.det_score),
                "embedding": f.embedding.astype(float).tolist(),
                "landmark": f.landmark_2d_106.astype(float).tolist()
                if hasattr(f, "landmark_2d_106") and f.landmark_2d_106 is not None
                else None,
                "age": int(f.age) if hasattr(f, "age") and f.age is not None else None,
                "gender": int(f.gender) if hasattr(f, "gender") and f.gender is not None else None,
            })
        return results

    def _mock(self, image: np.ndarray) -> list[dict[str, Any]]:
        """基于图像像素特征生成伪 embedding，保证同一图得到同一向量。"""
        h, w = image.shape[:2]
        # 用图像哈希种子伪造向量，512 维与 insightface 一致
        seed = int(hashlib.md5(image.tobytes()).hexdigest()[:8], 16)
        rng = np.random.default_rng(seed)
        embedding = rng.normal(size=512).astype(float)
        embedding = embedding / (np.linalg.norm(embedding) + 1e-8)
        return [
            {
                "bbox": [w * 0.25, h * 0.15, w * 0.75, h * 0.85],
                "confidence": 0.88,
                "embedding": embedding.tolist(),
                "landmark": None,
                "age": None,
                "gender": None,
                "_mock": True,
            }
        ]


def cosine_similarity(a: list[float] | np.ndarray, b: list[float] | np.ndarray) -> float:
    va, vb = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    denom = np.linalg.norm(va) * np.linalg.norm(vb)
    if denom < 1e-8:
        return 0.0
    return float(np.dot(va, vb) / denom)


def find_best_match(
    query: list[float] | np.ndarray,
    candidates: list[dict[str, Any]],
    threshold: float = 0.45,
) -> dict[str, Any] | None:
    """从候选人脸库中找最佳匹配。candidates 每项需含 person_id, embedding 字段。"""
    best_score = -1.0
    best_person_id: Any = None
    for c in candidates:
        s = cosine_similarity(query, c.get("embedding") or [])
        if s > best_score:
            best_score = s
            best_person_id = c.get("person_id")
    if best_score >= threshold and best_person_id is not None:
        return {"person_id": best_person_id, "score": best_score, "matched": True}
    return {"person_id": None, "score": best_score, "matched": False}


face_pipeline = FacePipeline()
