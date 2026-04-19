"""演示数据增强脚本（M8 阶段）。

为 M1 已生成的 180 个学生补充：
- 心理量表测评（每名学生 1~3 份不同量表）
- 文本情绪分析记录（部分学生）
- AI 对话样例
- 学业成绩
- 课堂分析任务 + 行为/表情记录
- 情绪时序（30 天/学生）
- 4 级预警工单

让大屏、关联分析、报告中心等所有页面都能直接展示「真实感十足」的演示效果。

用法：
    python scripts/seed_demo_extras.py
"""

from __future__ import annotations

import json
import random
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(PROJECT_ROOT / ".env")

random.seed(20260420)


def main() -> int:
    from app import create_app
    from app.extensions import db
    from app.models import (
        AIConversation,
        AIConversationMessage,
        Alert,
        AnalysisTask,
        BehaviorRecord,
        Clazz,
        EmotionRecord,
        EmotionTimeline,
        Exam,
        Grade,
        Score,
        Scale,
        ScaleAssessment,
        Student,
        Subject,
        TextAnalysis,
        Video,
    )
    from app.services.psychology_service import ensure_scales_seeded
    from app.services.correlation_service import recompute_alerts_for_visible

    app = create_app()
    with app.app_context():
        print("→ 确保量表已 seed...")
        ensure_scales_seeded()

        students = db.session.query(Student).filter_by(is_deleted=False).all()
        scales = db.session.query(Scale).all()
        if not students or not scales:
            print("[ERR] 请先运行 seed_demo_data.py")
            return 1

        # ====== 1. 量表测评 ======
        print(f"→ 为 {len(students)} 名学生生成量表测评...")
        for s in students:
            n_assess = random.randint(1, 3)
            chosen_scales = random.sample(scales, k=min(n_assess, len(scales)))
            for sc in chosen_scales:
                # 假装学生答题，用一个倾向（多数学生中等水平）
                level_bins = json.loads(sc.interpretation) if sc.interpretation else []
                if not level_bins:
                    continue
                # 大多数选第二档（轻微/正常）
                bin_idx = random.choices(
                    range(len(level_bins)), weights=[6, 8, 4, 2, 1][: len(level_bins)]
                )[0]
                target = level_bins[bin_idx]
                target_score = random.uniform(target["min"], target["max"])
                ass = ScaleAssessment(
                    student_id=s.id,
                    scale_id=sc.id,
                    answers="{}",
                    total_score=round(target_score, 1),
                    level=target["level"],
                    level_color=target.get("color", "gray"),
                    advice=target.get("advice", ""),
                    completed_at=datetime.utcnow() - timedelta(days=random.randint(1, 28)),
                )
                db.session.add(ass)

        db.session.commit()

        # ====== 2. 文本情绪分析 ======
        print("→ 生成文本情绪分析样本...")
        text_samples = [
            ("本周周记", "这周一切都还顺利，和同学相处也开心，老师讲课也听得懂。", "正面", "none", []),
            ("作文", "最近觉得有点累，作业很多，希望周末能好好休息。", "中性", "low", ["累"]),
            ("心情记录", "我感到很孤独，没人理解我，整夜睡不好。", "负面", "medium", ["孤独", "失眠"]),
            ("周记", "今天考试发挥不错，妈妈说要奖励我！", "正面", "none", []),
            ("作文", "压力好大，我感到喘不过气来。", "负面", "low", ["压力大"]),
            ("私密日记", "我不想活了，没人会想念我。", "负面", "high", ["不想活", "想消失"]),
        ]
        sample_students = random.sample(students, k=min(60, len(students)))
        for st in sample_students:
            title, content, polarity, risk, kws = random.choice(text_samples)
            db.session.add(
                TextAnalysis(
                    student_id=st.id,
                    title=title,
                    content=content,
                    polarity=polarity,
                    risk_level=risk,
                    risk_keywords=json.dumps(kws, ensure_ascii=False),
                    emotion_tags=json.dumps(["平和" if polarity == "正面" else "焦虑"], ensure_ascii=False),
                    summary=content[:30],
                    suggestion="保持关注，必要时与心理老师联系",
                )
            )

        # ====== 3. AI 对话样例 ======
        print("→ 生成 AI 对话样例...")
        chat_students = random.sample(students, k=min(30, len(students)))
        for st in chat_students:
            risk = random.choices(["none", "low", "medium", "high"], weights=[8, 5, 2, 1])[0]
            conv = AIConversation(
                student_id=st.id, title=f"{st.name} 的咨询", risk_level=risk, message_count=4
            )
            db.session.add(conv)
            db.session.flush()
            user_text = {
                "none": "今天有点累，但还好",
                "low": "我最近压力很大",
                "medium": "我感觉很难受，没人理解我",
                "high": "我真的撑不下去了",
            }[risk]
            ai_text = {
                "none": "听起来你今天经历了不少。能告诉我哪些事让你感到累吗？",
                "low": "我能感受到你的压力。压力虽然不舒服，但它也提醒我们需要喘息。",
                "medium": "听到你这样说我很担心。能再多告诉我一些你现在的感受吗？",
                "high": "请你一定告诉信任的老师或家人，也可以拨打 12320 心理援助热线。我会一直在这里陪你。",
            }[risk]
            db.session.add_all([
                AIConversationMessage(conversation_id=conv.id, role="user", content=user_text, risk_level=risk),
                AIConversationMessage(conversation_id=conv.id, role="assistant", content=ai_text, risk_level=risk),
            ])

        # ====== 4. 学业成绩 ======
        print("→ 生成学业成绩...")
        subjects = db.session.query(Subject).all()
        for grade in db.session.query(Grade).all():
            for i, sub in enumerate(subjects):
                exam = Exam(
                    name=f"{grade.name}{sub.name}期中测验",
                    subject_id=sub.id,
                    grade_id=grade.id,
                    exam_date=date.today() - timedelta(days=14),
                )
                db.session.add(exam)
                db.session.flush()
                grade_students = db.session.query(Student).filter_by(grade_id=grade.id, is_deleted=False).all()
                for st in grade_students:
                    db.session.add(
                        Score(
                            exam_id=exam.id,
                            student_id=st.id,
                            score=round(random.uniform(40, 100), 1),
                        )
                    )

        # ====== 5. 情绪时序（每生 30 天）======
        print("→ 生成 30 天情绪时序...")
        for st in students:
            base = random.uniform(70, 90)
            for i in range(30):
                d = date.today() - timedelta(days=i)
                noise = random.uniform(-8, 6)
                score = max(20, min(99, base + noise))
                if score < 50:
                    risk = "medium"
                    pol = "负面"
                elif score < 70:
                    risk = "low"
                    pol = "中性"
                else:
                    risk = "none"
                    pol = "正面"
                db.session.add(
                    EmotionTimeline(
                        student_id=st.id,
                        record_date=d,
                        score=round(score, 1),
                        polarity=pol,
                        risk_level=risk,
                        source="auto",
                    )
                )

        # ====== 6. 课堂分析任务 + 行为/表情记录（演示用 5 个班次）======
        print("→ 生成课堂分析任务...")
        classes = db.session.query(Clazz).filter_by(is_deleted=False).all()
        for c in random.sample(classes, k=min(4, len(classes))):
            video = Video(
                title=f"{c.grade.name}{c.name} · 数学课",
                storage_key=f"videos/demo/class_{c.id}.mp4",
                url=f"/storage/videos/demo/class_{c.id}.mp4",
                size_bytes=15 * 1024 * 1024,
                duration_seconds=45 * 60,
                fps=25.0,
                width=1280,
                height=720,
                class_id=c.id,
            )
            db.session.add(video)
            db.session.flush()

            task = AnalysisTask(
                video_id=video.id,
                status="success",
                progress=100,
                processed_frames=900,
                total_frames=900,
                sample_interval_sec=3.0,
                started_at=datetime.utcnow() - timedelta(hours=2),
                finished_at=datetime.utcnow() - timedelta(hours=1),
                summary=json.dumps(
                    {
                        "behavior_summary": {"学生": 800, "举手": 35, "趴桌": 12, "玩手机": 3},
                        "emotion_summary": {"中性": 320, "高兴": 200, "专注": 150, "疲惫": 30},
                        "total_frames": 900,
                        "dominant_emotion": "中性",
                    },
                    ensure_ascii=False,
                ),
            )
            db.session.add(task)
            db.session.flush()

            for i in range(60):
                ts = i * 30.0
                cnt = random.randint(20, 30)
                for _ in range(cnt):
                    db.session.add(
                        BehaviorRecord(
                            task_id=task.id,
                            video_id=video.id,
                            frame_time=ts,
                            label="person",
                            label_cn="学生",
                            confidence=0.9,
                        )
                    )
                if random.random() < 0.4:
                    db.session.add(
                        BehaviorRecord(
                            task_id=task.id, video_id=video.id, frame_time=ts,
                            label="hand_up", label_cn="举手", confidence=0.78,
                        )
                    )
                # 表情
                emotion_options = [("中性", 0.4), ("高兴", 0.25), ("专注", 0.2), ("疲惫", 0.1), ("惊讶", 0.05)]
                ec = random.choices([e[0] for e in emotion_options], weights=[e[1] for e in emotion_options])[0]
                db.session.add(
                    EmotionRecord(
                        task_id=task.id, video_id=video.id, frame_time=ts,
                        emotion=ec, emotion_cn=ec, confidence=random.uniform(0.6, 0.95),
                    )
                )

        db.session.commit()
        print("→ 重新计算所有学生的预警...")
        result = recompute_alerts_for_visible(student_ids=None)
        print(f"   生成预警 {result['alerts_count']} 条")

        print()
        print("=" * 60)
        print("✅ 演示数据已增强完成！")
        print("   - 量表测评、文本分析、AI 对话、学业成绩、情绪时序")
        print("   - 4 段课堂视频分析任务 + 行为/表情记录")
        print(f"   - {result['alerts_count']} 条预警工单")
        print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
