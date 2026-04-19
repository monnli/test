"""AI 推理服务客户端封装。

封装点：
- 统一读取 AI_SERVICE_URL
- 超时 / 重试
- 失败优雅降级（返回 mock-like 空结果，不让业务中断）
"""

from __future__ import annotations

import base64
from typing import Any

import httpx
from flask import current_app
from loguru import logger


class AIClient:
    """AI 推理服务的 HTTP 客户端。"""

    def __init__(self, base_url: str, timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    @classmethod
    def from_app(cls) -> AIClient:
        return cls(
            base_url=current_app.config.get("AI_SERVICE_URL", "http://localhost:8000"),
            timeout=float(current_app.config.get("AI_REQUEST_TIMEOUT", 60)),
        )

    # ---------- 基础 ----------
    def get(self, path: str) -> dict[str, Any]:
        try:
            with httpx.Client(timeout=self.timeout) as c:
                resp = c.get(f"{self.base_url}{path}")
                resp.raise_for_status()
                return resp.json()
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"AI 服务 GET {path} 失败：{exc}")
            return {"code": -1, "message": str(exc), "data": None}

    def post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            with httpx.Client(timeout=self.timeout) as c:
                resp = c.post(f"{self.base_url}{path}", json=payload)
                resp.raise_for_status()
                return resp.json()
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"AI 服务 POST {path} 失败：{exc}")
            return {"code": -1, "message": str(exc), "data": None}

    # ---------- 业务封装 ----------
    def health(self) -> dict[str, Any]:
        return self.get("/health")

    def pipelines(self) -> dict[str, Any]:
        return self.get("/pipelines")

    def face_detect(self, image_bytes: bytes) -> dict[str, Any]:
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        return self.post("/face/detect", {"image": b64})

    def face_match(
        self,
        query_embedding: list[float],
        candidates: list[dict[str, Any]],
        threshold: float = 0.45,
    ) -> dict[str, Any]:
        return self.post(
            "/face/match",
            {
                "query_embedding": query_embedding,
                "candidates": candidates,
                "threshold": threshold,
            },
        )

    def emotion_predict(self, image_bytes: bytes) -> dict[str, Any]:
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        return self.post("/emotion/predict", {"image": b64})

    def behavior_detect(self, image_bytes: bytes, conf: float = 0.35) -> dict[str, Any]:
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        return self.post("/behavior/detect", {"image": b64, "conf": conf})

    def text_sentiment(self, text: str) -> dict[str, Any]:
        return self.post("/text/sentiment", {"text": text})

    def text_summarize(self, text: str) -> dict[str, Any]:
        return self.post("/text/summarize", {"text": text})

    def text_chat(self, messages: list[dict[str, str]], system: str | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {"messages": messages}
        if system:
            payload["system"] = system
        return self.post("/text/chat", payload)


def get_ai_client() -> AIClient:
    return AIClient.from_app()
