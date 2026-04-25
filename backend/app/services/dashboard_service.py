"""数据大屏聚合接口 service。"""

from __future__ import annotations

import json
import statistics
from datetime import date, datetime, timedelta

from sqlalchemy import func

from ..extensions import db
from ..services.video_service import BEHAVIOR_EIGHT_CN, _normalize_behavior_cn
from ..models import (
    AIConversation,
    Alert,
    AnalysisTask,
    BehaviorRecord,
    Clazz,
    EmotionRecord,
    EmotionTimeline,
    Grade,
    School,
    ScaleAssessment,
    Student,
    Teacher,
    TextAnalysis,
)


def overview() -> dict:
    """大屏顶部总览。"""
    today = date.today()
    yesterday = today - timedelta(days=1)
    last_week = today - timedelta(days=7)

    school_count = db.session.query(School).filter_by(is_deleted=False).count()
    grade_count = db.session.query(Grade).filter_by(is_deleted=False).count()
    class_count = db.session.query(Clazz).filter_by(is_deleted=False).count()
    student_count = db.session.query(Student).filter_by(is_deleted=False).count()
    teacher_count = db.session.query(Teacher).filter_by(is_deleted=False).count()

    today_alerts = (
        db.session.query(Alert)
        .filter(func.date(Alert.created_at) == today)
        .count()
    )
    open_alerts = (
        db.session.query(Alert)
        .filter(Alert.status.in_(["open", "acknowledged"]))
        .count()
    )

    week_videos = (
        db.session.query(AnalysisTask)
        .filter(func.date(AnalysisTask.created_at) >= last_week)
        .count()
    )
    week_assessments = (
        db.session.query(ScaleAssessment)
        .filter(func.date(ScaleAssessment.created_at) >= last_week)
        .count()
    )

    # 心理健康指数（学校平均，过去 30 天平均）
    last_month = today - timedelta(days=30)
    rows = (
        db.session.query(EmotionTimeline.score)
        .filter(EmotionTimeline.record_date >= last_month)
        .all()
    )
    psy_index = round(statistics.mean(r[0] for r in rows), 1) if rows else 85.0

    return {
        "school_count": school_count,
        "grade_count": grade_count,
        "class_count": class_count,
        "student_count": student_count,
        "teacher_count": teacher_count,
        "today_alerts": today_alerts,
        "open_alerts": open_alerts,
        "week_videos": week_videos,
        "week_assessments": week_assessments,
        "psy_index": psy_index,
    }


def alert_distribution() -> dict:
    rows = db.session.query(Alert.level, func.count(Alert.id)).group_by(Alert.level).all()
    by_level: dict[str, int] = {"green": 0, "yellow": 0, "orange": 0, "red": 0}
    for level, cnt in rows:
        by_level[level] = cnt
    return {"by_level": by_level}


def class_engagement(top_n: int = 8) -> list[dict]:
    """各班级综合活力指数（基于近期心理时序均分）。"""
    today = date.today()
    last_month = today - timedelta(days=30)

    classes = db.session.query(Clazz).filter_by(is_deleted=False).all()
    items: list[dict] = []
    for c in classes:
        student_ids = [
            s[0]
            for s in db.session.query(Student.id).filter_by(class_id=c.id, is_deleted=False).all()
        ]
        if not student_ids:
            continue
        scores = (
            db.session.query(EmotionTimeline.score)
            .filter(
                EmotionTimeline.student_id.in_(student_ids),
                EmotionTimeline.record_date >= last_month,
            )
            .all()
        )
        avg = round(statistics.mean(r[0] for r in scores), 1) if scores else 80.0
        items.append({
            "class_id": c.id,
            "class_name": f"{c.grade.name if c.grade else ''}{c.name}",
            "student_count": len(student_ids),
            "engagement": avg,
        })
    items.sort(key=lambda x: x["engagement"], reverse=True)
    return items[:top_n]


def emotion_overview_30d() -> list[dict]:
    """近 30 天全体学生情绪曲线。"""
    today = date.today()
    last_month = today - timedelta(days=30)
    rows = (
        db.session.query(EmotionTimeline.record_date, func.avg(EmotionTimeline.score))
        .filter(EmotionTimeline.record_date >= last_month)
        .group_by(EmotionTimeline.record_date)
        .order_by(EmotionTimeline.record_date)
        .all()
    )
    return [{"date": r[0].strftime("%m-%d"), "score": round(float(r[1]), 1)} for r in rows]


def behavior_distribution_today() -> dict:
    """今日各类行为分布（标准八类；历史 label 会归一）。"""
    today = date.today()
    rows = (
        db.session.query(
            BehaviorRecord.label_cn,
            BehaviorRecord.label,
            func.count(BehaviorRecord.id),
        )
        .filter(func.date(BehaviorRecord.created_at) == today)
        .group_by(BehaviorRecord.label_cn, BehaviorRecord.label)
        .all()
    )
    merged: dict[str, int] = {cn: 0 for cn in BEHAVIOR_EIGHT_CN}
    for label_cn, label, cnt in rows:
        nk = _normalize_behavior_cn(label_cn, label)
        merged[nk] = merged.get(nk, 0) + int(cnt)

    items = [{"name": k, "value": v} for k, v in merged.items() if v > 0]
    if not items:
        # 无今日记录时的演示数据（与课堂标准八类一致）
        return {
            "items": [
                {"name": "抬头听课", "value": 520},
                {"name": "低头写字", "value": 180},
                {"name": "低头看书", "value": 140},
                {"name": "举手", "value": 95},
                {"name": "站立", "value": 72},
                {"name": "转头", "value": 48},
                {"name": "小组讨论", "value": 36},
                {"name": "教师指导", "value": 24},
            ]
        }
    return {"items": items}


def emotion_distribution_today() -> dict:
    today = date.today()
    rows = (
        db.session.query(EmotionRecord.emotion_cn, func.count(EmotionRecord.id))
        .filter(func.date(EmotionRecord.created_at) == today)
        .group_by(EmotionRecord.emotion_cn)
        .all()
    )
    if not rows:
        return {
            "items": [
                {"name": "中性", "value": 750},
                {"name": "高兴", "value": 480},
                {"name": "专注", "value": 320},
                {"name": "惊讶", "value": 110},
                {"name": "疲惫", "value": 70},
                {"name": "悲伤", "value": 40},
                {"name": "愤怒", "value": 12},
            ]
        }
    return {"items": [{"name": r[0], "value": r[1]} for r in rows]}


def recent_alerts(limit: int = 8) -> list[dict]:
    rows = db.session.query(Alert).order_by(Alert.id.desc()).limit(limit).all()
    out = []
    for a in rows:
        student = db.session.get(Student, a.student_id)
        out.append({
            "id": a.id,
            "student_name": student.name if student else "未知",
            "level": a.level,
            "score": a.score,
            "title": a.title,
            "created_at": a.created_at.strftime("%H:%M"),
            "first_reason": (json.loads(a.reasons)[0] if a.reasons else "—"),
        })
    return out


def top_risk_students(limit: int = 10) -> list[dict]:
    """风险评分最高的学生（依 alert.score）。"""
    rows = (
        db.session.query(Alert)
        .filter(Alert.status.in_(["open", "acknowledged"]))
        .order_by(Alert.score.desc())
        .limit(limit)
        .all()
    )
    out = []
    for a in rows:
        student = db.session.get(Student, a.student_id)
        out.append({
            "student_id": a.student_id,
            "student_name": student.name if student else "未知",
            "level": a.level,
            "score": round(a.score, 1),
        })
    return out
