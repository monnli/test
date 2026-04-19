"""Flask 扩展实例集中管理。各扩展在此创建，避免循环引用。"""

from __future__ import annotations

from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
ma = Marshmallow()
cors = CORS()
socketio = SocketIO(cors_allowed_origins="*", async_mode="threading")
