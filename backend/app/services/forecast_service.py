"""情绪趋势预测服务。

简化实现：基于历史时序的指数平滑 + 趋势项。
对于演示目的足够直观，技术上扩展到 LSTM 也只需替换内部计算。
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from ..extensions import db
from ..models import EmotionTimeline, Student


def _holt_double_exponential(series: list[float], alpha: float = 0.5, beta: float = 0.3, horizon: int = 7) -> list[float]:
    """Holt 双参数指数平滑法预测未来 horizon 步。"""
    if not series:
        return [80.0] * horizon
    if len(series) == 1:
        return [series[0]] * horizon

    level = series[0]
    trend = series[1] - series[0]
    for i in range(1, len(series)):
        new_level = alpha * series[i] + (1 - alpha) * (level + trend)
        new_trend = beta * (new_level - level) + (1 - beta) * trend
        level, trend = new_level, new_trend

    return [level + (i + 1) * trend for i in range(horizon)]


def predict_student_emotion(student_id: int, history_days: int = 30, horizon: int = 7) -> dict[str, Any]:
    student = db.session.get(Student, student_id)
    if not student or student.is_deleted:
        from ..utils.exceptions import NotFoundError

        raise NotFoundError("学生不存在")

    since = date.today() - timedelta(days=history_days)
    rows = (
        db.session.query(EmotionTimeline)
        .filter(EmotionTimeline.student_id == student_id, EmotionTimeline.record_date >= since)
        .order_by(EmotionTimeline.record_date)
        .all()
    )
    history = [(r.record_date.strftime("%Y-%m-%d"), float(r.score)) for r in rows]
    series = [v for _, v in history]

    forecast = _holt_double_exponential(series, horizon=horizon)
    forecast = [max(0, min(100, round(v, 1))) for v in forecast]

    today = date.today()
    forecast_dates = [(today + timedelta(days=i + 1)).strftime("%Y-%m-%d") for i in range(horizon)]

    # 智能解读
    avg_recent = sum(series[-7:]) / max(1, min(7, len(series))) if series else 80.0
    avg_forecast = sum(forecast) / len(forecast) if forecast else 80.0
    diff = avg_forecast - avg_recent

    if diff < -5:
        trend_label = "未来 7 天预测呈明显下降趋势，建议尽快关注"
        trend_color = "red"
    elif diff < -2:
        trend_label = "未来 7 天预测略有下降，建议关注"
        trend_color = "orange"
    elif diff > 5:
        trend_label = "未来 7 天预测呈明显上升趋势"
        trend_color = "green"
    else:
        trend_label = "未来 7 天预测基本稳定"
        trend_color = "blue"

    # 风险阈值预警：预测中是否会跌破 50（危险线）
    risk_alert = any(v < 50 for v in forecast)

    return {
        "student": {"id": student.id, "name": student.name},
        "history": [{"date": d, "score": v} for d, v in history],
        "forecast": [{"date": d, "score": v} for d, v in zip(forecast_dates, forecast)],
        "avg_recent_7d": round(avg_recent, 1),
        "avg_forecast_7d": round(avg_forecast, 1),
        "trend_diff": round(diff, 1),
        "trend_label": trend_label,
        "trend_color": trend_color,
        "risk_alert": risk_alert,
        "method": "Holt 双参数指数平滑法（α=0.5, β=0.3）",
    }
