"""权限装饰器与数据范围工具。

5 级角色 + 数据范围权限：
- 学校管理员/心理学老师：本校全部
- 年级组长：所任年级
- 班主任：本班全部科目 + 自任教科目跨班
- 科任老师：自任教的「班级×科目」交叉范围
"""

from __future__ import annotations

from functools import wraps
from typing import Callable

from flask import g, request
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from loguru import logger

from ..extensions import db
from ..models import (
    Clazz,
    Grade,
    GradeHead,
    ROLE_GRADE_HEAD,
    ROLE_HEAD_TEACHER,
    ROLE_PSY_TEACHER,
    ROLE_SCHOOL_ADMIN,
    ROLE_SUBJECT_TEACHER,
    ROLE_SUPER_ADMIN,
    Student,
    Teacher,
    TeacherClassSubject,
    User,
)
from .exceptions import AuthError, PermissionDeniedError


def _load_current_user() -> User:
    verify_jwt_in_request()
    user_id = get_jwt_identity()
    user = db.session.get(User, int(user_id)) if user_id else None
    if not user or user.is_deleted or not user.is_active:
        raise AuthError("用户不存在或已禁用")
    g.current_user = user
    return user


def login_required(fn: Callable) -> Callable:
    """登录拦截。"""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        _load_current_user()
        return fn(*args, **kwargs)

    return wrapper


def roles_required(*role_codes: str) -> Callable:
    """要求用户拥有列出角色之一。super_admin 自动通过。"""

    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = _load_current_user()
            if user.is_super:
                return fn(*args, **kwargs)
            user_roles = set(user.role_codes)
            if not (user_roles & set(role_codes)):
                logger.warning(
                    f"权限拒绝：user={user.username} 需要角色 {role_codes}, 实际 {user_roles}"
                )
                raise PermissionDeniedError(
                    f"需要 {','.join(role_codes)} 角色之一"
                )
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def admin_required(fn: Callable) -> Callable:
    """要求学校管理员或心理学老师。"""
    return roles_required(ROLE_SCHOOL_ADMIN, ROLE_PSY_TEACHER)(fn)


def get_current_user() -> User:
    user = getattr(g, "current_user", None)
    if user is None:
        user = _load_current_user()
    return user


# ============ 数据范围权限 ============


class DataScope:
    """计算当前用户能看到的数据范围。

    返回的属性都是 ID 集合：
    - school_ids: 可访问的学校 ID 集合
    - grade_ids: 可访问的年级 ID 集合（None 表示本校全部）
    - class_ids: 可访问的班级 ID 集合（None 表示本年级/本校全部）
    - subject_filters: list[(class_id, subject_id)] 表示「班级×科目」的精细授权
    - all_subjects_in_class_ids: set[int] 表示这些班级可看任意科目
    - is_full: 是否拥有本校全部数据权限
    """

    def __init__(
        self,
        is_full: bool = False,
        school_ids: set[int] | None = None,
        grade_ids: set[int] | None = None,
        class_ids: set[int] | None = None,
        all_subjects_in_class_ids: set[int] | None = None,
        subject_filters: set[tuple[int, int]] | None = None,
    ):
        self.is_full = is_full
        self.school_ids = school_ids or set()
        self.grade_ids = grade_ids
        self.class_ids = class_ids
        self.all_subjects_in_class_ids = all_subjects_in_class_ids or set()
        self.subject_filters = subject_filters or set()

    def to_dict(self) -> dict:
        return {
            "is_full": self.is_full,
            "school_ids": sorted(self.school_ids),
            "grade_ids": sorted(self.grade_ids) if self.grade_ids is not None else None,
            "class_ids": sorted(self.class_ids) if self.class_ids is not None else None,
            "all_subjects_in_class_ids": sorted(self.all_subjects_in_class_ids),
            "subject_filters": [list(t) for t in sorted(self.subject_filters)],
        }


