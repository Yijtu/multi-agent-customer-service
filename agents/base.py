"""业务 Agent 的基类。

三个业务 Agent（tech / order / product）行为高度一致：
- 都用 create_agent 封装 LLM + tools
- 都需要把 user_profile 注入到 prompt
- 都提取 result['messages'][-1].content

把公共逻辑提取到基类，子类只需声明 tools / system_prompt / fallback。

支持 Hand-off：业务 Agent 回复中包含 [HANDOFF:agent_name] 标记时，
系统会将请求转发给目标 Agent。
"""

from typing import List, Optional, Tuple
import re

from langchain.agents import create_agent

from config import model, DEFAULT_LANGUAGE
from state import UserProfile


class BaseBusinessAgent:
    """业务 Agent 基类。子类必须设置 tools / system_prompt / fallback。"""

    tools: list = []
    system_prompt: str = ""
    fallback_message: str = "抱歉，服务暂时不可用。"

    # 合法的 handoff 目标
    VALID_HANDOFF_TARGETS = {"tech_support", "order_service", "product_consult"}

    def __init__(self):
        self.llm = model
        self.agent = create_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=self.system_prompt,
        )

    def handle(
        self,
        message: str,
        profile: Optional[UserProfile] = None,
        chat_history: Optional[List] = None,
    ) -> Tuple[str, str]:
        """处理用户消息，结合 profile 提供个性化回复。

        Returns:
            (response, handoff_target) 元组。
            handoff_target 为空串表示无 handoff。
        """
        enriched = self._enrich_message(message, profile)
        messages = [{"role": "user", "content": enriched}]
        result = self.agent.invoke({"messages": messages})

        if result["messages"]:
            response = result["messages"][-1].content
            # 检查是否包含 handoff 标记
            handoff_target = self._parse_handoff(response)
            if handoff_target:
                # 清除 handoff 标记，只保留正文
                response = re.sub(r"\[HANDOFF:\w+\]", "", response).strip()
            return response, handoff_target
        return self.fallback_message, ""

    @staticmethod
    def _enrich_message(message: str, profile: Optional[UserProfile]) -> str:
        """把 profile 摘要拼到用户消息前面。profile 为空时原样返回。"""
        if not profile:
            return message

        lines = []
        if profile.get("budget"):
            lines.append(f"- 预算: ¥{profile['budget']}")
        if profile.get("preferences"):
            lines.append(f"- 偏好: {', '.join(profile['preferences'])}")
        if profile.get("interested_products"):
            lines.append(f"- 感兴趣的产品: {', '.join(profile['interested_products'])}")
        if profile.get("mentioned_orders"):
            lines.append(f"- 提到过的订单: {', '.join(profile['mentioned_orders'])}")

        # 多语言指令
        lang = profile.get("language", DEFAULT_LANGUAGE)
        lang_name = _LANGUAGE_NAMES.get(lang, "")
        if lang_name and lang != DEFAULT_LANGUAGE:
            lines.append(f"- 语言偏好: {lang_name}")

        if not lines:
            return message

        profile_block = "【用户画像】\n" + "\n".join(lines)
        result = f"{profile_block}\n\n【当前问题】\n{message}"

        # 非默认语言时追加语言指令
        if lang_name and lang != DEFAULT_LANGUAGE:
            result += f"\n\n【重要】请用{lang_name}回复用户。"

        return result

    @classmethod
    def _parse_handoff(cls, response: str) -> str:
        """从 Agent 回复中解析 [HANDOFF:target] 标记。

        Returns:
            目标 agent 名称，无效或不存在时返回空串。
        """
        match = re.search(r"\[HANDOFF:(\w+)\]", response)
        if match:
            target = match.group(1)
            if target in cls.VALID_HANDOFF_TARGETS:
                return target
        return ""


# 语言代码 → 语言名称映射
_LANGUAGE_NAMES = {
    "zh": "中文",
    "en": "English",
    "ja": "日本語",
    "ko": "한국어",
}
