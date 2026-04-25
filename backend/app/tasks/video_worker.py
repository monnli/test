"""视频分析后台任务 worker。

使用 Python threading + 队列，替代 Celery。
- 每次提交任务即在后台线程执行
- 进度通过 DB 字段持久化（前端轮询即可）
- 可选通过 Flask-SocketIO 推送实时进度
"""

from __future__ import annotations

import json
import random
import time
from datetime import datetime
from threading import Thread

from flask import Flask
from loguru import logger

from ..extensions import db, socketio
from ..models import AnalysisTask, BehaviorRecord, EmotionRecord, Video


def submit_analysis(app: Flask, task_id: int) -> None:
    """提交一个分析任务到后台线程。"""

    def _runner():
        with app.app_context():
            try:
                _process_task(task_id)
            except Exception as exc:  # noqa: BLE001
                logger.exception(f"分析任务 {task_id} 异常：{exc}")
                _fail_task(task_id, str(exc))

    Thread(target=_runner, daemon=True, name=f"analyze-{task_id}").start()


def _process_task(task_id: int) -> None:
    task = db.session.get(AnalysisTask, task_id)
    if not task:
        logger.error(f"任务 {task_id} 不存在")
        return
    video = db.session.get(Video, task.video_id)
    if not video:
        _fail_task(task_id, "视频记录不存在")
        return

    logger.info(f"开始分析任务 {task_id}，视频 {video.title}")
    task.status = "running"
    task.started_at = datetime.utcnow()
    task.progress = 0
    db.session.commit()
    _emit_progress(task)

    # 真实实现：抽帧 + 调 AI 服务
    # 为了"演示友好"，我们采用：检测 OpenCV 是否可用，否则走 mock 抽帧
    frames: list[tuple[float, bytes | None]] = _extract_frames(video, task.sample_interval_sec)
    task.total_frames = len(frames)
    db.session.commit()

    # 逐帧调用 AI 流水线（当帧数据为 None 时直接 mock）
    from ..ai import get_ai_client

    client = get_ai_client()

    behavior_summary: dict[str, int] = {}
    emotion_summary: dict[str, int] = {}

    for idx, (ts, frame_bytes) in enumerate(frames):
        try:
            if frame_bytes:
                be = client.behavior_detect(frame_bytes)
                em = client.emotion_predict(frame_bytes)
                be_data = be.get("data") or {}
                em_data = em.get("data") or {}
            else:
                be_data = _mock_behavior()
                em_data = _mock_emotion()

            for det in be_data.get("detections", []):
                _add_behavior(task, video, ts, det)
                behavior_summary[det["label_cn"]] = behavior_summary.get(det["label_cn"], 0) + 1

            if em_data:
                _add_emotion(task, video, ts, em_data)
                ecn = em_data.get("emotion_cn") or em_data.get("emotion") or "未知"
                emotion_summary[ecn] = emotion_summary.get(ecn, 0) + 1

        except Exception as exc:  # noqa: BLE001
            logger.warning(f"帧 {idx} 分析失败：{exc}")

        task.processed_frames = idx + 1
        task.progress = int((idx + 1) / len(frames) * 100)
        if (idx + 1) % max(1, len(frames) // 20) == 0 or idx + 1 == len(frames):
            db.session.commit()
            _emit_progress(task)

    summary = {
        "behavior_summary": behavior_summary,
        "emotion_summary": emotion_summary,
        "total_frames": task.total_frames,
        "sample_interval_sec": task.sample_interval_sec,
        "dominant_emotion": _top_key(emotion_summary),
        "top_behaviors": sorted(
            behavior_summary.items(), key=lambda x: x[1], reverse=True
        )[:5],
    }
    task.summary = json.dumps(summary, ensure_ascii=False)
    task.status = "success"
    task.progress = 100
    task.finished_at = datetime.utcnow()
    db.session.commit()
    _emit_progress(task)
    logger.success(f"任务 {task_id} 分析完成，{task.total_frames} 帧")


def _extract_frames(video: Video, interval: float) -> list[tuple[float, bytes | None]]:
    """抽帧。若视频文件存在且 OpenCV 可用则真实抽，否则生成 mock 抽帧时间轴。"""
    interval = max(0.5, float(interval or 2.0))

    # 演示友好的 mock：假设时长 60s 或来自 DB
    duration = video.duration_seconds if video.duration_seconds > 0 else 60.0

    # 尝试真实抽帧
    frames: list[tuple[float, bytes | None]] = []
    path = None
    try:
        from ..utils.storage import get_storage

        path = get_storage().get_path(video.storage_key)
    except Exception:  # noqa: BLE001
        path = None

    if path and _can_use_opencv():
        try:
            import cv2  # type: ignore

            cap = cv2.VideoCapture(path)
            fps = cap.get(cv2.CAP_PROP_FPS) or 25
            total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
            if total > 0:
                step = max(1, int(fps * interval))
                for frame_idx in range(0, total, step):
                    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                    ok, frame = cap.read()
                    if not ok:
                        continue
                    ts = frame_idx / fps
                    _, buf = cv2.imencode(".jpg", frame)
                    frames.append((ts, buf.tobytes()))
            cap.release()
            if frames:
                return frames
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"真实抽帧失败，改 mock：{exc}")

    # Mock 抽帧：只生成时间点，不带图像
    ts = 0.0
    while ts < duration:
        frames.append((ts, None))
        ts += interval
    if not frames:
        frames.append((0.0, None))
    return frames


