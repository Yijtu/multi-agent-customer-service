"""订单服务代理。

负责：订单查询、物流跟踪、退换货咨询。
可用工具：query_order, track_shipping
"""

from agents.base import BaseBusinessAgent
from tools.order_tools import query_order, track_shipping


class OrderServiceAgent(BaseBusinessAgent):
    """订单服务代理。"""

    tools = [query_order, track_shipping]

    system_prompt = """你是一个专业的订单服务专员。你的职责是：
1. 帮助用户查询订单状态
2. 提供物流跟踪信息
3. 解答退换货相关问题
4. 使用工具获取准确信息

回复要求：
- 信息准确完整
- 主动提供相关信息
- 如果需要订单号，礼貌询问
- 如果用户画像中有已提过的订单号，优先使用，不要重复询问"""

    fallback_message = "抱歉，订单查询服务暂时不可用。请稍后再试。"
