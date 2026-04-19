"""心理健康相关数据模型。"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel, SoftDeleteMixin


class Scale(BaseModel, SoftDeleteMixin):
    """心理量表定义。"""

    __tablename__ = "scales"

    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, comment="如 PHQ-9")
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    target: Mapped[str] = mapped_column(String(64), comment="评估目标，如「抑郁筛查」")
    description: Mapped[str | None] = mapped_column(Text)
    interpretation: Mapped[str | None] = mapped_column(
        Text, comment="JSON: [{min:0,max:4,level:'正常',color:'green',advice:''}]"
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    questions = relationship(
        "ScaleQuestion", back_populates="scale", cascade="all, delete-orphan",
        order_by="ScaleQuestion.sort_order",
    )


class ScaleQuestion(BaseModel):
    """量表题目。"""

    __tablename__ = "scale_questions"

    scale_id: Mapped[int] = mapped_column(ForeignKey("scales.id"), nullable=False, index=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[str] = mapped_column(Text, comment="JSON: [{label:'从不',score:0},...]")
    dimension: Mapped[str | None] = mapped_column(String(64), comment="所属维度（多维量表）")
    reverse: Mapped[bool] = mapped_column(default=False, comment="是否反向计分")

    scale: Mapped[Scale] = relationship(back_populates="questions")


class ScaleAssessment(BaseModel):
    """学生量表测评结果。"""

    __tablename__ = "scale_assessments"

    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True, nullable=False)
    scale_id: Mapped[int] = mapped_column(ForeignKey("scales.id"), index=True, nullable=False)
    operator_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), comment="操作老师")
    answers: Mapped[str] = mapped_column(Text, comment="JSON {question_id: option_score}")
    total_score: Mapped[float] = mapped_column(Float, default=0.0)
    dimension_scores: Mapped[str | None] = mapped_column(Text, comment="JSON {dim: score}")
    level: Mapped[str] = mapped_column(String(32), default="正常")
    level_color: Mapped[str] = mapped_column(String(16), default="green")
    advice: Mapped[str | None] = mapped_column(Text)
    completed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class TextAnalysis(BaseModel):
    """学生文本（周记/作文）AI 情绪分析记录。"""

    __tablename__ = "text_analyses"

    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True, nullable=False)
    operator_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str | None] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    polarity: Mapped[str] = mapped_column(String(16), default="中性")
    risk_level: Mapped[str] = mapped_column(String(16), default="none")
    risk_keywords: Mapped[str | None] = mapped_column(String(500), comment="JSON 数组")
    emotion_tags: Mapped[str | None] = mapped_column(String(255), comment="JSON 数组")
    summary: Mapped[str | None] = mapped_column(Text)
    suggestion: Mapped[str | None] = mapped_column(Text)
    raw_response: Mapped[str | None] = mapped_column(Text)


class AIConversation(BaseModel):
    """AI 心理对话会话。"""

    __tablename__ = "ai_conversations"

    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True, nullable=False)
    operator_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str | None] = mapped_column(String(200))
    risk_level: Mapped[str] = mapped_column(String(16), default="none", comment="对话最高风险等级")
    message_count: Mapped[int] = mapped_column(Integer, default=0)


class AIConversationMessage(BaseModel):
    """对话消息。"""

    __tablename__ = "ai_conversation_messages"

    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("ai_conversations.id"), index=True, nullable=False
    )
    role: Mapped[str] = mapped_column(String(16), nullable=False, comment="user/assistant/system")
    content: Mapped[str] = mapped_column(Text, nullable=False)
    risk_level: Mapped[str | None] = mapped_column(String(16))
    risk_keywords: Mapped[str | None] = mapped_column(String(500))


class EmotionTimeline(BaseModel):
    """学生情绪时序点（按天聚合）。可由量表/文本/课堂分析自动写入。"""

    __tablename__ = "emotion_timeline"

    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True, nullable=False)
    record_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    score: Mapped[float] = mapped_column(Float, default=80.0, comment="0-100 综合心理健康指数")
    polarity: Mapped[str] = mapped_column(String(16), default="中性")
    risk_level: Mapped[str] = mapped_column(String(16), default="none")
    source: Mapped[str] = mapped_column(String(32), default="auto", comment="量表/文本/课堂/手动")
    note: Mapped[str | None] = mapped_column(Text)
