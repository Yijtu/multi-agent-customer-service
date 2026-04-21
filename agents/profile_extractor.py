"""用户画像提取代理。

从用户当前消息中提取画像信息（预算、偏好、订单号等），
并与已有 profile 合并，支持跨轮次累积。
"""

from typing import List

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from config import model
from state import UserProfile
from utils.json_parser import safe_parse_json


class ProfileExtractor:
    """用户画像提取器。"""

    def __init__(self):
        self.llm = model
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """你是用户画像分析专家。从用户消息中提取以下信息：

- budget: 预算金额（整数，单位元），如 "预算1500" → 1500
- preferences: 偏好关键词列表，如 "喜欢降噪" → ["降噪"]
- mentioned_orders: 订单号列表，如 "我的订单 ORD001" → ["ORD001"]
- interested_products: 感兴趣的产品列表，如 "想买智能手表" → ["智能手表"]
- language: 用户使用的语言代码，如 "zh"、"en"

返回格式（JSON）：
{{"budget": 数字或null, "preferences": [...], "mentioned_orders": [...], "interested_products": [...], "language": "代码"}}

规则：
- 如果消息中没有某个字段的信息，对应值设为 null 或空列表
- 只提取消息中**明确提到**的信息，不要猜测
- 只返回JSON，不要其他内容。"""),
            ("human", "{message}"),
        ])

    def extract(self, message: str, current_profile: UserProfile) -> UserProfile:
        """提取并合并用户画像。

        Args:
            message: 当前用户消息。
            current_profile: 已有的用户画像（可能为空字典）。

        Returns:
            合并后的新画像。
        """
        chain = self.prompt | self.llm | StrOutputParser()
        result = chain.invoke({"message": message})

        extracted = safe_parse_json(result, default={})
        return self._merge(current_profile, extracted)

    @staticmethod
    def _merge(old: UserProfile, new: dict) -> UserProfile:
        """合并新旧画像。

        - 标量字段（budget / language）：新值非空则覆盖
        - 列表字段（preferences / mentioned_orders / interested_products）：追加去重
        """
        merged: UserProfile = dict(old)  # 复制，避免修改原 dict

        # 标量字段：非 null 才覆盖
        for key in ("budget", "language"):
            value = new.get(key)
            if value is not None and value != "":
                merged[key] = value

        # 列表字段：追加去重
        for key in ("preferences", "mentioned_orders", "interested_products"):
            new_items = new.get(key) or []
            if not new_items:
                continue
            old_items = merged.get(key) or []
            merged[key] = _dedup_preserve_order(old_items + new_items)

        return merged


def _dedup_preserve_order(items: List[str]) -> List[str]:
    """保序去重：保留首次出现的顺序。"""
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result
