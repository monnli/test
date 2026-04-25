"""组织架构接口（学校 / 年级 / 班级 / 学生 / 教师 / 科目 / 任课关系）。"""

from __future__ import annotations

from flask import Blueprint, request

from ..services import org_service as svc
from ..utils.permissions import (
    admin_required,
    assert_can_access_class,
    assert_can_access_student,
    compute_data_scope,
    get_current_user,
    get_visible_class_ids,
    login_required,
    roles_required,
)
from ..utils.response import ok
from ..models import ROLE_SUPER_ADMIN

orgs_bp = Blueprint("orgs", __name__)


# ---------- 学校 ----------
@orgs_bp.get("/schools")
@login_required
def get_schools():
    user = get_current_user()
    items = svc.list_schools(keyword=request.args.get("keyword"))
    if not user.is_super and user.school_id:
        items = [i for i in items if i["id"] == user.school_id]
    return ok({"items": items, "total": len(items)})


@orgs_bp.post("/schools")
@roles_required(ROLE_SUPER_ADMIN)
def add_school():
    return ok(svc.create_school(request.get_json() or {}), "创建成功")


@orgs_bp.put("/schools/<int:school_id>")
@roles_required(ROLE_SUPER_ADMIN)
def edit_school(school_id: int):
    return ok(svc.update_school(school_id, request.get_json() or {}), "更新成功")


@orgs_bp.delete("/schools/<int:school_id>")
@roles_required(ROLE_SUPER_ADMIN)
def remove_school(school_id: int):
    svc.delete_school(school_id)
    return ok(message="已删除")


# ---------- 年级 ----------
@orgs_bp.get("/grades")
@login_required
def get_grades():
    user = get_current_user()
    school_id = request.args.get("school_id", type=int)
    if not user.is_super and user.school_id:
        school_id = user.school_id
    items = svc.list_grades(school_id=school_id)
    scope = compute_data_scope(user)
    if not scope.is_full and scope.grade_ids is not None:
        items = [i for i in items if i["id"] in scope.grade_ids]
    return ok({"items": items, "total": len(items)})


@orgs_bp.post("/grades")
@admin_required
def add_grade():
    return ok(svc.create_grade(request.get_json() or {}), "创建成功")


@orgs_bp.put("/grades/<int:grade_id>")
@admin_required
def edit_grade(grade_id: int):
    return ok(svc.update_grade(grade_id, request.get_json() or {}), "更新成功")


@orgs_bp.delete("/grades/<int:grade_id>")
@admin_required
def remove_grade(grade_id: int):
    svc.delete_grade(grade_id)
    return ok(message="已删除")


# ---------- 班级 ----------
@orgs_bp.get("/classes")
@login_required
def get_classes():
    user = get_current_user()
    grade_id = request.args.get("grade_id", type=int)
    school_id = request.args.get("school_id", type=int)
    if not user.is_super and user.school_id:
        school_id = user.school_id
    visible = get_visible_class_ids(user)
    items = svc.list_classes(grade_id=grade_id, school_id=school_id, class_ids=visible)
    return ok({"items": items, "total": len(items)})


@orgs_bp.post("/classes")
@admin_required
def add_class():
    return ok(svc.create_class(request.get_json() or {}), "创建成功")


@orgs_bp.put("/classes/<int:class_id>")
@admin_required
def edit_class(class_id: int):
    return ok(svc.update_class(class_id, request.get_json() or {}), "更新成功")


@orgs_bp.delete("/classes/<int:class_id>")
@admin_required
def remove_class(class_id: int):
    svc.delete_class(class_id)
    return ok(message="已删除")


# ---------- 学生 ----------
@orgs_bp.get("/students")
@login_required
def get_students():
    user = get_current_user()
    page = request.args.get("page", default=1, type=int)
    page_size = request.args.get("page_size", default=20, type=int)
    class_id = request.args.get("class_id", type=int)
    grade_id = request.args.get("grade_id", type=int)
    school_id = request.args.get("school_id", type=int)
    keyword = request.args.get("keyword")

    if not user.is_super and user.school_id:
        school_id = user.school_id

    visible = get_visible_class_ids(user)
    return ok(
        svc.list_students(
            class_id=class_id,
            grade_id=grade_id,
            school_id=school_id,
            keyword=keyword,
            visible_class_ids=visible,
            page=page,
            page_size=page_size,
        )
    )


