"""课堂视频分析 API 测试（mock 模式）。"""

from __future__ import annotations

import io
import time

import pytest

from app.ai import client as ai_client_module


@pytest.fixture(autouse=True)
def mock_ai_service(monkeypatch):
    def _behavior(self, image_bytes, conf=0.35):
        return {
            "code": 0,
            "data": {
                "detections": [
                    {"label": "person", "label_cn": "学生", "confidence": 0.9, "bbox": [0, 0, 10, 10]},
                    {"label": "hand_up", "label_cn": "举手", "confidence": 0.7, "bbox": [0, 0, 5, 5]},
                ],
                "summary": {"学生": 1, "举手": 1},
            },
        }

    def _emotion(self, image_bytes):
        return {
            "code": 0,
            "data": {
                "emotion": "Happiness",
                "emotion_cn": "高兴",
                "confidence": 0.85,
                "probs": {"Happiness": 0.85},
            },
        }

    monkeypatch.setattr(ai_client_module.AIClient, "behavior_detect", _behavior)
    monkeypatch.setattr(ai_client_module.AIClient, "emotion_predict", _emotion)


def _fake_video_file() -> tuple[bytes, str]:
    # 不是真实视频，后端使用 OpenCV 探测失败时会退回 mock
    return b"\x00\x00\x00\x20ftypisom", "sample.mp4"


def test_upload_and_analyze(seeded_app, client, login):
    headers = login("admin")
    data, fname = _fake_video_file()
    resp = client.post(
        "/api/classroom/videos",
        data={
            "file": (io.BytesIO(data), fname),
            "title": "测试视频",
        },
        headers=headers,
        content_type="multipart/form-data",
    )
    assert resp.status_code == 200, resp.get_json()
    video = resp.get_json()["data"]
    assert video["id"]

    r = client.post(f"/api/classroom/videos/{video['id']}/analyze", headers=headers)
    assert r.status_code == 200
    task = r.get_json()["data"]
    assert task["status"] in ("pending", "running", "success")

    # 轮询任务完成
    for _ in range(50):
        detail = client.get(f"/api/classroom/tasks/{task['id']}", headers=headers).get_json()["data"]
        if detail["status"] in ("success", "failed"):
            break
        time.sleep(0.2)

    report = client.get(f"/api/classroom/tasks/{task['id']}/report", headers=headers).get_json()["data"]
    assert report["task"]["status"] == "success"
    assert len(report["behavior_timeline"]) > 0
    assert len(report["emotion_timeline"]) > 0
    assert report["metrics"]["hand_up_count"] > 0


def test_list_videos_empty(seeded_app, client, login):
    headers = login("admin")
    resp = client.get("/api/classroom/videos", headers=headers)
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert "items" in data


def test_upload_without_file(seeded_app, client, login):
    headers = login("admin")
    resp = client.post(
        "/api/classroom/videos",
        data={},
        headers=headers,
        content_type="multipart/form-data",
    )
    assert resp.status_code in (400, 422)
