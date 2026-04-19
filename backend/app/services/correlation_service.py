"""关联分析与预警计算。

核心算法：
1. 对每名学生汇总最近的多维数据：
   - 学业：成绩平均分 / 排名 / 趋势
   - 心理：最近量表评级 / 最近文本风险等级 / AI 对话风险
   - 课堂：最近视频参与度 / 玩手机/趴桌等异常行为
   - 情绪时序：最近 7/30 天平均健康指数
2. 加权计算综合风险评分（0-100）
3. 自动生成或更新预警工单（支持归因解释）
"""

from __future__ import annotations

import json
import statistics
from datetime import date, datetime, timedelta
from typing import Any

from loguru import logger
from sqlalchemy import func

from ..extensions import db
from ..models import (
    Alert,
    BehaviorRecord,
    EmotionTimeline,
    InterventionRecord,
    Score,
    Student,
    TextAnalysis,
    AIConversation,
    ScaleAssessment,
)


# ===== 多维数据采集 =====

def collect_student_features(student_id: int) -> dict[str, Any]:
    """汇总单个学生的多维特征。"""
    student = db.session.get(Student, student_id)
    if not student or student.is_deleted:
        return {}

    # 心理：最近 30 天情绪时序
    since30 = date.today() - timedelta(days=30)
    since7 = date.today() - timedelta(days=7)
    timeline = (
        db.session.query(EmotionTimeline)
        .filter(EmotionTimeline.student_id == student_id, EmotionTimeline.record_date >= since30)
        .all()
    )
    scores30 = [t.score for t in timeline]
    scores7 = [t.score for t in timeline if t.record_date >= since7]

    # 量表
    last_assess = (
        db.session.query(ScaleAssessment)
        .filter_by(student_id=student_id)
        .order_by(ScaleAssessment.id.desc())
        .first()
    )

    # 文本：最近一次
    last_text = (
        db.session.query(TextAnalysis)
        .filter_by(student_id=student_id)
        .order_by(TextAnalysis.id.desc())
        .first()
    )

    # 对话：最高风险
    convs = db.session.query(AIConversation).filter_by(student_id=student_id).all()
    risk_order = {"none": 0, "low": 1, "medium": 2, "high": 3}
    conv_risk = "none"
    for c in convs:
        if risk_order.get(c.risk_level, 0) > risk_order.get(conv_risk, 0):
            conv_risk = c.risk_level

    # 学业：最近 5 次成绩
    scores = (
        db.session.query(Score)
        .filter_by(student_id=student_id)
        .order_by(Score.id.desc())
        .limit(10)
        .all()
    )
    score_values = [s.score for s in scores]

    # 课堂：玩手机 / 趴桌
    behaviors = (
        db.session.query(BehaviorRecord)
        .filter_by(student_id=student_id)
        .order_by(BehaviorRecord.id.desc())
        .limit(500)
        .all()
    )
    phone_cnt = sum(1 for b in behaviors if b.label in ("cell phone", "using_phone"))
    sleep_cnt = sum(1 for b in behaviors if b.label in ("sleeping", "lying"))

    return {
        "student_id": student_id,
        "student_name": student.name,
        "class_id": student.class_id,
        "psy_score_avg_30d": round(statistics.mean(scores30), 1) if scores30 else 80.0,
        "psy_score_avg_7d": round(statistics.mean(scores7), 1) if scores7 else 80.0,
        "psy_score_min_30d": min(scores30) if scores30 else 80.0,
        "scale_level": last_assess.level if last_assess else "未测评",
        "scale_color": last_assess.level_color if last_assess else "gray",
        "scale_score": last_assess.total_score if last_assess else 0.0,
        "text_polarity": last_text.polarity if last_text else "未分析",
        "text_risk_level": last_text.risk_level if last_text else "none",
        "conversation_risk": conv_risk,
        "score_avg": round(statistics.mean(score_values), 1) if score_values else 80.0,
        "score_trend": _trend(score_values),
        "score_count": len(score_values),
        "classroom_phone_count": phone_cnt,
        "classroom_sleep_count": sleep_cnt,
    }


