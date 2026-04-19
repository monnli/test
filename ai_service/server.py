"""青苗守护者 · AI 推理微服务（FastAPI）

M0 阶段：仅提供基础健康检查 + 流水线注册占位。
M2 起逐步接入 YOLOv8 / InsightFace / HSEmotion / MediaPipe 等真实模型。
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from pydantic import BaseModel

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

AI_DEVICE = os.getenv("AI_DEVICE", "cuda")
AI_MODEL_DIR = Path(os.getenv("AI_MODEL_DIR", PROJECT_ROOT / "ai_service" / "models"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logger.remove()
logger.add(sys.stderr, level=LOG_LEVEL)

app = FastAPI(
    title="青苗守护者 AI 推理服务",
    description="负责课堂行为、表情、人脸、文本等多模态 AI 推理任务",
    version="0.1.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class HealthResponse(BaseModel):
    service: str
    status: str
    device: str
    timestamp: int
    pipelines: dict


@app.get("/", summary="服务信息")
def root():
    return {
        "name": "qingmiao-ai-service",
        "version": "0.1.0",
        "device": AI_DEVICE,
        "model_dir": str(AI_MODEL_DIR),
    }


@app.get("/health", response_model=HealthResponse, summary="健康检查")
def health():
    return HealthResponse(
        service="qingmiao-ai-service",
        status="healthy",
        device=AI_DEVICE,
        timestamp=int(time.time()),
        pipelines={
            "behavior": "not_loaded",
            "emotion": "not_loaded",
            "face": "not_loaded",
            "text": "ready",
        },
    )


@app.get("/info", summary="设备与依赖信息")
def info():
    payload: dict = {
        "device": AI_DEVICE,
        "model_dir": str(AI_MODEL_DIR),
        "python_version": sys.version,
    }
    try:
        import torch  # type: ignore

        payload["torch"] = torch.__version__
        payload["cuda_available"] = bool(torch.cuda.is_available())
        if torch.cuda.is_available():
            payload["cuda_device"] = torch.cuda.get_device_name(0)
    except Exception:  # noqa: BLE001
        payload["torch"] = "not_installed"
        payload["cuda_available"] = False
    return payload


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("AI_HOST", "0.0.0.0")
    port = int(os.getenv("AI_PORT", "8000"))
    uvicorn.run("server:app", host=host, port=port, reload=False)
