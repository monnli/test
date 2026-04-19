"""报告生成服务。"""

from __future__ import annotations

import io
import json
from datetime import date, datetime, timedelta
from typing import Any

from loguru import logger

from ..ai import get_ai_client
from ..extensions import db
from ..models import (
    Alert,
    Clazz,
    EmotionTimeline,
    Report,
    School,
    ScaleAssessment,
    Student,
    TextAnalysis,
)
from ..utils.exceptions import NotFoundError, ValidationError
from ..utils.storage import get_storage


def _stringify_date(d: date) -> str:
    return d.strftime("%Y-%m-%d")


def _gather_class_data(class_id: int, days: int = 7) -> dict:
    clazz = db.session.get(Clazz, class_id)
    if not clazz or clazz.is_deleted:
        raise NotFoundError("班级不存在")
    student_ids = [
        s[0] for s in db.session.query(Student.id).filter_by(class_id=class_id, is_deleted=False).all()
    ]
    since = date.today() - timedelta(days=days)
    timeline = (
        db.session.query(EmotionTimeline)
        .filter(EmotionTimeline.student_id.in_(student_ids), EmotionTimeline.record_date >= since)
        .all()
    )
    avg_score = (
        sum(t.score for t in timeline) / len(timeline) if timeline else 80.0
    )
    alerts = (
        db.session.query(Alert)
        .filter(Alert.student_id.in_(student_ids))
        .order_by(Alert.score.desc())
        .limit(20)
        .all()
    )
    by_level: dict[str, int] = {"green": 0, "yellow": 0, "orange": 0, "red": 0}
    for a in alerts:
        by_level[a.level] = by_level.get(a.level, 0) + 1

    text_count = (
        db.session.query(TextAnalysis)
        .filter(TextAnalysis.student_id.in_(student_ids), TextAnalysis.created_at >= since)
        .count()
    )
    assess_count = (
        db.session.query(ScaleAssessment)
        .filter(ScaleAssessment.student_id.in_(student_ids), ScaleAssessment.created_at >= since)
        .count()
    )

    return {
        "class": {
            "id": clazz.id,
            "name": f"{clazz.grade.name if clazz.grade else ''}{clazz.name}",
            "head_teacher_id": clazz.head_teacher_id,
            "student_count": len(student_ids),
        },
        "period": f"近 {days} 天",
        "avg_psy_score": round(avg_score, 1),
        "alerts_by_level": by_level,
        "high_risk_students": [
            {
                "name": (db.session.get(Student, a.student_id) or Student()).name,
                "level": a.level,
                "score": a.score,
                "title": a.title,
            }
            for a in alerts[:5]
        ],
        "text_count": text_count,
        "assess_count": assess_count,
    }


def _gather_student_data(student_id: int) -> dict:
    student = db.session.get(Student, student_id)
    if not student or student.is_deleted:
        raise NotFoundError("学生不存在")
    timeline = (
        db.session.query(EmotionTimeline)
        .filter_by(student_id=student_id)
        .order_by(EmotionTimeline.record_date.desc())
        .limit(30)
        .all()
    )
    last_assess = (
        db.session.query(ScaleAssessment)
        .filter_by(student_id=student_id)
        .order_by(ScaleAssessment.id.desc())
        .first()
    )
    last_text = (
        db.session.query(TextAnalysis)
        .filter_by(student_id=student_id)
        .order_by(TextAnalysis.id.desc())
        .first()
    )
    open_alert = (
        db.session.query(Alert)
        .filter(Alert.student_id == student_id, Alert.status.in_(["open", "acknowledged"]))
        .order_by(Alert.score.desc())
        .first()
    )
    avg_score = sum(t.score for t in timeline) / len(timeline) if timeline else 80.0
    return {
        "student": {"id": student.id, "name": student.name, "class_id": student.class_id, "gender": student.gender},
        "avg_psy_score": round(avg_score, 1),
        "scale": {
            "name": last_assess.level if last_assess else "未测评",
            "score": last_assess.total_score if last_assess else 0,
        },
        "text": {
            "polarity": last_text.polarity if last_text else "未分析",
            "risk_level": last_text.risk_level if last_text else "none",
            "summary": last_text.summary if last_text else None,
        },
        "alert": {
            "level": open_alert.level if open_alert else "green",
            "score": open_alert.score if open_alert else 0,
            "reasons": json.loads(open_alert.reasons) if open_alert and open_alert.reasons else [],
        },
        "timeline_30d": [
            {"date": t.record_date.strftime("%Y-%m-%d"), "score": t.score} for t in timeline[::-1]
        ],
    }


