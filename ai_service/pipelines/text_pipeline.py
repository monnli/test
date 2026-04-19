"""文本分析流水线（通义千问）。

功能：
- 情绪极性分析（正面 / 中性 / 负面）+ 情绪标签
- 风险关键词识别（自伤、自杀、抑郁、孤独、暴力等敏感词）
- 心理状态归纳（一段话总结学生心理状态）
- AI 心理对话（带专业提示词的辅导员人设）

特点：
- 不需要本地模型，requires_model = False
- DASHSCOPE_API_KEY 未配置时降级为本地规则版 mock
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from typing import Any

from loguru import logger

from .base import BasePipeline, PipelineStatus

# 高风险关键词词典（仅供 mock 与兜底，实际由 LLM 判定为准）
RISK_KEYWORDS = {
    "high": [
        "自杀", "自残", "想死", "去死", "不想活", "结束生命", "活不下去", "解脱", "跳楼",
        "割腕", "上吊", "轻生",
    ],
    "medium": [
        "抑郁", "压抑", "绝望", "无意义", "没人爱", "没有人爱", "孤独", "崩溃",
        "想消失", "讨厌自己", "没有朋友", "没有意义", "没意思",
    ],
    "low": [
        "难过", "烦躁", "焦虑", "压力大", "失眠", "哭", "委屈", "不开心", "心累", "无聊",
    ],
}

PSY_SYSTEM_PROMPT = """你是「青苗守护者」平台的 AI 心理辅导员「知心」，专为中小学生服务。
请遵循以下原则：
1. 始终温和、耐心、共情，不评判、不说教，使用学生能理解的语言。
2. 你不是医生，不能做诊断，遇到自伤/自杀想法应温柔提醒「告诉信任的老师/拨打 12320」并立即标记高风险。
3. 鼓励学生表达情绪，引导积极思考，但不强行灌输价值观。
4. 涉及隐私敏感话题（家暴、性、霸凌等），表达关心，提示寻求专业帮助。
5. 回复控制在 80~200 字，先共情后引导。
"""


class TextPipeline(BasePipeline):
    name = "text"
    requires_model = False  # 不需要本地模型

    def __init__(self):
        super().__init__()
        self.api_key: str | None = None
        self.model_name: str = os.getenv("QWEN_MODEL", "qwen-plus")

    def _load(self) -> None:
        api_key = os.getenv("DASHSCOPE_API_KEY", "").strip()
        if not api_key or api_key.startswith("sk-your"):
            raise RuntimeError("DASHSCOPE_API_KEY 未配置")
        try:
            import dashscope  # type: ignore

            dashscope.api_key = api_key
            self.api_key = api_key
            self._model = dashscope
        except ImportError as exc:
            raise RuntimeError(f"dashscope SDK 未安装：{exc}") from exc

    # ---------- 对外能力 ----------
    def analyze_sentiment(self, text: str) -> dict[str, Any]:
        """情绪极性 + 风险等级分析。"""
        return self.run(text, mode="sentiment")

    def chat(self, messages: list[dict[str, str]], system: str | None = None) -> dict[str, Any]:
        """多轮对话。messages: [{role, content}]。"""
        return self.run(messages=messages, mode="chat", system=system)

    def summarize_psychology(self, text: str) -> dict[str, Any]:
        """归纳一段文本的心理状态。"""
        return self.run(text, mode="summarize")

    # ---------- 真实 / mock 实现 ----------
    def _infer(self, *args, **kwargs) -> dict[str, Any]:
        mode = kwargs.get("mode", "sentiment")
        if mode == "chat":
            return self._chat_real(kwargs.get("messages", []), kwargs.get("system"))
        if mode == "summarize":
            return self._summarize_real(args[0] if args else kwargs.get("text", ""))
        return self._sentiment_real(args[0] if args else kwargs.get("text", ""))

    def _mock(self, *args, **kwargs) -> dict[str, Any]:
        mode = kwargs.get("mode", "sentiment")
        if mode == "chat":
            return self._chat_mock(kwargs.get("messages", []))
        if mode == "summarize":
            return self._summarize_mock(args[0] if args else kwargs.get("text", ""))
        return self._sentiment_mock(args[0] if args else kwargs.get("text", ""))

    # ---------- 情绪分析：真实 ----------
    def _sentiment_real(self, text: str) -> dict[str, Any]:
        prompt = (
            "请你作为一名青少年心理学专家，分析下面这段学生文本的情绪。\n"
            "严格用 JSON 格式输出，字段：\n"
            "  polarity：正面/中性/负面 之一\n"
            "  emotion_tags：情绪标签列表（如 高兴/孤独/焦虑/愤怒 等，最多 4 个）\n"
            "  risk_level：none/low/medium/high 之一\n"
            "  risk_keywords：检测到的风险词列表（无则空数组）\n"
            "  reason：判断依据（一句话）\n\n"
            f"学生文本：\n{text}\n"
        )
        result = self._call_qwen(
            messages=[{"role": "user", "content": prompt}],
            response_format="json",
        )
        return _parse_json_or_default(result, _default_sentiment(text))

    def _summarize_real(self, text: str) -> dict[str, Any]:
        prompt = (
            "请你作为青少年心理咨询师，对下面学生写的一段文字进行心理状态归纳。\n"
            "严格 JSON 输出：\n"
            "  summary：一段 100 字以内的心理状态描述\n"
            "  highlights：值得关注的句子列表（最多 3 句）\n"
            "  suggestion：给班主任/心理老师的简短建议\n\n"
            f"学生文本：\n{text}\n"
        )
        result = self._call_qwen(
            messages=[{"role": "user", "content": prompt}],
            response_format="json",
        )
        return _parse_json_or_default(result, _default_summary(text))

    def _chat_real(self, messages: list[dict[str, str]], system: str | None) -> dict[str, Any]:
        full_messages = [{"role": "system", "content": system or PSY_SYSTEM_PROMPT}]
        full_messages.extend(messages)
        result = self._call_qwen(messages=full_messages)
        # 顺便做风险分析
        last_user = next(
            (m["content"] for m in reversed(messages) if m.get("role") == "user"),
            "",
        )
        risk = self._detect_risk_keywords(last_user)
        return {
            "reply": result,
            "risk_level": risk["risk_level"],
            "risk_keywords": risk["risk_keywords"],
        }

    def _call_qwen(
        self,
        messages: list[dict[str, str]],
        response_format: str | None = None,
    ) -> str:
        import dashscope  # type: ignore
        from dashscope.api_entities.dashscope_response import GenerationResponse  # type: ignore

        kwargs: dict[str, Any] = {
            "model": self.model_name,
            "messages": messages,
            "result_format": "message",
        }
        resp: GenerationResponse = dashscope.Generation.call(**kwargs)
        if resp.status_code != 200:
            raise RuntimeError(f"通义千问调用失败 {resp.status_code}: {resp.message}")
        return resp.output["choices"][0]["message"]["content"]

    # ---------- 情绪分析：mock ----------
    def _sentiment_mock(self, text: str) -> dict[str, Any]:
        return _default_sentiment(text, mock=True)

    def _summarize_mock(self, text: str) -> dict[str, Any]:
        return _default_summary(text, mock=True)

    def _chat_mock(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        last_user = next(
            (m["content"] for m in reversed(messages) if m.get("role") == "user"),
            "",
        )
        risk = self._detect_risk_keywords(last_user)
        templates = [
            "我能感受到你最近承受了不少压力，谢谢你愿意告诉我。能再多说说让你最难受的那件事吗？",
            "听起来这真的不容易。你愿意试着把心情用一两个词描述一下吗？比如「闷闷的」「乱乱的」？",
            "你说出来本身就是很勇敢的事。我们可以一起想想，有没有一件小小的、做了能让自己舒服一点的事？",
            "我在听，请慢慢说。今天发生的事里，有没有一个让你略微开心的小瞬间？",
        ]
        seed = int(hashlib.md5((last_user or "x").encode()).hexdigest()[:8], 16)
        reply = templates[seed % len(templates)]
        if risk["risk_level"] in ("high", "medium"):
            reply = (
                "我注意到你说的这些话，我非常担心你。请你一定告诉信任的老师或家人，"
                "也可以拨打 12320 心理援助热线。我会一直在这里陪你。"
            )
        return {
            "reply": reply,
            "risk_level": risk["risk_level"],
            "risk_keywords": risk["risk_keywords"],
            "_mock": True,
        }

    # ---------- 风险词检测（兜底）----------
    @staticmethod
    def _detect_risk_keywords(text: str) -> dict[str, Any]:
        if not text:
            return {"risk_level": "none", "risk_keywords": []}
        hits_high = [k for k in RISK_KEYWORDS["high"] if k in text]
        hits_med = [k for k in RISK_KEYWORDS["medium"] if k in text]
        hits_low = [k for k in RISK_KEYWORDS["low"] if k in text]
        if hits_high:
            level = "high"
        elif hits_med:
            level = "medium"
        elif hits_low:
            level = "low"
        else:
            level = "none"
        return {"risk_level": level, "risk_keywords": hits_high + hits_med + hits_low}


# ---------- 工具函数 ----------
def _default_sentiment(text: str, mock: bool = False) -> dict[str, Any]:
    risk = TextPipeline._detect_risk_keywords(text)
    polarity = "负面" if risk["risk_level"] in ("high", "medium") else (
        "中性" if risk["risk_level"] == "low" else "正面"
    )
    tags: list[str] = []
    if "开心" in text or "快乐" in text or "高兴" in text:
        tags.append("高兴")
    if "难过" in text or "伤心" in text:
        tags.append("难过")
    if "焦虑" in text or "紧张" in text or "压力" in text:
        tags.append("焦虑")
    if "孤独" in text or "没人" in text:
        tags.append("孤独")
    return {
        "polarity": polarity,
        "emotion_tags": tags or (["平和"] if polarity == "正面" else []),
        "risk_level": risk["risk_level"],
        "risk_keywords": risk["risk_keywords"],
        "reason": "基于关键词与情绪词匹配的本地分析（mock）" if mock else "本地规则兜底",
        "_mock": mock,
    }


def _default_summary(text: str, mock: bool = False) -> dict[str, Any]:
    sentences = re.split(r"[。！？\n]", text)
    sentences = [s.strip() for s in sentences if s.strip()]
    return {
        "summary": (text[:80] + "...") if len(text) > 80 else text or "（无文本）",
        "highlights": sentences[:3],
        "suggestion": "建议班主任与该学生进行 1 对 1 沟通，了解近期情绪变化。",
        "_mock": mock,
    }


def _parse_json_or_default(raw: str, default: dict[str, Any]) -> dict[str, Any]:
    if not raw:
        return default
    # 尝试从 ```json ``` 块或裸 JSON 中解析
    json_match = re.search(r"\{[\s\S]*\}", raw)
    if json_match:
        try:
            data = json.loads(json_match.group(0))
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass
    return default


text_pipeline = TextPipeline()
