"""实时课堂分析接口。"""

from __future__ import annotations

from datetime import datetime

from flask import Blueprint, current_app, request

from ..extensions import db
from ..models import Camera, ClassSession
from ..tasks.live_worker import is_running, start_live_analysis, stop_live_analysis
from ..utils.exceptions import NotFoundError, ValidationError
from ..utils.permissions import admin_required, get_current_user, login_required
from ..utils.response import ok

live_bp = Blueprint("live", __name__)


@live_bp.post("/session/manual-start")
@admin_required
def manual_start():
    """管理员手动启动一个摄像头的实时分析（不通过课表）。"""
    payload = request.get_json() or {}
    camera_id = payload.get("camera_id")
    if not camera_id:
        raise ValidationError("camera_id 必填")
    camera = db.session.get(Camera, camera_id)
    if not camera:
        raise NotFoundError("摄像头不存在")
    if is_running(camera.id):
        return ok(message="已在运行中")

    user = get_current_user()
    session = ClassSession(
        class_id=camera.class_id or 0,
        session_date=datetime.now().date(),
        period=0,
        camera_id=camera.id,
        trigger_type="manual",
        status="scheduled",
        title=f"手动启动 · 摄像头 {camera.name}",
        teacher_id=None,
    )
    db.session.add(session)
    db.session.commit()

    start_live_analysis(current_app._get_current_object(), session.id)
    return ok({"session_id": session.id}, "已启动")


@live_bp.post("/session/<int:session_id>/stop")
@admin_required
def manual_stop(session_id: int):
    stop_live_analysis(current_app._get_current_object(), session_id, reason="manual")
    return ok(message="已停止")


@live_bp.get("/session/active")
@login_required
def list_active_sessions():
    rows = (
        db.session.query(ClassSession)
        .filter(ClassSession.status == "running")
        .order_by(ClassSession.id.desc())
        .all()
    )
    items = []
    for s in rows:
        cam = db.session.get(Camera, s.camera_id) if s.camera_id else None
        items.append({
            "id": s.id,
            "title": s.title,
            "class_id": s.class_id,
            "teacher_id": s.teacher_id,
            "subject_id": s.subject_id,
            "camera_id": s.camera_id,
            "camera_name": cam.name if cam else None,
            "trigger_type": s.trigger_type,
            "started_at": s.started_at.strftime("%H:%M:%S") if s.started_at else None,
            "engagement_score": s.engagement_score,
        })
    return ok({"items": items, "total": len(items)})


@live_bp.get("/camera/<int:camera_id>/status")
@login_required
def camera_status(camera_id: int):
    active = (
        db.session.query(ClassSession)
        .filter(ClassSession.camera_id == camera_id, ClassSession.status == "running")
        .first()
    )
    return ok({
        "camera_id": camera_id,
        "is_running": is_running(camera_id),
        "active_session_id": active.id if active else None,
    })