def _gather_school_data() -> dict:
    """学校综合数据。"""
    student_count = db.session.query(Student).filter_by(is_deleted=False).count()
    class_count = db.session.query(Clazz).filter_by(is_deleted=False).count()
    timeline = (
        db.session.query(EmotionTimeline)
        .filter(EmotionTimeline.record_date >= date.today() - timedelta(days=30))
        .all()
    )
    avg = sum(t.score for t in timeline) / len(timeline) if timeline else 85.0
    by_level: dict[str, int] = {"green": 0, "yellow": 0, "orange": 0, "red": 0}
    rows = db.session.query(Alert).all()
    for a in rows:
        by_level[a.level] = by_level.get(a.level, 0) + 1
    return {
        "student_count": student_count,
        "class_count": class_count,
        "avg_psy_score_30d": round(avg, 1),
        "alerts_by_level": by_level,
        "alerts_total": len(rows),
    }


# ===== 内容生成 =====

def _build_class_markdown(data: dict) -> str:
    cls = data["class"]
    lvl = data["alerts_by_level"]
    md = [
        f"# 班级周报 · {cls['name']}",
        f"**报告周期**：{data['period']}　|　**学生人数**：{cls['student_count']} 人",
        "",
        "## 一、综合心理健康状况",
        f"- 班级综合心理健康指数（平均）：**{data['avg_psy_score']:.1f} / 100**",
        f"- 本周文本情绪分析：{data['text_count']} 次",
        f"- 本周量表测评：{data['assess_count']} 份",
        "",
        "## 二、预警分布",
        f"- 紧急 🔴：{lvl.get('red', 0)} 条　|　重点 🟠：{lvl.get('orange', 0)} 条　|　关注 🟡：{lvl.get('yellow', 0)} 条　|　正常 🟢：{lvl.get('green', 0)} 条",
        "",
        "## 三、需要重点关注的学生",
    ]
    if data["high_risk_students"]:
        for s in data["high_risk_students"]:
            md.append(f"- **{s['name']}**（{s['level']}）评分 {s['score']:.0f} - {s['title']}")
    else:
        md.append("- 暂无需要特别关注的学生")
    md.extend([
        "",
        "## 四、AI 综合建议",
        "_由通义千问基于班级数据自动生成_",
        "",
    ])
    return "\n".join(md)


def _build_student_markdown(data: dict) -> str:
    s = data["student"]
    md = [
        f"# 学生心理档案 · {s['name']}",
        f"**性别**：{s['gender']}　|　**学生 ID**：#{s['id']}",
        "",
        "## 一、心理健康指数",
        f"- 30 天平均：**{data['avg_psy_score']:.1f} / 100**",
        "",
        "## 二、最近量表测评",
        f"- 评级：**{data['scale']['name']}**　|　得分：{data['scale']['score']}",
        "",
        "## 三、最近文本分析",
        f"- 极性：{data['text']['polarity']}　|　风险等级：{data['text']['risk_level']}",
    ]
    if data["text"]["summary"]:
        md.append(f"- 归纳：{data['text']['summary']}")
    md.extend([
        "",
        "## 四、当前预警",
        f"- 等级：**{data['alert']['level']}**　|　评分：{data['alert']['score']:.0f}",
    ])
    if data["alert"]["reasons"]:
        md.append("- 主要原因：")
        for r in data["alert"]["reasons"]:
            md.append(f"  - {r}")
    md.extend([
        "",
        "## 五、AI 综合建议",
        "_由通义千问基于学生档案自动生成_",
        "",
    ])
    return "\n".join(md)


def _build_school_markdown(data: dict) -> str:
    lvl = data["alerts_by_level"]
    md = [
        "# 学校心理健康综合报告",
        f"**学生总数**：{data['student_count']} 人　|　**班级数**：{data['class_count']}",
        "",
        "## 一、整体心理状况",
        f"- 30 天平均心理健康指数：**{data['avg_psy_score_30d']:.1f} / 100**",
        f"- 累计预警：{data['alerts_total']} 条",
        "",
        "## 二、预警等级分布",
        f"- 紧急：{lvl.get('red', 0)}　|　重点：{lvl.get('orange', 0)}　|　关注：{lvl.get('yellow', 0)}　|　正常：{lvl.get('green', 0)}",
        "",
        "## 三、AI 综合建议",
        "_由通义千问基于全校数据自动生成_",
        "",
    ]
    return "\n".join(md)


def _ai_advice(scope: str, data: dict) -> str:
    """让 LLM 给出综合建议。"""
    prompt = (
        f"你是青少年心理学专家。请基于下面的{scope}数据，写一段 200~300 字的综合分析与建议，"
        "面向班主任与心理老师，要专业、温和、可操作。直接输出正文，不要加标题。\n\n"
        f"数据：\n{json.dumps(data, ensure_ascii=False, default=str)[:1500]}"
    )
    resp = get_ai_client().text_chat([{"role": "user", "content": prompt}])
    return (resp.get("data") or {}).get(
        "reply", "建议加强对该群体的日常情绪关注，定期开展团体心理活动，并对高风险学生做 1 对 1 谈话。"
    )


