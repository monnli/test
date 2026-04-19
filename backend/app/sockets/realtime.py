"""实时摄像头 WebSocket 处理。

客户端事件：
- connect        连接
- frame          {frame: base64, timestamp}  发来一帧
服务端回传：
- analysis_result {timestamp, faces:[], emotion:{}, behavior:{}}
"""

from __future__ import annotations

import base64
import time

from flask_socketio import emit
from loguru import logger

from ..ai import AIClient
from ..extensions import socketio

NS = "/ws"


@socketio.on("connect", namespace=NS)
def on_connect():
    logger.info("WebSocket 客户端已连接")
    emit("connected", {"ts": int(time.time())})


@socketio.on("disconnect", namespace=NS)
def on_disconnect():
    logger.info("WebSocket 客户端已断开")


@socketio.on("frame", namespace=NS)
def on_frame(payload: dict):
    """接收客户端发来的一帧，调用 AI 服务分析后回传结果。"""
    img_b64 = payload.get("frame") or ""
    ts = payload.get("timestamp") or int(time.time() * 1000)
    if not img_b64:
        return
    if img_b64.startswith("data:"):
        img_b64 = img_b64.split(",", 1)[-1]
    try:
        img_bytes = base64.b64decode(img_b64)
    except Exception as exc:  # noqa: BLE001
        emit("analysis_result", {"timestamp": ts, "error": f"图像解码失败：{exc}"})
        return

    from flask import current_app

    client = AIClient(
        base_url=current_app.config.get("AI_SERVICE_URL", "http://localhost:8000"),
        timeout=6.0,
    )

    behavior = client.behavior_detect(img_bytes).get("data") or {}
    emotion = client.emotion_predict(img_bytes).get("data") or {}

    emit(
        "analysis_result",
        {
            "timestamp": ts,
            "behavior": {
                "detections": behavior.get("detections", []),
                "summary": behavior.get("summary", {}),
            },
            "emotion": {
                "emotion": emotion.get("emotion"),
                "emotion_cn": emotion.get("emotion_cn"),
                "confidence": emotion.get("confidence"),
            },
        },
    )
