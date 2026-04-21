"""实时摄像头拉流分析 worker。

每个活跃的 session 一个后台线程：
- 用 OpenCV 拉流（RTSP / HLS / 本地文件 / file_loop 循环）
- 每 N 秒抽一帧 → 调 AI 服务的 /classroom/analyze
- 写入行为/表情/出勤记录
- 空教室 5 分钟自动停止
- 关键帧保存（每 30 秒一张）

所有活跃 session 通过 _running 字典管理。
"""

from __future__ import annotations

import base64
import json
import os
import time
from datetime import datetime
from threading import Thread
from typing import Any

from flask import Flask
from loguru import logger

from ..extensions import db, socketio
from ..models import (
    AttendanceRecord,
    BehaviorRecord,
    Camera,
    ClassSession,
    EmotionRecord,
    FaceEmbedding,
    Student,
)


# camera_id → worker 线程
_running: dict[int, bool] = {}


def start_live_analysis(app: Flask, session_id: int) -> bool:
    """启动实时分析线程。返回是否启动成功（已在运行则返回 False）。"""
    with app.app_context():
        session = db.session.get(ClassSession, session_id)
        if not session or not session.camera_id:
            logger.warning(f"session {session_id} 无摄像头，无法启动实时分析")
            return False
        if _running.get(session.camera_id):
            logger.info(f"camera {session.camera_id} 已有实时分析，跳过")
            return False

        _running[session.camera_id] = True
        session.status = "running"
        session.started_at = datetime.utcnow()
        db.session.commit()

    Thread(
        target=_worker,
        args=(app, session_id),
        daemon=True,
        name=f"live-{session_id}",
    ).start()
    logger.info(f"🟢 实时分析已启动 session={session_id}")
    return True


def stop_live_analysis(app: Flask, session_id: int, reason: str = "manual") -> None:
    with app.app_context():
        session = db.session.get(ClassSession, session_id)
        if not session:
            return
        if session.camera_id:
            _running[session.camera_id] = False
        session.status = "auto_ended" if reason != "manual" else "ended"
        session.ended_at = datetime.utcnow()
        db.session.commit()
        logger.info(f"🔴 实时分析已停止 session={session_id} reason={reason}")


def is_running(camera_id: int) -> bool:
    return _running.get(camera_id, False)


def _load_face_library(school_id: int) -> list[dict[str, Any]]:
    """读取本校全部学生人脸 embedding。"""
    rows = (
        db.session.query(FaceEmbedding, Student)
        .join(Student, Student.id == FaceEmbedding.student_id)
        .filter(Student.school_id == school_id, Student.is_deleted.is_(False))
        .all()
    )
    lib: list[dict[str, Any]] = []
    for face, st in rows:
        try:
            emb = json.loads(face.embedding)
        except Exception:
            continue
        lib.append({"person_id": st.id, "name": st.name, "embedding": emb})
    return lib


