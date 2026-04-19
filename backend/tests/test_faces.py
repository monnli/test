"""人脸库 API 测试。

AI 服务通过 monkeypatch 模拟，不依赖真实 AI 服务进程。
"""

from __future__ import annotations

import io
import pytest
from PIL import Image

from app.ai import client as ai_client_module


@pytest.fixture(autouse=True)
def mock_ai_service(monkeypatch):
    """Mock 出 AI 服务的返回，避免测试依赖外部进程。"""
    fake_embedding = [0.1] * 512

    def _face_detect(self, image_bytes):
        return {
            "code": 0,
            "message": "ok",
            "data": {
                "faces": [
                    {
                        "bbox": [10, 10, 100, 120],
                        "confidence": 0.95,
                        "embedding": fake_embedding,
                    }
                ],
                "count": 1,
                "pipeline_status": "mock",
            },
        }

    def _face_match(self, query_embedding, candidates, threshold=0.45):
        if not candidates:
            return {"code": 0, "data": {"matched": False, "person_id": None, "score": -1.0}}
        return {
            "code": 0,
            "data": {
                "matched": True,
                "person_id": candidates[0]["person_id"],
                "score": 0.99,
            },
        }

    monkeypatch.setattr(ai_client_module.AIClient, "face_detect", _face_detect)
    monkeypatch.setattr(ai_client_module.AIClient, "face_match", _face_match)


def _mini_jpg_bytes() -> bytes:
    img = Image.new("RGB", (120, 160), color=(200, 150, 130))
    buf = io.BytesIO()
    img.save(buf, "JPEG")
    return buf.getvalue()


def _make_student(seeded_app):
    """seeded_app 已创建 6 个学生，取第一个。"""
    from app.extensions import db
    from app.models import Student

    return db.session.query(Student).first()


def test_face_library_stats_empty(seeded_app, client, login):
    headers = login("admin")
    resp = client.get("/api/faces/stats", headers=headers)
    assert resp.status_code == 200
    data = resp.json["data"]
    assert data["total_faces"] == 0
    assert data["registered_students"] == 0
    assert data["total_students"] == 6


def test_register_face_via_base64(seeded_app, client, login):
    headers = login("admin")
    student = _make_student(seeded_app)

    import base64

    b64 = base64.b64encode(_mini_jpg_bytes()).decode()
    resp = client.post(
        f"/api/faces/by-student/{student.id}",
        json={"image": b64},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json["data"]
    assert data["student_id"] == student.id
    assert data["dim"] == 512


def test_register_face_dedup(seeded_app, client, login):
    headers = login("admin")
    student = _make_student(seeded_app)
    import base64

    b64 = base64.b64encode(_mini_jpg_bytes()).decode()
    r1 = client.post(f"/api/faces/by-student/{student.id}", json={"image": b64}, headers=headers)
    r2 = client.post(f"/api/faces/by-student/{student.id}", json={"image": b64}, headers=headers)
    assert r1.status_code == 200 and r2.status_code == 200
    assert r2.json["data"].get("duplicated") is True


def test_list_faces(seeded_app, client, login):
    headers = login("admin")
    student = _make_student(seeded_app)
    import base64

    b64 = base64.b64encode(_mini_jpg_bytes()).decode()
    client.post(f"/api/faces/by-student/{student.id}", json={"image": b64}, headers=headers)
    resp = client.get(f"/api/faces/by-student/{student.id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json["data"]["total"] >= 1


def test_face_recognize(seeded_app, client, login):
    headers = login("admin")
    student = _make_student(seeded_app)
    import base64

    b64 = base64.b64encode(_mini_jpg_bytes()).decode()
    client.post(f"/api/faces/by-student/{student.id}", json={"image": b64}, headers=headers)

    resp = client.post("/api/faces/recognize", json={"image": b64}, headers=headers)
    assert resp.status_code == 200
    data = resp.json["data"]
    assert data["count"] >= 1
    assert data["results"][0]["matched"] is True
    assert data["results"][0]["student"]["id"] == student.id


def test_register_face_requires_admin(seeded_app, client, login):
    headers = login("sub1")
    student = _make_student(seeded_app)
    import base64

    b64 = base64.b64encode(_mini_jpg_bytes()).decode()
    resp = client.post(
        f"/api/faces/by-student/{student.id}",
        json={"image": b64},
        headers=headers,
    )
    assert resp.status_code == 403


def test_delete_face(seeded_app, client, login):
    headers = login("admin")
    student = _make_student(seeded_app)
    import base64

    b64 = base64.b64encode(_mini_jpg_bytes()).decode()
    created = client.post(
        f"/api/faces/by-student/{student.id}",
        json={"image": b64},
        headers=headers,
    ).json["data"]
    resp = client.delete(f"/api/faces/{created['id']}", headers=headers)
    assert resp.status_code == 200
    listed = client.get(f"/api/faces/by-student/{student.id}", headers=headers).json["data"]
    assert listed["total"] == 0
