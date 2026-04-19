"""数据大屏 API。"""

from __future__ import annotations

from flask import Blueprint

from ..services import dashboard_service as svc
from ..utils.permissions import login_required
from ..utils.response import ok

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.get("/overview")
@login_required
def overview():
    return ok(svc.overview())


@dashboard_bp.get("/all")
@login_required
def all_in_one():
    """大屏一次拉所有数据，减少请求次数。"""
    return ok({
        "overview": svc.overview(),
        "alert_distribution": svc.alert_distribution(),
        "class_engagement": svc.class_engagement(),
        "emotion_30d": svc.emotion_overview_30d(),
        "behavior_today": svc.behavior_distribution_today(),
        "emotion_today": svc.emotion_distribution_today(),
        "recent_alerts": svc.recent_alerts(),
        "top_risk": svc.top_risk_students(),
    })
