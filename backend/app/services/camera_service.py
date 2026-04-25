"""摄像头与课表服务。"""

from __future__ import annotations

from datetime import date, datetime, time as dtime
from typing import Any

from sqlalchemy import and_, or_, tuple_

from ..extensions import db
from ..models import Camera, ClassSchedule, Clazz, Subject, Teacher
from ..utils.exceptions import ConflictError, NotFoundError, ValidationError


# ==================== 摄像头 ====================

def serialize_camera(c: Camera) -> dict[str, Any]:
    clazz = db.session.get(Clazz, c.class_id) if c.class_id else None
    return {
        "id": c.id,
        "school_id": c.school_id,
        "class_id": c.class_id,
        "class_name": (clazz.grade.name + clazz.name) if clazz and clazz.grade else None,
        "name": c.name,
        "location": c.location,
        "stream_url": c.stream_url,
        "stream_type": c.stream_type,
        "resolution": c.resolution,
        "status": c.status,
        "last_heartbeat": c.last_heartbeat.strftime("%Y-%m-%d %H:%M:%S") if c.last_heartbeat else None,
        "note": c.note,
        "created_at": c.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    }


def list_cameras(school_id: int | None = None) -> list[dict]:
    q = db.session.query(Camera).filter(Camera.is_deleted.is_(False))
    if school_id:
        q = q.filter_by(school_id=school_id)
    return [serialize_camera(c) for c in q.order_by(Camera.id).all()]


def create_camera(data: dict) -> dict:
    name = (data.get("name") or "").strip()
    stream_url = (data.get("stream_url") or "").strip()
    if not name or not stream_url:
        raise ValidationError("名称与视频流地址不能为空")
    class_id = data.get("class_id")
    school_id = data.get("school_id")
    if class_id:
        # 一个班级只能绑一个摄像头
        existing = db.session.query(Camera).filter_by(class_id=class_id, is_deleted=False).first()
        if existing:
            raise ConflictError("该班级已绑定摄像头")
        clazz = db.session.get(Clazz, class_id)
        if clazz and not school_id:
            school_id = clazz.grade.school_id if clazz.grade else None
    if not school_id:
        raise ValidationError("必须指定学校")
    c = Camera(
        school_id=school_id,
        class_id=class_id,
        name=name,
        location=data.get("location"),
        stream_url=stream_url,
        stream_type=data.get("stream_type") or "file_loop",
        resolution=data.get("resolution"),
        status=data.get("status") or "online",
        note=data.get("note"),
    )
    db.session.add(c)
    db.session.commit()
    return serialize_camera(c)


def update_camera(cam_id: int, data: dict) -> dict:
    c = db.session.get(Camera, cam_id)
    if not c or c.is_deleted:
        raise NotFoundError("摄像头不存在")
    for field in ("name", "location", "stream_url", "stream_type", "resolution", "status", "note"):
        if field in data:
            setattr(c, field, data[field])
    if "class_id" in data and data["class_id"] != c.class_id:
        new_class = data["class_id"]
        if new_class:
            existing = db.session.query(Camera).filter(
                Camera.class_id == new_class,
                Camera.is_deleted.is_(False),
                Camera.id != cam_id,
            ).first()
            if existing:
                raise ConflictError("目标班级已绑定另一个摄像头")
        c.class_id = new_class
    db.session.commit()
    return serialize_camera(c)


def delete_camera(cam_id: int) -> None:
    c = db.session.get(Camera, cam_id)
    if not c or c.is_deleted:
        raise NotFoundError("摄像头不存在")
    c.is_deleted = True
    c.deleted_at = datetime.utcnow()
    db.session.commit()


def heartbeat_camera(cam_id: int) -> None:
    c = db.session.get(Camera, cam_id)
    if not c:
        return
    c.last_heartbeat = datetime.utcnow()
    c.status = "online"
    db.session.commit()


# ==================== 课表 ====================

