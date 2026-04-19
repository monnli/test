"""健康检查接口。用于探活与依赖检测。"""

from __future__ import annotations

import time

import httpx
from flask import Blueprint, current_app, jsonify
from sqlalchemy import text

from ..extensions import db

health_bp = Blueprint("health", __name__)


@health_bp.get("")
def health():
    """基础健康检查：仅返回服务状态。"""
    return jsonify(
        code=0,
        message="ok",
        data={
            "service": "qingmiao-guardian-backend",
            "status": "healthy",
            "timestamp": int(time.time()),
        },
    )


@health_bp.get("/deep")
def deep_health():
    """深度健康检查：探测所有依赖（DB / Redis / MinIO / AI）。"""
    results: dict[str, dict] = {}

    # MySQL
    try:
        db.session.execute(text("SELECT 1"))
        results["mysql"] = {"status": "ok"}
    except Exception as exc:  # noqa: BLE001
        results["mysql"] = {"status": "error", "detail": str(exc)}

    # Redis
    try:
        import redis

        r = redis.Redis(
            host=current_app.config["REDIS_HOST"],
            port=current_app.config["REDIS_PORT"],
            password=current_app.config["REDIS_PASSWORD"],
            db=current_app.config["REDIS_DB"],
            socket_connect_timeout=2,
        )
        r.ping()
        results["redis"] = {"status": "ok"}
    except Exception as exc:  # noqa: BLE001
        results["redis"] = {"status": "error", "detail": str(exc)}

    # MinIO
    try:
        from minio import Minio

        client = Minio(
            current_app.config["MINIO_ENDPOINT"],
            access_key=current_app.config["MINIO_ACCESS_KEY"],
            secret_key=current_app.config["MINIO_SECRET_KEY"],
            secure=current_app.config["MINIO_SECURE"],
        )
        list(client.list_buckets())
        results["minio"] = {"status": "ok"}
    except Exception as exc:  # noqa: BLE001
        results["minio"] = {"status": "error", "detail": str(exc)}

    # AI 服务
    try:
        with httpx.Client(timeout=3.0) as client:
            resp = client.get(f"{current_app.config['AI_SERVICE_URL']}/health")
            resp.raise_for_status()
        results["ai_service"] = {"status": "ok"}
    except Exception as exc:  # noqa: BLE001
        results["ai_service"] = {"status": "error", "detail": str(exc)}

    overall = "healthy" if all(v["status"] == "ok" for v in results.values()) else "degraded"
    return jsonify(
        code=0,
        message=overall,
        data={
            "service": "qingmiao-guardian-backend",
            "status": overall,
            "dependencies": results,
            "timestamp": int(time.time()),
        },
    )
