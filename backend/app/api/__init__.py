"""REST API 蓝图集合。"""

from __future__ import annotations

from flask import Blueprint

from .auth import auth_bp
from .health import health_bp
from .orgs import orgs_bp
from .users import users_bp

api_bp = Blueprint("api", __name__)
api_bp.register_blueprint(health_bp, url_prefix="/health")
api_bp.register_blueprint(auth_bp, url_prefix="/auth")
api_bp.register_blueprint(users_bp, url_prefix="/users")
api_bp.register_blueprint(orgs_bp, url_prefix="/orgs")
