"""应用配置。所有配置项从环境变量加载，支持 .env 文件。"""

from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

load_dotenv(PROJECT_ROOT / ".env")


def _get_bool(key: str, default: bool = False) -> bool:
    value = os.getenv(key)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _get_int(key: str, default: int) -> int:
    value = os.getenv(key)
    if value is None or value == "":
        return default
    try:
        return int(value)
    except ValueError:
        return default


class BaseConfig:
    """所有环境共用的基础配置。"""

    APP_NAME = "qingmiao-guardian"
    APP_ENV = os.getenv("APP_ENV", "development")
    DEBUG = _get_bool("FLASK_DEBUG", False)
    TESTING = False

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-please-change")

    # JWT
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=_get_int("JWT_ACCESS_TOKEN_EXPIRES", 3600))
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(seconds=_get_int("JWT_REFRESH_TOKEN_EXPIRES", 2592000))
    JWT_TOKEN_LOCATION = ["headers"]
    JWT_HEADER_NAME = "Authorization"
    JWT_HEADER_TYPE = "Bearer"

    # MySQL
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT = _get_int("MYSQL_PORT", 3306)
    MYSQL_USER = os.getenv("MYSQL_USER", "qingmiao")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "qingmiao123")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "qingmiao_guardian")

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
        f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 3600,
        "pool_size": 10,
        "max_overflow": 20,
    }

    # 文件存储
    STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "local").lower()  # local | minio
    LOCAL_STORAGE_DIR = Path(os.getenv("LOCAL_STORAGE_DIR", PROJECT_ROOT / "storage"))

    # MinIO（仅当 STORAGE_BACKEND=minio 时使用）
    MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin123")
    MINIO_BUCKET_VIDEOS = os.getenv("MINIO_BUCKET_VIDEOS", "qingmiao-videos")
    MINIO_BUCKET_FACES = os.getenv("MINIO_BUCKET_FACES", "qingmiao-faces")
    MINIO_BUCKET_REPORTS = os.getenv("MINIO_BUCKET_REPORTS", "qingmiao-reports")
    MINIO_SECURE = _get_bool("MINIO_SECURE", False)

    # AI 服务
    AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://localhost:8000")
    AI_REQUEST_TIMEOUT = _get_int("AI_REQUEST_TIMEOUT", 60)

    # 通义千问
    DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
    QWEN_MODEL = os.getenv("QWEN_MODEL", "qwen-plus")
    QWEN_VL_MODEL = os.getenv("QWEN_VL_MODEL", "qwen-vl-plus")

    # 上传
    MAX_VIDEO_SIZE_MB = _get_int("MAX_VIDEO_SIZE_MB", 500)
    MAX_CONTENT_LENGTH = MAX_VIDEO_SIZE_MB * 1024 * 1024
    ALLOWED_VIDEO_EXTS = set(
        ext.strip().lower()
        for ext in os.getenv("ALLOWED_VIDEO_EXTS", "mp4,avi,mov,mkv").split(",")
        if ext.strip()
    )

    # CORS
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")

    # 日志
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
    LOG_DIR = Path(os.getenv("LOG_DIR", PROJECT_ROOT / "logs"))


class DevelopmentConfig(BaseConfig):
    DEBUG = True


class ProductionConfig(BaseConfig):
    DEBUG = False


class TestingConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}


CONFIG_MAP: dict[str, type[BaseConfig]] = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}


def get_config() -> type[BaseConfig]:
    env = os.getenv("APP_ENV", "development").lower()
    return CONFIG_MAP.get(env, DevelopmentConfig)
