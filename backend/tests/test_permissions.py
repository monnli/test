"""数据范围权限测试。"""

from __future__ import annotations


def test_admin_sees_all_classes(seeded_app, client, login):
    headers = login("admin")
    resp = client.get("/api/orgs/classes", headers=headers)
    assert resp.status_code == 200
    items = resp.get_json()["data"]["items"]
    assert len(items) == 2  # 学校全部 2 个班


def test_head_teacher_sees_own_class(seeded_app, client, login):
    headers = login("head1")
    resp = client.get("/api/orgs/classes", headers=headers)
    assert resp.status_code == 200
    items = resp.get_json()["data"]["items"]
    # 班主任虽然班级直接管理 1 个，但又教语文（在 1 班）
    assert len(items) == 1
    assert items[0]["name"] == "1 班"


def test_subject_teacher_sees_taught_classes(seeded_app, client, login):
    headers = login("sub1")
    resp = client.get("/api/orgs/classes", headers=headers)
    assert resp.status_code == 200
    items = resp.get_json()["data"]["items"]
    # 数学老师教 1、2 班数学
    assert {i["name"] for i in items} == {"1 班", "2 班"}


def test_subject_teacher_sees_only_taught_students(seeded_app, client, login):
    headers = login("sub1")
    resp = client.get("/api/orgs/students", headers=headers)
    assert resp.status_code == 200
    body = resp.get_json()["data"]
    # 1 班 3 + 2 班 3 = 6
    assert body["total"] == 6


def test_head_teacher_sees_only_own_class_students(seeded_app, client, login):
    headers = login("head1")
    resp = client.get("/api/orgs/students", headers=headers)
    assert resp.status_code == 200
    body = resp.get_json()["data"]
    assert body["total"] == 3


def test_subject_teacher_cannot_create_school(seeded_app, client, login):
    headers = login("sub1")
    resp = client.post(
        "/api/orgs/schools",
        json={"name": "新学校"},
        headers=headers,
    )
    assert resp.status_code == 403


def test_admin_can_create_grade(seeded_app, client, login):
    headers = login("admin")
    schools = client.get("/api/orgs/schools", headers=headers).get_json()["data"]["items"]
    school_id = schools[0]["id"]
    resp = client.post(
        "/api/orgs/grades",
        json={"school_id": school_id, "name": "八年级", "level": 8},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.get_json()["data"]["name"] == "八年级"
