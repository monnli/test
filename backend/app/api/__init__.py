"""REST API 蓝图集合。"""

from __future__ import annotations

from flask import Blueprint

from .ai import ai_bp
from .auth import auth_bp
from .classroom import classroom_bp
from .faces import faces_bp
from .health import health_bp
from .orgs import orgs_bp
from .users import users_bp

api_bp = Blueprint("api", __name__)
api_bp.register_blueprint(health_bp, url_prefix="/health")
api_bp.register_blueprint(auth_bp, url_prefix="/auth")
api_bp.register_blueprint(users_bp, url_prefix="/users")
api_bp.register_blueprint(orgs_bp, url_prefix="/orgs")
api_bp.register_blueprint(faces_bp, url_prefix="/faces")
api_bp.register_blueprint(ai_bp, url_prefix="/ai")
api_bp.register_blueprint(classroom_bp, url_prefix="/classroom")

from .psychology import psy_bp  # noqa: E402

api_bp.register_blueprint(psy_bp, url_prefix="/psychology")

from .alerts import alerts_bp  # noqa: E402

api_bp.register_blueprint(alerts_bp, url_prefix="/alerts")

from .dashboard import dashboard_bp  # noqa: E402

api_bp.register_blueprint(dashboard_bp, url_prefix="/dashboard")

from .reports import reports_bp  # noqa: E402

api_bp.register_blueprint(reports_bp, url_prefix="/reports")

from .ethics import ethics_bp  # noqa: E402

api_bp.register_blueprint(ethics_bp, url_prefix="/ethics")

from .enhance import enhance_bp  # noqa: E402

api_bp.register_blueprint(enhance_bp, url_prefix="/enhance")

from .cameras import cameras_bp  # noqa: E402

api_bp.register_blueprint(cameras_bp, url_prefix="/m10")

from .live import live_bp  # noqa: E402

api_bp.register_blueprint(live_bp, url_prefix="/m10/live")
