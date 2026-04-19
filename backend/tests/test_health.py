"""健康检查接口测试。"""

from __future__ import annotations

import pytest

from app import create_app
from config import TestingConfig


@pytest.fixture()
def app():
    application = create_app(TestingConfig)
    with application.app_context():
        yield application


@pytest.fixture()
def client(app):
    return app.test_client()


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
