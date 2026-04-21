"""姿态关键点 + 课堂行为派生流水线。

基于 MediaPipe Pose 的 33 关键点检测，派生课堂行为：
- 举手 / 趴桌 / 坐姿 / 站立 / 睡觉 / 抬头 / 低头
- 玩手机（结合 YOLO cell phone 检测框的 IoU）

Mock 模式：基于 bbox 位置与图像 hash 生成稳定的行为分布。
"""

from __future__ import annotations

import hashlib
import random
from typing import Any

import numpy as np
from loguru import logger

from .base import BasePipeline

# 行为标签中文映射
BEHAVIOR_LABELS_CN = {
    "hand_up": "举手",
    "lying": "趴桌",
    "sitting": "坐姿",
    "standing": "站立",
    "sleeping": "睡觉",
    "head_up": "抬头",
    "head_down": "低头",
    "using_phone": "玩手机",
    "talking": "交头接耳",
}


class PosePipeline(BasePipeline):
    name = "pose"

    def _load(self) -> None:
        import mediapipe as mp  # type: ignore

        self._model = mp.solutions.pose.Pose(
            static_image_mode=True,
            model_complexity=1,
            enable_segmentation=False,
            min_detection_confidence=0.3,
        )
        self._face_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.3,
        )

    def _infer(self, image: np.ndarray) -> dict[str, Any]:
        result = self._model.process(image)
        if not result.pose_landmarks:
            return {"behaviors": [], "landmarks": None, "pitch": None}

        # 提取关键点归一化坐标
        lms = [(lm.x, lm.y, lm.z, lm.visibility) for lm in result.pose_landmarks.landmark]

        # MediaPipe Pose 关键点索引（参考：https://google.github.io/mediapipe/solutions/pose）
        NOSE, LEFT_SHOULDER, RIGHT_SHOULDER = 0, 11, 12
        LEFT_ELBOW, RIGHT_ELBOW = 13, 14
        LEFT_WRIST, RIGHT_WRIST = 15, 16
        LEFT_HIP, RIGHT_HIP = 23, 24

        behaviors = _derive_pose_behaviors(lms)

        # pitch 角度（通过 FaceMesh 如果可用）
        pitch = None
        try:
            face_res = self._face_mesh.process(image)
            if face_res.multi_face_landmarks:
                pitch = _estimate_head_pitch(face_res.multi_face_landmarks[0])
                if pitch is not None:
                    if pitch < -25:
                        behaviors.append("head_down")
                    elif -10 < pitch < 20:
                        behaviors.append("head_up")
        except Exception:  # noqa: BLE001
            pass

        return {
            "behaviors": list(set(behaviors)),
            "landmarks": lms,
            "pitch": pitch,
            "behaviors_cn": [BEHAVIOR_LABELS_CN.get(b, b) for b in set(behaviors)],
        }

    def _mock(self, image: np.ndarray) -> dict[str, Any]:
        """Mock：基于图像 hash 随机生成稳定行为。"""
        seed = int(hashlib.md5(image.tobytes()).hexdigest()[:8], 16)
        rng = random.Random(seed)
        behaviors = []
        r = rng.random()
        if r < 0.06:
            behaviors.append("hand_up")
        if r < 0.03:
            behaviors.append("lying")
        if r < 0.02:
            behaviors.append("sleeping")
        if rng.random() < 0.7:
            behaviors.append("head_up")
        else:
            behaviors.append("head_down")
        behaviors.append("sitting")

        return {
            "behaviors": behaviors,
            "landmarks": None,
            "pitch": rng.uniform(-30, 15),
            "behaviors_cn": [BEHAVIOR_LABELS_CN.get(b, b) for b in behaviors],
            "_mock": True,
        }


def _derive_pose_behaviors(lms: list[tuple[float, float, float, float]]) -> list[str]:
    """从关键点派生行为。"""
    if not lms or len(lms) < 25:
        return []

    NOSE = 0
    LEFT_SHOULDER, RIGHT_SHOULDER = 11, 12
    LEFT_WRIST, RIGHT_WRIST = 15, 16
    LEFT_HIP, RIGHT_HIP = 23, 24

    behaviors = []

    try:
        nose_y = lms[NOSE][1]
        ls_y = lms[LEFT_SHOULDER][1]
        rs_y = lms[RIGHT_SHOULDER][1]
        lw_y = lms[LEFT_WRIST][1]
        rw_y = lms[RIGHT_WRIST][1]
        lh_y = lms[LEFT_HIP][1]
        rh_y = lms[RIGHT_HIP][1]

        # 可见性阈值
        vis = 0.5

        # 举手：手腕高于肩膀 15% 画面高度
        if lms[LEFT_WRIST][3] > vis and lw_y < ls_y - 0.10:
            behaviors.append("hand_up")
        if lms[RIGHT_WRIST][3] > vis and rw_y < rs_y - 0.10:
            behaviors.append("hand_up")

        # 趴桌：鼻子低于肩膀 30% 画面高度（正常时鼻子 < 肩膀）
        if lms[NOSE][3] > vis and (ls_y + rs_y) / 2 > 0 and nose_y > (ls_y + rs_y) / 2 + 0.15:
            behaviors.append("lying")

        # 站立 / 坐姿：根据躯干高度比例
        if lms[LEFT_HIP][3] > vis and lms[RIGHT_HIP][3] > vis:
            shoulder_y = (ls_y + rs_y) / 2
            hip_y = (lh_y + rh_y) / 2
            body_height = hip_y - shoulder_y
            if body_height > 0.35:  # 躯干相对较长 → 站立
                behaviors.append("standing")
            else:
                behaviors.append("sitting")
        else:
            behaviors.append("sitting")

    except Exception as exc:  # noqa: BLE001
        logger.debug(f"pose derive error: {exc}")

    return behaviors


def _estimate_head_pitch(face_landmarks) -> float | None:
    """用 FaceMesh 估计头部 pitch 角度（正值为抬头，负值为低头）。"""
    try:
        # 使用简化方法：鼻尖 vs 眼睛中心的 y 差
        # FaceMesh 468 关键点标准：鼻尖 1，左眼外角 33，右眼外角 263
        nose = face_landmarks.landmark[1]
        left_eye = face_landmarks.landmark[33]
        right_eye = face_landmarks.landmark[263]
        eye_center_y = (left_eye.y + right_eye.y) / 2
        # 鼻尖相对眼睛的 y 差（正常时鼻子略低于眼睛）
        delta = (nose.y - eye_center_y)
        # 归一化为近似角度
        pitch = -(delta - 0.06) * 300  # 粗略映射
        return max(-60, min(60, pitch))
    except Exception:
        return None


pose_pipeline = PosePipeline()