def _trend(values: list[float]) -> str:
    if len(values) < 2:
        return "稳定"
    recent = values[: max(1, len(values) // 2)]
    older = values[len(values) // 2 :]
    if not recent or not older:
        return "稳定"
    diff = statistics.mean(recent) - statistics.mean(older)
    if diff > 5:
        return "上升"
    if diff < -5:
        return "下降"
    return "稳定"


# ===== 风险评分 =====

def compute_risk_score(features: dict) -> tuple[float, str, list[str]]:
    """根据特征计算风险评分（0-100，越高越危险）。

    返回：(score, level, reasons)
    """
    score = 0.0
    reasons: list[str] = []

    # 心理健康指数（占 35%）
    psy = features.get("psy_score_avg_30d", 80.0)
    if psy < 50:
        score += 35
        reasons.append(f"近 30 天心理健康指数偏低（{psy:.0f}/100）")
    elif psy < 65:
        score += 22
        reasons.append(f"近 30 天心理健康指数较低（{psy:.0f}/100）")
    elif psy < 75:
        score += 10

    # 量表评级（占 20%）
    color = features.get("scale_color", "gray")
    color_score = {"green": 0, "blue": 5, "orange": 12, "red": 18, "purple": 20, "gray": 0}
    s = color_score.get(color, 0)
    if s:
        score += s
        reasons.append(f"最近量表评级：{features.get('scale_level', '未知')}")

    # 文本风险（占 15%）
    text_risk = features.get("text_risk_level", "none")
    text_score = {"none": 0, "low": 5, "medium": 10, "high": 15}.get(text_risk, 0)
    if text_score:
        score += text_score
        reasons.append(f"最近文本检测到 {text_risk} 风险")

    # 对话风险（占 15%）
    conv_risk = features.get("conversation_risk", "none")
    conv_score = {"none": 0, "low": 4, "medium": 9, "high": 15}.get(conv_risk, 0)
    if conv_score:
        score += conv_score
        reasons.append(f"AI 对话累计风险：{conv_risk}")

    # 学业（占 10%）
    score_avg = features.get("score_avg", 80.0)
    trend = features.get("score_trend", "稳定")
    if score_avg < 60:
        score += 8
        reasons.append(f"学业平均分较低（{score_avg:.0f}）")
    if trend == "下降":
        score += 4
        reasons.append("学业成绩呈下降趋势")

    # 课堂行为（占 5%）
    phone_cnt = features.get("classroom_phone_count", 0)
    sleep_cnt = features.get("classroom_sleep_count", 0)
    if phone_cnt > 5 or sleep_cnt > 5:
        score += 5
        reasons.append(f"课堂中检测到玩手机 {phone_cnt} 次、趴桌 {sleep_cnt} 次")

    score = min(100.0, score)
    if score >= 60:
        level = "red"
    elif score >= 40:
        level = "orange"
    elif score >= 20:
        level = "yellow"
    else:
        level = "green"

    if not reasons:
        reasons.append("近期数据均处于正常范围")
    return score, level, reasons


def upsert_alert(student_id: int, score: float, level: str, reasons: list[str], sources: list[str]) -> Alert | None:
    """创建/更新预警。green 不创建工单。"""
    if level == "green":
        return None

    # 查最近一条同学生未关闭的预警
    existing = (
        db.session.query(Alert)
        .filter(Alert.student_id == student_id, Alert.status.in_(["open", "acknowledged"]))
        .order_by(Alert.id.desc())
        .first()
    )
    if existing:
        existing.level = level
        existing.score = score
        existing.title = f"{level.upper()} 级预警 · 综合评分 {score:.0f}"
        existing.reasons = json.dumps(reasons, ensure_ascii=False)
        existing.sources = json.dumps(sources, ensure_ascii=False)
        db.session.commit()
        return existing

    alert = Alert(
        student_id=student_id,
        level=level,
        score=score,
        title=f"{level.upper()} 级预警 · 综合评分 {score:.0f}",
        reasons=json.dumps(reasons, ensure_ascii=False),
        sources=json.dumps(sources, ensure_ascii=False),
        status="open",
    )
    db.session.add(alert)
    db.session.commit()
    logger.warning(f"新增 {level} 级预警：学生 {student_id} 评分 {score:.0f}")
    return alert


def recompute_alerts_for_visible(student_ids: list[int] | None) -> dict:
    """批量重算指定学生（None 则全量）的预警。"""
    q = db.session.query(Student).filter(Student.is_deleted.is_(False))
    if student_ids is not None:
        if not student_ids:
            return {"updated": 0, "alerts": []}
        q = q.filter(Student.id.in_(student_ids))
    students = q.all()

    created = 0
    updated_alerts: list[dict] = []
    for s in students:
        features = collect_student_features(s.id)
        score, level, reasons = compute_risk_score(features)
        sources = []
        if features.get("scale_color", "gray") not in ("gray",):
            sources.append("量表")
        if features.get("text_risk_level") != "none":
            sources.append("文本")
        if features.get("conversation_risk") != "none":
            sources.append("AI对话")
        if features.get("classroom_phone_count", 0) or features.get("classroom_sleep_count", 0):
            sources.append("课堂行为")
        if features.get("score_count", 0):
            sources.append("学业成绩")

        alert = upsert_alert(s.id, score, level, reasons, sources)
        if alert:
            created += 1
            updated_alerts.append(serialize_alert(alert))
    return {"processed": len(students), "alerts_count": created, "alerts": updated_alerts[:50]}


# ===== 预警 CRUD =====

def list_alerts(
    level: str | None = None,
    status: str | None = None,
    student_ids: list[int] | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    q = db.session.query(Alert)
    if level:
        q = q.filter_by(level=level)
    if status:
        q = q.filter_by(status=status)
    if student_ids is not None:
        if not student_ids:
            return {"items": [], "total": 0, "page": page, "page_size": page_size}
        q = q.filter(Alert.student_id.in_(student_ids))
    total = q.count()
    items = (
        q.order_by(Alert.score.desc(), Alert.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "items": [serialize_alert(a) for a in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


def alert_stats(student_ids: list[int] | None) -> dict:
    q = db.session.query(Alert)
    if student_ids is not None:
        if not student_ids:
            return {"total": 0, "by_level": {}, "by_status": {}}
        q = q.filter(Alert.student_id.in_(student_ids))
    rows = q.all()
    by_level: dict[str, int] = {}
    by_status: dict[str, int] = {}
    for a in rows:
        by_level[a.level] = by_level.get(a.level, 0) + 1
        by_status[a.status] = by_status.get(a.status, 0) + 1
    return {"total": len(rows), "by_level": by_level, "by_status": by_status}


def acknowledge_alert(alert_id: int, user_id: int) -> dict:
    alert = db.session.get(Alert, alert_id)
    if not alert:
        from ..utils.exceptions import NotFoundError

        raise NotFoundError("预警不存在")
    alert.status = "acknowledged"
    alert.handler_id = user_id
    alert.acknowledged_at = datetime.utcnow()
    db.session.commit()
    return serialize_alert(alert)


def resolve_alert(alert_id: int, user_id: int, note: str | None) -> dict:
    alert = db.session.get(Alert, alert_id)
    if not alert:
        from ..utils.exceptions import NotFoundError

        raise NotFoundError("预警不存在")
    alert.status = "resolved"
    alert.handler_id = user_id
    alert.resolved_at = datetime.utcnow()
    if note:
        alert.note = note
    db.session.commit()
    return serialize_alert(alert)


def close_alert(alert_id: int, user_id: int) -> dict:
    alert = db.session.get(Alert, alert_id)
    if not alert:
        from ..utils.exceptions import NotFoundError

        raise NotFoundError("预警不存在")
    alert.status = "closed"
    alert.closed_at = datetime.utcnow()
    db.session.commit()
    return serialize_alert(alert)


def add_intervention(alert_id: int, user_id: int, action: str, summary: str, follow_up: str | None) -> dict:
    alert = db.session.get(Alert, alert_id)
    if not alert:
        from ..utils.exceptions import NotFoundError

        raise NotFoundError("预警不存在")
    rec = InterventionRecord(
        alert_id=alert_id,
        student_id=alert.student_id,
        operator_id=user_id,
        action=action,
        summary=summary,
        follow_up=follow_up,
    )
    db.session.add(rec)
    db.session.commit()
    return {
        "id": rec.id,
        "alert_id": rec.alert_id,
        "student_id": rec.student_id,
        "action": rec.action,
        "summary": rec.summary,
        "follow_up": rec.follow_up,
        "created_at": rec.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    }


def list_interventions(alert_id: int) -> list[dict]:
    rows = (
        db.session.query(InterventionRecord)
        .filter_by(alert_id=alert_id)
        .order_by(InterventionRecord.id.desc())
        .all()
    )
    return [
        {
            "id": r.id,
            "alert_id": r.alert_id,
            "student_id": r.student_id,
            "operator_id": r.operator_id,
            "action": r.action,
            "summary": r.summary,
            "follow_up": r.follow_up,
            "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        }
        for r in rows
    ]


def serialize_alert(a: Alert) -> dict:
    student = db.session.get(Student, a.student_id)
    return {
        "id": a.id,
        "student_id": a.student_id,
        "student_name": student.name if student else None,
        "class_id": student.class_id if student else None,
        "level": a.level,
        "score": a.score,
        "title": a.title,
        "reasons": json.loads(a.reasons) if a.reasons else [],
        "sources": json.loads(a.sources) if a.sources else [],
        "status": a.status,
        "handler_id": a.handler_id,
        "acknowledged_at": a.acknowledged_at.strftime("%Y-%m-%d %H:%M:%S") if a.acknowledged_at else None,
        "resolved_at": a.resolved_at.strftime("%Y-%m-%d %H:%M:%S") if a.resolved_at else None,
        "closed_at": a.closed_at.strftime("%Y-%m-%d %H:%M:%S") if a.closed_at else None,
        "created_at": a.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    }


# ===== 关联视图 =====

def correlation_matrix(student_ids: list[int] | None) -> dict:
    """全体学生的多维数据矩阵，前端用来画散点矩阵 / 相关性热力图。"""
    q = db.session.query(Student).filter(Student.is_deleted.is_(False))
    if student_ids is not None:
        if not student_ids:
            return {"items": [], "fields": []}
        q = q.filter(Student.id.in_(student_ids))
    students = q.all()
    items: list[dict] = []
    for s in students:
        f = collect_student_features(s.id)
        if not f:
            continue
        score, level, _ = compute_risk_score(f)
        items.append({
            "student_id": s.id,
            "name": s.name,
            "class_id": s.class_id,
            "psy_30d": f["psy_score_avg_30d"],
            "score_avg": f["score_avg"],
            "scale_score": f["scale_score"],
            "phone_count": f["classroom_phone_count"],
            "risk_score": round(score, 1),
            "level": level,
        })
    return {
        "items": items,
        "fields": [
            {"key": "psy_30d", "label": "心理健康指数"},
            {"key": "score_avg", "label": "学业平均分"},
            {"key": "scale_score", "label": "量表评分"},
            {"key": "phone_count", "label": "课堂玩手机次数"},
            {"key": "risk_score", "label": "综合风险评分"},
        ],
    }
