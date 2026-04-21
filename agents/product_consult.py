"""产品咨询代理。

负责：产品介绍、功能讲解、按预算推荐。
可用工具：search_product, get_product_recommendations
"""

from agents.base import BaseBusinessAgent
from tools.product_tools import search_product, get_product_recommendations


class ProductConsultAgent(BaseBusinessAgent):
    """产品咨询代理。"""

    tools = [search_product, get_product_recommendations]

    system_prompt = """你是一个热情的产品顾问。你的职责是：
1. 介绍产品功能和特点
2. 根据用户需求推荐合适的产品
3. 解答价格和库存问题
4. 使用工具获取最新产品信息

回复要求：
- 热情有亲和力
- 突出产品优势
- 根据用户需求推荐
- 不要过度推销
- 如果用户画像中有预算和偏好，主动调用推荐工具并据此筛选"""

    fallback_message = "抱歉，产品信息查询暂时不可用。请稍后再试。"
