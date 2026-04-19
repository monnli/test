"""认证相关接口：登录、刷新、登出、当前用户、修改密码。"""

from __future__ import annotations

from flask import Blueprint, request
from flask_jwt_extended import (
    create_access_token,
    get_jwt_identity,
    jwt_required,
)

from ..extensions import db
from ..models import User
from ..services.auth_service import change_password, login, serialize_user
from ..utils.exceptions import AuthError
from ..utils.permissions import compute_data_scope, get_current_user, login_required
from ..utils.response import ok

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/login")
def api_login():
    payload = request.get_json(silent=True) or {}
    username = (payload.get("username") or "").strip()
    password = payload.get("password") or ""
    return ok(login(username, password), "登录成功")


@auth_bp.post("/refresh")
@jwt_required(refresh=True)
def api_refresh():
    user_id = get_jwt_identity()
    user = db.session.get(User, int(user_id))
    if not user or user.is_deleted or not user.is_active:
        raise AuthError("账号无效")
    new_access = create_access_token(
        identity=str(user.id), additional_claims={"username": user.username}
    )
    return ok({"access_token": new_access}, "已刷新")


@auth_bp.post("/logout")
@login_required
def api_logout():
    # JWT 模式无服务端 session，登出由前端清除 token 即可
    return ok(message="已登出")


@auth_bp.get("/me")
@login_required
def api_me():
    user = get_current_user()
    data = serialize_user(user)
    data["data_scope"] = compute_data_scope(user).to_dict()
    return ok(data)


@auth_bp.post("/change-password")
@login_required
def api_change_password():
    user = get_current_user()
    payload = request.get_json(silent=True) or {}
    change_password(user, payload.get("old_password", ""), payload.get("new_password", ""))
    return ok(message="密码已修改")