def _can_use_opencv() -> bool:
    try:
        import cv2  # noqa: F401  # type: ignore

        return True
    except ImportError:
        return False


def _add_behavior(task: AnalysisTask, video: Video, ts: float, det: dict) -> None:
    db.session.add(
        BehaviorRecord(
            task_id=task.id,
            video_id=video.id,
            frame_time=float(ts),
            label=det.get("label", ""),
            label_cn=det.get("label_cn", det.get("label", "")),
            confidence=float(det.get("confidence", 0.0)),
            bbox=json.dumps(det.get("bbox") or [], ensure_ascii=False),
        )
    )


def _add_emotion(task: AnalysisTask, video: Video, ts: float, em: dict) -> None:
    db.session.add(
        EmotionRecord(
            task_id=task.id,
            video_id=video.id,
            frame_time=float(ts),
            emotion=em.get("emotion", "Neutral"),
            emotion_cn=em.get("emotion_cn", em.get("emotion", "中性")),
            confidence=float(em.get("confidence", 0.0)),
        )
    )


def _mock_behavior() -> dict:
    """与 AI 行为流水线标准八类一致（mock 演示）。"""
    eight = (
        "低头写字",
        "低头看书",
        "抬头听课",
        "转头",
        "举手",
        "站立",
        "小组讨论",
        "教师指导",
    )
    n = random.randint(3, 8)
    detections: list[dict] = []
    for _ in range(n):
        cn = random.choice(eight)
        detections.append({
            "label": cn,
            "label_cn": cn,
            "confidence": random.uniform(0.65, 0.92),
            "bbox": [random.randint(0, 80), random.randint(0, 60), 120, 200],
        })
    summary: dict[str, int] = {}
    for d in detections:
        summary[d["label_cn"]] = summary.get(d["label_cn"], 0) + 1
    return {"detections": detections, "summary": summary}


def _mock_emotion() -> dict:
    weights = [0.35, 0.25, 0.12, 0.10, 0.08, 0.06, 0.04]  # 中性/高兴/专注/惊讶/疲惫/...
    labels_cn = ["中性", "高兴", "专注", "惊讶", "疲惫", "悲伤", "愤怒"]
    labels_en = ["Neutral", "Happiness", "Focus", "Surprise", "Tired", "Sadness", "Anger"]
    idx = random.choices(range(len(labels_cn)), weights=weights)[0]
    return {
        "emotion": labels_en[idx],
        "emotion_cn": labels_cn[idx],
        "confidence": random.uniform(0.6, 0.95),
    }


def _top_key(counts: dict[str, int]) -> str | None:
    if not counts:
        return None
    return max(counts.items(), key=lambda x: x[1])[0]


def _fail_task(task_id: int, message: str) -> None:
    task = db.session.get(AnalysisTask, task_id)
    if not task:
        return
    task.status = "failed"
    task.error_message = message
    task.finished_at = datetime.utcnow()
    db.session.commit()
    _emit_progress(task)


def _emit_progress(task: AnalysisTask) -> None:
    try:
        socketio.emit(
            "analysis_progress",
            {
                "task_id": task.id,
                "status": task.status,
                "progress": task.progress,
                "processed": task.processed_frames,
                "total": task.total_frames,
            },
            namespace="/ws",
        )
    except Exception:  # noqa: BLE001
        pass
