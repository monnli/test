"""下载公开的课堂测试视频供真实压测使用。

不自动下载版权视频，而是生成一份 README 告诉用户去哪里下载 + 合规说明。

用法：
    python scripts/download_test_videos.py
"""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TARGET = PROJECT_ROOT / "storage" / "test_videos"

README = """# 青苗守护者 · 真实课堂测试视频

由于版权原因，我们不自动下载课堂视频。请从以下合规渠道自行获取：

## 公开数据集（推荐）

1. **ClassroomAct Dataset**（GitHub 公开）
   https://github.com/xxxxxxx/classroomAct
   包含 8 种课堂行为标注，直接下载使用。

2. **中国课堂学生行为数据集（BJTU）**
   北京交通大学开源，需发邮件申请。

## 合规的 B 站公开课视频

- 在 B 站搜索"公开课 录制"、"中学 课堂"，选择 CC BY 开源视频下载
- 工具：yt-dlp（`pip install yt-dlp`）
  ```
  yt-dlp -o "sample_%(id)s.mp4" "https://www.bilibili.com/video/BVxxx"
  ```

## 自录视频（最可控）

团队成员在本校教室自己录一段 30 秒视频放到这里即可。

---

## 下载后的文件放置

把 mp4 文件放到本目录下，然后运行：

```
python scripts/benchmark_video.py storage/test_videos/your_video.mp4
```

将生成识别结果报告（HTML + 关键帧截图），放进答辩 PPT。

---

## 报告建议截图的画面

1. 多人课堂全景（证明学生级别识别）
2. 有举手的画面（证明姿态识别）
3. 有趴桌的画面（证明异常行为检测）
4. 不同表情（证明表情识别）
5. 参与度低谷的时刻 + 参与度恢复的时刻（证明时间轴）
"""


def main():
    TARGET.mkdir(parents=True, exist_ok=True)
    readme_path = TARGET / "README.md"
    readme_path.write_text(README, encoding="utf-8")
    print(f"[OK] 已创建 {TARGET}")
    print(f"[OK] 请阅读 {readme_path} 了解如何获取测试视频")
    print()
    print("提示：如果只是想快速演示，直接运行：")
    print("    python scripts/generate_demo_videos.py")
    print("  会合成 5 段课堂演示视频到 storage/demo_videos/")


if __name__ == "__main__":
    main()
