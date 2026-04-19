"""预警与关联分析接口。"""

from __future__ import annotations

from flask import Blueprint, request

from ..services import correlation_service as svc
from ..utils.permissions import (
    get_current_user,
    get_visible_student_ids,
    login_required,
)
from ..utils.response import ok

alerts_bp = Blueprint("alerts", __name__)


@alerts_bp.get("")
@login_required
def list_alerts():
    user = get_current_user()
    visible = get_visible_student_ids(user)
    return ok(
        svc.list_alerts(
            level=request.args.get("level"),
            status=request.args.get("status"),
            student_ids=visible,
            page=request.args.get("page", default=1, type=int),
            page_size=request.args.get("page_size", default=20, type=int),
        )
    )


@alerts_bp.get("/stats")
@login_required
def alert_stats():
    user = get_current_user()
    visible = get_visible_student_ids(user)
    return ok(svc.alert_stats(student_ids=visible))


@alerts_bp.post("/recompute")
@login_required
def recompute():
    user = get_current_user()
    visible = get_visible_student_ids(user)
    return ok(svc.recompute_alerts_for_visible(student_ids=visible), "已重算")


@alerts_bp.post("/<int:alert_id>/acknowledge")
@login_required
def acknowledge(alert_id: int):
    user = get_current_user()
    return ok(svc.acknowledge_alert(alert_id, user.id), "已签收")


@alerts_bp.post("/<int:alert_id>/resolve")
@login_required
def resolve(alert_id: int):
    user = get_current_user()
    payload = request.get_json() or {}
    return ok(svc.resolve_alert(alert_id, user.id, payload.get("note")), "已处理")


@alerts_bp.post("/<int:alert_id>/close")
@login_required
def close(alert_id: int):
    user = get_current_user()
    return ok(svc.close_alert(alert_id, user.id), "已关闭")


@alerts_bp.get("/<int:alert_id>/interventions")
@login_required
def list_interventions(alert_id: int):
    return ok({"items": svc.list_interventions(alert_id)})


@alerts_bp.post("/<int:alert_id>/interventions")
@login_required
def add_intervention(alert_id: int):
    user = get_current_user()
    payload = request.get_json() or {}
    return ok(
        svc.add_intervention(
            alert_id,
            user.id,
            payload.get("action", "其他"),
            payload.get("summary", ""),
            payload.get("follow_up"),
        ),
        "已记录",
    )


# 关联分析
@alerts_bp.get("/correlation/matrix")
@login_required
def correlation_matrix():
    user = get_current_user()
    visible = get_visible_student_ids(user)
    return ok(svc.correlation_matrix(visible))
