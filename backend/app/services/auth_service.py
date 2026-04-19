"""认证业务服务。"""

from __future__ import annotations

from datetime import datetime

from flask import request
from flask_jwt_extended import create_access_token, create_refresh_token
from loguru import logger

from ..extensions import db
from ..models import ROLE_LABELS, User
from ..utils.exceptions import AuthError, ValidationError
from ..utils.security import hash_password, verify_password


def login(username: str, password: str) -> dict:
    if not username or not password:
        raise ValidationError("账号和密码不能为空")
    user: User | None = (
        db.session.query(User).filter_by(username=username, is_deleted=False).first()
    )
    if not user:
        raise AuthError("账号不存在或密码错误")
    if not user.is_active:
        raise AuthError("账号已被禁用")
    if not verify_password(password, user.password_hash):
        raise AuthError("账号不存在或密码错误")

    user.last_login_at = datetime.utcnow()
    user.last_login_ip = request.remote_addr if request else None
    db.session.commit()

    identity = str(user.id)
    access = create_access_token(identity=identity, additional_claims={"username": user.username})
    refresh = create_refresh_token(identity=identity)
    logger.info(f"用户 {user.username} 登录成功")
    return {
        "access_token": access,
        "refresh_token": refresh,
        "user": serialize_user(user),
    }


def serialize_user(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "real_name": user.real_name,
        "phone": user.phone,
        "email": user.email,
        "avatar": user.avatar,
        "school_id": user.school_id,
        "is_active": user.is_active,
        "is_super": user.is_super,
        "roles": [
            {"code": code, "name": ROLE_LABELS.get(code, code)} for code in user.role_codes
        ],
        "last_login_at": user.last_login_at.strftime("%Y-%m-%d %H:%M:%S")
        if user.last_login_at
        else None,
    }


def change_password(user: User, old_password: str, new_password: str) -> None:
    if not new_password or len(new_password) < 6:
        raise ValidationError("新密码长度至少 6 位")
    if not verify_password(old_password, user.password_hash):
        raise AuthError("原密码错误")
    user.password_hash = hash_password(new_password)
    db.session.commit()
    logger.info(f"用户 {user.username} 修改密码成功")
