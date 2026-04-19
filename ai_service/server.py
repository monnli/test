"""青苗守护者 · AI 推理微服务（FastAPI）。

对外接口：
- GET  /health             健康检查
- GET  /info               设备、依赖信息
- GET  /pipelines          所有流水线加载状态
- POST /face/detect        人脸检测 + 提取 embedding
- POST /face/match         对比查询 embedding 与候选库
- POST /emotion/predict    表情识别
- POST /behavior/detect    课堂行为检测
- POST /text/sentiment     文本情绪分析
- POST /text/summarize     文本心理归纳
- POST /text/chat          AI 心理对话
"""

from __future__ import annotations

import base64
import io
import os
import sys
import time
from pathlib import Path
from typing import Any, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from PIL import Image
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

AI_DEVICE = os.getenv("AI_DEVICE", "cuda")
AI_MODEL_DIR = Path(os.getenv("AI_MODEL_DIR", PROJECT_ROOT / "ai_service" / "models"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logger.remove()
logger.add(sys.stderr, level=LOG_LEVEL, format="<green>{time:HH:mm:ss}</green> | <level>{level: <7}</level> | {message}")

sys.path.insert(0, str(Path(__file__).resolve().parent))

from pipelines import (  # noqa: E402
    behavior_pipeline,
    emotion_pipeline,
    face_pipeline,
    find_best_match,
    text_pipeline,
)
from utils.image import decode_base64_image  # noqa: E402


app = FastAPI(
    title="青苗守护者 AI 推理服务",
    description="负责课堂行为、表情、人脸、文本等多模态 AI 推理任务",
    version="0.2.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========================== 通用模型 ==========================

class BaseResponse(BaseModel):
    code: int = 0
    message: str = "ok"
    data: Any = None


# ========================== 基础接口 ==========================

@app.get("/", summary="服务信息")
def root():
    return {
        "name": "qingmiao-ai-service",
        "version": "0.2.0",
        "device": AI_DEVICE,
        "model_dir": str(AI_MODEL_DIR),
    }


@app.get("/health", summary="健康检查")
def health():
    return {
        "code": 0,
        "message": "ok",
        "data": {
            "service": "qingmiao-ai-service",
            "status": "healthy",
            "device": AI_DEVICE,
            "timestamp": int(time.time()),
        },
    }


@app.get("/info", summary="设备与依赖信息")
def info():
    payload: dict[str, Any] = {
        "device": AI_DEVICE,
        "model_dir": str(AI_MODEL_DIR),
        "python_version": sys.version.split()[0],
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
    return {"code": 0, "message": "ok", "data": payload}


@app.get("/pipelines", summary="所有流水线状态")
def list_pipelines():
    return {
        "code": 0,
        "message": "ok",
        "data": {
            "pipelines": [
                face_pipeline.status_info(),
                emotion_pipeline.status_info(),
                behavior_pipeline.status_info(),
                text_pipeline.status_info(),
            ]
        },
    }


@app.post("/pipelines/{name}/load", summary="主动加载某个流水线")
def load_pipeline(name: str):
    mapping = {
        "face": face_pipeline,
        "emotion": emotion_pipeline,
        "behavior": behavior_pipeline,
        "text": text_pipeline,
    }
    if name not in mapping:
        raise HTTPException(status_code=404, detail=f"未知流水线：{name}")
    mapping[name].ensure_loaded()
    return {"code": 0, "message": "ok", "data": mapping[name].status_info()}


# ========================== 人脸 ==========================

class FaceDetectRequest(BaseModel):
    image: str = Field(..., description="base64 编码的图像（可带 data URL 前缀）")


class FaceMatchRequest(BaseModel):
    query_embedding: List[float]
    candidates: List[dict] = Field(..., description="每项包含 person_id 与 embedding")
    threshold: float = 0.45


@app.post("/face/detect", summary="人脸检测 + 提取 embedding")
def face_detect(req: FaceDetectRequest):
    try:
        img = decode_base64_image(req.image)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"图像解码失败：{exc}")
    faces = face_pipeline.run(img)
    return {
        "code": 0,
        "message": "ok",
        "data": {
            "faces": faces,
            "count": len(faces),
            "pipeline_status": face_pipeline.status,
        },
    }


@app.post("/face/match", summary="1:N 人脸比对")
def face_match(req: FaceMatchRequest):
    result = find_best_match(req.query_embedding, req.candidates, req.threshold)
    return {"code": 0, "message": "ok", "data": result}


# ========================== 表情 ==========================

class EmotionRequest(BaseModel):
    image: str = Field(..., description="base64 编码的人脸图像")


@app.post("/emotion/predict", summary="表情识别")
def emotion_predict(req: EmotionRequest):
    try:
        img = decode_base64_image(req.image)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"图像解码失败：{exc}")
    result = emotion_pipeline.run(img)
    return {
        "code": 0,
        "message": "ok",
        "data": {**result, "pipeline_status": emotion_pipeline.status},
    }


# ========================== 行为 ==========================

class BehaviorRequest(BaseModel):
    image: str
    conf: float = 0.35


@app.post("/behavior/detect", summary="课堂行为检测")
def behavior_detect(req: BehaviorRequest):
    try:
        img = decode_base64_image(req.image)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"图像解码失败：{exc}")
    result = behavior_pipeline.run(img, conf=req.conf)
    return {
        "code": 0,
        "message": "ok",
        "data": {**result, "pipeline_status": behavior_pipeline.status},
    }


# ========================== 文本 ==========================

class TextRequest(BaseModel):
    text: str


class ChatRequest(BaseModel):
    messages: List[dict]
    system: Optional[str] = None


@app.post("/text/sentiment", summary="文本情绪分析")
def text_sentiment(req: TextRequest):
    result = text_pipeline.analyze_sentiment(req.text)
    return {"code": 0, "message": "ok", "data": {**result, "pipeline_status": text_pipeline.status}}


@app.post("/text/summarize", summary="文本心理归纳")
def text_summarize(req: TextRequest):
    result = text_pipeline.summarize_psychology(req.text)
    return {"code": 0, "message": "ok", "data": {**result, "pipeline_status": text_pipeline.status}}


@app.post("/text/chat", summary="AI 心理对话")
def text_chat(req: ChatRequest):
    result = text_pipeline.chat(req.messages, req.system)
    return {"code": 0, "message": "ok", "data": {**result, "pipeline_status": text_pipeline.status}}


# ========================== 启动 ==========================

if __name__ == "__main__":
    import uvicorn

    host = os.getenv("AI_HOST", "0.0.0.0")
    port = int(os.getenv("AI_PORT", "8000"))
    uvicorn.run("server:app", host=host, port=port, reload=False)
