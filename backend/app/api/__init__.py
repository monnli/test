"""REST API 蓝图集合。"""

from __future__ import annotations

from flask import Blueprint

from .health import health_bp

api_bp = Blueprint("api", __name__)
api_bp.register_blueprint(health_bp, url_prefix="/health")
