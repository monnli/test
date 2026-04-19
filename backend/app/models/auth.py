"""认证与权限模型：用户、角色、权限、用户角色绑定。"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel, SoftDeleteMixin

# ===== 系统内置角色编码 =====
ROLE_SCHOOL_ADMIN = "school_admin"      # 学校管理员
ROLE_PSY_TEACHER = "psy_teacher"        # 心理学老师（同管理员权限）
ROLE_GRADE_HEAD = "grade_head"          # 年级组长
ROLE_HEAD_TEACHER = "head_teacher"      # 班主任
ROLE_SUBJECT_TEACHER = "subject_teacher"  # 科任老师
ROLE_SUPER_ADMIN = "super_admin"        # 平台超管（隐藏）

ROLE_LABELS: dict[str, str] = {
    ROLE_SUPER_ADMIN: "超级管理员",
    ROLE_SCHOOL_ADMIN: "学校管理员",
    ROLE_PSY_TEACHER: "心理学老师",
    ROLE_GRADE_HEAD: "年级组长",
    ROLE_HEAD_TEACHER: "班主任",
    ROLE_SUBJECT_TEACHER: "科任老师",
}


class User(BaseModel, SoftDeleteMixin):
    """系统用户（教师账号）。学生与家长不在 M1 范围内。"""

    __tablename__ = "users"

    username: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True, comment="登录账号"
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False, comment="密码哈希")
    real_name: Mapped[str] = mapped_column(String(64), nullable=False, comment="真实姓名")
    phone: Mapped[str | None] = mapped_column(String(32), comment="手机号")
    email: Mapped[str | None] = mapped_column(String(128), comment="邮箱")
    avatar: Mapped[str | None] = mapped_column(String(255), comment="头像 URL")
    school_id: Mapped[int | None] = mapped_column(
        ForeignKey("schools.id"), nullable=True, index=True, comment="所属学校"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, comment="最后登录时间")
    last_login_ip: Mapped[str | None] = mapped_column(String(64), comment="最后登录 IP")

    teacher = relationship(
        "Teacher", back_populates="user", uselist=False, foreign_keys="Teacher.user_id"
    )
    user_roles: Mapped[list[UserRole]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    @property
    def role_codes(self) -> list[str]:
        return [ur.role.code for ur in self.user_roles if ur.role]

    @property
    def is_super(self) -> bool:
        return ROLE_SUPER_ADMIN in self.role_codes

    @property
    def is_admin_level(self) -> bool:
        codes = self.role_codes
        return any(c in codes for c in (ROLE_SUPER_ADMIN, ROLE_SCHOOL_ADMIN, ROLE_PSY_TEACHER))


class Role(BaseModel):
    """角色。"""

    __tablename__ = "roles"

    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, comment="角色编码")
    name: Mapped[str] = mapped_column(String(64), nullable=False, comment="角色名称")
    description: Mapped[str | None] = mapped_column(String(255), comment="说明")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment="排序")
    is_builtin: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否内置")

    role_permissions: Mapped[list[RolePermission]] = relationship(
        back_populates="role", cascade="all, delete-orphan"
    )

    @property
    def permission_codes(self) -> list[str]:
        return [rp.permission.code for rp in self.role_permissions if rp.permission]


class Permission(BaseModel):
    """权限点。"""

    __tablename__ = "permissions"

    code: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, comment="权限编码")
    name: Mapped[str] = mapped_column(String(128), nullable=False, comment="权限名称")
    module: Mapped[str] = mapped_column(String(64), nullable=False, index=True, comment="所属模块")
    description: Mapped[str | None] = mapped_column(String(255), comment="说明")


class RolePermission(BaseModel):
    """角色-权限绑定。"""

    __tablename__ = "role_permissions"
    __table_args__ = (UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),)

    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False, index=True)
    permission_id: Mapped[int] = mapped_column(
        ForeignKey("permissions.id"), nullable=False, index=True
    )

    role: Mapped[Role] = relationship(back_populates="role_permissions")
    permission: Mapped[Permission] = relationship()


class UserRole(BaseModel):
    """用户-角色绑定。"""

    __tablename__ = "user_roles"
    __table_args__ = (UniqueConstraint("user_id", "role_id", name="uq_user_role"),)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False, index=True)

    user: Mapped[User] = relationship(back_populates="user_roles")
    role: Mapped[Role] = relationship()


class OperationLog(BaseModel):
    """操作日志。"""

    __tablename__ = "operation_logs"

    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    username: Mapped[str | None] = mapped_column(String(64), comment="冗余账号名")
    method: Mapped[str] = mapped_column(String(16), nullable=False)
    path: Mapped[str] = mapped_column(String(255), nullable=False)
    action: Mapped[str | None] = mapped_column(String(128), comment="动作描述")
    ip: Mapped[str | None] = mapped_column(String(64))
    user_agent: Mapped[str | None] = mapped_column(String(255))
    status_code: Mapped[int | None] = mapped_column(Integer)
    duration_ms: Mapped[int | None] = mapped_column(Integer, comment="耗时毫秒")
