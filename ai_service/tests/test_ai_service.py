"""AI 服务 mock 模式下的接口测试。

不依赖 GPU、不依赖本地模型权重、不依赖通义千问 API。
"""

from __future__ import annotations


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "healthy"


def test_info(client):
    resp = client.get("/info")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "device" in data
    assert "cuda_available" in data


def test_pipelines_status(client):
    resp = client.get("/pipelines")
    assert resp.status_code == 200
    data = resp.json()["data"]
    names = {p["name"] for p in data["pipelines"]}
    assert {"face", "emotion", "behavior", "text", "pose"}.issubset(names)


def test_face_detect_mock(client, sample_image_b64):
    resp = client.post("/face/detect", json={"image": sample_image_b64})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["count"] >= 1
    face = data["faces"][0]
    assert len(face["embedding"]) == 512
    assert face.get("_mock") is True


def test_face_match(client):
    embedding = [0.1] * 512
    candidates = [
        {"person_id": 1, "embedding": [0.1] * 512},
        {"person_id": 2, "embedding": [-0.1] * 512},
    ]
    resp = client.post(
        "/face/match",
        json={"query_embedding": embedding, "candidates": candidates, "threshold": 0.9},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["matched"] is True
    assert data["person_id"] == 1


def test_emotion_predict_mock(client, sample_image_b64):
    resp = client.post("/emotion/predict", json={"image": sample_image_b64})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "emotion_cn" in data
    assert "probs" in data


def test_behavior_detect_mock(client, sample_image_b64):
    resp = client.post("/behavior/detect", json={"image": sample_image_b64})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "detections" in data
    assert "summary" in data


def test_text_sentiment_positive(client):
    resp = client.post("/text/sentiment", json={"text": "今天特别开心"})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["polarity"] in ("正面", "中性", "负面")


def test_text_sentiment_risk_high(client):
    resp = client.post("/text/sentiment", json={"text": "我不想活了"})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["risk_level"] == "high"


def test_text_chat_risk_response(client):
    resp = client.post(
        "/text/chat",
        json={"messages": [{"role": "user", "content": "我想自杀"}]},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["risk_level"] == "high"
    assert "12320" in data["reply"] or "老师" in data["reply"]


def test_text_summarize(client):
    resp = client.post(
        "/text/summarize",
        json={"text": "今天有点难过。考试没考好。妈妈批评了我。晚上没怎么睡着。"},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "summary" in data
    assert "highlights" in data


def test_face_detect_bad_image(client):
    resp = client.post("/face/detect", json={"image": "not-a-valid-base64"})
    assert resp.status_code == 400


def test_classroom_analyze(client, sample_image_b64):
    resp = client.post(
        "/classroom/analyze",
        json={"image": sample_image_b64, "camera_key": "test_cam", "recognize_face": False},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "students" in data
    assert "summary" in data
    assert "total_persons" in data["summary"]
    assert "engagement_score" in data["summary"]
