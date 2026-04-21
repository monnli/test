"""为 M10 补充：摄像头 + 课表 + 本学期演示数据。

学期：2026 春季（2026-02-17 ~ 2026-07-05）
每班 1 个摄像头（绑定 storage/demo_videos/class_X_Y.mp4 循环播放）
每班每周 5 天 × 5 节课 = 25 条课表记录

用法：
    python scripts/seed_cameras_and_schedules.py
"""

from __future__ import annotations

import sys
from datetime import date, time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(PROJECT_ROOT / ".env")

# 学期
SEMESTER_FROM = date(2026, 2, 17)
SEMESTER_TO = date(2026, 7, 5)

# 每天 5 节课
PERIODS = [
    (1, time(8, 0), time(8, 45)),
    (2, time(9, 0), time(9, 45)),
    (3, time(10, 0), time(10, 45)),
    (4, time(11, 0), time(11, 45)),
    (5, time(14, 30), time(15, 15)),
]


def main() -> int:
    from app import create_app
    from app.extensions import db
    from app.models import Camera, ClassSchedule, Clazz, Subject, Teacher, TeacherClassSubject

    app = create_app()
    with app.app_context():
        classes = db.session.query(Clazz).filter_by(is_deleted=False).order_by(Clazz.id).all()
        subjects = db.session.query(Subject).filter_by(is_deleted=False).order_by(Subject.id).all()
        if not classes or not subjects:
            print("[ERR] 请先运行 seed_demo_data.py")
            return 1

        print(f"→ 为 {len(classes)} 个班级生成摄像头...")
        video_dir = PROJECT_ROOT / "storage" / "demo_videos"
        video_dir.mkdir(parents=True, exist_ok=True)

        for idx, c in enumerate(classes):
            school_id = c.grade.school_id if c.grade else None
            if not school_id:
                continue
            # 每班 1 个摄像头
            existing = db.session.query(Camera).filter_by(class_id=c.id, is_deleted=False).first()
            if existing:
                continue
            # 对应视频路径，循环 5 个
            codes = ["7_1", "7_2", "8_1", "8_2", "9_1"]
            code = codes[idx % len(codes)]
            video_path = f"storage/demo_videos/class_{code}.mp4"
            cam = Camera(
                school_id=school_id,
                class_id=c.id,
                name=f"{c.grade.name}{c.name}·前置",
                location=f"{c.grade.name}{c.name}教室前方",
                stream_url=video_path,
                stream_type="file_loop",
                resolution="1280x720",
                status="online",
            )
            db.session.add(cam)
        db.session.commit()
        print(f"[OK] 摄像头已创建")

        print(f"→ 生成课表（学期 {SEMESTER_FROM} ~ {SEMESTER_TO}）...")
        # 每班每周 5 天 × 5 节，按学科轮转
        count = 0
        for c in classes:
            # 找该班所有任课关系
            tcs_rows = db.session.query(TeacherClassSubject).filter_by(class_id=c.id).all()
            if not tcs_rows:
                continue
            # 如果该班 TCS 少，用全校教师补齐
            fallback_tcs = db.session.query(TeacherClassSubject).limit(10).all()

            for weekday in range(1, 6):  # 周一到周五
                for p, start_t, end_t in PERIODS:
                    # 优先用该班 TCS，不够就回退
                    tcs = tcs_rows[(weekday * 5 + p) % len(tcs_rows)] if tcs_rows else (
                        fallback_tcs[p % len(fallback_tcs)] if fallback_tcs else None
                    )
                    if not tcs:
                        continue

                    existing = db.session.query(ClassSchedule).filter_by(
                        class_id=c.id, weekday=weekday, period=p,
                        effective_from=SEMESTER_FROM, is_deleted=False,
                    ).first()
                    if existing:
                        continue

                    db.session.add(ClassSchedule(
                        class_id=c.id,
                        subject_id=tcs.subject_id,
                        teacher_id=tcs.teacher_id,
                        weekday=weekday,
                        period=p,
                        start_time=start_t,
                        end_time=end_t,
                        effective_from=SEMESTER_FROM,
                        effective_to=SEMESTER_TO,
                    ))
                    count += 1
        db.session.commit()
        print(f"[OK] 课表已生成 {count} 条")

        print()
        print("=" * 60)
        print("✅ 摄像头与课表已 seed 完成")
        print("   下一步：")
        print("   1. python scripts/generate_demo_videos.py  生成演示 mp4")
        print("   2. 启动后端，进入 /classroom/cameras 查看")
        print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
