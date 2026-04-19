"""组织架构服务：学校 / 年级 / 班级 / 学生 / 教师 / 科目 / 任课关系。"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from loguru import logger
from sqlalchemy import or_

from ..extensions import db
from ..models import (
    Clazz,
    Grade,
    GradeHead,
    School,
    Student,
    Subject,
    Teacher,
    TeacherClassSubject,
)
from ..utils.exceptions import ConflictError, NotFoundError, ValidationError


def _parse_date(value: Any) -> date | None:
    if value in (None, "", "null"):
        return None
    if isinstance(value, date):
        return value
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        raise ValidationError(f"日期格式错误：{value}")


# =================== 学校 ===================

def serialize_school(s: School) -> dict:
    return {
        "id": s.id,
        "name": s.name,
        "code": s.code,
        "address": s.address,
        "contact": s.contact,
        "phone": s.phone,
        "description": s.description,
        "created_at": s.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    }


def list_schools(keyword: str | None = None) -> list[dict]:
    q = db.session.query(School).filter(School.is_deleted.is_(False))
    if keyword:
        q = q.filter(or_(School.name.like(f"%{keyword}%"), School.code.like(f"%{keyword}%")))
    return [serialize_school(s) for s in q.order_by(School.id).all()]


def create_school(data: dict) -> dict:
    name = (data.get("name") or "").strip()
    if not name:
        raise ValidationError("学校名称不能为空")
    if db.session.query(School).filter_by(name=name, is_deleted=False).first():
        raise ConflictError("学校名称已存在")
    s = School(
        name=name,
        code=data.get("code"),
        address=data.get("address"),
        contact=data.get("contact"),
        phone=data.get("phone"),
        description=data.get("description"),
    )
    db.session.add(s)
    db.session.commit()
    return serialize_school(s)


def update_school(school_id: int, data: dict) -> dict:
    s = db.session.get(School, school_id)
    if not s or s.is_deleted:
        raise NotFoundError("学校不存在")
    for field in ("name", "code", "address", "contact", "phone", "description"):
        if field in data:
            setattr(s, field, data[field])
    db.session.commit()
    return serialize_school(s)


def delete_school(school_id: int) -> None:
    s = db.session.get(School, school_id)
    if not s or s.is_deleted:
        raise NotFoundError("学校不存在")
    s.is_deleted = True
    s.deleted_at = datetime.utcnow()
    db.session.commit()


# =================== 年级 ===================

def serialize_grade(g: Grade) -> dict:
    return {
        "id": g.id,
        "school_id": g.school_id,
        "school_name": g.school.name if g.school else None,
        "name": g.name,
        "level": g.level,
        "class_count": db.session.query(Clazz)
        .filter_by(grade_id=g.id, is_deleted=False)
        .count(),
    }


def list_grades(school_id: int | None = None) -> list[dict]:
    q = db.session.query(Grade).filter(Grade.is_deleted.is_(False))
    if school_id:
        q = q.filter_by(school_id=school_id)
    return [serialize_grade(g) for g in q.order_by(Grade.school_id, Grade.level).all()]


def create_grade(data: dict) -> dict:
    school_id = data.get("school_id")
    name = (data.get("name") or "").strip()
    if not school_id or not name:
        raise ValidationError("学校与年级名称不能为空")
    if (
        db.session.query(Grade)
        .filter_by(school_id=school_id, name=name, is_deleted=False)
        .first()
    ):
        raise ConflictError("该学校已有同名年级")
    g = Grade(school_id=school_id, name=name, level=int(data.get("level") or 1))
    db.session.add(g)
    db.session.commit()
    return serialize_grade(g)


def update_grade(grade_id: int, data: dict) -> dict:
    g = db.session.get(Grade, grade_id)
    if not g or g.is_deleted:
        raise NotFoundError("年级不存在")
    if "name" in data:
        g.name = data["name"]
    if "level" in data:
        g.level = int(data["level"])
    db.session.commit()
    return serialize_grade(g)


def delete_grade(grade_id: int) -> None:
    g = db.session.get(Grade, grade_id)
    if not g or g.is_deleted:
        raise NotFoundError("年级不存在")
    g.is_deleted = True
    g.deleted_at = datetime.utcnow()
    db.session.commit()


# =================== 班级 ===================

def serialize_class(c: Clazz) -> dict:
    head = c.head_teacher
    return {
        "id": c.id,
        "grade_id": c.grade_id,
        "grade_name": c.grade.name if c.grade else None,
        "school_id": c.grade.school_id if c.grade else None,
        "name": c.name,
        "head_teacher_id": c.head_teacher_id,
        "head_teacher_name": head.name if head else None,
        "student_count": db.session.query(Student)
        .filter_by(class_id=c.id, is_deleted=False)
        .count(),
    }


def list_classes(
    grade_id: int | None = None,
    school_id: int | None = None,
    class_ids: list[int] | None = None,
) -> list[dict]:
    q = db.session.query(Clazz).filter(Clazz.is_deleted.is_(False))
    if grade_id:
        q = q.filter_by(grade_id=grade_id)
    if school_id:
        q = q.join(Grade, Grade.id == Clazz.grade_id).filter(Grade.school_id == school_id)
    if class_ids is not None:
        if not class_ids:
            return []
        q = q.filter(Clazz.id.in_(class_ids))
    return [serialize_class(c) for c in q.order_by(Clazz.grade_id, Clazz.name).all()]


def create_class(data: dict) -> dict:
    grade_id = data.get("grade_id")
    name = (data.get("name") or "").strip()
    if not grade_id or not name:
        raise ValidationError("年级与班级名称不能为空")
    if (
        db.session.query(Clazz)
        .filter_by(grade_id=grade_id, name=name, is_deleted=False)
        .first()
    ):
        raise ConflictError("该年级已有同名班级")
    c = Clazz(grade_id=grade_id, name=name, head_teacher_id=data.get("head_teacher_id"))
    db.session.add(c)
    db.session.commit()
    return serialize_class(c)


def update_class(class_id: int, data: dict) -> dict:
    c = db.session.get(Clazz, class_id)
    if not c or c.is_deleted:
        raise NotFoundError("班级不存在")
    if "name" in data:
        c.name = data["name"]
    if "head_teacher_id" in data:
        c.head_teacher_id = data["head_teacher_id"] or None
    db.session.commit()
    return serialize_class(c)


def delete_class(class_id: int) -> None:
    c = db.session.get(Clazz, class_id)
    if not c or c.is_deleted:
        raise NotFoundError("班级不存在")
    c.is_deleted = True
    c.deleted_at = datetime.utcnow()
    db.session.commit()


# =================== 学生 ===================

def serialize_student(s: Student) -> dict:
    return {
        "id": s.id,
        "student_no": s.student_no,
        "name": s.name,
        "gender": s.gender,
        "birth_date": s.birth_date.strftime("%Y-%m-%d") if s.birth_date else None,
        "avatar": s.avatar,
        "school_id": s.school_id,
        "grade_id": s.grade_id,
        "class_id": s.class_id,
        "class_name": s.clazz.name if s.clazz else None,
        "parent_name": s.parent_name,
        "parent_phone": s.parent_phone,
        "enrollment_date": s.enrollment_date.strftime("%Y-%m-%d")
        if s.enrollment_date
        else None,
        "note": s.note,
    }


def list_students(
    class_id: int | None = None,
    grade_id: int | None = None,
    school_id: int | None = None,
    keyword: str | None = None,
    visible_class_ids: list[int] | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    q = db.session.query(Student).filter(Student.is_deleted.is_(False))
    if class_id:
        q = q.filter_by(class_id=class_id)
    if grade_id:
        q = q.filter_by(grade_id=grade_id)
    if school_id:
        q = q.filter_by(school_id=school_id)
    if visible_class_ids is not None:
        if not visible_class_ids:
            return {"items": [], "total": 0, "page": page, "page_size": page_size}
        q = q.filter(Student.class_id.in_(visible_class_ids))
    if keyword:
        q = q.filter(or_(Student.name.like(f"%{keyword}%"), Student.student_no.like(f"%{keyword}%")))
    total = q.count()
    items = (
        q.order_by(Student.class_id, Student.student_no)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "items": [serialize_student(s) for s in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


def create_student(data: dict) -> dict:
    class_id = data.get("class_id")
    name = (data.get("name") or "").strip()
    student_no = (data.get("student_no") or "").strip()
    if not class_id or not name or not student_no:
        raise ValidationError("学号、姓名、班级均不能为空")
    clazz = db.session.get(Clazz, class_id)
    if not clazz or clazz.is_deleted:
        raise NotFoundError("班级不存在")
    if db.session.query(Student).filter_by(student_no=student_no, is_deleted=False).first():
        raise ConflictError("学号已存在")
    grade = clazz.grade
    s = Student(
        student_no=student_no,
        name=name,
        gender=data.get("gender") or "未知",
        birth_date=_parse_date(data.get("birth_date")),
        school_id=grade.school_id,
        grade_id=grade.id,
        class_id=class_id,
        parent_name=data.get("parent_name"),
        parent_phone=data.get("parent_phone"),
        enrollment_date=_parse_date(data.get("enrollment_date")),
        note=data.get("note"),
        avatar=data.get("avatar"),
    )
    db.session.add(s)
    db.session.commit()
    return serialize_student(s)


def update_student(student_id: int, data: dict) -> dict:
    s = db.session.get(Student, student_id)
    if not s or s.is_deleted:
        raise NotFoundError("学生不存在")
    for field in ("name", "gender", "parent_name", "parent_phone", "note", "avatar"):
        if field in data:
            setattr(s, field, data[field])
    if "birth_date" in data:
        s.birth_date = _parse_date(data["birth_date"])
    if "enrollment_date" in data:
        s.enrollment_date = _parse_date(data["enrollment_date"])
    if "class_id" in data and data["class_id"] != s.class_id:
        clazz = db.session.get(Clazz, data["class_id"])
        if not clazz or clazz.is_deleted:
            raise NotFoundError("目标班级不存在")
        s.class_id = clazz.id
        s.grade_id = clazz.grade_id
        s.school_id = clazz.grade.school_id
    db.session.commit()
    return serialize_student(s)


def delete_student(student_id: int) -> None:
    s = db.session.get(Student, student_id)
    if not s or s.is_deleted:
        raise NotFoundError("学生不存在")
    s.is_deleted = True
    s.deleted_at = datetime.utcnow()
    db.session.commit()


# =================== 教师 ===================

def serialize_teacher(t: Teacher) -> dict:
    return {
        "id": t.id,
        "user_id": t.user_id,
        "username": t.user.username if t.user else None,
        "teacher_no": t.teacher_no,
        "name": t.name,
        "gender": t.gender,
        "school_id": t.school_id,
        "phone": t.phone,
        "email": t.email,
        "title": t.title,
        "avatar": t.avatar,
    }


def list_teachers(
    school_id: int | None = None, keyword: str | None = None
) -> list[dict]:
    q = db.session.query(Teacher).filter(Teacher.is_deleted.is_(False))
    if school_id:
        q = q.filter_by(school_id=school_id)
    if keyword:
        q = q.filter(
            or_(Teacher.name.like(f"%{keyword}%"), Teacher.teacher_no.like(f"%{keyword}%"))
        )
    return [serialize_teacher(t) for t in q.order_by(Teacher.school_id, Teacher.id).all()]


def create_teacher(data: dict) -> dict:
    name = (data.get("name") or "").strip()
    teacher_no = (data.get("teacher_no") or "").strip()
    school_id = data.get("school_id")
    if not name or not teacher_no or not school_id:
        raise ValidationError("姓名、工号、所属学校均不能为空")
    if db.session.query(Teacher).filter_by(teacher_no=teacher_no, is_deleted=False).first():
        raise ConflictError("工号已存在")
    t = Teacher(
        name=name,
        teacher_no=teacher_no,
        school_id=school_id,
        gender=data.get("gender") or "未知",
        phone=data.get("phone"),
        email=data.get("email"),
        title=data.get("title"),
        avatar=data.get("avatar"),
        user_id=data.get("user_id"),
    )
    db.session.add(t)
    db.session.commit()
    return serialize_teacher(t)


def update_teacher(teacher_id: int, data: dict) -> dict:
    t = db.session.get(Teacher, teacher_id)
    if not t or t.is_deleted:
        raise NotFoundError("教师不存在")
    for field in ("name", "gender", "phone", "email", "title", "avatar"):
        if field in data:
            setattr(t, field, data[field])
    db.session.commit()
    return serialize_teacher(t)


def delete_teacher(teacher_id: int) -> None:
    t = db.session.get(Teacher, teacher_id)
    if not t or t.is_deleted:
        raise NotFoundError("教师不存在")
    t.is_deleted = True
    t.deleted_at = datetime.utcnow()
    db.session.commit()


# =================== 科目 ===================

def serialize_subject(s: Subject) -> dict:
    return {"id": s.id, "name": s.name, "code": s.code, "sort_order": s.sort_order}


def list_subjects() -> list[dict]:
    return [
        serialize_subject(s)
        for s in db.session.query(Subject)
        .filter(Subject.is_deleted.is_(False))
        .order_by(Subject.sort_order, Subject.id)
        .all()
    ]


def create_subject(data: dict) -> dict:
    name = (data.get("name") or "").strip()
    if not name:
        raise ValidationError("科目名称不能为空")
    if db.session.query(Subject).filter_by(name=name, is_deleted=False).first():
        raise ConflictError("科目名称已存在")
    s = Subject(name=name, code=data.get("code"), sort_order=int(data.get("sort_order") or 0))
    db.session.add(s)
    db.session.commit()
    return serialize_subject(s)


def update_subject(subject_id: int, data: dict) -> dict:
    s = db.session.get(Subject, subject_id)
    if not s or s.is_deleted:
        raise NotFoundError("科目不存在")
    for field in ("name", "code", "sort_order"):
        if field in data:
            setattr(s, field, data[field])
    db.session.commit()
    return serialize_subject(s)


def delete_subject(subject_id: int) -> None:
    s = db.session.get(Subject, subject_id)
    if not s or s.is_deleted:
        raise NotFoundError("科目不存在")
    s.is_deleted = True
    s.deleted_at = datetime.utcnow()
    db.session.commit()


# =================== 任课关系 ===================

def serialize_tcs(r: TeacherClassSubject) -> dict:
    return {
        "id": r.id,
        "teacher_id": r.teacher_id,
        "teacher_name": r.teacher.name if r.teacher else None,
        "class_id": r.class_id,
        "class_name": r.clazz.name if r.clazz else None,
        "grade_id": r.clazz.grade_id if r.clazz else None,
        "grade_name": r.clazz.grade.name if r.clazz and r.clazz.grade else None,
        "subject_id": r.subject_id,
        "subject_name": r.subject.name if r.subject else None,
    }


def list_teacher_class_subjects(
    teacher_id: int | None = None,
    class_id: int | None = None,
    subject_id: int | None = None,
) -> list[dict]:
    q = db.session.query(TeacherClassSubject)
    if teacher_id:
        q = q.filter_by(teacher_id=teacher_id)
    if class_id:
        q = q.filter_by(class_id=class_id)
    if subject_id:
        q = q.filter_by(subject_id=subject_id)
    return [serialize_tcs(r) for r in q.all()]


def create_teacher_class_subject(data: dict) -> dict:
    teacher_id = data.get("teacher_id")
    class_id = data.get("class_id")
    subject_id = data.get("subject_id")
    if not teacher_id or not class_id or not subject_id:
        raise ValidationError("教师、班级、科目均不能为空")
    if (
        db.session.query(TeacherClassSubject)
        .filter_by(teacher_id=teacher_id, class_id=class_id, subject_id=subject_id)
        .first()
    ):
        raise ConflictError("该任课关系已存在")
    r = TeacherClassSubject(teacher_id=teacher_id, class_id=class_id, subject_id=subject_id)
    db.session.add(r)
    db.session.commit()
    return serialize_tcs(r)


def delete_teacher_class_subject(record_id: int) -> None:
    r = db.session.get(TeacherClassSubject, record_id)
    if not r:
        raise NotFoundError("任课关系不存在")
    db.session.delete(r)
    db.session.commit()


# =================== 年级组长任职 ===================

def list_grade_heads(grade_id: int | None = None, teacher_id: int | None = None) -> list[dict]:
    q = db.session.query(GradeHead)
    if grade_id:
        q = q.filter_by(grade_id=grade_id)
    if teacher_id:
        q = q.filter_by(teacher_id=teacher_id)
    rows = q.all()
    return [
        {
            "id": r.id,
            "grade_id": r.grade_id,
            "grade_name": r.grade.name if r.grade else None,
            "teacher_id": r.teacher_id,
            "teacher_name": r.teacher.name if r.teacher else None,
        }
        for r in rows
    ]


def assign_grade_head(teacher_id: int, grade_id: int) -> dict:
    if (
        db.session.query(GradeHead)
        .filter_by(teacher_id=teacher_id, grade_id=grade_id)
        .first()
    ):
        raise ConflictError("已任该年级组长")
    r = GradeHead(teacher_id=teacher_id, grade_id=grade_id)
    db.session.add(r)
    db.session.commit()
    return {"id": r.id, "teacher_id": teacher_id, "grade_id": grade_id}


def revoke_grade_head(record_id: int) -> None:
    r = db.session.get(GradeHead, record_id)
    if not r:
        raise NotFoundError("任职关系不存在")
    db.session.delete(r)
    db.session.commit()
