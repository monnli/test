"""负责任 AI 仪表盘接口。"""

from __future__ import annotations

from flask import Blueprint

from ..services import ethics_service as svc
from ..utils.permissions import login_required
from ..utils.response import ok

ethics_bp = Blueprint("ethics", __name__)


@ethics_bp.get("/overview")
@login_required
def overview():
    return ok(svc.ethics_overview())
