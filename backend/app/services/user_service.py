"""用户与角色服务。"""

from __future__ import annotations

from datetime import datetime
from typing import Iterable

from sqlalchemy import or_

from ..extensions import db
from ..models import ROLE_LABELS, Role, User, UserRole
from ..utils.exceptions import ConflictError, NotFoundError, ValidationError
from ..utils.security import hash_password


def serialize_user_full(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "real_name": user.real_name,
        "phone": user.phone,
        "email": user.email,
        "avatar": user.avatar,
        "school_id": user.school_id,
        "is_active": user.is_active,
        "last_login_at": user.last_login_at.strftime("%Y-%m-%d %H:%M:%S")
        if user.last_login_at
        else None,
        "last_login_ip": user.last_login_ip,
        "created_at": user.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "roles": [
            {"code": code, "name": ROLE_LABELS.get(code, code)} for code in user.role_codes
        ],
    }


def list_users(
    keyword: str | None = None,
    school_id: int | None = None,
    role_code: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    q = db.session.query(User).filter(User.is_deleted.is_(False))
    if school_id:
        q = q.filter_by(school_id=school_id)
    if keyword:
        q = q.filter(
            or_(User.username.like(f"%{keyword}%"), User.real_name.like(f"%{keyword}%"))
        )
    if role_code:
        q = (
            q.join(UserRole, UserRole.user_id == User.id)
            .join(Role, Role.id == UserRole.role_id)
            .filter(Role.code == role_code)
        )
    total = q.count()
    items = (
        q.order_by(User.id).offset((page - 1) * page_size).limit(page_size).all()
    )
    return {
        "items": [serialize_user_full(u) for u in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


def create_user(data: dict) -> dict:
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    real_name = (data.get("real_name") or "").strip()
    if not username or not password or not real_name:
        raise ValidationError("账号、密码、姓名均不能为空")
    if len(password) < 6:
        raise ValidationError("密码长度至少 6 位")
    if db.session.query(User).filter_by(username=username, is_deleted=False).first():
        raise ConflictError("账号已存在")
    user = User(
        username=username,
        password_hash=hash_password(password),
        real_name=real_name,
        phone=data.get("phone"),
        email=data.get("email"),
        avatar=data.get("avatar"),
        school_id=data.get("school_id"),
        is_active=bool(data.get("is_active", True)),
    )
    db.session.add(user)
    db.session.flush()

    role_codes: Iterable[str] = data.get("role_codes") or []
    _set_roles(user, role_codes)

    db.session.commit()
    return serialize_user_full(user)


def update_user(user_id: int, data: dict) -> dict:
    user = db.session.get(User, user_id)
    if not user or user.is_deleted:
        raise NotFoundError("用户不存在")
    for field in ("real_name", "phone", "email", "avatar", "school_id"):
        if field in data:
            setattr(user, field, data[field])
    if "is_active" in data:
        user.is_active = bool(data["is_active"])
    if "role_codes" in data:
        _set_roles(user, data["role_codes"] or [])
    db.session.commit()
    return serialize_user_full(user)


def reset_password(user_id: int, new_password: str) -> None:
    if not new_password or len(new_password) < 6:
        raise ValidationError("新密码长度至少 6 位")
    user = db.session.get(User, user_id)
    if not user or user.is_deleted:
        raise NotFoundError("用户不存在")
    user.password_hash = hash_password(new_password)
    db.session.commit()


def delete_user(user_id: int) -> None:
    user = db.session.get(User, user_id)
    if not user or user.is_deleted:
        raise NotFoundError("用户不存在")
    user.is_deleted = True
    user.deleted_at = datetime.utcnow()
    user.is_active = False
    db.session.commit()


def _set_roles(user: User, role_codes: Iterable[str]) -> None:
    """重置用户角色。"""
    code_list = list(set(role_codes))
    db.session.query(UserRole).filter_by(user_id=user.id).delete()
    if not code_list:
        return
    roles = db.session.query(Role).filter(Role.code.in_(code_list)).all()
    for role in roles:
        db.session.add(UserRole(user_id=user.id, role_id=role.id))


def list_roles() -> list[dict]:
    roles = db.session.query(Role).order_by(Role.sort_order, Role.id).all()
    return [
        {
            "id": r.id,
            "code": r.code,
            "name": r.name,
            "description": r.description,
            "is_builtin": r.is_builtin,
            "sort_order": r.sort_order,
        }
        for r in roles
    ]
