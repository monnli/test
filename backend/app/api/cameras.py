"""摄像头与课表接口。"""

from __future__ import annotations

from flask import Blueprint, request

from ..services import camera_service as svc
from ..utils.permissions import admin_required, get_current_user, login_required
from ..utils.response import ok

cameras_bp = Blueprint("cameras", __name__)


# ========== 摄像头 ==========

@cameras_bp.get("/cameras")
@login_required
def list_cameras():
    user = get_current_user()
    school_id = request.args.get("school_id", type=int)
    if not user.is_super and user.school_id:
        school_id = user.school_id
    items = svc.list_cameras(school_id=school_id)
    return ok({"items": items, "total": len(items)})


@cameras_bp.post("/cameras")
@admin_required
def add_camera():
    return ok(svc.create_camera(request.get_json() or {}), "已创建")


@cameras_bp.put("/cameras/<int:cam_id>")
@admin_required
def edit_camera(cam_id: int):
    return ok(svc.update_camera(cam_id, request.get_json() or {}), "已更新")


@cameras_bp.delete("/cameras/<int:cam_id>")
@admin_required
def remove_camera(cam_id: int):
    svc.delete_camera(cam_id)
    return ok(message="已删除")


# ========== 课表 ==========

@cameras_bp.get("/schedules")
@login_required
def list_schedules():
    items = svc.list_schedules(
        class_id=request.args.get("class_id", type=int),
        teacher_id=request.args.get("teacher_id", type=int),
        weekday=request.args.get("weekday", type=int),
    )
    return ok({"items": items, "total": len(items)})


@cameras_bp.post("/schedules")
@admin_required
def add_schedule():
    return ok(svc.create_schedule(request.get_json() or {}), "已创建")


@cameras_bp.put("/schedules/<int:schedule_id>")
@admin_required
def edit_schedule(schedule_id: int):
    return ok(svc.update_schedule(schedule_id, request.get_json() or {}), "已更新")


@cameras_bp.delete("/schedules/<int:schedule_id>")
@admin_required
def remove_schedule(schedule_id: int):
    svc.delete_schedule(schedule_id)
    return ok(message="已删除")


@cameras_bp.post("/schedules/check-conflict")
@admin_required
def check_conflict():
    conflicts = svc.schedule_conflicts(request.get_json() or {})
    return ok({"conflicts": conflicts, "has_conflict": bool(conflicts)})


@cameras_bp.get("/schedules/active")
@login_required
def get_active_schedules():
    items = svc.find_active_schedules()
    return ok({"items": [svc.serialize_schedule(s) for s in items], "total": len(items)})
