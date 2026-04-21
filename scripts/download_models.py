"""AI 模型权重下载脚本。

用法：
    python scripts/download_models.py [--only face|emotion|behavior]

说明：
- 未安装相应 Python 包时会提示 pip 安装命令，不报错退出
- 已存在的权重会跳过
- 默认存放在 ai_service/models/ 下
- 不装也不影响系统运行（AI 流水线会自动降级为 mock 模式）
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_DIR = PROJECT_ROOT / "ai_service" / "models"


def download_yolov8():
    target = MODEL_DIR / "yolov8n.pt"
    if target.exists():
        print(f"[SKIP] YOLOv8 已存在：{target}")
        return
    print("[..] 下载 YOLOv8n（约 6 MB）...")
    try:
        from ultralytics import YOLO  # type: ignore

        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        model = YOLO("yolov8n.pt")  # 触发下载
        # ultralytics 下载到缓存，复制一份到 MODEL_DIR
        src = Path(model.ckpt_path) if hasattr(model, "ckpt_path") and model.ckpt_path else None
        if src and src.exists():
            import shutil

            shutil.copy(src, target)
            print(f"[OK] YOLOv8n 已就绪：{target}")
        else:
            print("[OK] YOLOv8n 已通过 ultralytics 缓存（推理时会自动使用）")
    except ImportError:
        print("[MISS] ultralytics 未安装，请执行：pip install ultralytics")
    except Exception as exc:  # noqa: BLE001
        print(f"[ERR] YOLOv8 下载失败：{exc}")


def download_insightface():
    target_dir = MODEL_DIR / "insightface"
    if (target_dir / "models" / "buffalo_l").exists() or list((target_dir / "models").glob("buffalo_l*")) if (target_dir / "models").exists() else False:
        print(f"[SKIP] InsightFace buffalo_l 已存在：{target_dir}")
        return
    print("[..] 下载 InsightFace buffalo_l（约 250 MB，首次较慢）...")
    try:
        from insightface.app import FaceAnalysis  # type: ignore

        target_dir.mkdir(parents=True, exist_ok=True)
        app = FaceAnalysis(name="buffalo_l", root=str(target_dir))
        app.prepare(ctx_id=-1, det_size=(640, 640))
        print(f"[OK] InsightFace 已就绪：{target_dir}")
    except ImportError:
        print("[MISS] insightface 未安装，请执行：pip install insightface onnxruntime")
    except Exception as exc:  # noqa: BLE001
        print(f"[ERR] InsightFace 下载失败：{exc}")


def download_hsemotion():
    print("[..] HSEmotion 模型会在首次调用时自动从 torch hub 下载")
    try:
        from hsemotion.facial_emotions import HSEmotionRecognizer  # type: ignore

        _ = HSEmotionRecognizer(model_name="enet_b0_8_best_afew", device="cpu")
        print("[OK] HSEmotion 已就绪")
    except ImportError:
        print("[MISS] hsemotion 未安装，请执行：pip install hsemotion timm")
    except Exception as exc:  # noqa: BLE001
        print(f"[ERR] HSEmotion 下载失败：{exc}")


def check_mediapipe():
    try:
        import mediapipe as mp  # type: ignore

        _ = mp.solutions.pose.Pose()
        _ = mp.solutions.face_mesh.FaceMesh()
        print("[OK] MediaPipe Pose + FaceMesh 已就绪")
    except ImportError:
        print("[MISS] mediapipe 未安装，请执行：pip install mediapipe")
    except Exception as exc:  # noqa: BLE001
        print(f"[ERR] MediaPipe 初始化失败：{exc}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", choices=["face", "emotion", "behavior", "pose"], help="只下载指定模型")
    args = parser.parse_args()

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    print(f"模型目录：{MODEL_DIR}")
    print("-" * 60)

    if args.only in (None, "behavior"):
        download_yolov8()
    if args.only in (None, "face"):
        download_insightface()
    if args.only in (None, "emotion"):
        download_hsemotion()
    if args.only in (None, "pose"):
        check_mediapipe()

    print("-" * 60)
    print("提示：")
    print("  - 未安装的模型包在 AI 流水线首次调用时会自动降级为 mock 模式")
    print("  - 系统在 mock 模式下依然可以演示完整链路")
    print("  - 正式演示前建议运行此脚本，让所有模型就绪")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
