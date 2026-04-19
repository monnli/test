"""认证接口测试。"""

from __future__ import annotations


def test_login_success(seeded_app, client):
    resp = client.post("/api/auth/login", json={"username": "admin", "password": "123456"})
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["code"] == 0
    assert body["data"]["access_token"]
    assert body["data"]["user"]["username"] == "admin"


def test_login_wrong_password(seeded_app, client):
    resp = client.post("/api/auth/login", json={"username": "admin", "password": "wrong"})
    assert resp.status_code == 401
    assert resp.get_json()["code"] in (401, 1)


def test_me_requires_token(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_me_with_token(seeded_app, client, login):
    headers = login("admin")
    resp = client.get("/api/auth/me", headers=headers)
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["data"]["username"] == "admin"
    assert "data_scope" in body["data"]


def test_change_password(seeded_app, client, login):
    headers = login("head1")
    resp = client.post(
        "/api/auth/change-password",
        json={"old_password": "123456", "new_password": "654321"},
        headers=headers,
    )
    assert resp.status_code == 200

    # 旧密码登录失败
    resp = client.post("/api/auth/login", json={"username": "head1", "password": "123456"})
    assert resp.status_code == 401
    # 新密码登录成功
    resp = client.post("/api/auth/login", json={"username": "head1", "password": "654321"})
    assert resp.status_code == 200
