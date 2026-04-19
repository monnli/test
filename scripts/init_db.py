"""数据库初始化脚本（M1 起会真正使用）。

M0 阶段：仅探活 MySQL 连接。
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(PROJECT_ROOT / ".env")


def main() -> int:
    try:
        import pymysql  # type: ignore

        conn = pymysql.connect(
            host=os.getenv("MYSQL_HOST", "localhost"),
            port=int(os.getenv("MYSQL_PORT", "3306")),
            user=os.getenv("MYSQL_USER", "qingmiao"),
            password=os.getenv("MYSQL_PASSWORD", "qingmiao123"),
            database=os.getenv("MYSQL_DATABASE", "qingmiao_guardian"),
            charset="utf8mb4",
            connect_timeout=5,
        )
        with conn.cursor() as cur:
            cur.execute("SELECT VERSION()")
            (version,) = cur.fetchone()
        conn.close()
        print(f"[OK] MySQL 连接成功，版本：{version}")
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"[ERR] MySQL 连接失败：{exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
