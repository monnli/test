"""课堂视频上传/分析服务。"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime
from typing import Any

from flask import current_app
from loguru import logger
from werkzeug.datastructures import FileStorage

from ..extensions import db
from ..models import AnalysisTask, BehaviorRecord, Clazz, EmotionRecord, User, Video
from ..utils.exceptions import NotFoundError, PermissionDeniedError, ValidationError
from ..utils.permissions import get_current_user, get_visible_class_ids
from ..utils.storage import get_storage

# 与 ai_service 行为流水线一致的标准八类（用于报告指标聚合）
BEHAVIOR_EIGHT_CN: tuple[str, ...] = (
    "低头写字",
    "低头看书",
    "抬头听课",
    "转头",
    "举手",
    "站立",
    "小组讨论",
    "教师指导",
)


def _normalize_behavior_cn(label_cn: str | None, label: str | None) -> str:
    """将历史/英文 label 归一到标准八类，供时间轴与统计一致展示。"""
    cn = (label_cn or "").strip()
    lb = (label or "").strip()
    if cn in BEHAVIOR_EIGHT_CN:
        return cn
    if lb in BEHAVIOR_EIGHT_CN:
        return lb
    if cn in ("学生",) or lb == "person":
        return "抬头听课"
    if lb == "hand_up" or cn in ("举手",):
        return "举手"
    if lb in ("cell phone", "cell_phone") or cn in ("手机", "玩手机", "cell phone"):
        return "低头看书"
    if cn in ("书本", "阅读") or lb == "book":
        return "低头看书"
    if cn in ("笔记本", "写作") or lb in ("laptop", "mouse", "keyboard"):
        return "低头写字"
    if cn in ("趴桌",) or lb == "lying":
        return "低头写字"
    if cn in ("睡觉",) or lb == "sleeping":
        return "低头看书"
    if cn in ("坐姿", "抬头", "听课") or lb in ("sitting", "person_head_up", "listen"):
        return "抬头听课"
    if cn in ("站立",) or lb == "standing":
        return "站立"
    if cn in ("交头接耳",) or lb == "talking":
        return "小组讨论"
    if cn in ("教师",) or lb == "teacher":
        return "教师指导"
    return "转头"


def allowed_video(filename: str, allowed: set[str]) -> bool:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in allowed


def assert_video_accessible(video: Video, user: User) -> None:
    visible = get_visible_class_ids(user)
    if visible is None:
        return
    cid = video.class_id
    if cid is None or cid not in visible:
        raise PermissionDeniedError("无权访问该视频")


def get_video_for_user(video_id: int, user: User) -> Video:
    video = db.session.get(Video, video_id)
    if not video:
        raise NotFoundError("视频不存在")
    assert_video_accessible(video, user)
    return video


def create_video_from_upload(
    file: FileStorage,
    class_id: int | None,
    title: str | None,
    uploaded_by: int | None,
) -> dict[str, Any]:
    if not file or not file.filename:
        raise ValidationError("请选择视频文件")

    allowed = current_app.config.get("ALLOWED_VIDEO_EXTS", {"mp4", "avi", "mov", "mkv"})
    if not allowed_video(file.filename, allowed):
        raise ValidationError(f"文件类型不支持，允许：{','.join(sorted(allowed))}")

    data = file.read()
    if not data:
        raise ValidationError("文件为空")

    hash_hex = hashlib.md5(data).hexdigest()
    ext = file.filename.rsplit(".", 1)[-1].lower()
    key = f"videos/{datetime.utcnow():%Y%m%d}/{hash_hex}.{ext}"
    storage = get_storage()
    storage.save(key, data)

    clazz = db.session.get(Clazz, class_id) if class_id else None

    duration, fps, width, height = _probe_video_meta(storage.get_path(key))

    v = Video(
        title=title or file.filename,
        storage_key=key,
        url=storage.get_url(key),
        size_bytes=len(data),
        class_id=clazz.id if clazz else None,
        duration_seconds=duration,
        fps=fps,
        width=width,
        height=height,
        uploaded_by=uploaded_by,
    )
    db.session.add(v)
    db.session.commit()
    logger.info(f"视频已上传 id={v.id} size={len(data)} key={key}")
    return serialize_video(v)


def _probe_video_meta(path: str | None) -> tuple[float, float, int, int]:
    if not path or not os.path.exists(path):
        return 60.0, 0.0, 0, 0
    try:
        import cv2  # type: ignore

        cap = cv2.VideoCapture(path)
        fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
        frames = float(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0.0)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        cap.release()
        duration = (frames / fps) if fps else 0.0
        return duration or 60.0, fps, width, height
    except Exception:  # noqa: BLE001
        return 60.0, 0.0, 0, 0


def list_videos(
    class_ids: list[int] | None = None,
    page: int = 1,
    page_size: int = 10,
) -> dict[str, Any]:
    q = db.session.query(Video)
    if class_ids is not None:
        if not class_ids:
            return {"items": [], "total": 0, "page": page, "page_size": page_size}
        q = q.filter(Video.class_id.in_(class_ids))
    total = q.count()
    items = (
        q.order_by(Video.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "items": [serialize_video(v) for v in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


def create_analysis_task(video_id: int, sample_interval: float = 2.0) -> dict[str, Any]:
    user = get_current_user()
    get_video_for_user(video_id, user)
    # 已有未完成任务则直接返回
    existing = (
        db.session.query(AnalysisTask)
        .filter(AnalysisTask.video_id == video_id, AnalysisTask.status.in_(["pending", "running"]))
        .first()
    )
    if existing:
        return serialize_task(existing)

    task = AnalysisTask(
        video_id=video_id,
        status="pending",
        progress=0,
        sample_interval_sec=float(sample_interval),
    )
    db.session.add(task)
    db.session.commit()

    from flask import current_app
    from ..tasks.video_worker import submit_analysis

    submit_analysis(current_app._get_current_object(), task.id)
    return serialize_task(task)


def get_task(task_id: int) -> dict[str, Any]:
    task = db.session.get(AnalysisTask, task_id)
    if not task:
        raise NotFoundError("任务不存在")
    return serialize_task(task)


def list_tasks_of_video(video_id: int) -> list[dict[str, Any]]:
    user = get_current_user()
    get_video_for_user(video_id, user)
    rows = (
        db.session.query(AnalysisTask)
        .filter_by(video_id=video_id)
        .order_by(AnalysisTask.id.desc())
        .all()
    )
    return [serialize_task(t) for t in rows]


def delete_video(video_id: int) -> None:
    user = get_current_user()
    video = get_video_for_user(video_id, user)
    storage = get_storage()
    storage_key = video.storage_key
    task_ids = [
        r[0]
        for r in db.session.query(AnalysisTask.id).filter_by(video_id=video.id).all()
    ]
    db.session.query(BehaviorRecord).filter_by(video_id=video.id).delete(synchronize_session=False)
    db.session.query(EmotionRecord).filter_by(video_id=video.id).delete(synchronize_session=False)
    if task_ids:
        db.session.query(AnalysisTask).filter(AnalysisTask.id.in_(task_ids)).delete(
            synchronize_session=False
        )
    db.session.delete(video)
    db.session.commit()
    try:
        storage.delete(storage_key)
    except Exception:  # noqa: BLE001
        logger.warning(f"删除存储文件失败 key={storage_key}")


def detect_frame_from_upload(video_id: int, image_bytes: bytes, conf: float = 0.35) -> dict[str, Any]:
    """报告页视频回放：当前帧走 AI 行为检测（YOLO），与异步任务独立。"""
    if not image_bytes:
        raise ValidationError("图像为空")
    user = get_current_user()
    get_video_for_user(video_id, user)
    from ..ai import get_ai_client

    raw = get_ai_client().behavior_detect(image_bytes, conf=conf)
    data = raw.get("data")
    if not isinstance(data, dict):
        return {"detections": [], "summary": {}, "_error": raw.get("message") or "AI 无数据"}
    return data


def get_task_report(task_id: int) -> dict[str, Any]:
    task = db.session.get(AnalysisTask, task_id)
    if not task:
        raise NotFoundError("任务不存在")
    video = db.session.get(Video, task.video_id)

    bhv = db.session.query(BehaviorRecord).filter_by(task_id=task_id).all()
    emo = db.session.query(EmotionRecord).filter_by(task_id=task_id).all()

    # 时间轴聚合（每 5 秒一个 bucket）
    bucket = 5.0
    behavior_timeline: dict[float, dict[str, int]] = {}
    emotion_timeline: dict[float, dict[str, int]] = {}

    for r in bhv:
        b = round(r.frame_time / bucket) * bucket
        nk = _normalize_behavior_cn(r.label_cn, r.label)
        behavior_timeline.setdefault(b, {}).setdefault(nk, 0)
        behavior_timeline[b][nk] += 1
    for r in emo:
        b = round(r.frame_time / bucket) * bucket
        emotion_timeline.setdefault(b, {}).setdefault(r.emotion_cn, 0)
        emotion_timeline[b][r.emotion_cn] += 1

    summary = {}
    if task.summary:
        try:
            summary = json.loads(task.summary)
        except Exception:  # noqa: BLE001
            summary = {}

    by_cn = {cn: 0 for cn in BEHAVIOR_EIGHT_CN}
    for r in bhv:
        nk = _normalize_behavior_cn(r.label_cn, r.label)
        by_cn[nk] += 1

    listen = by_cn["抬头听课"]
    hand_up = by_cn["举手"]
    head_down = by_cn["低头写字"] + by_cn["低头看书"]
    discuss = by_cn["小组讨论"]
    engagement = min(
        100,
        max(40, int(55 + listen + hand_up * 2 + discuss - head_down * 2)),
    )

    return {
        "task": serialize_task(task),
        "video": serialize_video(video) if video else None,
        "summary": summary,
        "metrics": {
            "total_person_detections": listen + by_cn["站立"],
            "hand_up_count": hand_up,
            "phone_count": head_down,
            "engagement_score": engagement,
            "behavior_by_class": by_cn,
        },
        "behavior_timeline": [
            {"time": t, **{k: v for k, v in cnt.items()}}
            for t, cnt in sorted(behavior_timeline.items())
        ],
        "emotion_timeline": [
            {"time": t, **{k: v for k, v in cnt.items()}}
            for t, cnt in sorted(emotion_timeline.items())
        ],
    }


def serialize_video(v: Video) -> dict[str, Any]:
    return {
        "id": v.id,
        "title": v.title,
        "class_id": v.class_id,
        "url": v.url,
        "storage_key": v.storage_key,
        "size_bytes": v.size_bytes,
        "size_mb": round(v.size_bytes / 1024 / 1024, 2) if v.size_bytes else 0,
        "duration_seconds": v.duration_seconds,
        "fps": v.fps,
        "width": v.width,
        "height": v.height,
        "uploaded_by": v.uploaded_by,
        "created_at": v.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    }


def serialize_task(t: AnalysisTask) -> dict[str, Any]:
    return {
        "id": t.id,
        "video_id": t.video_id,
        "status": t.status,
        "progress": t.progress,
        "processed_frames": t.processed_frames,
        "total_frames": t.total_frames,
        "sample_interval_sec": t.sample_interval_sec,
        "error_message": t.error_message,
        "started_at": t.started_at.strftime("%Y-%m-%d %H:%M:%S") if t.started_at else None,
        "finished_at": t.finished_at.strftime("%Y-%m-%d %H:%M:%S") if t.finished_at else None,
        "created_at": t.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    }
