"""AI 服务调试与联调接口。

提供给前端 AI 监控页使用：
- 状态查询（健康 / 流水线加载情况）
- 文本情绪 / 归纳 / 对话（走后端中转，含操作审计）
- 表情 / 行为图片测试（走后端中转）
"""

from __future__ import annotations

import base64

from flask import Blueprint, request

from ..ai import get_ai_client
from ..utils.exceptions import ValidationError
from ..utils.permissions import admin_required, login_required
from ..utils.response import ok

ai_bp = Blueprint("ai", __name__)


def _extract_image_b64() -> bytes:
    if "file" in request.files:
        return request.files["file"].read()
    payload = request.get_json(silent=True) or {}
    image = payload.get("image")
    if not image:
        raise ValidationError("缺少图像（file 或 image 字段）")
    if image.startswith("data:"):
        image = image.split(",", 1)[-1]
    return base64.b64decode(image)


@ai_bp.get("/health")
@login_required
def api_ai_health():
    return ok(get_ai_client().health().get("data"))


@ai_bp.get("/pipelines")
@login_required
def api_ai_pipelines():
    return ok(get_ai_client().pipelines().get("data"))


@ai_bp.post("/pipelines/<name>/load")
@admin_required
def api_ai_load_pipeline(name: str):
    client = get_ai_client()
    resp = client.post(f"/pipelines/{name}/load", {})
    return ok(resp.get("data"), resp.get("message", "ok"))


@ai_bp.post("/text/sentiment")
@login_required
def api_ai_text_sentiment():
    payload = request.get_json(silent=True) or {}
    text = (payload.get("text") or "").strip()
    if not text:
        raise ValidationError("text 不能为空")
    return ok(get_ai_client().text_sentiment(text).get("data"))


@ai_bp.post("/text/summarize")
@login_required
def api_ai_text_summarize():
    payload = request.get_json(silent=True) or {}
    text = (payload.get("text") or "").strip()
    if not text:
        raise ValidationError("text 不能为空")
    return ok(get_ai_client().text_summarize(text).get("data"))


@ai_bp.post("/text/chat")
@login_required
def api_ai_text_chat():
    payload = request.get_json(silent=True) or {}
    messages = payload.get("messages") or []
    if not messages:
        raise ValidationError("messages 不能为空")
    system = payload.get("system")
    return ok(get_ai_client().text_chat(messages, system).get("data"))


@ai_bp.post("/emotion")
@login_required
def api_ai_emotion():
    img = _extract_image_b64()
    return ok(get_ai_client().emotion_predict(img).get("data"))


@ai_bp.post("/behavior")
@login_required
def api_ai_behavior():
    img = _extract_image_b64()
    conf = float(request.args.get("conf", 0.35))
    return ok(get_ai_client().behavior_detect(img, conf=conf).get("data"))
