"""业务异常。"""

from __future__ import annotations


class APIError(Exception):
    """业务异常。由全局错误处理捕获并转为统一响应。"""

    def __init__(self, message: str, code: int = 1, status: int = 400):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status = status


class AuthError(APIError):
    def __init__(self, message: str = "未授权", code: int = 401):
        super().__init__(message=message, code=code, status=401)


class PermissionDeniedError(APIError):
    def __init__(self, message: str = "无权访问该资源", code: int = 403):
        super().__init__(message=message, code=code, status=403)


class NotFoundError(APIError):
    def __init__(self, message: str = "资源不存在", code: int = 404):
        super().__init__(message=message, code=code, status=404)


class ConflictError(APIError):
    def __init__(self, message: str = "数据冲突", code: int = 409):
        super().__init__(message=message, code=code, status=409)


class ValidationError(APIError):
    def __init__(self, message: str = "参数错误", code: int = 422):
        super().__init__(message=message, code=code, status=422)
