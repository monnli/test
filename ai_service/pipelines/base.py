"""AI 流水线基类。

所有流水线遵循以下约定：
1. 延迟加载模型（首次调用才 load，不拖累启动速度）
2. 加载失败时自动降级为 mock 模式（返回模拟结果）
3. 统一错误处理与日志
4. 提供 status() 查看加载状态

mock 模式的价值：
- 任何机器都能跑通完整链路（无 GPU、无模型权重也能开发前后端）
- 单元测试不依赖真实模型权重
- 演示机容灾：模型加载失败自动降级，不会整个系统崩溃
"""

from __future__ import annotations

import os
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from loguru import logger

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
AI_MODEL_DIR = Path(os.getenv("AI_MODEL_DIR", PROJECT_ROOT / "ai_service" / "models"))
AI_DEVICE = os.getenv("AI_DEVICE", "cuda").lower()

# 全局强制 Mock 开关：设为 true/1/yes 时，所有流水线无条件走 mock，
# 完全跳过模型加载（启动快、零翻车、结果稳定）
FORCE_MOCK = os.getenv("FORCE_MOCK", "true").lower() in ("1", "true", "yes", "on")


class PipelineStatus:
    NOT_LOADED = "not_loaded"       # 尚未尝试加载
    LOADING = "loading"              # 正在加载
    READY = "ready"                  # 加载成功，使用真实模型
    MOCK = "mock"                    # 加载失败，使用 mock 模式
    ERROR = "error"                  # 运行时出错


class BasePipeline(ABC):
    """所有 AI 流水线的基类。"""

    name: str = "base"
    requires_model: bool = True       # 是否需要本地模型（False 表示只调 API，如文本流水线）

    def __init__(self):
        self.status: str = PipelineStatus.NOT_LOADED
        self.error_detail: str | None = None
        self.loaded_at: float | None = None
        self.device: str = AI_DEVICE
        self._model: Any = None

    # ---------- 生命周期 ----------
    def ensure_loaded(self) -> None:
        """确保模型已加载（幂等）。

        若 FORCE_MOCK=true（默认）直接进入 mock 模式，完全跳过真实模型加载。
        """
        if self.status in (PipelineStatus.READY, PipelineStatus.MOCK):
            return

        if FORCE_MOCK:
            self.status = PipelineStatus.MOCK
            self.error_detail = "FORCE_MOCK=true，全局 Mock 模式"
            logger.info(f"[{self.name}] 已启用全局 Mock 模式（FORCE_MOCK=true）")
            return

        self.status = PipelineStatus.LOADING
        logger.info(f"[{self.name}] 开始加载模型 (device={self.device})")
        start = time.time()
        try:
            self._load()
            self.status = PipelineStatus.READY
            self.loaded_at = time.time()
            logger.success(f"[{self.name}] 模型加载完成，耗时 {time.time() - start:.2f}s")
        except Exception as exc:  # noqa: BLE001
            self.error_detail = str(exc)
            self.status = PipelineStatus.MOCK
            logger.warning(
                f"[{self.name}] 模型加载失败，降级为 mock 模式：{exc}"
            )

    @abstractmethod
    def _load(self) -> None:
        """由子类实现，加载真实模型。失败时抛出异常即可，基类自动降级。"""

    # ---------- 推理 ----------
    def run(self, *args, **kwargs) -> Any:
        """对外统一入口。"""
        self.ensure_loaded()
        try:
            if self.status == PipelineStatus.READY:
                return self._infer(*args, **kwargs)
            return self._mock(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001
            logger.exception(f"[{self.name}] 推理异常，返回 mock 结果")
            self.status = PipelineStatus.ERROR
            self.error_detail = str(exc)
            return self._mock(*args, **kwargs)

    @abstractmethod
    def _infer(self, *args, **kwargs) -> Any:
        """真实推理。子类实现。"""

    @abstractmethod
    def _mock(self, *args, **kwargs) -> Any:
        """mock 降级。子类实现。"""

    # ---------- 状态 ----------
    def status_info(self) -> dict:
        return {
            "name": self.name,
            "status": self.status,
            "device": self.device,
            "error": self.error_detail,
            "loaded_at": self.loaded_at,
            "requires_model": self.requires_model,
        }
