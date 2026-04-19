"""预警 / 关联分析测试。"""

from __future__ import annotations


def test_recompute_creates_alerts_for_no_data(seeded_app, client, login):
    headers = login("admin")
    r = client.post("/api/alerts/recompute", headers=headers)
    assert r.status_code == 200
    data = r.get_json()["data"]
    assert data["processed"] == 6
    # 学生没有任何数据 → 大概率是 green 不创建预警
    assert data["alerts_count"] == 0


def test_alert_workflow(seeded_app, client, login):
    headers = login("admin")
    # 手动写入一条预警以便测试工单流转
    from app.extensions import db
    from app.models import Alert, Student

    student = db.session.query(Student).first()
    alert = Alert(
        student_id=student.id,
        level="red",
        score=80.0,
        title="测试预警",
        reasons='["测试原因"]',
        sources='["测试"]',
        status="open",
    )
    db.session.add(alert)
    db.session.commit()

    listing = client.get("/api/alerts", headers=headers).get_json()["data"]
    assert listing["total"] >= 1

    stats = client.get("/api/alerts/stats", headers=headers).get_json()["data"]
    assert stats["by_level"].get("red", 0) >= 1

    r = client.post(f"/api/alerts/{alert.id}/acknowledge", headers=headers)
    assert r.status_code == 200
    assert r.get_json()["data"]["status"] == "acknowledged"

    r = client.post(
        f"/api/alerts/{alert.id}/interventions",
        json={"action": "谈话", "summary": "已与学生沟通", "follow_up": "下周回访"},
        headers=headers,
    )
    assert r.status_code == 200

    intervs = client.get(f"/api/alerts/{alert.id}/interventions", headers=headers).get_json()["data"]
    assert intervs["items"][0]["action"] == "谈话"

    r = client.post(f"/api/alerts/{alert.id}/resolve", json={"note": "已干预"}, headers=headers)
    assert r.get_json()["data"]["status"] == "resolved"

    r = client.post(f"/api/alerts/{alert.id}/close", headers=headers)
    assert r.get_json()["data"]["status"] == "closed"


def test_correlation_matrix(seeded_app, client, login):
    headers = login("admin")
    r = client.get("/api/alerts/correlation/matrix", headers=headers)
    assert r.status_code == 200
    data = r.get_json()["data"]
    assert "items" in data
    assert "fields" in data
