"""视频识别压力测试 / 真实性能评估脚本。

对一段课堂视频跑完整流水线，输出：
- 每秒处理帧数（FPS）
- 检测到学生总数
- 各类行为统计
- 各类情绪统计
- 参与度时间曲线
- HTML 报告（含 3~5 张关键帧截图 + 检测框叠加）

用法：
    python scripts/benchmark_video.py <video_path> [--output report.html] [--interval 2.0]

适用场景：
- 答辩前跑一段真实课堂视频，输出报告作为项目证据
- 真实性能评估（CPU / GPU 对比）
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

REPORT_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>青苗守护者 · 视频识别压测报告</title>
<style>
  body {{ font-family: -apple-system, 'PingFang SC', sans-serif; max-width: 1200px; margin: 24px auto; padding: 16px; color: #1f2937; }}
  h1 {{ background: linear-gradient(90deg, #22c55e, #0ea5e9); -webkit-background-clip: text; color: transparent; }}
  .grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 20px 0; }}
  .card {{ border: 1px solid #e5e7eb; border-radius: 8px; padding: 12px; text-align: center; }}
  .label {{ color: #64748b; font-size: 12px; }}
  .value {{ font-size: 28px; font-weight: 700; color: #0ea5e9; margin-top: 4px; }}
  .chart {{ margin: 20px 0; padding: 12px; border: 1px solid #e5e7eb; border-radius: 8px; }}
  .bar {{ height: 18px; background: #e0f2fe; margin: 4px 0; border-radius: 4px; overflow: hidden; position: relative; }}
  .bar-fill {{ height: 100%; background: linear-gradient(90deg, #22c55e, #0ea5e9); }}
  .bar-label {{ position: absolute; left: 8px; top: 0; color: #0f172a; font-size: 12px; line-height: 18px; }}
  .frames {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }}
  .frame {{ border: 1px solid #e5e7eb; border-radius: 8px; padding: 8px; }}
  .frame img {{ width: 100%; border-radius: 4px; }}
  .frame .caption {{ color: #64748b; font-size: 12px; text-align: center; margin-top: 4px; }}
</style>
</head>
<body>
<h1>青苗守护者 · 视频识别压测报告</h1>
<p><strong>视频：</strong>{video_path}</p>
<p><strong>时长：</strong>{duration:.1f}s　|　<strong>分辨率：</strong>{resolution}　|　<strong>总帧数：</strong>{total_frames}</p>
<p><strong>采样间隔：</strong>{interval}s　|　<strong>识别帧数：</strong>{sampled}　|　<strong>总耗时：</strong>{elapsed:.1f}s　|　<strong>平均 FPS：</strong>{fps:.2f}</p>

<div class="grid">
  <div class="card"><div class="label">检测到最多学生数（单帧）</div><div class="value">{max_persons}</div></div>
  <div class="card"><div class="label">累计举手次数</div><div class="value">{total_hand_up}</div></div>
  <div class="card"><div class="label">累计低头次数</div><div class="value">{total_head_down}</div></div>
  <div class="card"><div class="label">平均参与度</div><div class="value">{avg_engagement:.1f}</div></div>
</div>

<div class="chart">
  <h3>行为分布</h3>
  {behavior_bars}
</div>

<div class="chart">
  <h3>情绪分布</h3>
  {emotion_bars}
</div>

<div class="chart">
  <h3>参与度曲线（采样点）</h3>
  <svg viewBox="0 0 1000 200" style="width: 100%; height: 200px;">
    <polyline points="{engagement_polyline}" fill="none" stroke="#0ea5e9" stroke-width="2" />
  </svg>
</div>

<h3>关键帧采样</h3>
<div class="frames">{key_frames}</div>

<p style="color:#94a3b8; font-size: 12px; margin-top: 32px;">
  生成时间：{gen_time}<br/>
  本报告由青苗守护者 scripts/benchmark_video.py 自动生成
</p>
</body>
</html>
"""


