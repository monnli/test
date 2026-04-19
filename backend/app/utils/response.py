"""统一响应格式工具。"""

from __future__ import annotations

from typing import Any

from flask import jsonify


def ok(data: Any = None, message: str = "ok") -> tuple:
    return jsonify(code=0, message=message, data=data), 200


def fail(message: str, code: int = 1, status: int = 400, data: Any = None) -> tuple:
    return jsonify(code=code, message=message, data=data), status
