"""报告模型。"""

from __future__ import annotations

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel


class Report(BaseModel):
    __tablename__ = "reports"

    type: Mapped[str] = mapped_column(String(32), nullable=False, comment="class/student/school")
    target_id: Mapped[int | None] = mapped_column(comment="班级/学生/学校 ID")
    target_name: Mapped[str | None] = mapped_column(String(128))
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    period: Mapped[str | None] = mapped_column(String(64), comment="如 2026-W17")
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="Markdown 报告正文")
    summary: Mapped[str | None] = mapped_column(Text)
    pdf_key: Mapped[str | None] = mapped_column(String(255))
    operator_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
