"""摄像头与课表模型。"""

from __future__ import annotations

from datetime import date, datetime, time as dtime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text, Time, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel, SoftDeleteMixin


class Camera(BaseModel, SoftDeleteMixin):
    """教室摄像头。"""

    __tablename__ = "cameras"

    school_id: Mapped[int] = mapped_column(ForeignKey("schools.id"), nullable=False, index=True)
    class_id: Mapped[int | None] = mapped_column(
        ForeignKey("classes.id"), nullable=True, index=True, comment="绑定班级"
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    location: Mapped[str | None] = mapped_column(String(255))
    stream_url: Mapped[str] = mapped_column(String(500), nullable=False, comment="rtsp/hls/文件路径")
    stream_type: Mapped[str] = mapped_column(
        String(16), default="file_loop",
        comment="rtsp / hls / file / file_loop / webrtc"
    )
    resolution: Mapped[str | None] = mapped_column(String(32), comment="如 1920x1080")
    status: Mapped[str] = mapped_column(
        String(16), default="online", comment="online / offline / disabled"
    )
    last_heartbeat: Mapped[datetime | None] = mapped_column(DateTime)
    note: Mapped[str | None] = mapped_column(Text)


class ClassSchedule(BaseModel, SoftDeleteMixin):
    """课表：某班某天第几节由某老师上某科。"""

    __tablename__ = "class_schedules"

    class_id: Mapped[int] = mapped_column(ForeignKey("classes.id"), nullable=False, index=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"), nullable=False, index=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("teachers.id"), nullable=False, index=True)
    weekday: Mapped[int] = mapped_column(Integer, nullable=False, comment="1-7 周一到周日")
    period: Mapped[int] = mapped_column(Integer, nullable=False, comment="第几节课 1-10")
    start_time: Mapped[dtime] = mapped_column(Time, nullable=False)
    end_time: Mapped[dtime] = mapped_column(Time, nullable=False)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date] = mapped_column(Date, nullable=False)
    note: Mapped[str | None] = mapped_column(String(255))

    __table_args__ = (
        UniqueConstraint(
            "class_id", "weekday", "period", "effective_from",
            name="uq_class_schedule_slot",
        ),
    )
