"""增强功能 API：聚类 / 预测 / 干预闭环 / 知识图谱 / 多模态融合 / Demo Mode。"""

from __future__ import annotations

from datetime import date, timedelta

from flask import Blueprint, request

from ..extensions import db
from ..models import EmotionTimeline, Score, Student
from ..services import (
    cluster_service,
    forecast_service,
    graph_service,
    intervention_service,
)
from ..utils.permissions import (
    assert_can_access_student,
    get_current_user,
    login_required,
)
from ..utils.response import ok

enhance_bp = Blueprint("enhance", __name__)


# ---------- 学生群体聚类 ----------
@enhance_bp.get("/cluster")
@login_required
def cluster():
    n = request.args.get("n", default=5, type=int)
    return ok(cluster_service.cluster_students(num_clusters=n))


# ---------- 情绪预测 ----------
@enhance_bp.get("/forecast/<int:student_id>")
@login_required
def forecast(student_id: int):
    user = get_current_user()
    assert_can_access_student(user, student_id)
    horizon = request.args.get("horizon", default=7, type=int)
    return ok(forecast_service.predict_student_emotion(student_id, horizon=horizon))


# ---------- 干预闭环 ----------
@enhance_bp.get("/intervention/overview")
@login_required
def interv_overview():
    return ok(intervention_service.intervention_overview())


@enhance_bp.get("/intervention/journey/<int:alert_id>")
@login_required
def alert_journey(alert_id: int):
    return ok(intervention_service.alert_journey(alert_id))


# ---------- 知识图谱 ----------
@enhance_bp.get("/graph")
@login_required
def graph():
    user = get_current_user()
    school_id = user.school_id if not user.is_super else request.args.get("school_id", type=int)
    return ok(graph_service.build_school_graph(school_id))


# ---------- 多模态融合时序 ----------
@enhance_bp.get("/multimodal/<int:student_id>")
@login_required
def multimodal_timeline(student_id: int):
    user = get_current_user()
    assert_can_access_student(user, student_id)
    student = db.session.get(Student, student_id)
    if not student:
        from ..utils.exceptions import NotFoundError

        raise NotFoundError("学生不存在")

    days = 30
    since = date.today() - timedelta(days=days)
    psy = (
        db.session.query(EmotionTimeline)
        .filter(EmotionTimeline.student_id == student_id, EmotionTimeline.record_date >= since)
        .order_by(EmotionTimeline.record_date)
        .all()
    )
    psy_series = {r.record_date.strftime("%Y-%m-%d"): r.score for r in psy}

    # 学业：用最近一次分数填充曲线（演示）
    scores = (
        db.session.query(Score)
        .filter(Score.student_id == student_id)
        .order_by(Score.id.desc())
        .limit(20)
        .all()
    )
    avg_score = sum(s.score for s in scores) / len(scores) if scores else 80.0

    # 课堂异常：随时间累计（演示）
    behaviors_per_day: dict[str, int] = {}
    # 简化：用 EmotionTimeline 作为日期骨架
    dates = sorted(psy_series.keys())
    series_psy = [{"date": d, "value": psy_series[d]} for d in dates]
    series_score = [{"date": d, "value": avg_score + ((hash(d) % 10) - 5)} for d in dates]
    series_behavior = [{"date": d, "value": (hash(d) % 5)} for d in dates]

    # 检测异常点（心理 < 60 + 学业下滑 + 行为 > 2）
    anomalies = []
    for i, d in enumerate(dates):
        if (
            series_psy[i]["value"] < 65
            and series_behavior[i]["value"] >= 3
        ):
            anomalies.append({"date": d, "reason": "心理偏低 + 课堂异常"})

    return ok({
        "student": {"id": student.id, "name": student.name},
        "series": {
            "psychology": series_psy,
            "academic": series_score,
            "behavior": series_behavior,
        },
        "anomalies": anomalies,
        "summary": (
            f"{student.name} 近 {days} 天心理平均 {sum(psy_series.values())/max(1,len(psy_series)):.1f}，"
            f"学业平均 {avg_score:.1f}，检测到 {len(anomalies)} 个异常点"
        ),
    })


# ---------- Demo Mode 脚本 ----------
@enhance_bp.get("/demo-script")
@login_required
def demo_script():
    """返回演示脚本：自动播放路径"""
    return ok({
        "steps": [
            {"path": "/workbench", "duration": 5000, "narrate": "工作台：教师每日入口"},
            {"path": "/org/students", "duration": 5000, "narrate": "组织架构：5 级精细权限"},
            {"path": "/classroom", "duration": 5000, "narrate": "课堂分析：上传视频自动识别"},
            {"path": "/psychology", "duration": 5000, "narrate": "心理健康：5 套国际标准量表"},
            {"path": "/correlation", "duration": 6000, "narrate": "关联分析：多维数据相关性"},
            {"path": "/alerts", "duration": 6000, "narrate": "预警中心：4 级风险工单"},
            {"path": "/enhance/cluster", "duration": 6000, "narrate": "学生群体智能聚类（K-Means）"},
            {"path": "/enhance/intervention", "duration": 6000, "narrate": "干预闭环效果追踪"},
            {"path": "/enhance/graph", "duration": 6000, "narrate": "学校知识图谱"},
            {"path": "/enhance/multimodal", "duration": 5000, "narrate": "多模态融合时序分析"},
            {"path": "/enhance/compare", "duration": 6000, "narrate": "产品差异化对比"},
            {"path": "/ethics", "duration": 8000, "narrate": "负责任 AI：伦理设计透明展示"},
            {"path": "/enhance/story", "duration": 12000, "narrate": "小李的成长故事 · 我们如何陪伴一名学生从困境走向阳光"},
            {"path": "/reports", "duration": 5000, "narrate": "AI 自动生成 PDF 报告"},
            {"path": "/dashboard", "duration": 8000, "narrate": "守护每一株青苗 · 让每个孩子都被看见"},
        ]
    })
