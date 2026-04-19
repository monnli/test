"""组织架构模型：学校 → 年级 → 班级 → 学生。"""

from __future__ import annotations

from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel, SoftDeleteMixin


class School(BaseModel, SoftDeleteMixin):
    """学校。"""

    __tablename__ = "schools"

    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, comment="学校名称")
    code: Mapped[str | None] = mapped_column(String(64), unique=True, comment="学校编号")
    address: Mapped[str | None] = mapped_column(String(255), comment="地址")
    contact: Mapped[str | None] = mapped_column(String(64), comment="联系人")
    phone: Mapped[str | None] = mapped_column(String(32), comment="联系电话")
    description: Mapped[str | None] = mapped_column(String(500), comment="备注")

    grades: Mapped[list[Grade]] = relationship(back_populates="school", cascade="all, delete-orphan")


class Grade(BaseModel, SoftDeleteMixin):
    """年级。"""

    __tablename__ = "grades"
    __table_args__ = (UniqueConstraint("school_id", "name", name="uq_grade_school_name"),)

    school_id: Mapped[int] = mapped_column(ForeignKey("schools.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False, comment="年级名称，如「七年级」")
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=1, comment="年级级别 1-12")

    school: Mapped[School] = relationship(back_populates="grades")
    classes: Mapped[list[Clazz]] = relationship(back_populates="grade", cascade="all, delete-orphan")


class Clazz(BaseModel, SoftDeleteMixin):
    """班级。Class 是 Python 关键字相关，所以叫 Clazz。"""

    __tablename__ = "classes"
    __table_args__ = (UniqueConstraint("grade_id", "name", name="uq_class_grade_name"),)

    grade_id: Mapped[int] = mapped_column(ForeignKey("grades.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False, comment="班级名称，如「1 班」")
    head_teacher_id: Mapped[int | None] = mapped_column(
        ForeignKey("teachers.id"), nullable=True, comment="班主任 ID"
    )
    student_count: Mapped[int] = mapped_column(Integer, default=0, comment="学生数（缓存值）")

    grade: Mapped[Grade] = relationship(back_populates="classes")
    head_teacher: Mapped[Teacher | None] = relationship(foreign_keys=[head_teacher_id])
    students: Mapped[list[Student]] = relationship(
        back_populates="clazz", cascade="all, delete-orphan", foreign_keys="Student.class_id"
    )


class Student(BaseModel, SoftDeleteMixin):
    """学生。"""

    __tablename__ = "students"

    student_no: Mapped[str] = mapped_column(
        String(32), unique=True, nullable=False, comment="学号"
    )
    name: Mapped[str] = mapped_column(String(64), nullable=False, comment="姓名")
    gender: Mapped[str] = mapped_column(String(8), default="未知", comment="性别 男/女/未知")
    birth_date: Mapped[date | None] = mapped_column(Date, comment="出生日期")
    avatar: Mapped[str | None] = mapped_column(String(255), comment="头像 URL")
    school_id: Mapped[int] = mapped_column(ForeignKey("schools.id"), nullable=False, index=True)
    grade_id: Mapped[int] = mapped_column(ForeignKey("grades.id"), nullable=False, index=True)
    class_id: Mapped[int] = mapped_column(ForeignKey("classes.id"), nullable=False, index=True)
    parent_name: Mapped[str | None] = mapped_column(String(64), comment="家长姓名")
    parent_phone: Mapped[str | None] = mapped_column(String(32), comment="家长电话")
    enrollment_date: Mapped[date | None] = mapped_column(Date, comment="入学日期")
    note: Mapped[str | None] = mapped_column(String(500), comment="备注")

    clazz: Mapped[Clazz] = relationship(back_populates="students", foreign_keys=[class_id])


class Subject(BaseModel, SoftDeleteMixin):
    """学科。语文、数学、英语…"""

    __tablename__ = "subjects"

    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, comment="科目名")
    code: Mapped[str | None] = mapped_column(String(32), unique=True, comment="科目编码")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment="排序")


class Teacher(BaseModel, SoftDeleteMixin):
    """教师档案（与 User 是 1:1，User 负责账号，Teacher 负责档案）。"""

    __tablename__ = "teachers"

    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), unique=True, nullable=True, comment="关联账号"
    )
    teacher_no: Mapped[str] = mapped_column(
        String(32), unique=True, nullable=False, comment="教师工号"
    )
    name: Mapped[str] = mapped_column(String(64), nullable=False, comment="姓名")
    gender: Mapped[str] = mapped_column(String(8), default="未知", comment="性别")
    school_id: Mapped[int] = mapped_column(ForeignKey("schools.id"), nullable=False, index=True)
    phone: Mapped[str | None] = mapped_column(String(32), comment="手机号")
    email: Mapped[str | None] = mapped_column(String(128), comment="邮箱")
    title: Mapped[str | None] = mapped_column(String(64), comment="职称")
    avatar: Mapped[str | None] = mapped_column(String(255), comment="头像 URL")

    user = relationship("User", back_populates="teacher", uselist=False, foreign_keys=[user_id])


class TeacherClassSubject(BaseModel):
    """教师任课关系：教师 × 班级 × 科目（多对多）。"""

    __tablename__ = "teacher_class_subjects"
    __table_args__ = (
        UniqueConstraint(
            "teacher_id", "class_id", "subject_id", name="uq_teacher_class_subject"
        ),
    )

    teacher_id: Mapped[int] = mapped_column(ForeignKey("teachers.id"), nullable=False, index=True)
    class_id: Mapped[int] = mapped_column(ForeignKey("classes.id"), nullable=False, index=True)
    subject_id: Mapped[int] = mapped_column(
        ForeignKey("subjects.id"), nullable=False, index=True
    )

    teacher: Mapped[Teacher] = relationship()
    clazz: Mapped[Clazz] = relationship()
    subject: Mapped[Subject] = relationship()


class GradeHead(BaseModel):
    """年级组长任职关系：教师 × 年级（一个教师可能任多个年级组长，少见但要支持）。"""

    __tablename__ = "grade_heads"
    __table_args__ = (UniqueConstraint("teacher_id", "grade_id", name="uq_grade_head"),)

    teacher_id: Mapped[int] = mapped_column(ForeignKey("teachers.id"), nullable=False, index=True)
    grade_id: Mapped[int] = mapped_column(ForeignKey("grades.id"), nullable=False, index=True)

    teacher: Mapped[Teacher] = relationship()
    grade: Mapped[Grade] = relationship()
