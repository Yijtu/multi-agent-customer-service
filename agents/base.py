"""业务 Agent 的基类。

三个业务 Agent（tech / order / product）行为高度一致：
- 都用 create_agent 封装 LLM + tools
- 都需要把 user_profile 注入到 prompt
- 都提取 result['messages'][-1].content

把公共逻辑提取到基类，子类只需声明 tools / system_prompt / fallback。
"""

from typing import List, Optional

from langchain.agents import create_agent

from config import model
from state import UserProfile


class BaseBusinessAgent:
    """业务 Agent 基类。子类必须设置 tools / system_prompt / fallback。"""

    tools: list = []
    system_prompt: str = ""
    fallback_message: str = "抱歉，服务暂时不可用。"

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
    ) -> str:
        """处理用户消息，结合 profile 提供个性化回复。"""
        enriched = self._enrich_message(message, profile)
        messages = [{"role": "user", "content": enriched}]
        result = self.agent.invoke({"messages": messages})

        if result["messages"]:
            return result["messages"][-1].content
        return self.fallback_message

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

        if not lines:
            return message

        profile_block = "【用户画像】\n" + "\n".join(lines)
        return f"{profile_block}\n\n【当前问题】\n{message}"
