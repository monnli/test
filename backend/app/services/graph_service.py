"""学生关系知识图谱服务。"""

from __future__ import annotations

from ..extensions import db
from ..models import (
    Alert,
    Clazz,
    Grade,
    School,
    ScaleAssessment,
    Student,
    Subject,
    Teacher,
    TeacherClassSubject,
)


def build_school_graph(school_id: int | None = None, max_students: int = 60) -> dict:
    """生成学校知识图谱节点 + 边。"""
    nodes: list[dict] = []
    links: list[dict] = []
    seen: set[str] = set()

    def add_node(node_id: str, name: str, category: int, value: int = 1, symbol_size: int = 20):
        if node_id in seen:
            return
        seen.add(node_id)
        nodes.append({
            "id": node_id,
            "name": name,
            "category": category,
            "value": value,
            "symbolSize": symbol_size,
        })

    def add_link(src: str, tgt: str, value: float = 1):
        links.append({"source": src, "target": tgt, "value": value})

    schools = (
        db.session.query(School).filter_by(id=school_id, is_deleted=False).all()
        if school_id
        else db.session.query(School).filter_by(is_deleted=False).all()
    )

    for sch in schools:
        sch_id = f"school_{sch.id}"
        add_node(sch_id, sch.name, 0, symbol_size=60)

        for g in sch.grades:
            if g.is_deleted:
                continue
            g_id = f"grade_{g.id}"
            add_node(g_id, g.name, 1, symbol_size=40)
            add_link(sch_id, g_id)

            for c in g.classes:
                if c.is_deleted:
                    continue
                c_id = f"class_{c.id}"
                add_node(c_id, c.name, 2, symbol_size=30)
                add_link(g_id, c_id)

                # 学生（限量）
                student_count = 0
                for st in c.students:
                    if st.is_deleted or student_count >= max_students // len(schools):
                        continue
                    student_count += 1
                    s_id = f"student_{st.id}"
                    # 高风险学生节点放大
                    risky = (
                        db.session.query(Alert)
                        .filter(Alert.student_id == st.id, Alert.level.in_(["red", "orange"]))
                        .first()
                    )
                    add_node(s_id, st.name, 3, symbol_size=18 if risky else 12)
                    add_link(c_id, s_id, 0.5)

        # 教师
        teachers = db.session.query(Teacher).filter_by(school_id=sch.id, is_deleted=False).limit(20).all()
        for t in teachers:
            t_id = f"teacher_{t.id}"
            add_node(t_id, t.name, 4, symbol_size=22)
            tcs = db.session.query(TeacherClassSubject).filter_by(teacher_id=t.id).all()
            for r in tcs:
                add_link(t_id, f"class_{r.class_id}", 0.3)

    return {
        "categories": [
            {"name": "学校", "itemStyle": {"color": "#0ea5e9"}},
            {"name": "年级", "itemStyle": {"color": "#22c55e"}},
            {"name": "班级", "itemStyle": {"color": "#a78bfa"}},
            {"name": "学生", "itemStyle": {"color": "#f59e0b"}},
            {"name": "教师", "itemStyle": {"color": "#ef4444"}},
        ],
        "nodes": nodes,
        "links": links,
    }
