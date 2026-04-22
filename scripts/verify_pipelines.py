"""端到端验证 5 个流水线都能加载真模型。

流程：
1. 依次加载 face / emotion / behavior / pose / text 流水线
2. 对每个跑一次推理
3. 打印 status（ready / mock / error）
4. 最后输出汇总表

用法：
    python scripts/verify_pipelines.py
    python scripts/verify_pipelines.py --image path/to/test.jpg  # 用真实图测
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "ai_service"))

# 加载 .env 里的 API key
try:
    from dotenv import load_dotenv

    load_dotenv(PROJECT_ROOT / ".env")
except Exception:
    pass


def _make_dummy_image():
    """512x512 RGB 随机图，供 mock 或真实推理用。"""
    import numpy as np

    rng = np.random.default_rng(2026)
    return rng.integers(0, 255, size=(512, 512, 3), dtype=np.uint8)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", help="测试图片路径（可选，不填用随机图）")
    args = parser.parse_args()

    try:
        from pipelines import (
            behavior_pipeline,
            emotion_pipeline,
            face_pipeline,
            pose_pipeline,
            text_pipeline,
        )
    except ImportError as exc:
        print(f"[ERR] 无法导入流水线：{exc}")
        sys.exit(1)

    if args.image and Path(args.image).exists():
        try:
            from PIL import Image  # type: ignore
            import numpy as np

            img = np.array(Image.open(args.image).convert("RGB"))
            print(f"[使用真实图像] {args.image}  shape={img.shape}")
        except Exception as exc:  # noqa: BLE001
            print(f"[WARN] 读图失败，用随机图：{exc}")
            img = _make_dummy_image()
    else:
        img = _make_dummy_image()

    print()
    print("=" * 60)
    print("流水线验证")
    print("=" * 60)

    results = []

    print("\n[1/5] Face（InsightFace）...")
    try:
        face_pipeline.ensure_loaded()
        r = face_pipeline.run(img)
        print(f"  状态：{face_pipeline.status}  检测到 {len(r)} 张脸")
        results.append(("face", face_pipeline.status, face_pipeline.error_detail))
    except Exception as exc:  # noqa: BLE001
        print(f"  [ERR] {exc}")
        results.append(("face", "error", str(exc)))

    print("\n[2/5] Emotion（HSEmotion）...")
    try:
        emotion_pipeline.ensure_loaded()
        r = emotion_pipeline.run(img)
        print(f"  状态：{emotion_pipeline.status}  结果：{r.get('emotion_cn')} ({r.get('confidence', 0):.2f})")
        results.append(("emotion", emotion_pipeline.status, emotion_pipeline.error_detail))
    except Exception as exc:  # noqa: BLE001
        print(f"  [ERR] {exc}")
        results.append(("emotion", "error", str(exc)))

    print("\n[3/5] Behavior（YOLOv8 自训）...")
    try:
        behavior_pipeline.ensure_loaded()
        r = behavior_pipeline.run(img)
        dets = r.get("detections", [])
        labels = sorted({d["label_cn"] for d in dets})
        print(f"  状态：{behavior_pipeline.status}  检出 {len(dets)} 个目标  类别：{labels}")
        results.append(("behavior", behavior_pipeline.status, behavior_pipeline.error_detail))
    except Exception as exc:  # noqa: BLE001
        print(f"  [ERR] {exc}")
        results.append(("behavior", "error", str(exc)))

    print("\n[4/5] Pose（MediaPipe Pose + FaceMesh）...")
    try:
        pose_pipeline.ensure_loaded()
        r = pose_pipeline.run(img)
        print(f"  状态：{pose_pipeline.status}  行为：{r.get('behaviors_cn')}  pitch：{r.get('pitch')}")
        results.append(("pose", pose_pipeline.status, pose_pipeline.error_detail))
    except Exception as exc:  # noqa: BLE001
        print(f"  [ERR] {exc}")
        results.append(("pose", "error", str(exc)))

    print("\n[5/5] Text（通义千问）...")
    try:
        text_pipeline.ensure_loaded()
        r = text_pipeline.analyze_sentiment("今天上课特别开心，和同学一起合作完成了一个项目")
        print(f"  状态：{text_pipeline.status}")
        print(f"  分析结果：极性={r.get('polarity')}  风险={r.get('risk_level')}  "
              f"标签={r.get('emotion_tags')}")
        results.append(("text", text_pipeline.status, text_pipeline.error_detail))
    except Exception as exc:  # noqa: BLE001
        print(f"  [ERR] {exc}")
        results.append(("text", "error", str(exc)))

    # 汇总
    print()
    print("=" * 60)
    print("汇总")
    print("=" * 60)
    print(f"  {'流水线':<12}{'状态':<12}说明")
    print(f"  {'-' * 48}")
    for name, status, error in results:
        emoji = "✅" if status == "ready" else ("⚠️" if status == "mock" else "❌")
        note = error or ("真实模型" if status == "ready" else "使用 mock 降级")
        print(f"  {name:<12}{emoji} {status:<10}{note[:80]}")

    ready_count = sum(1 for _, s, _ in results if s == "ready")
    mock_count = sum(1 for _, s, _ in results if s == "mock")
    print()
    print(f"  ✅ 真实模型就绪：{ready_count}/5")
    if mock_count > 0:
        print(f"  ⚠️  mock 降级：{mock_count}/5（系统仍可运行，但不是真实推理）")
    print()
    print("=" * 60)


if __name__ == "__main__":
    main()
