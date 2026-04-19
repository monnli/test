"""pytest 公共 fixture。"""

from __future__ import annotations

import pytest

from app import create_app
from app.extensions import db
from config import TestingConfig


@pytest.fixture()
def app():
    application = create_app(TestingConfig)
    with application.app_context():
        from app import models  # noqa: F401

        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def seeded_app(app):
    """加载一份精简的种子数据，便于测试权限与查询。"""
    from app.utils.security import hash_password
    from app.models import (
        Clazz,
        Grade,
        Permission,
        ROLE_HEAD_TEACHER,
        ROLE_LABELS,
        ROLE_PSY_TEACHER,
        ROLE_SCHOOL_ADMIN,
        ROLE_SUBJECT_TEACHER,
        Role,
        RolePermission,
        School,
        Student,
        Subject,
        Teacher,
        TeacherClassSubject,
        User,
        UserRole,
    )

    perms: dict[str, Permission] = {}
    for code in ("user:list", "org:school:manage", "classroom:view"):
        p = Permission(code=code, name=code, module=code.split(":")[0])
        db.session.add(p)
        perms[code] = p
    db.session.flush()

    roles: dict[str, Role] = {}
    for code in (ROLE_SCHOOL_ADMIN, ROLE_PSY_TEACHER, ROLE_HEAD_TEACHER, ROLE_SUBJECT_TEACHER):
        r = Role(code=code, name=ROLE_LABELS.get(code, code), is_builtin=True)
        db.session.add(r)
        roles[code] = r
    db.session.flush()
    for r in roles.values():
        for p in perms.values():
            db.session.add(RolePermission(role_id=r.id, permission_id=p.id))
    db.session.flush()

    school = School(name="测试学校", code="T-001")
    db.session.add(school)
    db.session.flush()

    grade = Grade(school_id=school.id, name="七年级", level=7)
    db.session.add(grade)
    db.session.flush()

    c1 = Clazz(grade_id=grade.id, name="1 班")
    c2 = Clazz(grade_id=grade.id, name="2 班")
    db.session.add_all([c1, c2])
    db.session.flush()

    sub_chinese = Subject(name="语文", code="chinese")
    sub_math = Subject(name="数学", code="math")
    db.session.add_all([sub_chinese, sub_math])
    db.session.flush()

    def _make_user(username: str, role_code: str, real_name: str) -> User:
        u = User(
            username=username,
            password_hash=hash_password("123456"),
            real_name=real_name,
            school_id=school.id,
            is_active=True,
        )
        db.session.add(u)
        db.session.flush()
        db.session.add(UserRole(user_id=u.id, role_id=roles[role_code].id))
        return u

    admin_user = _make_user("admin", ROLE_SCHOOL_ADMIN, "校长")
    head_user = _make_user("head1", ROLE_HEAD_TEACHER, "1班班主任")
    sub_user = _make_user("sub1", ROLE_SUBJECT_TEACHER, "数学老师")

    head_teacher = Teacher(
        user_id=head_user.id, teacher_no="T-HT-1", name="1班班主任",
        school_id=school.id,
    )
    sub_teacher = Teacher(
        user_id=sub_user.id, teacher_no="T-SUB-1", name="数学老师",
        school_id=school.id,
    )
    db.session.add_all([head_teacher, sub_teacher])
    db.session.flush()

    c1.head_teacher_id = head_teacher.id
    db.session.add(TeacherClassSubject(
        teacher_id=head_teacher.id, class_id=c1.id, subject_id=sub_chinese.id,
    ))
    db.session.add(TeacherClassSubject(
        teacher_id=sub_teacher.id, class_id=c1.id, subject_id=sub_math.id,
    ))
    db.session.add(TeacherClassSubject(
        teacher_id=sub_teacher.id, class_id=c2.id, subject_id=sub_math.id,
    ))

    # 学生
    for cls in (c1, c2):
        for i in range(3):
            db.session.add(Student(
                student_no=f"{cls.id}-{i:02d}",
                name=f"学生{cls.id}{i}",
                gender="男" if i % 2 == 0 else "女",
                school_id=school.id,
                grade_id=grade.id,
                class_id=cls.id,
            ))

    db.session.commit()
    return app


def _login(client, username: str, password: str = "123456") -> str:
    resp = client.post("/api/auth/login", json={"username": username, "password": password})
    assert resp.status_code == 200, resp.get_json()
    return resp.get_json()["data"]["access_token"]


@pytest.fixture()
def login(client):
    """返回一个能登录指定账号的工厂函数。"""

    def _do_login(username: str, password: str = "123456"):
        token = _login(client, username, password)
        return {"Authorization": f"Bearer {token}"}

    return _do_login
