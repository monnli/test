"""课表驱动的实时分析调度器。

启动一个后台线程，每分钟扫描一次：
- 找到当前正在进行的所有课（根据 class_schedules 表）
- 对每节课查对应班级的摄像头
- 若无活跃 session 则创建并启动实时分析
- 若课程已结束则停止对应 session

使用方式：在 Flask 启动后调用 start_scheduler(app)。
"""

from __future__ import annotations

import time
from datetime import datetime
from threading import Thread

from flask import Flask
from loguru import logger


_scheduler_running = False


def start_scheduler(app: Flask) -> None:
    global _scheduler_running
    if _scheduler_running:
        return
    _scheduler_running = True
    Thread(target=_loop, args=(app,), daemon=True, name="class-scheduler").start()
    logger.info("📅 课表调度器已启动（每 60 秒扫描一次）")


def _loop(app: Flask) -> None:
    while _scheduler_running:
        try:
            with app.app_context():
                _tick(app)
        except Exception as exc:  # noqa: BLE001
            # 任何异常都不退出主循环（M10 新表未迁移时会报错是正常的）
            logger.debug(f"调度器本轮异常（不影响主功能）：{exc}")
        time.sleep(60)


def _tick(app: Flask) -> None:
    """单轮调度逻辑。任何异常静默吞掉，避免阻塞主循环。"""
    from ..extensions import db
    from ..models import Camera, ClassSchedule, ClassSession
    from ..services.camera_service import find_active_schedules
    from ..tasks.live_worker import is_running, start_live_analysis, stop_live_analysis

    now = datetime.now()

    # 1. 启动应启动的
    try:
        active = find_active_schedules(now)
    except Exception as exc:  # noqa: BLE001
        logger.debug(f"课表查询失败（class_schedules 表可能未建）：{exc}")
        active = []

    for sch in active:
        try:
            camera = (
                db.session.query(Camera)
                .filter_by(class_id=sch.class_id, is_deleted=False)
                .first()
            )
            if not camera:
                continue
            if is_running(camera.id):
                continue
            existing = (
                db.session.query(ClassSession)
                .filter(
                    ClassSession.camera_id == camera.id,
                    ClassSession.class_id == sch.class_id,
                    ClassSession.session_date == now.date(),
                    ClassSession.period == sch.period,
                    ClassSession.status.in_(["scheduled", "running"]),
                )
                .first()
            )
            if existing and existing.status == "running":
                continue
            if not existing:
                existing = ClassSession(
                    class_id=sch.class_id,
                    subject_id=sch.subject_id,
                    teacher_id=sch.teacher_id,
                    session_date=now.date(),
                    period=sch.period,
                    camera_id=camera.id,
                    trigger_type="schedule",
                    status="scheduled",
                    title=f"{sch.weekday}周{sch.period}节 自动识别",
                )
                db.session.add(existing)
                db.session.commit()

            start_live_analysis(app, existing.id)
        except Exception as exc:  # noqa: BLE001
            logger.debug(f"启动 session 失败：{exc}")
            try:
                db.session.rollback()
            except Exception:
                pass

    # 2. 停止已到点的
    try:
        running_sessions = (
            db.session.query(ClassSession).filter(ClassSession.status == "running").all()
        )
    except Exception as exc:  # noqa: BLE001
        logger.debug(f"查询运行中 session 失败（class_sessions 缺字段？）：{exc}")
        try:
            db.session.rollback()
        except Exception:
            pass
        return

    cur_time = now.time()
    for s in running_sessions:
        try:
            sch_candidates = (
                db.session.query(ClassSchedule)
                .filter(
                    ClassSchedule.is_deleted.is_(False),
                    ClassSchedule.class_id == s.class_id,
                    ClassSchedule.period == s.period,
                    ClassSchedule.weekday == now.isoweekday(),
                )
                .first()
            )
            if sch_candidates and cur_time > sch_candidates.end_time:
                stop_live_analysis(app, s.id, reason="scheduled_end")
        except Exception as exc:  # noqa: BLE001
            logger.debug(f"停止 session 失败：{exc}")
            try:
                db.session.rollback()
            except Exception:
                pass
