"""人脸库模型：每个学生可注册多张人脸，存 512 维 embedding（JSON 文本）。"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel


class FaceEmbedding(BaseModel):
    """学生人脸特征向量。"""

    __tablename__ = "face_embeddings"

    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False, index=True)
    embedding: Mapped[str] = mapped_column(Text, nullable=False, comment="JSON 编码的 512 维向量")
    dim: Mapped[int] = mapped_column(Integer, default=512, nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(255), comment="原图访问路径")
    image_hash: Mapped[str | None] = mapped_column(String(64), index=True, comment="原图 MD5 去重")
    confidence: Mapped[float] = mapped_column(default=0.0, comment="检测置信度")
    source: Mapped[str] = mapped_column(String(32), default="manual", comment="manual/batch/realtime")

    student = relationship("Student", backref="face_embeddings")
