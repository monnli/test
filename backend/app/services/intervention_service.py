"""干预闭环效果追踪服务。"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from ..extensions import db
from ..models import Alert, EmotionTimeline, InterventionRecord, Student


def intervention_overview() -> dict[str, Any]:
    """全校干预效果总览。"""
    all_alerts = db.session.query(Alert).all()
    closed = [a for a in all_alerts if a.status in ("resolved", "closed")]
    open_or_ack = [a for a in all_alerts if a.status in ("open", "acknowledged")]

    success_rate = round(len(closed) / len(all_alerts) * 100, 1) if all_alerts else 0.0
    interv_count = db.session.query(InterventionRecord).count()

    # 平均处理时长（创建到 resolved）
    durations = []
    for a in all_alerts:
        if a.resolved_at and a.created_at:
            durations.append((a.resolved_at - a.created_at).total_seconds() / 3600)
    avg_hours = round(sum(durations) / len(durations), 1) if durations else 0.0

    by_action: dict[str, int] = {}
    for r in db.session.query(InterventionRecord).all():
        by_action[r.action] = by_action.get(r.action, 0) + 1

    return {
        "total_alerts": len(all_alerts),
        "open_count": len(open_or_ack),
        "resolved_count": len(closed),
        "success_rate": success_rate,
        "intervention_count": interv_count,
        "avg_hours": avg_hours,
        "by_action": [{"name": k, "value": v} for k, v in by_action.items()],
        "funnel": [
            {"name": "已发现", "value": len(all_alerts)},
            {"name": "已签收", "value": len([a for a in all_alerts if a.acknowledged_at])},
            {"name": "已介入", "value": interv_count},
            {"name": "已处理", "value": len(closed)},
        ],
    }


def alert_journey(alert_id: int) -> dict[str, Any]:
    """单条预警的完整生命周期 + 干预前后对比。"""
    alert = db.session.get(Alert, alert_id)
    if not alert:
        from ..utils.exceptions import NotFoundError

        raise NotFoundError("预警不存在")

    student = db.session.get(Student, alert.student_id)
    interventions = (
        db.session.query(InterventionRecord)
        .filter_by(alert_id=alert_id)
        .order_by(InterventionRecord.id)
        .all()
    )

    # 干预前后心理曲线对比（前 14 天 vs 后 14 天）
    pivot = (
        interventions[0].created_at.date()
        if interventions
        else (alert.acknowledged_at.date() if alert.acknowledged_at else date.today())
    )
    before_start = pivot - timedelta(days=14)
    after_end = pivot + timedelta(days=14)

    rows = (
        db.session.query(EmotionTimeline)
        .filter(
            EmotionTimeline.student_id == alert.student_id,
            EmotionTimeline.record_date >= before_start,
            EmotionTimeline.record_date <= after_end,
        )
        .order_by(EmotionTimeline.record_date)
        .all()
    )
    before = [r for r in rows if r.record_date < pivot]
    after = [r for r in rows if r.record_date >= pivot]
    avg_before = sum(r.score for r in before) / len(before) if before else 0.0
    avg_after = sum(r.score for r in after) / len(after) if after else 0.0

    timeline_events = [
        {"time": alert.created_at.strftime("%Y-%m-%d %H:%M"), "type": "open", "label": "AI 自动发现", "color": "#ef4444"},
    ]
    if alert.acknowledged_at:
        timeline_events.append({"time": alert.acknowledged_at.strftime("%Y-%m-%d %H:%M"), "type": "ack", "label": "心理老师签收", "color": "#f59e0b"})
    for r in interventions:
        timeline_events.append({"time": r.created_at.strftime("%Y-%m-%d %H:%M"), "type": "interv", "label": f"{r.action}：{r.summary[:30]}", "color": "#0ea5e9"})
    if alert.resolved_at:
        timeline_events.append({"time": alert.resolved_at.strftime("%Y-%m-%d %H:%M"), "type": "resolve", "label": "已处理", "color": "#22c55e"})
    if alert.closed_at:
        timeline_events.append({"time": alert.closed_at.strftime("%Y-%m-%d %H:%M"), "type": "close", "label": "已关闭", "color": "#94a3b8"})

    return {
        "alert": {
            "id": alert.id,
            "level": alert.level,
            "score": alert.score,
            "title": alert.title,
            "status": alert.status,
        },
        "student": {"id": student.id, "name": student.name} if student else None,
        "timeline_events": timeline_events,
        "interventions": [
            {
                "id": r.id,
                "action": r.action,
                "summary": r.summary,
                "follow_up": r.follow_up,
                "created_at": r.created_at.strftime("%Y-%m-%d %H:%M"),
            }
            for r in interventions
        ],
        "comparison": {
            "before": [{"date": r.record_date.strftime("%Y-%m-%d"), "score": r.score} for r in before],
            "after": [{"date": r.record_date.strftime("%Y-%m-%d"), "score": r.score} for r in after],
            "avg_before": round(avg_before, 1),
            "avg_after": round(avg_after, 1),
            "improvement": round(avg_after - avg_before, 1),
        },
    }
