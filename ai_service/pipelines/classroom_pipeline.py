"""综合课堂分析流水线：一帧输入 → 全维度分析输出。

流程：
1. YOLO 检出 person + cell phone
2. 简易追踪器给每个 person 分配稳定 track_id
3. 对每个 person 裁图：
   - InsightFace 人脸识别 → 匹配人脸库得 student_id
   - MediaPipe Pose → 派生行为（举手/趴桌/...）
   - HSEmotion → 表情
4. 计算玩手机（person 与 phone IoU）
5. 计算参与度（当前帧级）

对外：一个 analyze(image, face_library=[], camera_id=None) 方法。
"""

from __future__ import annotations

from typing import Any

import numpy as np
from loguru import logger

from .behavior_pipeline import behavior_pipeline
from .emotion_pipeline import emotion_pipeline
from .face_pipeline import face_pipeline, find_best_match
from .pose_pipeline import pose_pipeline
from .tracker import SimpleTracker

# 各摄像头独立一个 tracker（用 camera_id 做 key）
_trackers: dict[str, SimpleTracker] = {}


def get_tracker(camera_key: str) -> SimpleTracker:
    if camera_key not in _trackers:
        _trackers[camera_key] = SimpleTracker()
    return _trackers[camera_key]


def reset_tracker(camera_key: str) -> None:
    _trackers.pop(camera_key, None)


def analyze(
    image: np.ndarray,
    face_library: list[dict[str, Any]] | None = None,
    camera_key: str = "default",
    recognize_face: bool = True,
) -> dict[str, Any]:
    """对一帧图像做全维度分析。

    Args:
        image: RGB ndarray
        face_library: [{person_id, embedding, name}] 可选
        camera_key: 摄像头 ID，用于独立的追踪器
        recognize_face: 是否调用 InsightFace（实时流可每 N 帧调一次以降低计算）
    """
    h, w = image.shape[:2]

    # 1. 行为检测（返回 person/cell phone/...）
    beh_result = behavior_pipeline.run(image)
    all_dets = beh_result.get("detections", [])
    persons = [d for d in all_dets if d.get("label") == "person"]
    phones = [d for d in all_dets if d.get("label") == "cell phone"]

    # 2. 追踪
    tracker = get_tracker(camera_key)
    tracked = tracker.update(persons)

    # 3. 对每个 track 做精细分析
    students: list[dict[str, Any]] = []
    for t in tracked:
        bbox = t.get("bbox") or [0, 0, 0, 0]
        x1, y1, x2, y2 = [int(max(0, v)) for v in bbox]
        x2 = min(w, x2)
        y2 = min(h, y2)
        if x2 <= x1 or y2 <= y1:
            continue
        crop = image[y1:y2, x1:x2]
        if crop.size == 0:
            continue

        # 3a. 人脸识别（可选，且仅对新 track 或久未识别的做）
        student_info = {"student_id": t.get("student_id"), "student_name": t.get("student_name"), "face_score": None}
        if recognize_face and face_library and (t.get("student_id") is None or t.get("_force_reid", False)):
            try:
                faces = face_pipeline.run(crop)
                if faces:
                    emb = faces[0].get("embedding")
                    if emb:
                        match = find_best_match(emb, face_library, threshold=0.42)
                        if match and match.get("matched"):
                            pid = match.get("person_id")
                            name = next((c.get("name") for c in face_library if c.get("person_id") == pid), None)
                            tracker.bind_student(
                                t["track_id"], int(pid), name or f"#{pid}", float(match.get("score") or 0)
                            )
                            student_info["student_id"] = int(pid)
                            student_info["student_name"] = name
                            student_info["face_score"] = float(match.get("score") or 0)
            except Exception as exc:  # noqa: BLE001
                logger.debug(f"face reid failed: {exc}")

        # 3b. 姿态行为
        pose_result = pose_pipeline.run(crop)
        behaviors = list(pose_result.get("behaviors") or [])
        behaviors_cn = list(pose_result.get("behaviors_cn") or [])
        pitch = pose_result.get("pitch")

        # 3c. 表情
        emo_result = emotion_pipeline.run(crop)

        # 3d. 玩手机：手机 bbox 与人体下半身 IoU
        using_phone = False
        for p in phones:
            pb = p.get("bbox") or [0, 0, 0, 0]
            # 手机中心点是否在人体下半身范围内
            cx = (pb[0] + pb[2]) / 2
            cy = (pb[1] + pb[3]) / 2
            if bbox[0] <= cx <= bbox[2] and (bbox[1] + bbox[3]) / 2 <= cy <= bbox[3]:
                using_phone = True
                if "using_phone" not in behaviors:
                    behaviors.append("using_phone")
                    behaviors_cn.append("玩手机")
                break

        students.append({
            "track_id": t.get("track_id"),
            "bbox": bbox,
            "confidence": t.get("confidence"),
            **student_info,
            "behaviors": behaviors,
            "behaviors_cn": behaviors_cn,
            "pitch": pitch,
            "emotion": emo_result.get("emotion"),
            "emotion_cn": emo_result.get("emotion_cn"),
            "emotion_confidence": emo_result.get("confidence"),
            "using_phone": using_phone,
        })

    # 4. 汇总
    total = len(students)
    head_up = sum(1 for s in students if "head_up" in s["behaviors"])
    head_down = sum(1 for s in students if "head_down" in s["behaviors"])
    hand_up = sum(1 for s in students if "hand_up" in s["behaviors"])
    lying = sum(1 for s in students if "lying" in s["behaviors"])
    using_phone_cnt = sum(1 for s in students if s["using_phone"])
    sleeping = sum(1 for s in students if "sleeping" in s["behaviors"])

    # 5. 参与度分数
    if total > 0:
        head_up_rate = head_up / total
        hand_up_rate = min(1.0, hand_up / max(1, total * 0.2))  # 20% 学生举手认为满分
        lying_rate = lying / total
        phone_rate = using_phone_cnt / total
        positive_emotion = sum(1 for s in students if s.get("emotion_cn") in ("高兴", "专注", "中性")) / total
        engagement = (
            head_up_rate * 40
            + hand_up_rate * 20
            + positive_emotion * 20
            + (1 - lying_rate) * 10
            + (1 - phone_rate) * 10
        )
    else:
        engagement = 0.0

    return {
        "students": students,
        "summary": {
            "total_persons": total,
            "head_up": head_up,
            "head_down": head_down,
            "hand_up": hand_up,
            "lying": lying,
            "sleeping": sleeping,
            "using_phone": using_phone_cnt,
            "engagement_score": round(engagement, 1),
            "attendance": [s["student_id"] for s in students if s.get("student_id")],
        },
        "detections_raw": all_dets,
    }
