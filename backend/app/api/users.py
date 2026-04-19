"""用户管理接口。"""

from __future__ import annotations

from flask import Blueprint, request

from ..services import user_service as svc
from ..utils.permissions import admin_required, get_current_user
from ..utils.response import ok

users_bp = Blueprint("users", __name__)


@users_bp.get("")
@admin_required
def get_users():
    user = get_current_user()
    school_id = request.args.get("school_id", type=int)
    if not user.is_super and user.school_id:
        school_id = user.school_id
    return ok(
        svc.list_users(
            keyword=request.args.get("keyword"),
            school_id=school_id,
            role_code=request.args.get("role_code"),
            page=request.args.get("page", default=1, type=int),
            page_size=request.args.get("page_size", default=20, type=int),
        )
    )


@users_bp.post("")
@admin_required
def add_user():
    return ok(svc.create_user(request.get_json() or {}), "创建成功")


@users_bp.put("/<int:user_id>")
@admin_required
def edit_user(user_id: int):
    return ok(svc.update_user(user_id, request.get_json() or {}), "更新成功")


@users_bp.delete("/<int:user_id>")
@admin_required
def remove_user(user_id: int):
    svc.delete_user(user_id)
    return ok(message="已删除")


@users_bp.post("/<int:user_id>/reset-password")
@admin_required
def reset_user_password(user_id: int):
    payload = request.get_json() or {}
    svc.reset_password(user_id, payload.get("new_password", ""))
    return ok(message="密码已重置")


@users_bp.get("/roles/all")
@admin_required
def get_all_roles():
    return ok({"items": svc.list_roles()})
