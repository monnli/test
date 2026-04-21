"""课堂分析相关数据模型。

涵盖：
- ClassSession   课次
- Video          视频文件
- AnalysisTask   分析任务
- BehaviorRecord 行为时间点记录
- EmotionRecord  表情时间点记录
- AttendanceRecord 出勤记录
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel


class ClassSession(BaseModel):
    """课次：某天某节课的某科目在某班。"""

    __tablename__ = "class_sessions"

    class_id: Mapped[int] = mapped_column(ForeignKey("classes.id"), nullable=False, index=True)
    subject_id: Mapped[int | None] = mapped_column(ForeignKey("subjects.id"), nullable=True)
    teacher_id: Mapped[int | None] = mapped_column(ForeignKey("teachers.id"), nullable=True)
    session_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    period: Mapped[int] = mapped_column(Integer, default=1, comment="第几节课")
    title: Mapped[str | None] = mapped_column(String(200), comment="课题")
    note: Mapped[str | None] = mapped_column(String(500))

    # M10 扩展
    camera_id: Mapped[int | None] = mapped_column(ForeignKey("cameras.id"), index=True)
    trigger_type: Mapped[str] = mapped_column(
        String(16), default="manual",
        comment="schedule / manual / upload"
    )
    status: Mapped[str] = mapped_column(
        String(16), default="scheduled",
        comment="scheduled / running / ended / auto_ended"
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime)
    engagement_score: Mapped[float] = mapped_column(Float, default=0.0)
    no_person_minutes: Mapped[int] = mapped_column(Integer, default=0)


class Video(BaseModel):
    """视频文件。"""

    __tablename__ = "videos"

    class_session_id: Mapped[int | None] = mapped_column(
        ForeignKey("class_sessions.id"), index=True, nullable=True
    )
    class_id: Mapped[int | None] = mapped_column(ForeignKey("classes.id"), index=True, nullable=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(255), nullable=False, comment="存储路径")
    url: Mapped[str | None] = mapped_column(String(255), comment="访问 URL")
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    duration_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    fps: Mapped[float] = mapped_column(Float, default=0.0)
    width: Mapped[int] = mapped_column(Integer, default=0)
    height: Mapped[int] = mapped_column(Integer, default=0)
    uploaded_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    note: Mapped[str | None] = mapped_column(String(500))


class AnalysisTask(BaseModel):
    """视频分析任务。"""

    __tablename__ = "analysis_tasks"

    video_id: Mapped[int] = mapped_column(ForeignKey("videos.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(16), default="pending", comment="pending/running/success/failed"
    )
    progress: Mapped[int] = mapped_column(Integer, default=0, comment="0-100")
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)
    sample_interval_sec: Mapped[float] = mapped_column(Float, default=2.0, comment="抽帧间隔")
    total_frames: Mapped[int] = mapped_column(Integer, default=0)
    processed_frames: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text, comment="JSON 汇总结果")

    video: Mapped[Video] = relationship()


class BehaviorRecord(BaseModel):
    """单帧行为检测记录。"""

    __tablename__ = "behavior_records"

    task_id: Mapped[int] = mapped_column(ForeignKey("analysis_tasks.id"), index=True, nullable=False)
    video_id: Mapped[int] = mapped_column(ForeignKey("videos.id"), index=True, nullable=False)
    frame_time: Mapped[float] = mapped_column(Float, nullable=False, comment="视频时间秒")
    label: Mapped[str] = mapped_column(String(64), nullable=False)
    label_cn: Mapped[str] = mapped_column(String(64), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    bbox: Mapped[str | None] = mapped_column(String(255), comment="JSON [x1,y1,x2,y2]")
    student_id: Mapped[int | None] = mapped_column(ForeignKey("students.id"), index=True)


class EmotionRecord(BaseModel):
    """单帧表情记录。"""

    __tablename__ = "emotion_records"

    task_id: Mapped[int] = mapped_column(ForeignKey("analysis_tasks.id"), index=True, nullable=False)
    video_id: Mapped[int] = mapped_column(ForeignKey("videos.id"), index=True, nullable=False)
    frame_time: Mapped[float] = mapped_column(Float, nullable=False)
    emotion: Mapped[str] = mapped_column(String(32), nullable=False)
    emotion_cn: Mapped[str] = mapped_column(String(32), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    bbox: Mapped[str | None] = mapped_column(String(255))
    student_id: Mapped[int | None] = mapped_column(ForeignKey("students.id"), index=True)


class AttendanceRecord(BaseModel):
    """出勤记录（基于人脸识别）。"""

    __tablename__ = "attendance_records"

    task_id: Mapped[int | None] = mapped_column(ForeignKey("analysis_tasks.id"), index=True)
    class_session_id: Mapped[int | None] = mapped_column(
        ForeignKey("class_sessions.id"), index=True
    )
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="present", comment="present/absent/late")
    detected_count: Mapped[int] = mapped_column(Integer, default=0)
    first_seen: Mapped[float] = mapped_column(Float, default=0.0)
    last_seen: Mapped[float] = mapped_column(Float, default=0.0)
