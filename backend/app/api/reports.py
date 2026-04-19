"""报告中心接口。"""

from __future__ import annotations

from flask import Blueprint, request, send_file
import io

from ..services import report_service as svc
from ..utils.permissions import (
    assert_can_access_class,
    assert_can_access_student,
    get_current_user,
    login_required,
)
from ..utils.response import ok

reports_bp = Blueprint("reports", __name__)


@reports_bp.get("")
@login_required
def list_reports():
    return ok(
        svc.list_reports(
            report_type=request.args.get("type"),
            page=request.args.get("page", default=1, type=int),
            page_size=request.args.get("page_size", default=20, type=int),
        )
    )


@reports_bp.get("/<int:report_id>")
@login_required
def get_report(report_id: int):
    return ok(svc.get_report(report_id))


@reports_bp.get("/<int:report_id>/pdf")
@login_required
def download_pdf(report_id: int):
    pdf_bytes, filename = svc.render_pdf(report_id)
    return send_file(
        io.BytesIO(pdf_bytes),
        download_name=filename,
        mimetype="application/pdf" if filename.endswith(".pdf") else "text/markdown",
        as_attachment=True,
    )


@reports_bp.post("/class/<int:class_id>")
@login_required
def gen_class_report(class_id: int):
    user = get_current_user()
    assert_can_access_class(user, class_id)
    return ok(svc.generate_class_report(class_id, user.id), "已生成")


@reports_bp.post("/student/<int:student_id>")
@login_required
def gen_student_report(student_id: int):
    user = get_current_user()
    assert_can_access_student(user, student_id)
    return ok(svc.generate_student_report(student_id, user.id), "已生成")


@reports_bp.post("/school")
@login_required
def gen_school_report():
    user = get_current_user()
    return ok(svc.generate_school_report(user.id), "已生成")