@orgs_bp.get("/students/<int:student_id>")
@login_required
def get_student_detail(student_id: int):
    user = get_current_user()
    assert_can_access_student(user, student_id)
    from ..extensions import db
    from ..models import Student

    s = db.session.get(Student, student_id)
    if not s or s.is_deleted:
        from ..utils.exceptions import NotFoundError

        raise NotFoundError("学生不存在")
    return ok(svc.serialize_student(s))


@orgs_bp.post("/students")
@admin_required
def add_student():
    return ok(svc.create_student(request.get_json() or {}), "创建成功")


@orgs_bp.put("/students/<int:student_id>")
@admin_required
def edit_student(student_id: int):
    return ok(svc.update_student(student_id, request.get_json() or {}), "更新成功")


@orgs_bp.delete("/students/<int:student_id>")
@admin_required
def remove_student(student_id: int):
    svc.delete_student(student_id)
    return ok(message="已删除")


# ---------- 教师 ----------
@orgs_bp.get("/teachers")
@login_required
def get_teachers():
    user = get_current_user()
    school_id = request.args.get("school_id", type=int)
    if not user.is_super and user.school_id:
        school_id = user.school_id
    items = svc.list_teachers(school_id=school_id, keyword=request.args.get("keyword"))
    return ok({"items": items, "total": len(items)})


@orgs_bp.post("/teachers")
@admin_required
def add_teacher():
    return ok(svc.create_teacher(request.get_json() or {}), "创建成功")


@orgs_bp.put("/teachers/<int:teacher_id>")
@admin_required
def edit_teacher(teacher_id: int):
    return ok(svc.update_teacher(teacher_id, request.get_json() or {}), "更新成功")


@orgs_bp.delete("/teachers/<int:teacher_id>")
@admin_required
def remove_teacher(teacher_id: int):
    svc.delete_teacher(teacher_id)
    return ok(message="已删除")


# ---------- 科目 ----------
@orgs_bp.get("/subjects")
@login_required
def get_subjects():
    items = svc.list_subjects()
    return ok({"items": items, "total": len(items)})


@orgs_bp.post("/subjects")
@admin_required
def add_subject():
    return ok(svc.create_subject(request.get_json() or {}), "创建成功")


@orgs_bp.put("/subjects/<int:subject_id>")
@admin_required
def edit_subject(subject_id: int):
    return ok(svc.update_subject(subject_id, request.get_json() or {}), "更新成功")


@orgs_bp.delete("/subjects/<int:subject_id>")
@admin_required
def remove_subject(subject_id: int):
    svc.delete_subject(subject_id)
    return ok(message="已删除")


# ---------- 任课关系 ----------
@orgs_bp.get("/teacher-class-subjects")
@login_required
def get_tcs():
    items = svc.list_teacher_class_subjects(
        teacher_id=request.args.get("teacher_id", type=int),
        class_id=request.args.get("class_id", type=int),
        subject_id=request.args.get("subject_id", type=int),
    )
    return ok({"items": items, "total": len(items)})


@orgs_bp.post("/teacher-class-subjects")
@admin_required
def add_tcs():
    return ok(svc.create_teacher_class_subject(request.get_json() or {}), "创建成功")


@orgs_bp.delete("/teacher-class-subjects/<int:record_id>")
@admin_required
def remove_tcs(record_id: int):
    svc.delete_teacher_class_subject(record_id)
    return ok(message="已删除")


# ---------- 年级组长任职 ----------
@orgs_bp.get("/grade-heads")
@login_required
def get_grade_heads():
    items = svc.list_grade_heads(
        grade_id=request.args.get("grade_id", type=int),
        teacher_id=request.args.get("teacher_id", type=int),
    )
    return ok({"items": items, "total": len(items)})


@orgs_bp.post("/grade-heads")
@admin_required
def add_grade_head():
    payload = request.get_json() or {}
    return ok(
        svc.assign_grade_head(payload.get("teacher_id"), payload.get("grade_id")),
        "已任命",
    )


@orgs_bp.delete("/grade-heads/<int:record_id>")
@admin_required
def remove_grade_head(record_id: int):
    svc.revoke_grade_head(record_id)
    return ok(message="已撤销")
