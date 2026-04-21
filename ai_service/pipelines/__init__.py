"""AI 流水线集合。"""

from .base import PipelineStatus
from .behavior_pipeline import CLASSROOM_BEHAVIORS_CN, behavior_pipeline
from .classroom_pipeline import analyze as analyze_classroom_frame
from .classroom_pipeline import reset_tracker as reset_classroom_tracker
from .emotion_pipeline import EMOTION_LABELS_CN, emotion_pipeline
from .face_pipeline import cosine_similarity, face_pipeline, find_best_match
from .pose_pipeline import BEHAVIOR_LABELS_CN, pose_pipeline
from .text_pipeline import text_pipeline

__all__ = [
    "PipelineStatus",
    "behavior_pipeline",
    "emotion_pipeline",
    "face_pipeline",
    "pose_pipeline",
    "text_pipeline",
    "cosine_similarity",
    "find_best_match",
    "CLASSROOM_BEHAVIORS_CN",
    "EMOTION_LABELS_CN",
    "BEHAVIOR_LABELS_CN",
    "analyze_classroom_frame",
    "reset_classroom_tracker",
]
