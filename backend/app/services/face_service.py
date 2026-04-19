"""人脸库业务服务。"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from loguru import logger
from sqlalchemy import func

from ..ai import get_ai_client
from ..extensions import db
from ..models import FaceEmbedding, Student
from ..utils.exceptions import NotFoundError, ValidationError
from ..utils.storage import get_storage

FACE_MATCH_THRESHOLD = 0.45


def _embedding_to_json(vec: list[float]) -> str:
    return json.dumps(vec, ensure_ascii=False)


def _embedding_from_json(text: str) -> list[float]:
    try:
        return json.loads(text)
    except Exception:  # noqa: BLE001
        return []


def register_face_for_student(
    student_id: int,
    image_bytes: bytes,
    source: str = "manual",
) -> dict[str, Any]:
    """为某学生注册一张人脸。"""
    student = db.session.get(Student, student_id)
    if not student or student.is_deleted:
        raise NotFoundError("学生不存在")
    if not image_bytes:
        raise ValidationError("图像数据不能为空")

    img_hash = hashlib.md5(image_bytes).hexdigest()
    existing = (
        db.session.query(FaceEmbedding)
        .filter_by(student_id=student_id, image_hash=img_hash)
        .first()
    )
    if existing:
        return {
            "id": existing.id,
            "student_id": student_id,
            "duplicated": True,
            "image_url": existing.image_url,
        }

    ai_resp = get_ai_client().face_detect(image_bytes)
    if ai_resp.get("code") != 0:
        raise ValidationError(f"AI 服务返回错误：{ai_resp.get('message')}")
    faces = ai_resp.get("data", {}).get("faces") or []
    if not faces:
        raise ValidationError("未检测到人脸")
    if len(faces) > 1:
        # 取面积最大的脸
        faces.sort(
            key=lambda f: (f["bbox"][2] - f["bbox"][0]) * (f["bbox"][3] - f["bbox"][1]),
            reverse=True,
        )

    face = faces[0]
    embedding = face.get("embedding") or []
    if not embedding:
        raise ValidationError("人脸特征提取失败")

    # 保存原图
    storage = get_storage()
    ext = "jpg"
    key = f"faces/student_{student_id}/{img_hash}.{ext}"
    storage.save(key, image_bytes)

    record = FaceEmbedding(
        student_id=student_id,
        embedding=_embedding_to_json(embedding),
        dim=len(embedding),
        image_url=storage.get_url(key),
        image_hash=img_hash,
        confidence=float(face.get("confidence", 0.0)),
        source=source,
    )
    db.session.add(record)
    db.session.commit()

    logger.info(f"为学生 {student.name}({student_id}) 注册人脸，ID={record.id}")
    return serialize_face(record)


def delete_face(face_id: int) -> None:
    face = db.session.get(FaceEmbedding, face_id)
    if not face:
        raise NotFoundError("人脸记录不存在")
    db.session.delete(face)
    db.session.commit()


def list_faces_by_student(student_id: int) -> list[dict[str, Any]]:
    rows = (
        db.session.query(FaceEmbedding)
        .filter_by(student_id=student_id)
        .order_by(FaceEmbedding.id.desc())
        .all()
    )
    return [serialize_face(r) for r in rows]


def delete_all_faces_for_student(student_id: int) -> int:
    count = db.session.query(FaceEmbedding).filter_by(student_id=student_id).delete()
    db.session.commit()
    return count


def face_library_stats() -> dict[str, Any]:
    total_faces = db.session.query(func.count(FaceEmbedding.id)).scalar() or 0
    total_students = (
        db.session.query(func.count(func.distinct(FaceEmbedding.student_id))).scalar() or 0
    )
    total_all_students = (
        db.session.query(func.count(Student.id)).filter_by(is_deleted=False).scalar() or 0
    )
    coverage = (total_students / total_all_students * 100) if total_all_students else 0.0
    return {
        "total_faces": total_faces,
        "registered_students": total_students,
        "total_students": total_all_students,
        "coverage_percent": round(coverage, 2),
    }


def recognize_face(
    image_bytes: bytes,
    threshold: float = FACE_MATCH_THRESHOLD,
    scope_student_ids: list[int] | None = None,
) -> dict[str, Any]:
    """从人脸库中识别出图片里的学生身份。"""
    ai_resp = get_ai_client().face_detect(image_bytes)
    if ai_resp.get("code") != 0:
        raise ValidationError(f"AI 服务返回错误：{ai_resp.get('message')}")
    faces = ai_resp.get("data", {}).get("faces") or []
    if not faces:
        return {"results": [], "count": 0}

    q = db.session.query(FaceEmbedding)
    if scope_student_ids is not None:
        if not scope_student_ids:
            return {"results": [], "count": 0}
        q = q.filter(FaceEmbedding.student_id.in_(scope_student_ids))
    rows = q.all()
    candidates = [
        {"person_id": r.student_id, "face_id": r.id, "embedding": _embedding_from_json(r.embedding)}
        for r in rows
    ]
    if not candidates:
        return {"results": [], "count": len(faces), "candidates": 0}

    client = get_ai_client()
    results: list[dict[str, Any]] = []
    for f in faces:
        embedding = f.get("embedding") or []
        match_resp = client.face_match(embedding, candidates, threshold)
        match = match_resp.get("data") or {}
        person_id = match.get("person_id")
        student_info: dict[str, Any] | None = None
        if person_id:
            student = db.session.get(Student, person_id)
            if student:
                student_info = {
                    "id": student.id,
                    "name": student.name,
                    "student_no": student.student_no,
                    "class_id": student.class_id,
                }
        results.append({
            "bbox": f.get("bbox"),
            "face_confidence": f.get("confidence"),
            "matched": match.get("matched", False),
            "score": match.get("score"),
            "student": student_info,
        })
    return {"results": results, "count": len(results), "candidates": len(candidates)}


def serialize_face(r: FaceEmbedding) -> dict[str, Any]:
    return {
        "id": r.id,
        "student_id": r.student_id,
        "student_name": r.student.name if r.student else None,
        "dim": r.dim,
        "image_url": r.image_url,
        "image_hash": r.image_hash,
        "confidence": r.confidence,
        "source": r.source,
        "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    }
