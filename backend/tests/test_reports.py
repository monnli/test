"""报告中心测试。"""

from __future__ import annotations

import pytest

from app.ai import client as ai_client_module


@pytest.fixture(autouse=True)
def mock_ai_chat(monkeypatch):
    def _chat(self, messages, system=None):
        return {"code": 0, "data": {"reply": "AI 综合建议：保持现状", "risk_level": "none", "risk_keywords": []}}

    monkeypatch.setattr(ai_client_module.AIClient, "text_chat", _chat)


def test_generate_school_and_download(seeded_app, client, login):
    headers = login("admin")
    r = client.post("/api/reports/school", headers=headers)
    assert r.status_code == 200
    rep = r.get_json()["data"]
    assert rep["type"] == "school"

    detail = client.get(f"/api/reports/{rep['id']}", headers=headers).get_json()["data"]
    assert "学校心理健康综合报告" in detail["content"]

    pdf_resp = client.get(f"/api/reports/{rep['id']}/pdf", headers=headers)
    assert pdf_resp.status_code == 200
    assert len(pdf_resp.data) > 100


def test_generate_class_report(seeded_app, client, login):
    headers = login("admin")
    from app.extensions import db
    from app.models import Clazz

    c = db.session.query(Clazz).first()
    r = client.post(f"/api/reports/class/{c.id}", headers=headers)
    assert r.status_code == 200
    assert r.get_json()["data"]["type"] == "class"


def test_generate_student_report(seeded_app, client, login):
    headers = login("admin")
    from app.extensions import db
    from app.models import Student

    s = db.session.query(Student).first()
    r = client.post(f"/api/reports/student/{s.id}", headers=headers)
    assert r.status_code == 200
    assert r.get_json()["data"]["type"] == "student"


def test_list_reports(seeded_app, client, login):
    headers = login("admin")
    client.post("/api/reports/school", headers=headers)
    r = client.get("/api/reports", headers=headers)
    assert r.status_code == 200
    assert r.get_json()["data"]["total"] >= 1
