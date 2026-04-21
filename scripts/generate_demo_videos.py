"""合成演示用的课堂视频。

为 5 个班级各生成一段 30 秒的模拟课堂视频（mp4），放在 storage/demo_videos/ 下。
合成原理：
- 用 OpenCV 画出"仿真课堂"：座位网格、学生圆圈（不同颜色代表状态）
- 随机波动：某些学生"举手"（色块向上）、"趴桌"（色块下沉）
- 加上时间戳、班级名、科目等文字
- 足以让 YOLO 检测到 person 伪造物，也能让 mock 模式出合理的识别结果

产出的视频会被 camera 的 stream_url 引用（file_loop 模式循环播放）。

用法：
    python scripts/generate_demo_videos.py

输出：
    storage/demo_videos/class_7_1.mp4
    storage/demo_videos/class_7_2.mp4
    ...（5 个）
"""

from __future__ import annotations

import os
import random
import sys
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "storage" / "demo_videos"

CLASSES = [
    ("7-1", "七年级 1 班", "语文"),
    ("7-2", "七年级 2 班", "数学"),
    ("8-1", "八年级 1 班", "英语"),
    ("8-2", "八年级 2 班", "物理"),
    ("9-1", "九年级 1 班", "化学"),
]


def _put_chinese_text(img, text: str, org, font_scale: float = 0.7, color=(255, 255, 255)):
    """OpenCV 原生 putText 不支持中文。这里用 PIL 绘制中文后拷回。"""
    try:
        from PIL import Image, ImageDraw, ImageFont

        pil = Image.fromarray(img)
        draw = ImageDraw.Draw(pil)
        # 尝试系统字体
        font = None
        for f in ["/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                  "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                  "C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simhei.ttf"]:
            if os.path.exists(f):
                font = ImageFont.truetype(f, int(22 * font_scale))
                break
        if font is None:
            font = ImageFont.load_default()
        draw.text(org, text, fill=color, font=font)
        return np.array(pil)
    except Exception:
        return img


def _draw_student(img, x, y, color, label: str = ""):
    import cv2  # type: ignore

    # 头
    cv2.circle(img, (x, y), 22, color, -1)
    cv2.circle(img, (x, y), 22, (0, 0, 0), 2)
    # 身体
    cv2.rectangle(img, (x - 18, y + 22), (x + 18, y + 70), color, -1)
    cv2.rectangle(img, (x - 18, y + 22), (x + 18, y + 70), (0, 0, 0), 2)
    if label:
        cv2.putText(img, label, (x - 12, y - 28), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)


def _draw_hand_up(img, x, y, color):
    import cv2  # type: ignore

    # 举起的手：从头顶向上画一条
    cv2.line(img, (x, y - 20), (x + 20, y - 60), color, 4)
    cv2.circle(img, (x + 20, y - 60), 8, color, -1)


def generate_video(code: str, class_name: str, subject: str):
    try:
        import cv2  # type: ignore
    except ImportError:
        print(f"[ERR] 请先安装 opencv-python-headless：pip install opencv-python-headless")
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"class_{code.replace('-', '_')}.mp4"

    width, height = 1280, 720
    fps = 15
    duration_sec = 30
    total_frames = fps * duration_sec

    # mp4v 编码，兼容性好
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))

    # 30 个学生的座位（6 列 x 5 行）
    students = []
    rows, cols = 5, 6
    margin_x, margin_y = 120, 150
    spacing_x = (width - 2 * margin_x) // (cols - 1)
    spacing_y = (height - 2 * margin_y) // (rows - 1)
    rng = random.Random(hash(code))
    for r in range(rows):
        for c in range(cols):
            x = margin_x + c * spacing_x
            y = margin_y + r * spacing_y
            # 每个学生一个基础色（肤色系）
            base_color = (
                200 + rng.randint(-20, 30),
                180 + rng.randint(-20, 30),
                170 + rng.randint(-20, 30),
            )
            students.append({
                "x": x, "y": y,
                "color": base_color,
                "name": f"S{r * cols + c + 1:02d}",
                "hand_up_phase": rng.random() * 10,  # 相位
                "lying_phase": rng.random() * 20,
            })

    print(f"→ 生成 {class_name} {subject}课 视频 ({total_frames} 帧)...")

    for fi in range(total_frames):
        t = fi / fps  # 秒

        # 背景：课堂环境（深蓝色墙 + 木地板）
        img = np.zeros((height, width, 3), dtype=np.uint8)
        img[:height // 2] = (120, 100, 80)  # 上半 墙
        img[height // 2:] = (80, 60, 40)  # 下半 地板

        # 黑板
        cv2.rectangle(img, (100, 30), (1180, 120), (30, 60, 30), -1)
        cv2.rectangle(img, (100, 30), (1180, 120), (200, 200, 200), 2)

        # 讲台
        cv2.rectangle(img, (540, 130), (740, 170), (80, 50, 30), -1)

        # 绘制每个学生
        for i, s in enumerate(students):
            color = s["color"]
            x, y = s["x"], s["y"]

            # 5% 概率举手（用正弦相位让不同学生错开）
            if np.sin(t * 0.7 + s["hand_up_phase"]) > 0.96:
                _draw_hand_up(img, x, y, color)

            # 1~2% 概率趴桌（y 偏移 + 颜色变暗）
            lying = np.sin(t * 0.3 + s["lying_phase"]) > 0.95
            if lying:
                _draw_student(img, x, y + 20, (100, 100, 100))
            else:
                _draw_student(img, x, y, color)

        # 顶部信息栏
        cv2.rectangle(img, (0, 0), (width, 28), (20, 30, 50), -1)
        from datetime import datetime as dt
        timestr = dt.now().strftime("%H:%M:%S")
        img = _put_chinese_text(
            img,
            f"🟢 {class_name}  |  {subject}课  |  {timestr}",
            (16, 4),
            color=(200, 255, 200),
        )

        writer.write(img)

    writer.release()
    print(f"✅ 已输出：{output_path}")


def main():
    for code, name, subject in CLASSES:
        generate_video(code, name, subject)
    print()
    print("=" * 60)
    print("✅ 5 段演示视频已生成在：")
    print(f"   {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
