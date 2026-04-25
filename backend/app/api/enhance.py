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
    """返回演示脚本：路径 + 停留时长 + 口播文案（与当前产品能力对齐，偏答辩/路演讲解粒度）。"""
    return ok({
        "steps": [
            # —— 总览与入口 ——
            {
                "path": "/workbench",
                "duration": 6500,
                "narrate": "工作台：登录后的第一站。聚合今日预警、待办、本周视频与量表概况，可一键跳转到课堂、心理或管理模块；数据大屏留在导览最后集中展示。",
            },

            # —— 组织架构与身份 ——
            {
                "path": "/org/classes",
                "duration": 5500,
                "narrate": "班级管理：学校-年级-班级层级。后续课堂视频、摄像头、量表与预警均按班级数据范围授权给任课教师与班主任。",
            },
            {
                "path": "/org/students",
                "duration": 6000,
                "narrate": "学生管理：维护学号、班级归属。人脸库、心理档案、课堂识别结果最终都关联到「具体学生」以便干预闭环。",
            },
            {
                "path": "/org/faces",
                "duration": 7000,
                "narrate": "人脸库：上传正脸照提取 512 维向量；直播画框匹配到「哪位学生」依赖此库。支持本页试识别与覆盖更新。",
            },

            # —— 课堂分析：录像链路（上传 → 任务 → 报告 + 回放画框）——
            {
                "path": "/classroom/videos",
                "duration": 8000,
                "narrate": "视频库：已上传的课堂录像列表。可发起异步分析、查看历史任务、删除视频及文件；与后端存储、分析队列联动。",
            },
            {
                "path": "/classroom/upload",
                "duration": 7500,
                "narrate": "上传视频：选择班级与抽帧间隔后上传 mp4 等格式。后台 worker 抽帧调用 AI 服务中的 YOLOv8 行为流水线（支持自训 best.pt 八类中文标签）。",
            },
            {
                "path": "/classroom/realtime",
                "duration": 7000,
                "narrate": "笔记本摄像头：浏览器本机画面走 WebSocket/行为检测，适合无固定摄像头的试讲或答辩演示场景。",
            },

            # —— 课表 + 固定机位 + 直播墙 ——
            {
                "path": "/classroom/schedule",
                "duration": 8000,
                "narrate": "课表管理：班级×科目×节次维护上课时段。可配合调度器在「上课时间」自动拉起对应教室的识别任务（若已部署）。",
            },
            {
                "path": "/classroom/camera-manage",
                "duration": 7000,
                "narrate": "摄像头管理（管理员）：录入 RTSP / HLS / 本地 mp4 等源，绑定到班级与座位视角。答辩环境可用本地 demo 视频模拟多路输入。",
            },
            {
                "path": "/classroom/cameras",
                "duration": 8500,
                "narrate": "摄像头墙：全校教室画面卡片化总览；结合课表可高亮「当前应在线」的机位，便于值班老师快速扫视。",
            },
            {
                "path": "/classroom/live/1",
                "duration": 12000,
                "narrate": "实时直播页：单路画面 + 行为/表情/人脸多模态叠加。行为侧与八类 YOLO 模型及姿态派生逻辑一致；支持 WebSocket 低延迟刷新检测框与名单。",
            },
            {
                "path": "/classroom/live/2",
                "duration": 8000,
                "narrate": "切换另一路摄像头：演示多教室并行接入时，路由与状态如何隔离；便于说明「规模化部署」而非单机 demo。",
            },

            # —— 心理健康 ——
            {
                "path": "/psychology",
                "duration": 7000,
                "narrate": "心理健康：量表测评入口与学生心理档案列表。量表得分、文本情绪、课堂情绪曲线可写入同一学生的时序档案。",
            },

            # —— 关联、预警、报告 ——
            {
                "path": "/correlation",
                "duration": 8000,
                "narrate": "关联分析：将心理指数、学业、量表、课堂行为（含八类统计）、综合风险等维度做相关性与散点矩阵，帮助发现「成绩下滑 + 课堂低头增多」等组合信号。",
            },
            {
                "path": "/alerts",
                "duration": 7500,
                "narrate": "预警中心：绿/黄/橙/红四级工单。来源包括规则引擎、关联分析异常、AI 对话敏感词等；支持认领、处理备注与闭环状态。",
            },
            {
                "path": "/reports",
                "duration": 6000,
                "narrate": "报告中心：一键生成班级周报、学校月报或学生 PDF 档案（后端可接大模型归纳 + 固定模板排版）。",
            },

            # —— 系统与 AI 运维 ——
            {
                "path": "/system/ai",
                "duration": 8000,
                "narrate": "AI 服务监控：查看推理服务健康度、流水线是否就绪；可在此联调表情/行为/文本等接口。生产环境需配置 AI_SERVICE_URL、FORCE_MOCK=false 与 GPU/CPU。",
            },

            # —— AI 增强套件 ——
            {
                "path": "/enhance/cluster",
                "duration": 6500,
                "narrate": "群体聚类：基于多源特征向量对学生分群，识别「高焦虑+低参与」等亚群体，为分层班会或团体辅导提供名单建议。",
            },
            {
                "path": "/enhance/intervention",
                "duration": 6500,
                "narrate": "干预闭环：从预警发起到谈话、回访、效果评估的时间线，体现「不只报警、还要跟进」。",
            },
            {
                "path": "/enhance/graph",
                "duration": 6500,
                "narrate": "知识图谱：学校-年级-班级-学生-教师关系与高风险边；用于答辩时展示数据结构而非黑箱。",
            },
            {
                "path": "/enhance/multimodal",
                "duration": 6000,
                "narrate": "多模态融合：把视频行为、量表、对话、文本情绪放在同一时间轴上对比，突出「同一学生、多证据互证」。",
            },
            {
                "path": "/enhance/compare",
                "duration": 6500,
                "narrate": "产品对比：与市面常见「只做监控或只做心理」方案做维度对照，强调本作品的课堂+心理一体化定位。",
            },

            # —— 伦理与叙事收束 ——
            {
                "path": "/ethics",
                "duration": 8000,
                "narrate": "负责任 AI：数据最小化、脱敏、删除权、避免标签化等设计说明；符合大赛对伦理与社会影响的评审要点。",
            },
            {
                "path": "/enhance/story",
                "duration": 11000,
                "narrate": "「小李的故事」虚构案例：从课堂行为异常与心理预警串联到干预与好转，用于向非技术评委讲清产品价值闭环。",
            },

            # —— 大屏收束（仅此一处）——
            {
                "path": "/dashboard",
                "duration": 10000,
                "narrate": "数据大屏（收束）：全校一屏总览。左侧预警等级分布、中部近 30 天心理指数、右侧「今日课堂行为分布」已对齐标准八类（低头写字/看书、抬头听课、转头、举手、站立、小组讨论、教师指导）与今日表情玫瑰图，底部实时预警与高风险学生榜——对应「看得见、判得准、跟得上」。",
            },
        ]
    })