def _parse_time(value: str | dtime | None) -> dtime:
    if value is None:
        raise ValidationError("时间不能为空")
    if isinstance(value, dtime):
        return value
    try:
        h, m = value.split(":")[:2]
        return dtime(int(h), int(m))
    except Exception:
        raise ValidationError(f"时间格式错误: {value}")


def _parse_date(value: str | date | None) -> date:
    if value is None:
        raise ValidationError("日期不能为空")
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except Exception:
        raise ValidationError(f"日期格式错误: {value}")


def serialize_schedule(s: ClassSchedule) -> dict:
    clazz = db.session.get(Clazz, s.class_id)
    sub = db.session.get(Subject, s.subject_id) if s.subject_id else None
    teacher = db.session.get(Teacher, s.teacher_id) if s.teacher_id else None
    return {
        "id": s.id,
        "class_id": s.class_id,
        "class_name": (clazz.grade.name + clazz.name) if clazz and clazz.grade else None,
        "subject_id": s.subject_id,
        "subject_name": sub.name if sub else None,
        "teacher_id": s.teacher_id,
        "teacher_name": teacher.name if teacher else None,
        "weekday": s.weekday,
        "period": s.period,
        "start_time": s.start_time.strftime("%H:%M"),
        "end_time": s.end_time.strftime("%H:%M"),
        "effective_from": s.effective_from.strftime("%Y-%m-%d"),
        "effective_to": s.effective_to.strftime("%Y-%m-%d"),
        "note": s.note,
    }


def list_schedules(
    class_id: int | None = None,
    teacher_id: int | None = None,
    weekday: int | None = None,
    class_ids: list[int] | None = None,
    subject_filters: set[tuple[int, int]] | None = None,
    all_subjects_in_class_ids: set[int] | None = None,
    is_full: bool = False,
) -> list[dict]:
    q = db.session.query(ClassSchedule).filter(ClassSchedule.is_deleted.is_(False))
    if class_id:
        q = q.filter_by(class_id=class_id)
    if teacher_id:
        q = q.filter_by(teacher_id=teacher_id)
    if weekday:
        q = q.filter_by(weekday=weekday)

    # 数据范围过滤（非管理员/非超管）
    if not is_full:
        if class_ids is not None:
            if not class_ids:
                return []
            q = q.filter(ClassSchedule.class_id.in_(class_ids))

        # 科任老师：仅允许（班级×科目）授权；若该班级在 all_subjects_in_class_ids，则允许该班级任意科目
        all_subjects_in_class_ids = all_subjects_in_class_ids or set()
        subject_filters = subject_filters or set()
        if subject_filters or all_subjects_in_class_ids:
            allowed = []
            if all_subjects_in_class_ids:
                allowed.append(ClassSchedule.class_id.in_(list(all_subjects_in_class_ids)))
            if subject_filters:
                allowed.append(tuple_(ClassSchedule.class_id, ClassSchedule.subject_id).in_(list(subject_filters)))
            q = q.filter(or_(*allowed))

    rows = q.order_by(ClassSchedule.weekday, ClassSchedule.period).all()
    return [serialize_schedule(s) for s in rows]


def _check_conflicts(data: dict, exclude_id: int | None = None) -> list[str]:
    """返回冲突描述列表。"""
    weekday = int(data["weekday"])
    class_id = int(data["class_id"])
    teacher_id = int(data["teacher_id"])
    start = _parse_time(data["start_time"])
    end = _parse_time(data["end_time"])
    if start >= end:
        return ["开始时间必须早于结束时间"]
    eff_from = _parse_date(data["effective_from"])
    eff_to = _parse_date(data["effective_to"])
    if eff_from > eff_to:
        return ["生效开始日期必须早于结束日期"]

    q = db.session.query(ClassSchedule).filter(
        ClassSchedule.is_deleted.is_(False),
        ClassSchedule.weekday == weekday,
        # 时间段重叠
        ClassSchedule.start_time < end,
        ClassSchedule.end_time > start,
        # 生效期重叠
        ClassSchedule.effective_from <= eff_to,
        ClassSchedule.effective_to >= eff_from,
    )
    if exclude_id:
        q = q.filter(ClassSchedule.id != exclude_id)
    candidates = q.all()

    conflicts: list[str] = []
    for other in candidates:
        if other.class_id == class_id:
            conflicts.append(
                f"班级冲突：同班级已有课程（周{other.weekday} 第{other.period}节）"
            )
        if other.teacher_id == teacher_id:
            conflicts.append(
                f"教师冲突：该教师同一时间已在其他班上课（班级{other.class_id}）"
            )
    return conflicts


