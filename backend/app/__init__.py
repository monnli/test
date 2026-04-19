"""应用工厂。"""

from __future__ import annotations

import sys
from pathlib import Path

from flask import Flask, jsonify
from loguru import logger

from config import BaseConfig, get_config

from .extensions import cors, db, jwt, ma, migrate, socketio


def _configure_logging(app: Flask) -> None:
    log_dir: Path = app.config["LOG_DIR"]
    log_dir.mkdir(parents=True, exist_ok=True)

    logger.remove()
    logger.add(
        sys.stderr,
        level=app.config["LOG_LEVEL"],
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>",
    )
    logger.add(
        log_dir / "app_{time:YYYY-MM-DD}.log",
        level=app.config["LOG_LEVEL"],
        rotation="00:00",
        retention="14 days",
        encoding="utf-8",
        enqueue=True,
    )
    logger.info(f"日志已初始化，级别 {app.config['LOG_LEVEL']}")


def _register_extensions(app: Flask) -> None:
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    ma.init_app(app)
    cors.init_app(
        app,
        resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}},
        supports_credentials=True,
    )
    socketio.init_app(app, cors_allowed_origins=app.config["CORS_ORIGINS"])


def _register_blueprints(app: Flask) -> None:
    from .api import api_bp

    app.register_blueprint(api_bp, url_prefix="/api")


def _register_error_handlers(app: Flask) -> None:
    @app.errorhandler(404)
    def _not_found(_err):
        return jsonify(code=404, message="资源不存在"), 404

    @app.errorhandler(405)
    def _method_not_allowed(_err):
        return jsonify(code=405, message="方法不被允许"), 405

    @app.errorhandler(500)
    def _internal_error(err):
        logger.exception(err)
        return jsonify(code=500, message="服务器内部错误"), 500


def create_app(config_class: type[BaseConfig] | None = None) -> Flask:
    """创建 Flask 应用实例。"""
    app = Flask(__name__)
    app.config.from_object(config_class or get_config())

    _configure_logging(app)
    _register_extensions(app)
    _register_blueprints(app)
    _register_error_handlers(app)

    @app.route("/")
    def index():
        return jsonify(
            name="青苗守护者 API",
            version="0.1.0",
            env=app.config["APP_ENV"],
            docs="/api/health",
        )

    logger.info(f"青苗守护者后端启动完成 (env={app.config['APP_ENV']})")
    return app