def _bar(label: str, value: int, max_value: int) -> str:
    pct = (value / max(1, max_value)) * 100
    return (
        f'<div class="bar"><div class="bar-fill" style="width:{pct:.0f}%"></div>'
        f'<div class="bar-label">{label}: {value} ({pct:.0f}%)</div></div>'
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("video", help="视频文件路径")
    parser.add_argument("--output", default="benchmark_report.html")
    parser.add_argument("--interval", type=float, default=2.0, help="抽帧间隔秒")
    parser.add_argument("--ai-url", default="http://localhost:8000")
    parser.add_argument("--keyframes", type=int, default=6)
    args = parser.parse_args()

    video_path = Path(args.video).resolve()
    if not video_path.exists():
        print(f"[ERR] 视频不存在：{video_path}")
        return 1

    try:
        import cv2  # type: ignore
    except ImportError:
        print("[ERR] 需要 opencv-python-headless：pip install opencv-python-headless")
        return 1

    import httpx

    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    step = max(1, int(fps * args.interval))

    print(f"→ 视频 {video_path.name}  {w}x{h}  {duration:.1f}s  {total_frames} 帧")
    print(f"→ 每 {step} 帧采样一次，总采样 ~{total_frames // step} 次")

    summary = {
        "behavior": {},
        "emotion": {},
        "max_persons": 0,
        "engagement_list": [],
        "keyframes": [],
    }
    start_ts = time.time()

    sampled = 0
    keyframe_interval = max(1, (total_frames // step) // args.keyframes)

    for frame_idx in range(0, total_frames, step):
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ok, frame = cap.read()
        if not ok:
            continue

        _, jpg = cv2.imencode(".jpg", frame)
        b64 = base64.b64encode(jpg.tobytes()).decode("utf-8")

        try:
            with httpx.Client(timeout=30) as client:
                r = client.post(
                    f"{args.ai_url}/classroom/analyze",
                    json={"image": b64, "camera_key": "bench", "recognize_face": False},
                )
                r.raise_for_status()
                data = r.json().get("data", {})
        except Exception as exc:  # noqa: BLE001
            print(f"  帧 {frame_idx} 分析失败：{exc}")
            continue

        students = data.get("students", [])
        s = data.get("summary", {})

        summary["max_persons"] = max(summary["max_persons"], s.get("total_persons", 0))
        summary["engagement_list"].append(s.get("engagement_score", 0))

        for st in students:
            for b in st.get("behaviors_cn", []):
                summary["behavior"][b] = summary["behavior"].get(b, 0) + 1
            emo = st.get("emotion_cn")
            if emo:
                summary["emotion"][emo] = summary["emotion"].get(emo, 0) + 1

        if sampled % keyframe_interval == 0 and len(summary["keyframes"]) < args.keyframes:
            # 把识别框画到帧上
            vis_frame = frame.copy()
            for st in students:
                bbox = st.get("bbox") or [0, 0, 0, 0]
                x1, y1, x2, y2 = [int(v) for v in bbox]
                cv2.rectangle(vis_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                label = (st.get("behaviors_cn") or ["学生"])[0]
                cv2.putText(vis_frame, label, (x1, max(18, y1 - 6)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            _, kf_jpg = cv2.imencode(".jpg", vis_frame)
            summary["keyframes"].append({
                "time": frame_idx / fps,
                "persons": s.get("total_persons", 0),
                "engagement": s.get("engagement_score", 0),
                "b64": base64.b64encode(kf_jpg.tobytes()).decode("utf-8"),
            })

        sampled += 1
        if sampled % 10 == 0:
            print(f"  进度 {sampled} / {total_frames // step}...")

    cap.release()

    elapsed = time.time() - start_ts
    bench_fps = sampled / elapsed if elapsed > 0 else 0
    avg_engagement = (
        sum(summary["engagement_list"]) / len(summary["engagement_list"])
        if summary["engagement_list"] else 0
    )

    # 生成 HTML
    max_b = max(summary["behavior"].values()) if summary["behavior"] else 1
    beh_bars = "".join(
        _bar(k, v, max_b) for k, v in sorted(summary["behavior"].items(), key=lambda x: -x[1])
    )
    max_e = max(summary["emotion"].values()) if summary["emotion"] else 1
    emo_bars = "".join(
        _bar(k, v, max_e) for k, v in sorted(summary["emotion"].items(), key=lambda x: -x[1])
    )
    n = len(summary["engagement_list"])
    engagement_polyline = " ".join(
        f"{int(i / max(1, n - 1) * 1000)},{int(200 - (e / 100) * 180)}"
        for i, e in enumerate(summary["engagement_list"])
    )
    key_frames_html = "".join(
        f'<div class="frame"><img src="data:image/jpeg;base64,{kf["b64"]}"/>'
        f'<div class="caption">时间 {kf["time"]:.1f}s · {kf["persons"]} 人 · 参与度 {kf["engagement"]:.0f}</div></div>'
        for kf in summary["keyframes"]
    )
    from datetime import datetime

    html = REPORT_TEMPLATE.format(
        video_path=str(video_path),
        duration=duration,
        resolution=f"{w}x{h}",
        total_frames=total_frames,
        interval=args.interval,
        sampled=sampled,
        elapsed=elapsed,
        fps=bench_fps,
        max_persons=summary["max_persons"],
        total_hand_up=summary["behavior"].get("举手", 0),
        total_head_down=summary["behavior"].get("低头", 0),
        avg_engagement=avg_engagement,
        behavior_bars=beh_bars or '<div style="color:#94a3b8">无数据</div>',
        emotion_bars=emo_bars or '<div style="color:#94a3b8">无数据</div>',
        engagement_polyline=engagement_polyline,
        key_frames=key_frames_html or '<div style="color:#94a3b8">无数据</div>',
        gen_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )

    Path(args.output).write_text(html, encoding="utf-8")

    print()
    print("=" * 60)
    print(f"✅ 压测完成")
    print(f"   采样 {sampled} 帧 · 耗时 {elapsed:.1f}s · 平均 {bench_fps:.2f} FPS")
    print(f"   最多学生数 {summary['max_persons']} · 平均参与度 {avg_engagement:.1f}")
    print(f"   报告：{args.output}")
    print("=" * 60)


if __name__ == "__main__":
    sys.exit(main() or 0)
