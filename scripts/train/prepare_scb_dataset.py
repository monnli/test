"""准备 SCB 课堂行为数据集。

数据源：https://github.com/Whiffe/SCB-dataset
该数据集是 YOLO 格式的中小学生课堂行为数据集，包含：
- 手（hand）
- 读（read）
- 写（write）
- 站立（stand）
- 举手（raise_hand）
- 玩手机（phone）
- 其他行为（根据不同版本略有差异）

本脚本流程：
1. 从 GitHub 克隆仓库（如已存在则跳过）
2. 把图像和标签复制/软链接到 data/scb/
3. 划分 train / val（默认 9:1）
4. 生成 scb.yaml 配置文件
5. 统计数据集规模与类别分布

用法：
    python scripts/train/prepare_scb_dataset.py
    python scripts/train/prepare_scb_dataset.py --val-ratio 0.15
"""

from __future__ import annotations

import argparse
import random
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "scb"
CACHE_DIR = PROJECT_ROOT / "data" / ".cache"
SCB_REPO = "https://github.com/Whiffe/SCB-dataset.git"

# SCB-v3 默认类别（若下载的是其他版本需调整）
DEFAULT_CLASSES = ["hand", "read", "write", "stand", "phone", "look_at_screen", "bow_head"]


def _run(cmd: list[str], cwd: Path | None = None) -> int:
    print(f"[RUN] {' '.join(cmd)}")
    return subprocess.call(cmd, cwd=cwd)


def clone_if_needed() -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    target = CACHE_DIR / "SCB-dataset"
    if target.exists():
        print(f"[SKIP] 仓库已存在：{target}")
        return target

    print(f"[CLONE] {SCB_REPO} → {target}")
    print("如果克隆很慢，可以 Ctrl+C 中断，手动从 GitHub ZIP 下载后解压到：")
    print(f"  {target}")
    code = _run(["git", "clone", "--depth", "1", SCB_REPO, str(target)])
    if code != 0:
        print("[ERR] git clone 失败，请手动下载：")
        print(f"  1. 访问 {SCB_REPO}")
        print(f"  2. 下载 ZIP，解压到 {target}")
        sys.exit(1)
    return target


def find_yolo_data(repo_dir: Path) -> tuple[Path, Path]:
    """在仓库里找 images / labels 目录。不同版本位置可能不同。"""
    candidates = [
        # SCB-v3
        (repo_dir / "SCB-Dataset-3" / "images", repo_dir / "SCB-Dataset-3" / "labels"),
        # SCB-v2
        (repo_dir / "SCB-Dataset-2" / "images", repo_dir / "SCB-Dataset-2" / "labels"),
        # 通用
        (repo_dir / "images", repo_dir / "labels"),
    ]
    for img_d, lbl_d in candidates:
        if img_d.exists() and lbl_d.exists():
            print(f"[FOUND] 图像目录：{img_d}")
            print(f"[FOUND] 标签目录：{lbl_d}")
            return img_d, lbl_d
    # 兜底：任意子目录下找 images 与 labels
    for img_d in repo_dir.rglob("images"):
        lbl_d = img_d.parent / "labels"
        if lbl_d.exists():
            print(f"[FOUND] 兜底匹配：{img_d}")
            return img_d, lbl_d
    print("[ERR] 未找到 images/labels 目录，请检查仓库结构：")
    for p in repo_dir.iterdir():
        print(f"  {p}")
    sys.exit(1)


def split_dataset(
    src_images: Path,
    src_labels: Path,
    val_ratio: float = 0.1,
) -> tuple[int, int]:
    """划分 train/val，复制到 DATA_DIR。"""
    # 清空旧数据
    for sub in ("images/train", "images/val", "labels/train", "labels/val"):
        d = DATA_DIR / sub
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True, exist_ok=True)

    # 收集所有图像文件
    all_images = []
    for ext in ("*.jpg", "*.jpeg", "*.png"):
        all_images.extend(src_images.rglob(ext))
    if not all_images:
        print(f"[ERR] 没找到图像文件于：{src_images}")
        sys.exit(1)

    print(f"[INFO] 共找到 {len(all_images)} 张图像")
    random.seed(2026)
    random.shuffle(all_images)
    val_count = int(len(all_images) * val_ratio)
    val_set = set(all_images[:val_count])

    train_n = val_n = 0
    missed = 0
    for img_path in all_images:
        # 找对应的 label（相对路径同名 .txt）
        rel = img_path.relative_to(src_images)
        label_path = src_labels / rel.with_suffix(".txt")
        if not label_path.exists():
            missed += 1
            continue

        split = "val" if img_path in val_set else "train"
        dst_img = DATA_DIR / "images" / split / img_path.name
        dst_lbl = DATA_DIR / "labels" / split / label_path.name
        # 使用硬链接节省空间，失败则复制
        try:
            dst_img.hardlink_to(img_path)
            dst_lbl.hardlink_to(label_path)
        except Exception:
            shutil.copy2(img_path, dst_img)
            shutil.copy2(label_path, dst_lbl)
        if split == "train":
            train_n += 1
        else:
            val_n += 1

    if missed:
        print(f"[WARN] {missed} 张图像没有对应标签，已跳过")
    print(f"[OK] 训练集：{train_n} 张  验证集：{val_n} 张")
    return train_n, val_n


def write_yaml(num_classes: int | None = None) -> None:
    yaml_path = DATA_DIR / "scb.yaml"
    classes = DEFAULT_CLASSES
    if num_classes is not None and num_classes != len(classes):
        # 如果实际类别数与默认不符，只命名前 N 个
        classes = DEFAULT_CLASSES[:num_classes] if num_classes <= len(DEFAULT_CLASSES) else \
            DEFAULT_CLASSES + [f"class_{i}" for i in range(len(DEFAULT_CLASSES), num_classes)]
    lines = [
        f"# 青苗守护者 · SCB 课堂行为数据集配置（自动生成）",
        f"path: {DATA_DIR.resolve().as_posix()}",
        f"train: images/train",
        f"val: images/val",
        f"",
        f"names:",
    ]
    for i, n in enumerate(classes):
        lines.append(f"  {i}: {n}")
    yaml_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[OK] 配置写入 {yaml_path}")


def detect_num_classes(src_labels: Path, sample: int = 500) -> int:
    """抽样标签文件检测类别数。"""
    class_ids = set()
    files = list(src_labels.rglob("*.txt"))[:sample]
    for f in files:
        try:
            for line in f.read_text().splitlines():
                parts = line.strip().split()
                if parts:
                    try:
                        class_ids.add(int(parts[0]))
                    except ValueError:
                        pass
        except Exception:
            continue
    return max(class_ids) + 1 if class_ids else len(DEFAULT_CLASSES)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--val-ratio", type=float, default=0.1)
    args = parser.parse_args()

    print("=" * 60)
    print("青苗守护者 · SCB 数据集准备")
    print("=" * 60)

    repo_dir = clone_if_needed()
    img_dir, lbl_dir = find_yolo_data(repo_dir)
    num_classes = detect_num_classes(lbl_dir)
    print(f"[INFO] 检测到类别数：{num_classes}")

    train_n, val_n = split_dataset(img_dir, lbl_dir, val_ratio=args.val_ratio)
    write_yaml(num_classes)

    print()
    print("=" * 60)
    print(f"✅ 数据集已准备完成：")
    print(f"   位置：{DATA_DIR}")
    print(f"   训练：{train_n} 张  验证：{val_n} 张")
    print(f"   类别数：{num_classes}")
    print()
    print("下一步：")
    print("   python scripts/train/train_yolov8_behavior.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
