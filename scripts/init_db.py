"""数据库初始化脚本：创建数据库（若不存在）+ 创建所有表 + 初始化 seed。

用法：
    python scripts/init_db.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(PROJECT_ROOT / ".env")


def ensure_database() -> bool:
    """确保 MySQL 中的目标数据库已创建。"""
    try:
        import pymysql
    except ImportError:
        print("[ERR] 请先安装 pymysql（pip install pymysql cryptography）")
        return False

    host = os.getenv("MYSQL_HOST", "localhost")
    port = int(os.getenv("MYSQL_PORT", "3306"))
    user = os.getenv("MYSQL_USER", "qingmiao")
    password = os.getenv("MYSQL_PASSWORD", "qingmiao123")
    database = os.getenv("MYSQL_DATABASE", "qingmiao_guardian")

    try:
        conn = pymysql.connect(
            host=host, port=port, user=user, password=password, charset="utf8mb4"
        )
        with conn.cursor() as cur:
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{database}` "
                f"DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        conn.close()
        print(f"[OK] 数据库 {database} 已就绪")
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"[ERR] 创建数据库失败：{exc}")
        return False


def main() -> int:
    if not ensure_database():
        return 1

    from app import create_app  # noqa: E402
    from app.extensions import db  # noqa: E402

    app = create_app()
    with app.app_context():
        from app import models  # noqa: F401

        print(f"[OK] 使用 ORM 创建所有表（数据库：{app.config['SQLALCHEMY_DATABASE_URI']}）")
        db.create_all()
        print("[OK] 所有表已创建")

    print()
    print("下一步：python scripts/seed_demo_data.py  生成演示数据")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