# ===== 对外 =====

def generate_class_report(class_id: int, operator_id: int | None) -> dict:
    data = _gather_class_data(class_id)
    md = _build_class_markdown(data)
    advice = _ai_advice(f"班级（{data['class']['name']}）", data)
    md = md.replace("_由通义千问基于班级数据自动生成_", advice)
    period = f"{date.today().strftime('%Y-W%V')}"
    rec = Report(
        type="class",
        target_id=class_id,
        target_name=data["class"]["name"],
        title=f"{data['class']['name']} 周报 · {period}",
        period=period,
        content=md,
        summary=advice[:200],
        operator_id=operator_id,
    )
    db.session.add(rec)
    db.session.commit()
    logger.info(f"生成班级报告 #{rec.id}")
    return serialize_report(rec)


def generate_student_report(student_id: int, operator_id: int | None) -> dict:
    data = _gather_student_data(student_id)
    md = _build_student_markdown(data)
    advice = _ai_advice(f"学生（{data['student']['name']}）", data)
    md = md.replace("_由通义千问基于学生档案自动生成_", advice)
    rec = Report(
        type="student",
        target_id=student_id,
        target_name=data["student"]["name"],
        title=f"{data['student']['name']} 心理档案报告 · {date.today()}",
        period=date.today().strftime("%Y-%m-%d"),
        content=md,
        summary=advice[:200],
        operator_id=operator_id,
    )
    db.session.add(rec)
    db.session.commit()
    return serialize_report(rec)


def generate_school_report(operator_id: int | None) -> dict:
    data = _gather_school_data()
    md = _build_school_markdown(data)
    advice = _ai_advice("全校", data)
    md = md.replace("_由通义千问基于全校数据自动生成_", advice)
    rec = Report(
        type="school",
        target_id=None,
        target_name="全校",
        title=f"学校心理健康综合报告 · {date.today()}",
        period=date.today().strftime("%Y-%m-%d"),
        content=md,
        summary=advice[:200],
        operator_id=operator_id,
    )
    db.session.add(rec)
    db.session.commit()
    return serialize_report(rec)


def list_reports(report_type: str | None = None, page: int = 1, page_size: int = 20) -> dict:
    q = db.session.query(Report)
    if report_type:
        q = q.filter_by(type=report_type)
    total = q.count()
    items = (
        q.order_by(Report.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "items": [serialize_report(r) for r in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


def get_report(report_id: int) -> dict:
    rec = db.session.get(Report, report_id)
    if not rec:
        raise NotFoundError("报告不存在")
    return serialize_report(rec, with_content=True)


def render_pdf(report_id: int) -> tuple[bytes, str]:
    rec = db.session.get(Report, report_id)
    if not rec:
        raise NotFoundError("报告不存在")

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.cidfonts import UnicodeCIDFont
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

        try:
            pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
            font_name = "STSong-Light"
        except Exception:  # noqa: BLE001
            font_name = "Helvetica"

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=40, rightMargin=40, topMargin=40, bottomMargin=40)
        styles = getSampleStyleSheet()
        body = ParagraphStyle("body", parent=styles["BodyText"], fontName=font_name, fontSize=11, leading=18)
        title = ParagraphStyle("title", parent=styles["Title"], fontName=font_name, fontSize=18, leading=24)
        h2 = ParagraphStyle("h2", parent=styles["Heading2"], fontName=font_name, fontSize=14, leading=20)

        flow = []
        for line in rec.content.splitlines():
            line = line.strip()
            if not line:
                flow.append(Spacer(1, 6))
                continue
            if line.startswith("# "):
                flow.append(Paragraph(line[2:], title))
            elif line.startswith("## "):
                flow.append(Paragraph(line[3:], h2))
            elif line.startswith("- "):
                flow.append(Paragraph("• " + line[2:].replace("**", ""), body))
            else:
                flow.append(Paragraph(line.replace("**", ""), body))
        doc.build(flow)
        pdf_bytes = buf.getvalue()
        # 保存 PDF 到本地存储
        key = f"reports/{rec.id}.pdf"
        get_storage().save(key, pdf_bytes)
        rec.pdf_key = get_storage().get_url(key)
        db.session.commit()
        return pdf_bytes, f"{rec.title}.pdf"
    except ImportError:
        # 退化为纯文本下载
        return rec.content.encode("utf-8"), f"{rec.title}.md"


def serialize_report(r: Report, with_content: bool = False) -> dict:
    out = {
        "id": r.id,
        "type": r.type,
        "target_id": r.target_id,
        "target_name": r.target_name,
        "title": r.title,
        "period": r.period,
        "summary": r.summary,
        "pdf_key": r.pdf_key,
        "operator_id": r.operator_id,
        "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    }
    if with_content:
        out["content"] = r.content
    return out
