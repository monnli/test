"""健康检查接口测试。"""

from __future__ import annotations


def test_root(client):
    resp = client.get("/")
    assert resp.status_code == 200
    payload = resp.get_json()
    assert payload["name"] == "青苗守护者 API"


def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    payload = resp.get_json()
    assert payload["code"] == 0
    assert payload["data"]["status"] == "healthy"
