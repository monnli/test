"""心理健康 API 测试。"""

from __future__ import annotations

import pytest

from app.ai import client as ai_client_module


@pytest.fixture(autouse=True)
def mock_ai(monkeypatch):
    def _sentiment(self, text):
        risk = "high" if "死" in text or "自杀" in text else ("low" if "难过" in text else "none")
        return {
            "code": 0,
            "data": {
                "polarity": "负面" if risk == "high" else "正面",
                "emotion_tags": ["难过"] if risk != "none" else ["平和"],
                "risk_level": risk,
                "risk_keywords": ["死"] if risk == "high" else [],
            },
        }

    def _summarize(self, text):
        return {"code": 0, "data": {"summary": text[:30], "highlights": [text[:20]], "suggestion": "关注"}}

    def _chat(self, messages, system=None):
        last = messages[-1]["content"]
        risk = "high" if "死" in last or "自杀" in last else "none"
        return {
            "code": 0,
            "data": {
                "reply": "我陪你慢慢说" if risk == "none" else "请联系老师或拨打 12320",
                "risk_level": risk,
                "risk_keywords": ["死"] if risk == "high" else [],
            },
        }

    monkeypatch.setattr(ai_client_module.AIClient, "text_sentiment", _sentiment)
    monkeypatch.setattr(ai_client_module.AIClient, "text_summarize", _summarize)
    monkeypatch.setattr(ai_client_module.AIClient, "text_chat", _chat)


def test_seed_and_list_scales(seeded_app, client, login):
    headers = login("admin")
    seeded = client.post("/api/psychology/scales/seed", headers=headers).get_json()["data"]
    assert seeded["seeded"] >= 5

    r = client.get("/api/psychology/scales", headers=headers)
    items = r.get_json()["data"]["items"]
    assert len(items) == 5
    codes = {it["code"] for it in items}
    assert {"PHQ-9", "GAD-7", "SCARED", "CES-DC", "MHT"}.issubset(codes)


def test_assessment_phq9_full_zero(seeded_app, client, login):
    headers = login("admin")
    client.post("/api/psychology/scales/seed", headers=headers)
    scales = client.get("/api/psychology/scales", headers=headers).get_json()["data"]["items"]
    phq = next(s for s in scales if s["code"] == "PHQ-9")
    detail = client.get(f"/api/psychology/scales/{phq['id']}", headers=headers).get_json()["data"]
    answers = {q["id"]: 0 for q in detail["questions"]}

    from app.extensions import db
    from app.models import Student

    student = db.session.query(Student).first()

    r = client.post(
        "/api/psychology/assessments",
        json={"student_id": student.id, "scale_id": phq["id"], "answers": answers},
        headers=headers,
    )
    assert r.status_code == 200
    data = r.get_json()["data"]
    assert data["total_score"] == 0
    assert data["level"] == "无明显抑郁"


def test_assessment_phq9_full_high(seeded_app, client, login):
    headers = login("admin")
    client.post("/api/psychology/scales/seed", headers=headers)
    scales = client.get("/api/psychology/scales", headers=headers).get_json()["data"]["items"]
    phq = next(s for s in scales if s["code"] == "PHQ-9")
    detail = client.get(f"/api/psychology/scales/{phq['id']}", headers=headers).get_json()["data"]
    answers = {q["id"]: 3 for q in detail["questions"]}

    from app.extensions import db
    from app.models import Student

    student = db.session.query(Student).first()
    r = client.post(
        "/api/psychology/assessments",
        json={"student_id": student.id, "scale_id": phq["id"], "answers": answers},
        headers=headers,
    )
    assert r.status_code == 200
    data = r.get_json()["data"]
    assert data["total_score"] == 27
    assert data["level"] == "重度抑郁"


def test_text_analysis(seeded_app, client, login):
    headers = login("admin")
    from app.extensions import db
    from app.models import Student

    student = db.session.query(Student).first()
    r = client.post(
        "/api/psychology/text-analyses",
        json={
            "student_id": student.id,
            "title": "周记",
            "content": "今天心里特别难过，考试又没考好",
        },
        headers=headers,
    )
    assert r.status_code == 200
    data = r.get_json()["data"]
    assert data["risk_level"] == "low"


def test_chat_high_risk(seeded_app, client, login):
    headers = login("admin")
    from app.extensions import db
    from app.models import Student

    student = db.session.query(Student).first()
    conv = client.post(
        "/api/psychology/conversations",
        json={"student_id": student.id, "title": "测试"},
        headers=headers,
    ).get_json()["data"]

    r = client.post(
        f"/api/psychology/conversations/{conv['id']}/messages",
        json={"content": "我想去死"},
        headers=headers,
    )
    assert r.status_code == 200
    data = r.get_json()["data"]
    assert data["assistant_message"]["risk_level"] == "high"
    assert "12320" in data["assistant_message"]["content"]


def test_profile(seeded_app, client, login):
    headers = login("admin")
    client.post("/api/psychology/scales/seed", headers=headers)
    from app.extensions import db
    from app.models import Student

    student = db.session.query(Student).first()
    r = client.get(f"/api/psychology/students/{student.id}/profile", headers=headers)
    assert r.status_code == 200
    data = r.get_json()["data"]
    assert data["student"]["id"] == student.id
    assert "timeline" in data
