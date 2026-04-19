"""人脸库管理接口。"""

from __future__ import annotations

from flask import Blueprint, request

from ..services import face_service as svc
from ..utils.exceptions import ValidationError
from ..utils.permissions import (
    admin_required,
    assert_can_access_student,
    get_current_user,
    get_visible_student_ids,
    login_required,
)
from ..utils.response import ok

faces_bp = Blueprint("faces", __name__)


def _extract_image_bytes() -> bytes:
    if "file" in request.files:
        return request.files["file"].read()
    payload = request.get_json(silent=True) or {}
    image_b64 = payload.get("image")
    if image_b64:
        import base64

        if image_b64.startswith("data:"):
            image_b64 = image_b64.split(",", 1)[-1]
        try:
            return base64.b64decode(image_b64)
        except Exception as exc:  # noqa: BLE001
            raise ValidationError(f"base64 解码失败：{exc}")
    raise ValidationError("请通过 multipart 的 file 字段或 JSON 的 image(base64) 字段上传图像")


@faces_bp.get("/stats")
@login_required
def api_face_stats():
    return ok(svc.face_library_stats())


@faces_bp.get("/by-student/<int:student_id>")
@login_required
def api_face_by_student(student_id: int):
    user = get_current_user()
    assert_can_access_student(user, student_id)
    items = svc.list_faces_by_student(student_id)
    return ok({"items": items, "total": len(items)})


@faces_bp.post("/by-student/<int:student_id>")
@admin_required
def api_register_face(student_id: int):
    user = get_current_user()
    assert_can_access_student(user, student_id)
    image_bytes = _extract_image_bytes()
    return ok(svc.register_face_for_student(student_id, image_bytes), "已注册")


@faces_bp.delete("/<int:face_id>")
@admin_required
def api_delete_face(face_id: int):
    svc.delete_face(face_id)
    return ok(message="已删除")


@faces_bp.delete("/by-student/<int:student_id>")
@admin_required
def api_delete_student_faces(student_id: int):
    user = get_current_user()
    assert_can_access_student(user, student_id)
    count = svc.delete_all_faces_for_student(student_id)
    return ok({"deleted": count}, f"已删除 {count} 张")


@faces_bp.post("/recognize")
@login_required
def api_recognize_face():
    """用图片在当前用户可见的学生范围内做人脸识别。"""
    user = get_current_user()
    image_bytes = _extract_image_bytes()
    scope_ids = get_visible_student_ids(user)
    threshold = float(request.args.get("threshold", 0.45))
    return ok(svc.recognize_face(image_bytes, threshold=threshold, scope_student_ids=scope_ids))
