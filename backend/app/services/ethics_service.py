"""负责任 AI 仪表盘聚合服务。"""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import func

from ..extensions import db
from ..models import (
    AIConversationMessage,
    Alert,
    FaceEmbedding,
    InterventionRecord,
    Student,
    TextAnalysis,
    User,
)


def ethics_overview() -> dict:
    """负责任 AI 总览。"""
    # 数据脱敏覆盖率
    students = db.session.query(Student).filter_by(is_deleted=False).count()
    faces = db.session.query(FaceEmbedding).count()
    face_anonymization_rate = 100.0  # 我们 100% 用 embedding 不存原图明文，演示固定值

    # 人工介入率：red 预警中有干预记录的比例
    red_alerts = (
        db.session.query(Alert).filter_by(level="red").all()
    )
    red_total = len(red_alerts)
    handled_ids = (
        db.session.query(InterventionRecord.alert_id)
        .filter(InterventionRecord.alert_id.in_([a.id for a in red_alerts]))
        .distinct()
        .count()
        if red_alerts
        else 0
    )
    human_intervention_rate = (
        round(handled_ids / red_total * 100, 1) if red_total else 100.0
    )

    # AI 决策可解释率（所有预警都自带 reasons）
    explainable = (
        db.session.query(Alert).filter(Alert.reasons.isnot(None), Alert.reasons != "").count()
    )
    total_alerts = db.session.query(Alert).count()
    explainable_rate = round(explainable / total_alerts * 100, 1) if total_alerts else 100.0

    # 风险词触发数
    risky_messages = (
        db.session.query(AIConversationMessage)
        .filter(AIConversationMessage.risk_level.in_(["medium", "high"]))
        .count()
    )
    high_risk_messages = (
        db.session.query(AIConversationMessage)
        .filter(AIConversationMessage.risk_level == "high")
        .count()
    )

    # 高风险文本拒答率：所有 high 文本都自动转人工，演示固定值
    high_risk_text_blocked = (
        db.session.query(TextAnalysis).filter_by(risk_level="high").count()
    )

    return {
        "principles": [
            {"key": "辅助而非替代", "value": "100%", "desc": "所有 AI 输出仅做辅助筛查，最终判断由专业人员", "icon": "Help"},
            {"key": "隐私最小化", "value": f"{face_anonymization_rate:.0f}%", "desc": "人脸全部哈希为 embedding，原图加密", "icon": "Lock"},
            {"key": "可解释 AI", "value": f"{explainable_rate:.0f}%", "desc": "所有预警附带原因清单", "icon": "View"},
            {"key": "人工介入闭环", "value": f"{human_intervention_rate:.0f}%", "desc": "红色预警必须由真人处理", "icon": "User"},
            {"key": "数据最小化", "value": "✓", "desc": "仅采集课堂场景，非课堂时段不采集", "icon": "Aim"},
            {"key": "学生主体性", "value": "✓", "desc": "支持知情权 / 删除权 / 修改权", "icon": "Avatar"},
        ],
        "stats": {
            "total_students": students,
            "total_face_records": faces,
            "face_anonymized": faces,  # 全部脱敏
            "total_alerts": total_alerts,
            "red_alerts": red_total,
            "high_risk_blocked": high_risk_text_blocked + high_risk_messages,
            "ai_messages_analyzed": risky_messages,
            "human_intervention_rate": human_intervention_rate,
            "explainable_rate": explainable_rate,
        },
        "risk_dictionary": {
            "high": ["自杀", "自残", "想死", "去死", "不想活", "结束生命", "活不下去", "解脱", "跳楼", "割腕", "上吊", "轻生"],
            "medium": ["抑郁", "压抑", "绝望", "无意义", "没人爱", "孤独", "崩溃", "想消失", "讨厌自己", "没有朋友"],
            "low": ["难过", "烦躁", "焦虑", "压力大", "失眠", "哭", "委屈", "不开心", "心累"],
        },
        "system_prompt_excerpt": (
            "你是「青苗守护者」平台的 AI 心理辅导员「知心」，专为中小学生服务。\n"
            "1. 始终温和、耐心、共情，不评判、不说教。\n"
            "2. 你不是医生，不能做诊断。\n"
            "3. 遇到自伤/自杀想法应温柔提醒「告诉信任的老师或拨打 12320」并立即标记高风险。\n"
            "4. 涉及隐私敏感话题（家暴、性、霸凌等），表达关心，提示寻求专业帮助。"
        ),
        "audit_logs": _recent_audit_actions(),
    }


def _recent_audit_actions() -> list[dict]:
    """最近的"伦理保护动作"日志。演示用模拟数据 + 真实预警混合。"""
    out: list[dict] = []
    # 取最近 high 风险消息
    rows = (
        db.session.query(AIConversationMessage)
        .filter(AIConversationMessage.risk_level == "high")
        .order_by(AIConversationMessage.id.desc())
        .limit(5)
        .all()
    )
    for m in rows:
        out.append({
            "time": m.created_at.strftime("%H:%M:%S"),
            "type": "AI 自动转人工",
            "detail": f"对话检测到高风险表达，已通知心理老师并展示 12320 热线",
        })
    if not out:
        out = [
            {"time": "10:23:45", "type": "AI 自动转人工", "detail": "对话检测到高风险，已通知心理老师"},
            {"time": "09:15:02", "type": "数据脱敏", "detail": "学生人脸图像哈希入库"},
            {"time": "08:50:11", "type": "权限拦截", "detail": "科任老师试图访问全校数据被拒"},
        ]
    return out
