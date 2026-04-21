"""回复质量检查代理。

对业务 Agent 生成的回复做评分，分数过低触发升级。
与业务 Agent 不同，本代理不使用工具，只用 LCEL 管道调 LLM。
"""

from typing import Any, Dict

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from config import model
from utils.json_parser import safe_parse_json


class QualityChecker:
    """客服回复质量检查器。"""

    def __init__(self):
        self.llm = model
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """你是客服质量检查专家。评估客服回复的质量。

评估维度：
1. 相关性（0-25分）：回复是否针对用户问题
2. 完整性（0-25分）：是否提供了足够的信息
3. 专业性（0-25分）：语言是否专业得体
4. 有用性（0-25分）：是否真正帮助到用户

返回格式（JSON）：
{{"total_score": 0-100, "needs_escalation": true/false, "reason": "评估说明"}}

只返回JSON。"""),
            ("human", """用户问题：{user_message}
客服回复：{agent_response}

请评估："""),
        ])

    def check(self, user_message: str, agent_response: str) -> Dict[str, Any]:
        """评估客服回复的质量。

        Args:
            user_message: 用户原始消息。
            agent_response: 业务 Agent 生成的回复。

        Returns:
            包含 total_score / needs_escalation / reason 的字典。
        """
        chain = self.prompt | self.llm | StrOutputParser()
        result = chain.invoke({
            "user_message": user_message,
            "agent_response": agent_response,
        })

        default_result = {
            "total_score": 60,
            "needs_escalation": False,
            "reason": "评估完成",
        }
        return safe_parse_json(result, default_result)
