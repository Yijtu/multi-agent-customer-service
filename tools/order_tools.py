"""订单相关的 Agent 工具。

这些函数会被 LangChain Agent 作为"可调用工具"使用。
每个工具的 docstring 会作为"工具说明"交给 LLM，
LLM 据此决定何时调用、传什么参数。
"""

import json

from langchain_core.tools import tool

from data.mock_data import MOCK_ORDERS


@tool
def query_order(order_id: str) -> str:
    """查询订单信息

    Args:
        order_id: 订单号，格式如 ORD001

    Returns:
        订单详情的 JSON 字符串
    """
    order = MOCK_ORDERS.get(order_id.upper())
    if order:
        return json.dumps(order, ensure_ascii=False, indent=2)
    return f"未找到订单 {order_id}"


@tool
def track_shipping(tracking_number: str) -> str:
    """查询物流信息

    Args:
        tracking_number: 物流单号

    Returns:
        物流状态信息
    """
    if tracking_number.startswith("SF"):
        return f"顺丰快递 {tracking_number}: 包裹已到达配送站，预计今日送达"
    elif tracking_number.startswith("YT"):
        return f"圆通快递 {tracking_number}: 已签收"
    return f"未找到物流信息 {tracking_number}"