def create_schedule(data: dict) -> dict:
    conflicts = _check_conflicts(data)
    if conflicts:
        raise ConflictError("；".join(conflicts))
    s = ClassSchedule(
        class_id=data["class_id"],
        subject_id=data["subject_id"],
        teacher_id=data["teacher_id"],
        weekday=int(data["weekday"]),
        period=int(data.get("period") or 1),
        start_time=_parse_time(data["start_time"]),
        end_time=_parse_time(data["end_time"]),
        effective_from=_parse_date(data["effective_from"]),
        effective_to=_parse_date(data["effective_to"]),
        note=data.get("note"),
    )
    db.session.add(s)
    db.session.commit()
    return serialize_schedule(s)


def update_schedule(schedule_id: int, data: dict) -> dict:
    s = db.session.get(ClassSchedule, schedule_id)
    if not s or s.is_deleted:
        raise NotFoundError("课表记录不存在")
    merged = {
        "class_id": data.get("class_id", s.class_id),
        "subject_id": data.get("subject_id", s.subject_id),
        "teacher_id": data.get("teacher_id", s.teacher_id),
        "weekday": data.get("weekday", s.weekday),
        "period": data.get("period", s.period),
        "start_time": data.get("start_time", s.start_time.strftime("%H:%M")),
        "end_time": data.get("end_time", s.end_time.strftime("%H:%M")),
        "effective_from": data.get("effective_from", s.effective_from.strftime("%Y-%m-%d")),
        "effective_to": data.get("effective_to", s.effective_to.strftime("%Y-%m-%d")),
    }
    conflicts = _check_conflicts(merged, exclude_id=schedule_id)
    if conflicts:
        raise ConflictError("；".join(conflicts))
    s.class_id = merged["class_id"]
    s.subject_id = merged["subject_id"]
    s.teacher_id = merged["teacher_id"]
    s.weekday = int(merged["weekday"])
    s.period = int(merged["period"])
    s.start_time = _parse_time(merged["start_time"])
    s.end_time = _parse_time(merged["end_time"])
    s.effective_from = _parse_date(merged["effective_from"])
    s.effective_to = _parse_date(merged["effective_to"])
    if "note" in data:
        s.note = data["note"]
    db.session.commit()
    return serialize_schedule(s)


def delete_schedule(schedule_id: int) -> None:
    s = db.session.get(ClassSchedule, schedule_id)
    if not s or s.is_deleted:
        raise NotFoundError("课表记录不存在")
    s.is_deleted = True
    s.deleted_at = datetime.utcnow()
    db.session.commit()


def find_active_schedules(now: datetime | None = None) -> list[ClassSchedule]:
    """查找当前正在进行的所有课。"""
    now = now or datetime.now()
    weekday = now.isoweekday()
    today = now.date()
    cur_time = now.time()
    return (
        db.session.query(ClassSchedule)
        .filter(
            ClassSchedule.is_deleted.is_(False),
            ClassSchedule.weekday == weekday,
            ClassSchedule.start_time <= cur_time,
            ClassSchedule.end_time >= cur_time,
            ClassSchedule.effective_from <= today,
            ClassSchedule.effective_to >= today,
        )
        .all()
    )


def schedule_conflicts(data: dict) -> list[str]:
    """预校验冲突（前端新建表单实时调用）。"""
    return _check_conflicts(data)
