"""心理健康服务。"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from typing import Any

from loguru import logger
from sqlalchemy import func

from ..ai import get_ai_client
from ..data.scales_data import SCALES
from ..extensions import db
from ..models import (
    AIConversation,
    AIConversationMessage,
    EmotionTimeline,
    Scale,
    ScaleAssessment,
    ScaleQuestion,
    Student,
    TextAnalysis,
)
from ..utils.exceptions import NotFoundError, ValidationError


# ================= 量表管理 =================

def ensure_scales_seeded() -> int:
    """确保 5 套量表已入库。"""
    count = 0
    for idx, scale_def in enumerate(SCALES):
        scale = db.session.query(Scale).filter_by(code=scale_def["code"]).first()
        if not scale:
            scale = Scale(
                code=scale_def["code"],
                name=scale_def["name"],
                target=scale_def["target"],
                description=scale_def["description"],
                interpretation=json.dumps(scale_def["interpretation"], ensure_ascii=False),
                sort_order=idx,
            )
            db.session.add(scale)
            db.session.flush()
        existing_qs = db.session.query(ScaleQuestion).filter_by(scale_id=scale.id).count()
        if existing_qs == 0:
            for q_idx, q in enumerate(scale_def["questions"]):
                db.session.add(
                    ScaleQuestion(
                        scale_id=scale.id,
                        sort_order=q_idx,
                        content=q["content"],
                        options=json.dumps(q["options"], ensure_ascii=False),
                        dimension=q.get("dimension"),
                        reverse=q.get("reverse", False),
                    )
                )
            count += 1
    db.session.commit()
    return count


def list_scales() -> list[dict[str, Any]]:
    rows = db.session.query(Scale).filter_by(is_deleted=False).order_by(Scale.sort_order).all()
    out: list[dict[str, Any]] = []
    for s in rows:
        count = db.session.query(ScaleQuestion).filter_by(scale_id=s.id).count()
        out.append({
            "id": s.id,
            "code": s.code,
            "name": s.name,
            "target": s.target,
            "description": s.description,
            "question_count": count,
            "sort_order": s.sort_order,
        })
    return out


def get_scale_with_questions(scale_id: int) -> dict[str, Any]:
    scale = db.session.get(Scale, scale_id)
    if not scale or scale.is_deleted:
        raise NotFoundError("量表不存在")
    return {
        "id": scale.id,
        "code": scale.code,
        "name": scale.name,
        "target": scale.target,
        "description": scale.description,
        "interpretation": json.loads(scale.interpretation) if scale.interpretation else [],
        "questions": [
            {
                "id": q.id,
                "sort_order": q.sort_order,
                "content": q.content,
                "options": json.loads(q.options) if q.options else [],
                "dimension": q.dimension,
                "reverse": q.reverse,
            }
            for q in scale.questions
        ],
    }


# ================= 测评 =================

def submit_assessment(
    student_id: int, scale_id: int, answers: dict[int, int], operator_id: int | None
) -> dict[str, Any]:
    student = db.session.get(Student, student_id)
    if not student or student.is_deleted:
        raise NotFoundError("学生不存在")
    scale = db.session.get(Scale, scale_id)
    if not scale or scale.is_deleted:
        raise NotFoundError("量表不存在")

    questions = list(scale.questions)
    if not questions:
        raise ValidationError("该量表题目为空")

    # 计算每题分数（考虑反向计分）
    total = 0.0
    dim_totals: dict[str, float] = {}
    for q in questions:
        opt_list = json.loads(q.options) if q.options else []
        max_score = max((o.get("score", 0) for o in opt_list), default=0)
        raw = answers.get(q.id)
        if raw is None:
            raw = answers.get(str(q.id))  # 兼容字符串 key
        if raw is None:
            continue
        score = float(raw)
        if q.reverse:
            score = max_score - score
        total += score
        if q.dimension:
            dim_totals[q.dimension] = dim_totals.get(q.dimension, 0.0) + score

    # 查解释区间
    bins = json.loads(scale.interpretation) if scale.interpretation else []
    level, color, advice = "未评级", "gray", ""
    for b in bins:
        if b["min"] <= total <= b["max"]:
            level, color, advice = b["level"], b.get("color", "gray"), b.get("advice", "")
            break

    assess = ScaleAssessment(
        student_id=student_id,
        scale_id=scale_id,
        operator_id=operator_id,
        answers=json.dumps({str(k): v for k, v in answers.items()}, ensure_ascii=False),
        total_score=total,
        dimension_scores=json.dumps(dim_totals, ensure_ascii=False) if dim_totals else None,
        level=level,
        level_color=color,
        advice=advice,
        completed_at=datetime.utcnow(),
    )
    db.session.add(assess)
    db.session.flush()

    # 写情绪时序（按心理健康指数：满分 100，分数越高心理越不健康，需要反转）
    max_possible = sum(
        max((o.get("score", 0) for o in json.loads(q.options)), default=0) for q in questions
    )
    health_score = max(0, 100 - int(total / max(1, max_possible) * 100))
    _upsert_emotion_timeline(
        student_id=student_id,
        on_date=date.today(),
        score=float(health_score),
        polarity="负面" if color in ("red", "purple") else ("中性" if color == "orange" else "正面"),
        risk_level={"red": "high", "purple": "high", "orange": "medium", "blue": "low"}.get(color, "none"),
        source="scale",
        note=f"{scale.code} {level}",
    )

    db.session.commit()
    return serialize_assessment(assess)


def list_assessments(
    student_id: int | None = None, scale_id: int | None = None, limit: int = 50
) -> list[dict[str, Any]]:
    q = db.session.query(ScaleAssessment)
    if student_id:
        q = q.filter_by(student_id=student_id)
    if scale_id:
        q = q.filter_by(scale_id=scale_id)
    rows = q.order_by(ScaleAssessment.id.desc()).limit(limit).all()
    return [serialize_assessment(r) for r in rows]


def serialize_assessment(a: ScaleAssessment) -> dict[str, Any]:
    scale = db.session.get(Scale, a.scale_id)
    student = db.session.get(Student, a.student_id)
    return {
        "id": a.id,
        "student_id": a.student_id,
        "student_name": student.name if student else None,
        "scale_id": a.scale_id,
        "scale_code": scale.code if scale else None,
        "scale_name": scale.name if scale else None,
        "total_score": a.total_score,
        "level": a.level,
        "level_color": a.level_color,
        "advice": a.advice,
        "dimension_scores": json.loads(a.dimension_scores) if a.dimension_scores else {},
        "completed_at": a.completed_at.strftime("%Y-%m-%d %H:%M:%S") if a.completed_at else None,
    }


# ================= 文本分析 =================

def analyze_text(
    student_id: int, content: str, title: str | None, operator_id: int | None
) -> dict[str, Any]:
    if not content or len(content.strip()) < 5:
        raise ValidationError("文本内容过短")
    student = db.session.get(Student, student_id)
    if not student or student.is_deleted:
        raise NotFoundError("学生不存在")

    client = get_ai_client()
    sentiment = client.text_sentiment(content).get("data") or {}
    summary = client.text_summarize(content).get("data") or {}

    rec = TextAnalysis(
        student_id=student_id,
        operator_id=operator_id,
        title=title,
        content=content,
        polarity=sentiment.get("polarity", "中性"),
        risk_level=sentiment.get("risk_level", "none"),
        risk_keywords=json.dumps(sentiment.get("risk_keywords", []), ensure_ascii=False),
        emotion_tags=json.dumps(sentiment.get("emotion_tags", []), ensure_ascii=False),
        summary=summary.get("summary"),
        suggestion=summary.get("suggestion"),
        raw_response=json.dumps(
            {"sentiment": sentiment, "summary": summary}, ensure_ascii=False
        ),
    )
    db.session.add(rec)
    db.session.flush()

    # 情绪时序：根据极性+风险等级
    score_map = {"正面": 85, "中性": 75, "负面": 55}
    risk_penalty = {"none": 0, "low": 5, "medium": 15, "high": 30}
    hs = max(20, score_map.get(rec.polarity, 70) - risk_penalty.get(rec.risk_level, 0))
    _upsert_emotion_timeline(
        student_id, date.today(), float(hs),
        rec.polarity, rec.risk_level, "text", title or "文本分析"
    )

    db.session.commit()
    return serialize_text_analysis(rec)


def list_text_analyses(student_id: int, limit: int = 50) -> list[dict[str, Any]]:
    rows = (
        db.session.query(TextAnalysis)
        .filter_by(student_id=student_id)
        .order_by(TextAnalysis.id.desc())
        .limit(limit)
        .all()
    )
    return [serialize_text_analysis(r) for r in rows]


def serialize_text_analysis(r: TextAnalysis) -> dict[str, Any]:
    return {
        "id": r.id,
        "student_id": r.student_id,
        "title": r.title,
        "content": r.content,
        "polarity": r.polarity,
        "risk_level": r.risk_level,
        "risk_keywords": json.loads(r.risk_keywords) if r.risk_keywords else [],
        "emotion_tags": json.loads(r.emotion_tags) if r.emotion_tags else [],
        "summary": r.summary,
        "suggestion": r.suggestion,
        "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    }


# ================= AI 对话 =================

def start_conversation(student_id: int, operator_id: int | None, title: str | None) -> dict:
    student = db.session.get(Student, student_id)
    if not student or student.is_deleted:
        raise NotFoundError("学生不存在")
    conv = AIConversation(
        student_id=student_id,
        operator_id=operator_id,
        title=title or f"{student.name} 的对话",
    )
    db.session.add(conv)
    db.session.commit()
    return serialize_conversation(conv)


def post_message(conv_id: int, user_content: str) -> dict[str, Any]:
    conv = db.session.get(AIConversation, conv_id)
    if not conv:
        raise NotFoundError("对话不存在")
    if not user_content.strip():
        raise ValidationError("消息内容不能为空")
    # 写用户消息
    user_msg = AIConversationMessage(conversation_id=conv_id, role="user", content=user_content)
    db.session.add(user_msg)
    db.session.flush()

    # 收集历史
    history = (
        db.session.query(AIConversationMessage)
        .filter_by(conversation_id=conv_id)
        .order_by(AIConversationMessage.id)
        .all()
    )
    messages = [{"role": m.role, "content": m.content} for m in history]

    resp = get_ai_client().text_chat(messages).get("data") or {}
    reply = resp.get("reply", "我在听")
    risk = resp.get("risk_level", "none")
    keywords = resp.get("risk_keywords", [])

    assistant_msg = AIConversationMessage(
        conversation_id=conv_id,
        role="assistant",
        content=reply,
        risk_level=risk,
        risk_keywords=json.dumps(keywords, ensure_ascii=False),
    )
    db.session.add(assistant_msg)

    # 更新对话最高风险
    risk_order = {"none": 0, "low": 1, "medium": 2, "high": 3}
    if risk_order.get(risk, 0) > risk_order.get(conv.risk_level, 0):
        conv.risk_level = risk
    conv.message_count = (conv.message_count or 0) + 2
    db.session.commit()

    # 若 high，写入情绪时序并打标
    if risk == "high":
        _upsert_emotion_timeline(
            conv.student_id, date.today(), 30.0, "负面", "high", "chat", "AI 对话检测到高风险"
        )
        logger.warning(f"学生 {conv.student_id} AI 对话触发高风险：{keywords}")

    return {
        "user_message": _serialize_message(user_msg),
        "assistant_message": _serialize_message(assistant_msg),
        "conversation": serialize_conversation(conv),
    }


def list_conversations(student_id: int | None = None) -> list[dict]:
    q = db.session.query(AIConversation)
    if student_id:
        q = q.filter_by(student_id=student_id)
    rows = q.order_by(AIConversation.id.desc()).limit(100).all()
    return [serialize_conversation(r) for r in rows]


def get_conversation_detail(conv_id: int) -> dict:
    conv = db.session.get(AIConversation, conv_id)
    if not conv:
        raise NotFoundError("对话不存在")
    msgs = (
        db.session.query(AIConversationMessage)
        .filter_by(conversation_id=conv_id)
        .order_by(AIConversationMessage.id)
        .all()
    )
    return {
        **serialize_conversation(conv),
        "messages": [_serialize_message(m) for m in msgs],
    }


def serialize_conversation(c: AIConversation) -> dict:
    return {
        "id": c.id,
        "student_id": c.student_id,
        "title": c.title,
        "risk_level": c.risk_level,
        "message_count": c.message_count,
        "created_at": c.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    }


def _serialize_message(m: AIConversationMessage) -> dict:
    return {
        "id": m.id,
        "role": m.role,
        "content": m.content,
        "risk_level": m.risk_level,
        "risk_keywords": json.loads(m.risk_keywords) if m.risk_keywords else [],
        "created_at": m.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    }


# ================= 情绪时序 =================

def _upsert_emotion_timeline(
    student_id: int,
    on_date: date,
    score: float,
    polarity: str,
    risk_level: str,
    source: str,
    note: str | None,
) -> None:
    existing = (
        db.session.query(EmotionTimeline)
        .filter_by(student_id=student_id, record_date=on_date, source=source)
        .first()
    )
    if existing:
        # 用更严重的结果覆盖（分数更低）
        if score < existing.score:
            existing.score = score
            existing.polarity = polarity
            existing.risk_level = risk_level
            existing.note = note
    else:
        db.session.add(
            EmotionTimeline(
                student_id=student_id,
                record_date=on_date,
                score=score,
                polarity=polarity,
                risk_level=risk_level,
                source=source,
                note=note,
            )
        )


def student_emotion_timeline(student_id: int, days: int = 30) -> list[dict]:
    since = date.today() - timedelta(days=days)
    rows = (
        db.session.query(EmotionTimeline)
        .filter(EmotionTimeline.student_id == student_id, EmotionTimeline.record_date >= since)
        .order_by(EmotionTimeline.record_date)
        .all()
    )
    return [
        {
            "date": r.record_date.strftime("%Y-%m-%d"),
            "score": r.score,
            "polarity": r.polarity,
            "risk_level": r.risk_level,
            "source": r.source,
            "note": r.note,
        }
        for r in rows
    ]


def student_psychology_profile(student_id: int) -> dict:
    """学生心理档案：最近量表 + 最近文本 + 最近对话 + 情绪曲线。"""
    student = db.session.get(Student, student_id)
    if not student or student.is_deleted:
        raise NotFoundError("学生不存在")
    recent_assess = list_assessments(student_id=student_id, limit=10)
    recent_text = list_text_analyses(student_id, limit=10)
    recent_conv = list_conversations(student_id)[:10]
    timeline = student_emotion_timeline(student_id, days=60)
    latest_score = timeline[-1]["score"] if timeline else 80.0
    risk_levels = [r["risk_level"] for r in timeline]
    order = {"none": 0, "low": 1, "medium": 2, "high": 3}
    top_risk = max(risk_levels, key=lambda x: order.get(x, 0)) if risk_levels else "none"
    return {
        "student": {"id": student.id, "name": student.name, "class_id": student.class_id},
        "latest_score": latest_score,
        "top_risk": top_risk,
        "assessments": recent_assess,
        "text_analyses": recent_text,
        "conversations": recent_conv,
        "timeline": timeline,
    }
