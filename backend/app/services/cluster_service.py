"""学生群体智能聚类服务（K-Means + 简化降维）。

为了避免引入 scikit-learn 等重型依赖，这里手写极简 K-Means 与 PCA。
4 维特征：心理指数 / 学业 / 量表得分 / 课堂异常 → 聚成 5 类。
"""

from __future__ import annotations

import math
import random
from typing import Any

from .correlation_service import collect_student_features
from ..extensions import db
from ..models import Student

CLUSTER_PROFILES = [
    {"name": "正常活力型", "color": "#22c55e", "icon": "Sunny", "advice": "继续保持，定期关心即可"},
    {"name": "学业焦虑型", "color": "#f59e0b", "icon": "Reading", "advice": "学习压力辅导，时间管理训练"},
    {"name": "社交困扰型", "color": "#0ea5e9", "icon": "User", "advice": "团体心理活动，搭档制学习"},
    {"name": "身心疲惫型", "color": "#a78bfa", "icon": "Coffee", "advice": "作息健康教育，体育锻炼"},
    {"name": "高风险关注型", "color": "#ef4444", "icon": "Warning", "advice": "心理咨询师 1 对 1 谈话，必要时转介"},
]


def _normalize(features: list[list[float]]) -> list[list[float]]:
    if not features:
        return features
    n_cols = len(features[0])
    mins = [min(r[i] for r in features) for i in range(n_cols)]
    maxs = [max(r[i] for r in features) for i in range(n_cols)]
    out = []
    for r in features:
        nr = []
        for i, v in enumerate(r):
            rng = maxs[i] - mins[i]
            nr.append((v - mins[i]) / rng if rng else 0.5)
        out.append(nr)
    return out


def _kmeans(points: list[list[float]], k: int, max_iter: int = 30) -> tuple[list[int], list[list[float]]]:
    if not points:
        return [], []
    random.seed(2026)
    centroids = random.sample(points, min(k, len(points)))
    while len(centroids) < k:
        centroids.append(random.choice(points))
    labels = [0] * len(points)
    for _ in range(max_iter):
        new_labels = []
        for p in points:
            dists = [sum((p[i] - c[i]) ** 2 for i in range(len(p))) for c in centroids]
            new_labels.append(dists.index(min(dists)))
        if new_labels == labels:
            break
        labels = new_labels
        for ci in range(k):
            members = [points[i] for i, lb in enumerate(labels) if lb == ci]
            if members:
                centroids[ci] = [sum(m[i] for m in members) / len(members) for i in range(len(members[0]))]
    return labels, centroids


def _simple_2d_projection(points: list[list[float]]) -> list[tuple[float, float]]:
    """简化降维：取前两维（心理指数 + 学业平均）作为 x/y。"""
    return [(p[0], p[1]) for p in points]


def cluster_students(num_clusters: int = 5) -> dict[str, Any]:
    students = db.session.query(Student).filter_by(is_deleted=False).limit(500).all()
    feats: list[list[float]] = []
    items: list[dict] = []
    for s in students:
        f = collect_student_features(s.id)
        if not f:
            continue
        vec = [
            f["psy_score_avg_30d"],
            f["score_avg"],
            f["scale_score"],
            f["classroom_phone_count"] + f["classroom_sleep_count"],
        ]
        feats.append(vec)
        items.append({
            "student_id": s.id,
            "student_name": s.name,
            "class_id": s.class_id,
            "psy": f["psy_score_avg_30d"],
            "score_avg": f["score_avg"],
            "scale_score": f["scale_score"],
            "abnormal": f["classroom_phone_count"] + f["classroom_sleep_count"],
            "raw": vec,
        })

    if not items:
        return {"items": [], "clusters": [], "centroids": []}

    norm = _normalize(feats)
    labels, centroids = _kmeans(norm, num_clusters)
    proj = _simple_2d_projection(feats)

    # 给每个簇按特征均值匹配画像
    cluster_stats: list[dict] = []
    for ci in range(num_clusters):
        member_idx = [i for i, lb in enumerate(labels) if lb == ci]
        if not member_idx:
            cluster_stats.append({**CLUSTER_PROFILES[ci % len(CLUSTER_PROFILES)], "cluster_id": ci, "count": 0})
            continue
        avg_psy = sum(items[i]["psy"] for i in member_idx) / len(member_idx)
        avg_score = sum(items[i]["score_avg"] for i in member_idx) / len(member_idx)
        avg_scale = sum(items[i]["scale_score"] for i in member_idx) / len(member_idx)
        avg_abn = sum(items[i]["abnormal"] for i in member_idx) / len(member_idx)

        # 智能匹配画像
        if avg_psy < 55 or avg_scale > 30:
            profile_idx = 4  # 高风险
        elif avg_score < 65:
            profile_idx = 1  # 学业焦虑
        elif avg_abn > 3:
            profile_idx = 3  # 身心疲惫
        elif avg_psy < 75:
            profile_idx = 2  # 社交困扰
        else:
            profile_idx = 0  # 正常
        profile = CLUSTER_PROFILES[profile_idx]

        # 抽样代表性学生（最接近聚类中心的 3 个）
        cx, cy = centroids[ci][0], centroids[ci][1]
        scored_members = sorted(
            member_idx,
            key=lambda i: (norm[i][0] - cx) ** 2 + (norm[i][1] - cy) ** 2,
        )[:3]
        samples = [items[i]["student_name"] for i in scored_members]

        cluster_stats.append({
            "cluster_id": ci,
            "name": profile["name"],
            "color": profile["color"],
            "icon": profile["icon"],
            "advice": profile["advice"],
            "count": len(member_idx),
            "avg_psy": round(avg_psy, 1),
            "avg_score": round(avg_score, 1),
            "avg_scale": round(avg_scale, 1),
            "avg_abnormal": round(avg_abn, 1),
            "sample_students": samples,
        })

    points_out = []
    for i, p in enumerate(items):
        points_out.append({
            "x": round(proj[i][0], 2),
            "y": round(proj[i][1], 2),
            "cluster": labels[i],
            "name": p["student_name"],
            "id": p["student_id"],
        })

    return {
        "clusters": cluster_stats,
        "points": points_out,
        "axis_labels": {"x": "心理健康指数", "y": "学业平均分"},
        "total": len(items),
    }