def _worker(app: Flask, session_id: int) -> None:
    """拉流 + 分析的核心循环。"""
    with app.app_context():
        session = db.session.get(ClassSession, session_id)
        if not session:
            return
        camera = db.session.get(Camera, session.camera_id) if session.camera_id else None
        if not camera:
            return

        # AI 客户端
        from ..ai import AIClient

        client = AIClient(
            base_url=app.config.get("AI_SERVICE_URL", "http://localhost:8000"),
            timeout=10.0,
        )

        face_library = _load_face_library(camera.school_id)
        logger.info(f"session {session_id} 人脸库加载 {len(face_library)} 条")

        # 拉流
        cap = _open_stream(camera.stream_url, camera.stream_type)
        if cap is None:
            logger.error(f"session {session_id} 无法打开视频流 {camera.stream_url}")
            stop_live_analysis(app, session_id, reason="stream_failed")
            return

        analyze_interval_sec = 3.0
        last_analyze = 0.0
        no_person_seconds = 0
        empty_threshold = 300  # 5 分钟空教室

        behavior_summary: dict[str, int] = {}
        emotion_summary: dict[str, int] = {}
        attendance: dict[int, dict] = {}  # student_id → {first_seen, last_seen, count}
        engagement_samples: list[float] = []

        try:
            while _running.get(camera.camera_id if hasattr(camera, "camera_id") else session.camera_id, True):
                ok, frame = _read_frame(cap, camera.stream_type)
                if not ok:
                    time.sleep(0.5)
                    continue

                now_sec = time.time()
                if now_sec - last_analyze < analyze_interval_sec:
                    time.sleep(0.1)
                    continue
                last_analyze = now_sec

                # 送 AI 分析
                try:
                    import cv2  # type: ignore

                    _, jpg = cv2.imencode(".jpg", frame)
                    b64 = base64.b64encode(jpg.tobytes()).decode("utf-8")
                except Exception:
                    continue

                result = client.post(
                    "/classroom/analyze",
                    {
                        "image": b64,
                        "face_library": face_library,
                        "camera_key": f"cam_{camera.id}",
                        "recognize_face": True,
                    },
                )
                data = result.get("data") or {}
                students = data.get("students") or []
                summary = data.get("summary") or {}

                # 空教室判断
                if summary.get("total_persons", 0) == 0:
                    no_person_seconds += analyze_interval_sec
                    if no_person_seconds >= empty_threshold:
                        logger.info(f"session {session_id} 空教室 {empty_threshold}s，自动休眠")
                        stop_live_analysis(app, session_id, reason="empty_classroom")
                        break
                else:
                    no_person_seconds = 0

                # 写记录（每次分析只抽一帧样本写入，避免 DB 过载）
                ts = now_sec - time.mktime(session.started_at.timetuple())
                for st in students:
                    for b in st.get("behaviors") or []:
                        behavior_summary[b] = behavior_summary.get(b, 0) + 1
                    db.session.add(BehaviorRecord(
                        task_id=0,  # 实时分析无 task
                        video_id=0,
                        frame_time=float(ts),
                        label=st.get("behaviors", ["person"])[0] if st.get("behaviors") else "person",
                        label_cn=st.get("behaviors_cn", ["学生"])[0] if st.get("behaviors_cn") else "学生",
                        confidence=float(st.get("confidence") or 0),
                        bbox=json.dumps(st.get("bbox") or [], ensure_ascii=False),
                        student_id=st.get("student_id"),
                    ))
                    emo = st.get("emotion_cn")
                    if emo:
                        emotion_summary[emo] = emotion_summary.get(emo, 0) + 1
                        db.session.add(EmotionRecord(
                            task_id=0, video_id=0, frame_time=float(ts),
                            emotion=st.get("emotion", ""), emotion_cn=emo,
                            confidence=float(st.get("emotion_confidence") or 0),
                            student_id=st.get("student_id"),
                        ))
                    # 出勤
                    sid = st.get("student_id")
                    if sid:
                        if sid not in attendance:
                            attendance[sid] = {"first_seen": ts, "last_seen": ts, "count": 1}
                        else:
                            attendance[sid]["last_seen"] = ts
                            attendance[sid]["count"] += 1

                engagement_samples.append(summary.get("engagement_score") or 0)
                db.session.commit()

                # WebSocket 推送实时结果
                try:
                    socketio.emit(
                        "live_analysis",
                        {
                            "session_id": session_id,
                            "camera_id": camera.id,
                            "timestamp": time.time(),
                            "summary": summary,
                            "students": [
                                {
                                    "track_id": s.get("track_id"),
                                    "student_id": s.get("student_id"),
                                    "student_name": s.get("student_name"),
                                    "bbox": s.get("bbox"),
                                    "behaviors_cn": s.get("behaviors_cn"),
                                    "emotion_cn": s.get("emotion_cn"),
                                    "using_phone": s.get("using_phone"),
                                }
                                for s in students
                            ],
                        },
                        namespace="/ws",
                    )
                except Exception:
                    pass

        except Exception as exc:  # noqa: BLE001
            logger.exception(f"session {session_id} 异常：{exc}")
            stop_live_analysis(app, session_id, reason=f"error: {exc}")
        finally:
            try:
                cap.release()
            except Exception:
                pass

            # 更新 session 最终结果
            with app.app_context():
                session = db.session.get(ClassSession, session_id)
                if session:
                    session.engagement_score = (
                        round(sum(engagement_samples) / len(engagement_samples), 1)
                        if engagement_samples else 0.0
                    )
                    if session.status == "running":
                        session.status = "ended"
                        session.ended_at = datetime.utcnow()
                    db.session.commit()

                    # 写出勤记录
                    for sid, rec in attendance.items():
                        db.session.add(AttendanceRecord(
                            class_session_id=session_id,
                            student_id=sid,
                            status="present",
                            detected_count=rec["count"],
                            first_seen=rec["first_seen"],
                            last_seen=rec["last_seen"],
                        ))
                    db.session.commit()
            logger.info(f"✅ session {session_id} 清理完成")


def _open_stream(url: str, stream_type: str):
    """打开视频流。返回 cv2.VideoCapture 或 None。"""
    try:
        import cv2  # type: ignore
    except ImportError:
        logger.warning("OpenCV 未安装，实时分析无法启动")
        return None

    if stream_type in ("rtsp", "hls"):
        cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
    elif stream_type in ("file", "file_loop"):
        # 本地文件
        if not os.path.exists(url):
            # 尝试相对路径
            for root in ("/app", ".", "/workspace"):
                candidate = os.path.join(root, url.lstrip("/"))
                if os.path.exists(candidate):
                    url = candidate
                    break
        if not os.path.exists(url):
            return None
        cap = cv2.VideoCapture(url)
    else:
        cap = cv2.VideoCapture(url)

    if not cap.isOpened():
        return None
    return cap


def _read_frame(cap, stream_type: str):
    """读一帧。file_loop 在读到结尾时自动倒带。"""
    ok, frame = cap.read()
    if not ok and stream_type == "file_loop":
        try:
            import cv2  # type: ignore

            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ok, frame = cap.read()
        except Exception:
            pass
    return ok, frame
