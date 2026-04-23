"""一键切换到 Mock 模式（所有流水线返回兜底结果）。

做的事：
1. 把 ai_service/models/yolov8_classroom.pt 改名为 .pt.bak（让 BehaviorPipeline 找不到真模型）
2. 把 yolov8_classroom_labels.json 也备份一下
3. 把 .env 里的 DASHSCOPE_API_KEY 改成空（让 TextPipeline 走关键词规则兜底）
4. 重启 AI 服务后，5 条流水线全部显示为 "mock" 状态

还原：python scripts/activate_real_models.py

用法：
    python scripts/use_mock_models.py
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
AI_MODEL_DIR = PROJECT_ROOT / "ai_service" / "models"
ENV_FILE = PROJECT_ROOT / ".env"


def backup_if_exists(path: Path) -> None:
    """把文件加 .bak 后缀备份（如果已有 .bak 则追加时间戳）。"""
    if not path.exists():
        print(f"[SKIP] 未发现：{path.name}")
        return
    bak = path.with_suffix(path.suffix + ".bak")
    if bak.exists():
        # 已有 .bak，加时间戳防覆盖
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        bak = path.with_suffix(path.suffix + f".bak_{ts}")
    path.rename(bak)
    size_mb = bak.stat().st_size / 1024 / 1024
    print(f"[OK] {path.name} → {bak.name}  （{size_mb:.1f} MB，已备份）")


def clear_dashscope_key() -> None:
    """把 .env 中 DASHSCOPE_API_KEY 行的值清空（保留 key 行方便还原时识别）。"""
    if not ENV_FILE.exists():
        print(f"[SKIP] 未找到 {ENV_FILE}")
        return

    lines = ENV_FILE.read_text(encoding="utf-8").splitlines()
    new_lines = []
    changed = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("DASHSCOPE_API_KEY=") and "DASHSCOPE_API_KEY=" != stripped:
            # 已有值 → 注释掉原行 + 加空值行
            new_lines.append(f"# [mock] {line}")
            new_lines.append("DASHSCOPE_API_KEY=")
            changed = True
            continue
        new_lines.append(line)

    if changed:
        ENV_FILE.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
        print(f"[OK] .env 中 DASHSCOPE_API_KEY 已置空（原值已注释保留）")
    else:
        print(f"[SKIP] .env 中 DASHSCOPE_API_KEY 已是空值，无需修改")


def main():
    print("=" * 60)
    print("青苗守护者 · 切换到 Mock 展示模式")
    print("=" * 60)
    print()

    # 1. 备份 YOLO 自训权重
    print("[1/3] 备份 YOLO 自训模型权重...")
    backup_if_exists(AI_MODEL_DIR / "yolov8_classroom.pt")
    backup_if_exists(AI_MODEL_DIR / "yolov8_classroom_labels.json")

    # 2. 清空通义千问 key
    print()
    print("[2/3] 清空通义千问 API Key...")
    clear_dashscope_key()

    # 3. 提示
    print()
    print("[3/3] 影响范围说明：")
    print("  - Behavior 行为检测 → 走 mock（基于图像哈希生成稳定的伪检测框）")
    print("  - Face 人脸识别    → 走 mock（生成稳定的 512 维伪向量）")
    print("  - Emotion 表情识别 → 走 mock（Dirichlet 随机分布，中性占主）")
    print("  - Pose 姿态识别    → 走 mock（根据图像哈希生成坐姿/抬头等）")
    print("  - Text 文本分析    → 走关键词词典规则（非 LLM）")
    print()
    print("=" * 60)
    print("✅ 已切换到 Mock 模式")
    print()
    print("下一步：")
    print("  1. 重启 AI 服务：cd ai_service && python server.py")
    print("  2. 重启后端：   cd backend && python run.py")
    print("  3. 浏览器访问 /system/ai，所有流水线状态应显示「降级」")
    print()
    print("还原真实模型：python scripts/activate_real_models.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
