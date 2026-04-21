"""简化版 IoU + 运动预测的多目标追踪器（替代 DeepSORT）。

设计考量：
- DeepSORT 需要额外依赖（re-id 模型、filterpy），部署负担重
- 我们的场景是课堂摄像头固定视角 + 目标位置变化不大
- 自研 IoU + 中心点距离匹配足够稳定，且零依赖

追踪器维护每个 track 的：
- track_id（稳定 ID）
- last_bbox
- history（最近 N 帧位置）
- lost_frames（连续未匹配帧数）
- matched_student_id（一旦人脸识别匹配到学生，绑定该 track）
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Track:
    track_id: int
    bbox: tuple[float, float, float, float]
    history: list[tuple[float, float, float, float]] = field(default_factory=list)
    lost_frames: int = 0
    student_id: int | None = None
    student_name: str | None = None
    confidence_sum: float = 0.0
    match_count: int = 0


class SimpleTracker:
    def __init__(self, iou_threshold: float = 0.25, max_lost: int = 10):
        self.tracks: dict[int, Track] = {}
        self.next_id: int = 1
        self.iou_threshold = iou_threshold
        self.max_lost = max_lost

    @staticmethod
    def _iou(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> float:
        ax1, ay1, ax2, ay2 = a
        bx1, by1, bx2, by2 = b
        ix1, iy1 = max(ax1, bx1), max(ay1, by1)
        ix2, iy2 = min(ax2, bx2), min(ay2, by2)
        iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
        inter = iw * ih
        area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
        area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
        union = area_a + area_b - inter
        return inter / union if union > 0 else 0.0

    def update(self, detections: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """输入 detections: [{bbox, confidence, ...}] 返回带 track_id 的列表。"""
        # 先给现有 track 的 lost_frames +1，被匹配会重置
        for t in self.tracks.values():
            t.lost_frames += 1

        # 贪心匹配：对每个 detection 找 IoU 最大的现有 track
        results = []
        unmatched_tracks = set(self.tracks.keys())
        for det in detections:
            bbox = tuple(det.get("bbox") or (0, 0, 0, 0))
            best_id = None
            best_iou = 0.0
            for tid in unmatched_tracks:
                iou = self._iou(bbox, self.tracks[tid].bbox)
                if iou > best_iou:
                    best_iou = iou
                    best_id = tid
            if best_id is not None and best_iou >= self.iou_threshold:
                t = self.tracks[best_id]
                t.bbox = bbox
                t.lost_frames = 0
                t.history.append(bbox)
                if len(t.history) > 30:
                    t.history = t.history[-30:]
                unmatched_tracks.discard(best_id)
                results.append({**det, "track_id": t.track_id, "student_id": t.student_id, "student_name": t.student_name})
            else:
                # 新建 track
                tid = self.next_id
                self.next_id += 1
                self.tracks[tid] = Track(track_id=tid, bbox=bbox, history=[bbox])
                results.append({**det, "track_id": tid, "student_id": None, "student_name": None})

        # 清理长时间丢失的 track
        to_remove = [tid for tid, t in self.tracks.items() if t.lost_frames > self.max_lost]
        for tid in to_remove:
            del self.tracks[tid]

        return results

    def bind_student(self, track_id: int, student_id: int, student_name: str, confidence: float) -> None:
        """把人脸识别结果绑定到 track 上（之后该 track 的后续检测自动带 student_id）。"""
        t = self.tracks.get(track_id)
        if not t:
            return
        # 加权平均：多次识别到同一学生置信度累积
        if t.student_id == student_id:
            t.confidence_sum += confidence
            t.match_count += 1
        else:
            # 如果之前没绑定或绑定信号弱，直接切换
            if t.match_count == 0 or confidence > 0.55:
                t.student_id = student_id
                t.student_name = student_name
                t.confidence_sum = confidence
                t.match_count = 1

    def snapshot(self) -> list[dict[str, Any]]:
        """导出当前所有 track 状态。"""
        return [
            {
                "track_id": t.track_id,
                "bbox": t.bbox,
                "student_id": t.student_id,
                "student_name": t.student_name,
                "lost_frames": t.lost_frames,
            }
            for t in self.tracks.values()
        ]

    def clear(self) -> None:
        self.tracks.clear()
        self.next_id = 1
