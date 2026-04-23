"""设置全局 Mock 模式开关（写入 .env 的 FORCE_MOCK）。

用法：
    python scripts/set_mock_mode.py             # 默认开启 mock（推荐）
    python scripts/set_mock_mode.py --off       # 关闭 mock，尝试加载真实模型

效果：
  FORCE_MOCK=true  → 5 条流水线无条件 mock，启动零延迟
  FORCE_MOCK=false → 流水线尝试加载真实模型，失败则自动 mock 降级
"""

from __future__ import annotations

import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--off", action="store_true", help="关闭全局 Mock（加载真实模型）")
    args = parser.parse_args()

    value = "false" if args.off else "true"

    if not ENV_FILE.exists():
        ENV_FILE.write_text(f"FORCE_MOCK={value}\n", encoding="utf-8")
        print(f"[OK] 已创建 .env，FORCE_MOCK={value}")
    else:
        lines = ENV_FILE.read_text(encoding="utf-8").splitlines()
        new_lines = []
        replaced = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("FORCE_MOCK=") or stripped.startswith("# FORCE_MOCK="):
                new_lines.append(f"FORCE_MOCK={value}")
                replaced = True
            else:
                new_lines.append(line)
        if not replaced:
            new_lines.append(f"FORCE_MOCK={value}")
        ENV_FILE.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
        print(f"[OK] .env 中 FORCE_MOCK 已设为 {value}")

    print()
    if value == "true":
        print("✅ 已切换到全局 Mock 模式")
        print("   - 所有流水线启动时立即进入 mock 状态，跳过真实模型加载")
        print("   - 同图 / 同文本 → 同结果，现场演示稳定不翻车")
    else:
        print("✅ 已关闭全局 Mock 模式")
        print("   - 下次启动时会尝试加载真实模型")
        print("   - 加载失败仍会自动降级到 mock")

    print()
    print("下一步：重启 AI 服务")
    print("  cd ai_service && python server.py")


if __name__ == "__main__":
    main()
