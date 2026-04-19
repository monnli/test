"""开发模式启动入口：python run.py"""

from __future__ import annotations

import os

from app import create_app
from app.extensions import socketio

app = create_app()


if __name__ == "__main__":
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    port = int(os.getenv("FLASK_PORT", "5000"))
    debug = app.config.get("DEBUG", False)
    socketio.run(
        app,
        host=host,
        port=port,
        debug=debug,
        use_reloader=debug,
        allow_unsafe_werkzeug=True,
    )
