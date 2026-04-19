"""心理健康接口。"""

from __future__ import annotations

from flask import Blueprint, request

from ..services import psychology_service as svc
from ..utils.permissions import (
    assert_can_access_student,
    get_current_user,
    login_required,
)
from ..utils.response import ok

psy_bp = Blueprint("psychology", __name__)


# ---- 量表 ----
@psy_bp.get("/scales")
@login_required
def list_scales():
    items = svc.list_scales()
    return ok({"items": items, "total": len(items)})


@psy_bp.get("/scales/<int:scale_id>")
@login_required
def get_scale(scale_id: int):
    return ok(svc.get_scale_with_questions(scale_id))


@psy_bp.post("/scales/seed")
@login_required
def seed_scales():
    cnt = svc.ensure_scales_seeded()
    return ok({"seeded": cnt}, "已初始化")


# ---- 测评 ----
@psy_bp.post("/assessments")
@login_required
def submit_assessment():
    user = get_current_user()
    payload = request.get_json() or {}
    student_id = int(payload.get("student_id"))
    assert_can_access_student(user, student_id)
    answers = payload.get("answers") or {}
    return ok(
        svc.submit_assessment(
            student_id=student_id,
            scale_id=int(payload.get("scale_id")),
            answers={int(k): int(v) for k, v in answers.items()},
            operator_id=user.id,
        ),
        "提交成功",
    )


@psy_bp.get("/assessments")
@login_required
def list_assessments():
    user = get_current_user()
    student_id = request.args.get("student_id", type=int)
    scale_id = request.args.get("scale_id", type=int)
    if student_id:
        assert_can_access_student(user, student_id)
    items = svc.list_assessments(student_id=student_id, scale_id=scale_id)
    return ok({"items": items, "total": len(items)})


# ---- 文本分析 ----
@psy_bp.post("/text-analyses")
@login_required
def analyze_text():
    user = get_current_user()
    payload = request.get_json() or {}
    student_id = int(payload.get("student_id"))
    assert_can_access_student(user, student_id)
    return ok(
        svc.analyze_text(
            student_id=student_id,
            content=payload.get("content", ""),
            title=payload.get("title"),
            operator_id=user.id,
        ),
        "已分析",
    )


@psy_bp.get("/text-analyses")
@login_required
def list_text_analyses():
    user = get_current_user()
    student_id = request.args.get("student_id", type=int)
    if not student_id:
        return ok({"items": [], "total": 0})
    assert_can_access_student(user, student_id)
    items = svc.list_text_analyses(student_id)
    return ok({"items": items, "total": len(items)})


# ---- AI 对话 ----
@psy_bp.post("/conversations")
@login_required
def start_conversation():
    user = get_current_user()
    payload = request.get_json() or {}
    student_id = int(payload.get("student_id"))
    assert_can_access_student(user, student_id)
    return ok(svc.start_conversation(student_id, user.id, payload.get("title")), "已创建")


@psy_bp.get("/conversations")
@login_required
def list_conversations():
    user = get_current_user()
    student_id = request.args.get("student_id", type=int)
    if student_id:
        assert_can_access_student(user, student_id)
    return ok({"items": svc.list_conversations(student_id), "total": 0})


@psy_bp.get("/conversations/<int:conv_id>")
@login_required
def get_conversation(conv_id: int):
    return ok(svc.get_conversation_detail(conv_id))


@psy_bp.post("/conversations/<int:conv_id>/messages")
@login_required
def post_message(conv_id: int):
    payload = request.get_json() or {}
    return ok(svc.post_message(conv_id, payload.get("content", "")))


# ---- 个人档案 ----
@psy_bp.get("/students/<int:student_id>/profile")
@login_required
def student_profile(student_id: int):
    user = get_current_user()
    assert_can_access_student(user, student_id)
    return ok(svc.student_psychology_profile(student_id))


@psy_bp.get("/students/<int:student_id>/timeline")
@login_required
def student_timeline(student_id: int):
    user = get_current_user()
    assert_can_access_student(user, student_id)
    days = request.args.get("days", default=60, type=int)
    return ok({"items": svc.student_emotion_timeline(student_id, days=days)})
