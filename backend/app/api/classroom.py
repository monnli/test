"""课堂视频分析接口。"""

from __future__ import annotations

from flask import Blueprint, request

from ..services import video_service as svc
from ..utils.permissions import (
    get_current_user,
    get_visible_class_ids,
    login_required,
)
from ..utils.response import ok

classroom_bp = Blueprint("classroom", __name__)


@classroom_bp.get("/videos")
@login_required
def list_videos():
    user = get_current_user()
    page = request.args.get("page", default=1, type=int)
    page_size = request.args.get("page_size", default=10, type=int)
    visible = get_visible_class_ids(user)
    return ok(svc.list_videos(class_ids=visible, page=page, page_size=page_size))


@classroom_bp.post("/videos")
@login_required
def upload_video():
    user = get_current_user()
    file = request.files.get("file")
    class_id = request.form.get("class_id", type=int) or request.args.get("class_id", type=int)
    title = request.form.get("title") or request.args.get("title")
    return ok(
        svc.create_video_from_upload(file, class_id, title, uploaded_by=user.id),
        "上传成功",
    )


@classroom_bp.post("/videos/<int:video_id>/analyze")
@login_required
def start_analyze(video_id: int):
    interval = float(request.args.get("interval", 2.0))
    return ok(svc.create_analysis_task(video_id, sample_interval=interval), "已提交分析")


@classroom_bp.get("/videos/<int:video_id>/tasks")
@login_required
def list_video_tasks(video_id: int):
    items = svc.list_tasks_of_video(video_id)
    return ok({"items": items, "total": len(items)})


@classroom_bp.get("/tasks/<int:task_id>")
@login_required
def get_task(task_id: int):
    return ok(svc.get_task(task_id))


@classroom_bp.get("/tasks/<int:task_id>/report")
@login_required
def get_task_report(task_id: int):
    return ok(svc.get_task_report(task_id))
