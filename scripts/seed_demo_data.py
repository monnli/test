"""演示数据 seed 脚本。

生成：
- 1 所学校（青苗实验中学）
- 7 个常用科目（语文/数学/英语/物理/化学/生物/道德与法治）
- 3 个年级（七/八/九年级），每年级 2 个班，共 6 个班
- 约 30 名学生/班 = 180 名学生
- 约 30 名教师，包含多种角色搭配
- 内置 6 个角色 + 完整权限点
- 各角色演示账号

用法：
    python -m scripts.seed_demo_data        # 在 backend 目录下执行
    或：cd /path/to/backend && python ../scripts/seed_demo_data.py
"""

from __future__ import annotations

import random
import sys
from datetime import date, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models import (  # noqa: E402
    Clazz,
    Grade,
    GradeHead,
    Permission,
    ROLE_GRADE_HEAD,
    ROLE_HEAD_TEACHER,
    ROLE_LABELS,
    ROLE_PSY_TEACHER,
    ROLE_SCHOOL_ADMIN,
    ROLE_SUBJECT_TEACHER,
    ROLE_SUPER_ADMIN,
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
from app.utils.security import hash_password  # noqa: E402

random.seed(2026)

# ===== 内置权限点 =====
BUILTIN_PERMISSIONS = [
    # 用户管理
    ("user:list", "查看用户", "user"),
    ("user:create", "创建用户", "user"),
    ("user:update", "修改用户", "user"),
    ("user:delete", "删除用户", "user"),
    ("user:reset_password", "重置密码", "user"),
    # 组织架构
    ("org:school:manage", "学校管理", "org"),
    ("org:grade:manage", "年级管理", "org"),
    ("org:class:manage", "班级管理", "org"),
    ("org:student:manage", "学生管理", "org"),
    ("org:teacher:manage", "教师管理", "org"),
    ("org:subject:manage", "科目管理", "org"),
    # 课堂分析
    ("classroom:view", "查看课堂分析", "classroom"),
    ("classroom:upload", "上传课堂视频", "classroom"),
    ("classroom:realtime", "实时摄像头分析", "classroom"),
    # 心理健康
    ("psy:view", "查看心理档案", "psy"),
    ("psy:assess", "下发量表测评", "psy"),
    ("psy:dialog", "查看 AI 对话记录", "psy"),
    # 关联与预警
    ("alert:view", "查看预警", "alert"),
    ("alert:handle", "处理预警", "alert"),
    # 报告
    ("report:view", "查看报告", "report"),
    ("report:export", "导出报告", "report"),
    # 大屏
    ("dashboard:view", "查看数据大屏", "dashboard"),
]

# ===== 角色权限映射 =====
ROLE_PERMISSIONS: dict[str, list[str]] = {
    ROLE_SUPER_ADMIN: [code for code, _, _ in BUILTIN_PERMISSIONS],
    ROLE_SCHOOL_ADMIN: [code for code, _, _ in BUILTIN_PERMISSIONS],
    ROLE_PSY_TEACHER: [code for code, _, _ in BUILTIN_PERMISSIONS],
    ROLE_GRADE_HEAD: [
        "org:class:manage", "org:student:manage",
        "classroom:view", "psy:view", "alert:view", "alert:handle",
        "report:view", "report:export", "dashboard:view",
    ],
    ROLE_HEAD_TEACHER: [
        "org:student:manage",
        "classroom:view", "classroom:upload", "classroom:realtime",
        "psy:view", "psy:assess",
        "alert:view", "alert:handle",
        "report:view", "report:export", "dashboard:view",
    ],
    ROLE_SUBJECT_TEACHER: [
        "classroom:view", "classroom:upload", "classroom:realtime",
        "psy:view",
        "alert:view",
        "report:view", "dashboard:view",
    ],
}

SUBJECTS = [
    ("语文", "chinese", 1),
    ("数学", "math", 2),
    ("英语", "english", 3),
    ("物理", "physics", 4),
    ("化学", "chemistry", 5),
    ("生物", "biology", 6),
    ("道德与法治", "ethics", 7),
]

GRADES = [("七年级", 7), ("八年级", 8), ("九年级", 9)]
CLASSES_PER_GRADE = 2
STUDENTS_PER_CLASS = 30

SURNAMES = [
    "李", "王", "张", "刘", "陈", "杨", "黄", "赵", "周", "吴",
    "徐", "孙", "马", "朱", "胡", "郭", "何", "高", "林", "罗",
    "郑", "梁", "谢", "宋", "唐", "许", "韩", "冯", "邓", "曹",
]
GIVEN_NAMES_M = ["浩然", "子轩", "宇轩", "皓轩", "梓睿", "俊杰", "明辉", "嘉豪", "天宇", "若飞", "致远", "博文"]
GIVEN_NAMES_F = ["欣怡", "梓涵", "诗涵", "雨萱", "可馨", "慧敏", "嘉怡", "佳琪", "依诺", "若曦", "思颖", "雅婷"]


def _rand_name(gender: str) -> str:
    surname = random.choice(SURNAMES)
    given = random.choice(GIVEN_NAMES_M if gender == "男" else GIVEN_NAMES_F)
    return surname + given


def _rand_phone() -> str:
    return "13" + "".join(random.choice("0123456789") for _ in range(9))


def _rand_birth_date(grade_level: int) -> date:
    age = 6 + grade_level
    today = date.today()
    return today.replace(year=today.year - age) - timedelta(days=random.randint(0, 365))


def seed_permissions_and_roles() -> dict[str, Role]:
    print("→ 初始化权限点与角色...")
    perm_map: dict[str, Permission] = {}
    for code, name, module in BUILTIN_PERMISSIONS:
        p = db.session.query(Permission).filter_by(code=code).first()
        if not p:
            p = Permission(code=code, name=name, module=module)
            db.session.add(p)
        perm_map[code] = p
    db.session.flush()

    role_map: dict[str, Role] = {}
    for sort, code in enumerate(
        [ROLE_SUPER_ADMIN, ROLE_SCHOOL_ADMIN, ROLE_PSY_TEACHER,
         ROLE_GRADE_HEAD, ROLE_HEAD_TEACHER, ROLE_SUBJECT_TEACHER]
    ):
        r = db.session.query(Role).filter_by(code=code).first()
        if not r:
            r = Role(
                code=code,
                name=ROLE_LABELS.get(code, code),
                description=ROLE_LABELS.get(code, code) + "的内置角色",
                is_builtin=True,
                sort_order=sort,
            )
            db.session.add(r)
        role_map[code] = r
    db.session.flush()

    # 重置角色-权限关系
    for code, role in role_map.items():
        db.session.query(RolePermission).filter_by(role_id=role.id).delete()
        for perm_code in ROLE_PERMISSIONS.get(code, []):
            perm = perm_map.get(perm_code)
            if perm:
                db.session.add(RolePermission(role_id=role.id, permission_id=perm.id))
    db.session.flush()
    return role_map


def seed_school() -> School:
    print("→ 初始化学校...")
    s = db.session.query(School).filter_by(name="青苗实验中学").first()
    if not s:
        s = School(
            name="青苗实验中学",
            code="QM-001",
            address="某省某市某区青苗大道 100 号",
            contact="教务处",
            phone="0571-88888888",
            description="演示数据 · 用于参赛与功能展示",
        )
        db.session.add(s)
        db.session.flush()
    return s


def seed_subjects() -> dict[str, Subject]:
    print("→ 初始化科目...")
    out: dict[str, Subject] = {}
    for name, code, order in SUBJECTS:
        s = db.session.query(Subject).filter_by(code=code).first()
        if not s:
            s = Subject(name=name, code=code, sort_order=order)
            db.session.add(s)
        out[code] = s
    db.session.flush()
    return out


def seed_grades_and_classes(school: School) -> tuple[list[Grade], list[Clazz]]:
    print("→ 初始化年级与班级...")
    grades: list[Grade] = []
    classes: list[Clazz] = []
    for name, level in GRADES:
        g = db.session.query(Grade).filter_by(school_id=school.id, name=name).first()
        if not g:
            g = Grade(school_id=school.id, name=name, level=level)
            db.session.add(g)
            db.session.flush()
        grades.append(g)
        for i in range(1, CLASSES_PER_GRADE + 1):
            cname = f"{i} 班"
            c = db.session.query(Clazz).filter_by(grade_id=g.id, name=cname).first()
            if not c:
                c = Clazz(grade_id=g.id, name=cname)
                db.session.add(c)
                db.session.flush()
            classes.append(c)
    return grades, classes


def seed_students(school: School, classes: list[Clazz]) -> int:
    print(f"→ 初始化学生（每班 {STUDENTS_PER_CLASS} 人）...")
    count = 0
    for c in classes:
        existing = db.session.query(Student).filter_by(class_id=c.id, is_deleted=False).count()
        need = STUDENTS_PER_CLASS - existing
        if need <= 0:
            continue
        for i in range(need):
            seq = existing + i + 1
            gender = random.choice(["男", "女"])
            no = f"{date.today().year}{c.grade.level:02d}{c.id:02d}{seq:02d}"
            s = Student(
                student_no=no,
                name=_rand_name(gender),
                gender=gender,
                birth_date=_rand_birth_date(c.grade.level),
                school_id=school.id,
                grade_id=c.grade_id,
                class_id=c.id,
                parent_name=random.choice(SURNAMES) + random.choice(["先生", "女士"]),
                parent_phone=_rand_phone(),
                enrollment_date=date.today().replace(month=9, day=1),
            )
            db.session.add(s)
            count += 1
    db.session.flush()
    return count


def _create_user_and_teacher(
    school: School,
    role_codes: list[str],
    role_map: dict[str, Role],
    username: str,
    password: str,
    real_name: str,
    teacher_no: str,
    gender: str = "男",
    title: str | None = None,
) -> Teacher:
    user = db.session.query(User).filter_by(username=username).first()
    if not user:
        user = User(
            username=username,
            password_hash=hash_password(password),
            real_name=real_name,
            phone=_rand_phone(),
            email=f"{username}@qingmiao.demo",
            school_id=school.id,
            is_active=True,
        )
        db.session.add(user)
        db.session.flush()
    else:
        user.password_hash = hash_password(password)
        user.is_active = True
    db.session.query(UserRole).filter_by(user_id=user.id).delete()
    for code in role_codes:
        role = role_map.get(code)
        if role:
            db.session.add(UserRole(user_id=user.id, role_id=role.id))

    teacher = db.session.query(Teacher).filter_by(teacher_no=teacher_no).first()
    if not teacher:
        teacher = Teacher(
            user_id=user.id,
            teacher_no=teacher_no,
            name=real_name,
            gender=gender,
            school_id=school.id,
            phone=user.phone,
            email=user.email,
            title=title,
        )
        db.session.add(teacher)
    else:
        teacher.user_id = user.id
        teacher.name = real_name
    db.session.flush()
    return teacher


def seed_teachers_and_relations(
    school: School,
    role_map: dict[str, Role],
    grades: list[Grade],
    classes: list[Clazz],
    subjects: dict[str, Subject],
) -> dict:
    print("→ 初始化教师 + 任课关系 + 演示账号...")
    accounts: list[dict] = []

    # 1. 超级管理员（隐藏，仅平台维护用）
    _create_user_and_teacher(
        school, [ROLE_SUPER_ADMIN], role_map,
        username="superadmin", password="super123",
        real_name="平台超管", teacher_no="T-SUPER",
    )
    accounts.append({"role": "超级管理员", "username": "superadmin", "password": "super123"})

    # 2. 学校管理员
    _create_user_and_teacher(
        school, [ROLE_SCHOOL_ADMIN], role_map,
        username="admin", password="admin123",
        real_name="校长 张华", teacher_no="T-ADMIN",
        title="校长",
    )
    accounts.append({"role": "学校管理员", "username": "admin", "password": "admin123"})

    # 3. 心理学老师
    _create_user_and_teacher(
        school, [ROLE_PSY_TEACHER], role_map,
        username="psy", password="psy12345",
        real_name="心理 王晴", teacher_no="T-PSY",
        gender="女", title="心理咨询师",
    )
    accounts.append({"role": "心理学老师", "username": "psy", "password": "psy12345"})

    # 4. 三个年级组长
    for i, g in enumerate(grades):
        username = f"grade_head_{g.level}"
        password = "grade123"
        teacher = _create_user_and_teacher(
            school, [ROLE_GRADE_HEAD, ROLE_SUBJECT_TEACHER], role_map,
            username=username, password=password,
            real_name=f"{g.name}组长 李{['明','强','勇'][i]}",
            teacher_no=f"T-GH-{g.level}",
            gender="男",
            title="年级组长",
        )
        existing = db.session.query(GradeHead).filter_by(
            teacher_id=teacher.id, grade_id=g.id
        ).first()
        if not existing:
            db.session.add(GradeHead(teacher_id=teacher.id, grade_id=g.id))
        accounts.append({
            "role": f"年级组长（{g.name}）",
            "username": username,
            "password": password,
        })

    # 5. 6 个班主任，并兼任「语文/数学/英语」其中一科
    head_subjects = ["chinese", "math", "english", "chinese", "math", "english"]
    for idx, c in enumerate(classes):
        username = f"head_{c.grade.level}_{c.name.replace(' 班','b')}"
        username = username.replace("班", "b")
        password = "head1234"
        teacher = _create_user_and_teacher(
            school, [ROLE_HEAD_TEACHER, ROLE_SUBJECT_TEACHER], role_map,
            username=username, password=password,
            real_name=f"{c.grade.name}{c.name}班主任",
            teacher_no=f"T-HT-{c.id:02d}",
            gender="女" if idx % 2 == 0 else "男",
            title="班主任",
        )
        c.head_teacher_id = teacher.id
        # 给班主任配自己班的任教科目
        sub = subjects[head_subjects[idx]]
        if not db.session.query(TeacherClassSubject).filter_by(
            teacher_id=teacher.id, class_id=c.id, subject_id=sub.id
        ).first():
            db.session.add(TeacherClassSubject(
                teacher_id=teacher.id, class_id=c.id, subject_id=sub.id
            ))
        # 班主任如果在其他班也任同科目，演示「跨班同科」权限
        for other in classes:
            if other.id != c.id and head_subjects[classes.index(other)] == head_subjects[idx]:
                if not db.session.query(TeacherClassSubject).filter_by(
                    teacher_id=teacher.id, class_id=other.id, subject_id=sub.id
                ).first():
                    db.session.add(TeacherClassSubject(
                        teacher_id=teacher.id, class_id=other.id, subject_id=sub.id
                    ))
        accounts.append({
            "role": f"班主任（{c.grade.name}{c.name}）",
            "username": username,
            "password": password,
        })

    # 6. 科任老师（每个非主科×班级一份），生成纯科任账号
    other_subject_keys = ["physics", "chemistry", "biology", "ethics"]
    pure_teacher_idx = 1
    for sub_key in other_subject_keys:
        sub = subjects[sub_key]
        # 每科 1 个老师覆盖所有班
        username = f"sub_{sub_key}"
        password = "sub12345"
        teacher = _create_user_and_teacher(
            school, [ROLE_SUBJECT_TEACHER], role_map,
            username=username, password=password,
            real_name=f"{sub.name}老师",
            teacher_no=f"T-SUB-{pure_teacher_idx:02d}",
            gender="男" if pure_teacher_idx % 2 == 0 else "女",
            title="科任老师",
        )
        for c in classes:
            if not db.session.query(TeacherClassSubject).filter_by(
                teacher_id=teacher.id, class_id=c.id, subject_id=sub.id
            ).first():
                db.session.add(TeacherClassSubject(
                    teacher_id=teacher.id, class_id=c.id, subject_id=sub.id
                ))
        accounts.append({
            "role": f"科任老师（{sub.name}）",
            "username": username,
            "password": password,
        })
        pure_teacher_idx += 1

    db.session.flush()
    return {"accounts": accounts}


def main() -> None:
    app = create_app()
    with app.app_context():
        print(f"使用数据库：{app.config['SQLALCHEMY_DATABASE_URI']}")
        db.create_all()

        role_map = seed_permissions_and_roles()
        school = seed_school()
        subjects = seed_subjects()
        grades, classes = seed_grades_and_classes(school)
        student_count = seed_students(school, classes)
        result = seed_teachers_and_relations(school, role_map, grades, classes, subjects)

        db.session.commit()

        print()
        print("=" * 70)
        print(f"✅ 演示数据 seed 完成：")
        print(f"   - 学校：{school.name}")
        print(f"   - 年级：{len(grades)} 个，班级：{len(classes)} 个")
        print(f"   - 本次新增学生：{student_count} 名")
        print(f"   - 科目：{len(subjects)} 个")
        print(f"   - 演示账号（共 {len(result['accounts'])} 个，密码请尽快修改）：")
        print("-" * 70)
        for acc in result["accounts"]:
            print(f"   {acc['role']:<22} {acc['username']:<20} 密码：{acc['password']}")
        print("=" * 70)


if __name__ == "__main__":
    main()
