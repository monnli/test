"""图像相关工具。"""

from __future__ import annotations

import base64
import io
from pathlib import Path

import numpy as np
from PIL import Image


def decode_base64_image(data: str) -> np.ndarray:
    """解码 base64 图像字符串为 RGB ndarray。支持 data URL 前缀。"""
    if data.startswith("data:"):
        _, data = data.split(",", 1)
    raw = base64.b64decode(data)
    img = Image.open(io.BytesIO(raw)).convert("RGB")
    return np.array(img)


def load_image(path: str | Path) -> np.ndarray:
    img = Image.open(path).convert("RGB")
    return np.array(img)


def to_bgr(rgb: np.ndarray) -> np.ndarray:
    """OpenCV / Insightface 默认使用 BGR。"""
    return rgb[:, :, ::-1].copy()


def encode_base64_image(img: np.ndarray, fmt: str = "JPEG") -> str:
    pil = Image.fromarray(img)
    buf = io.BytesIO()
    pil.save(buf, fmt, quality=88)
    return base64.b64encode(buf.getvalue()).decode("utf-8")
