"""M10 数据库迁移：为已有数据库补齐 M10 新增的表与字段。

对已经跑过 M3 及以前版本 seed 的数据库非破坏性升级：
- 给 class_sessions 表补 7 个字段（camera_id / trigger_type / status 等）
- 创建 cameras 表
- 创建 class_schedules 表

用法：
    python scripts/migrate_m10.py

幂等：多次运行不会报错，已存在的列/表会跳过。
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(PROJECT_ROOT / ".env")


# class_sessions 新增字段定义（列名, 类型 + 约束）
NEW_COLUMNS_CLASS_SESSIONS = [
    ("camera_id", "INT NULL"),
    ("trigger_type", "VARCHAR(16) DEFAULT 'manual' NOT NULL"),
    ("status", "VARCHAR(16) DEFAULT 'scheduled' NOT NULL"),
    ("started_at", "DATETIME NULL"),
    ("ended_at", "DATETIME NULL"),
    ("engagement_score", "FLOAT DEFAULT 0 NOT NULL"),
    ("no_person_minutes", "INT DEFAULT 0 NOT NULL"),
]

CREATE_CAMERAS_SQL = """
CREATE TABLE IF NOT EXISTS cameras (
    id INT AUTO_INCREMENT PRIMARY KEY,
    school_id INT NOT NULL,
    class_id INT NULL,
    name VARCHAR(128) NOT NULL,
    location VARCHAR(255) NULL,
    stream_url VARCHAR(500) NOT NULL,
    stream_type VARCHAR(16) DEFAULT 'file_loop' NOT NULL,
    resolution VARCHAR(32) NULL,
    status VARCHAR(16) DEFAULT 'online' NOT NULL,
    last_heartbeat DATETIME NULL,
    note TEXT NULL,
    is_deleted TINYINT(1) DEFAULT 0 NOT NULL,
    deleted_at DATETIME NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    INDEX idx_camera_school (school_id),
    INDEX idx_camera_class (class_id),
    INDEX idx_camera_deleted (is_deleted),
    INDEX idx_camera_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
"""

CREATE_SCHEDULES_SQL = """
CREATE TABLE IF NOT EXISTS class_schedules (
    id INT AUTO_INCREMENT PRIMARY KEY,
    class_id INT NOT NULL,
    subject_id INT NOT NULL,
    teacher_id INT NOT NULL,
    weekday INT NOT NULL,
    period INT NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    effective_from DATE NOT NULL,
    effective_to DATE NOT NULL,
    note VARCHAR(255) NULL,
    is_deleted TINYINT(1) DEFAULT 0 NOT NULL,
    deleted_at DATETIME NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    UNIQUE KEY uq_class_schedule_slot (class_id, weekday, period, effective_from),
    INDEX idx_schedule_class (class_id),
    INDEX idx_schedule_teacher (teacher_id),
    INDEX idx_schedule_weekday (weekday),
    INDEX idx_schedule_deleted (is_deleted),
    INDEX idx_schedule_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
"""


def main() -> int:
    try:
        import pymysql
    except ImportError:
        print("[ERR] 请先安装 pymysql：pip install pymysql cryptography")
        return 1

    host = os.getenv("MYSQL_HOST", "localhost")
    port = int(os.getenv("MYSQL_PORT", "3306"))
    user = os.getenv("MYSQL_USER", "qingmiao")
    password = os.getenv("MYSQL_PASSWORD", "qingmiao123")
    database = os.getenv("MYSQL_DATABASE", "qingmiao_guardian")

    print(f"连接数据库 {database}@{host}:{port} ...")
    conn = pymysql.connect(
        host=host, port=port, user=user, password=password,
        database=database, charset="utf8mb4",
    )
    try:
        with conn.cursor() as cur:
            # 1. class_sessions 补字段
            print("→ [1/3] 检查 class_sessions 表字段...")
            cur.execute("""
                SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA=%s AND TABLE_NAME='class_sessions'
            """, (database,))
            existing_cols = {row[0] for row in cur.fetchall()}

            added_count = 0
            for col_name, col_def in NEW_COLUMNS_CLASS_SESSIONS:
                if col_name in existing_cols:
                    print(f"   [SKIP] 字段 {col_name} 已存在")
                    continue
                sql = f"ALTER TABLE class_sessions ADD COLUMN {col_name} {col_def}"
                print(f"   [+] {sql}")
                cur.execute(sql)
                added_count += 1
            print(f"   → 共新增 {added_count} 个字段")

            # 2. cameras 表
            print("→ [2/3] 创建 cameras 表（若不存在）...")
            cur.execute(CREATE_CAMERAS_SQL)
            print("   [OK] cameras 表已就绪")

            # 3. class_schedules 表
            print("→ [3/3] 创建 class_schedules 表（若不存在）...")
            cur.execute(CREATE_SCHEDULES_SQL)
            print("   [OK] class_schedules 表已就绪")

        conn.commit()
        print()
        print("=" * 60)
        print("✅ M10 数据库迁移完成！")
        print()
        print("下一步（可选）：")
        print("  1. 合成演示视频：python scripts/generate_demo_videos.py")
        print("  2. 初始化摄像头+课表：python scripts/seed_cameras_and_schedules.py")
        print("  3. 重启后端")
        print("=" * 60)
        return 0
    except Exception as exc:
        conn.rollback()
        print(f"[ERR] 迁移失败：{exc}")
        return 1
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
