"""意图分类代理。

根据用户消息判断应该路由到哪个业务代理：
- tech_support: 技术问题
- order_service: 订单相关
- product_consult: 产品咨询
- escalate: 投诉或无法识别，需要人工介入
"""

from typing import Any, Dict

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from config import model
from utils.json_parser import safe_parse_json


class IntentClassifier:
    """基于 LLM 的意图分类器。"""

    def __init__(self):
        self.llm = model
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个意图分类专家。分析用户消息并返回意图分类。

可选意图：
- tech_support: 技术问题、故障排除、使用帮助
- order_service: 订单查询、物流跟踪、退换货
- product_consult: 产品咨询、价格询问、功能介绍
- escalate: 投诉、无法理解、需要人工

返回格式（JSON）：
{{"intent": "意图类型", "confidence": 0.0-1.0, "reason": "分类原因"}}

只返回JSON，不要其他内容。"""),
            ("human", "{message}"),
        ])

    def classify(self, message: str) -> Dict[str, Any]:
        """分类用户意图。

        Args:
            message: 用户消息。

        Returns:
            包含 intent / confidence / reason 的字典。
            LLM 解析失败时返回 escalate 兜底。
        """
        chain = self.prompt | self.llm | StrOutputParser()
        result = chain.invoke({"message": message})

        default_result = {
            "intent": "escalate",
            "confidence": 0.5,
            "reason": "解析失败",
        }
        parsed = safe_parse_json(result, default_result)

        if "intent" not in parsed:
            return default_result
        return parsed