def compute_data_scope(user: User) -> DataScope:
    """根据用户的角色与任职关系计算数据范围。"""
    if user.is_super:
        # 超管：全部数据
        return DataScope(is_full=True)

    role_codes = set(user.role_codes)

    # 学校管理员 / 心理学老师：本校全部
    if role_codes & {ROLE_SCHOOL_ADMIN, ROLE_PSY_TEACHER}:
        if user.school_id:
            return DataScope(is_full=True, school_ids={user.school_id})
        return DataScope()

    teacher: Teacher | None = user.teacher
    if not teacher:
        return DataScope(school_ids={user.school_id} if user.school_id else set())

    school_ids: set[int] = {teacher.school_id} if teacher.school_id else set()
    grade_ids: set[int] = set()
    class_ids: set[int] = set()
    all_subjects_in_class_ids: set[int] = set()
    subject_filters: set[tuple[int, int]] = set()

    # 年级组长
    if ROLE_GRADE_HEAD in role_codes:
        head_grades = (
            db.session.query(GradeHead.grade_id).filter(GradeHead.teacher_id == teacher.id).all()
        )
        grade_ids.update(g[0] for g in head_grades)

    # 班主任：本班全部科目
    if ROLE_HEAD_TEACHER in role_codes:
        head_classes = (
            db.session.query(Clazz.id, Clazz.grade_id)
            .filter(Clazz.head_teacher_id == teacher.id, Clazz.is_deleted.is_(False))
            .all()
        )
        for cid, gid in head_classes:
            class_ids.add(cid)
            all_subjects_in_class_ids.add(cid)
            grade_ids.add(gid)

    # 科任老师：班级×科目交叉
    if ROLE_SUBJECT_TEACHER in role_codes:
        rows = (
            db.session.query(
                TeacherClassSubject.class_id,
                TeacherClassSubject.subject_id,
                Clazz.grade_id,
            )
            .join(Clazz, Clazz.id == TeacherClassSubject.class_id)
            .filter(TeacherClassSubject.teacher_id == teacher.id)
            .all()
        )
        for cid, sid, gid in rows:
            class_ids.add(cid)
            grade_ids.add(gid)
            if cid not in all_subjects_in_class_ids:
                subject_filters.add((cid, sid))

    return DataScope(
        is_full=False,
        school_ids=school_ids,
        grade_ids=grade_ids if grade_ids else None,
        class_ids=class_ids if class_ids else None,
        all_subjects_in_class_ids=all_subjects_in_class_ids,
        subject_filters=subject_filters,
    )


def get_visible_class_ids(user: User) -> list[int] | None:
    """返回该用户可见的班级 ID 列表。None 表示「全部班级」（学校管理员或超管）。"""
    scope = compute_data_scope(user)
    if scope.is_full:
        return None
    if scope.class_ids is None:
        # 没有任何班级数据权限
        return []
    return sorted(scope.class_ids)


def get_visible_student_ids(user: User) -> list[int] | None:
    """返回该用户可见的学生 ID 列表。None 表示「全部」。"""
    scope = compute_data_scope(user)
    if scope.is_full:
        if scope.school_ids:
            rows = (
                db.session.query(Student.id)
                .filter(Student.school_id.in_(scope.school_ids), Student.is_deleted.is_(False))
                .all()
            )
            return [r[0] for r in rows]
        return None
    if not scope.class_ids:
        return []
    rows = (
        db.session.query(Student.id)
        .filter(Student.class_id.in_(scope.class_ids), Student.is_deleted.is_(False))
        .all()
    )
    return [r[0] for r in rows]


def assert_can_access_class(user: User, class_id: int) -> None:
    visible = get_visible_class_ids(user)
    if visible is None:
        return
    if class_id not in visible:
        raise PermissionDeniedError("无权访问该班级")


def assert_can_access_student(user: User, student_id: int) -> None:
    visible = get_visible_student_ids(user)
    if visible is None:
        return
    if student_id not in visible:
        raise PermissionDeniedError("无权访问该学生")
