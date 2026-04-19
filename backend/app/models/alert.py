"""学业成绩 + 预警 + 干预记录模型。"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel


class Exam(BaseModel):
    __tablename__ = "exams"

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    subject_id: Mapped[int | None] = mapped_column(ForeignKey("subjects.id"), index=True)
    grade_id: Mapped[int | None] = mapped_column(ForeignKey("grades.id"), index=True)
    exam_date: Mapped[date] = mapped_column(Date, nullable=False)
    full_score: Mapped[float] = mapped_column(Float, default=100.0)


class Score(BaseModel):
    __tablename__ = "scores"

    exam_id: Mapped[int] = mapped_column(ForeignKey("exams.id"), index=True, nullable=False)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True, nullable=False)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    rank_in_class: Mapped[int | None] = mapped_column(Integer)


class Alert(BaseModel):
    """预警工单。

    四级：
      green  正常
      yellow 关注
      orange 重点关注
      red    紧急介入
    """

    __tablename__ = "alerts"

    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True, nullable=False)
    level: Mapped[str] = mapped_column(String(16), nullable=False, index=True)  # green/yellow/orange/red
    score: Mapped[float] = mapped_column(Float, default=0.0, comment="风险评分 0-100")
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    reasons: Mapped[str | None] = mapped_column(Text, comment="JSON 数组：原因列表")
    sources: Mapped[str | None] = mapped_column(String(255), comment="JSON 数组：数据来源")
    status: Mapped[str] = mapped_column(
        String(16), default="open", comment="open/acknowledged/resolved/closed"
    )
    handler_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime)
    note: Mapped[str | None] = mapped_column(Text)


class InterventionRecord(BaseModel):
    """干预记录（人工填写）。"""

    __tablename__ = "intervention_records"

    alert_id: Mapped[int] = mapped_column(ForeignKey("alerts.id"), index=True, nullable=False)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True, nullable=False)
    operator_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False, comment="谈话/家访/转介/其他")
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    follow_up: Mapped[str | None] = mapped_column(Text)
