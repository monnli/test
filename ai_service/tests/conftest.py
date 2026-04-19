"""AI 服务测试 fixtures。"""

from __future__ import annotations

import base64
import io
import sys
from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from server import app  # noqa: E402


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture()
def sample_image_b64() -> str:
    img = Image.fromarray((np.ones((240, 320, 3)) * 128).astype("uint8"))
    buf = io.BytesIO()
    img.save(buf, "JPEG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")
