"""产品咨询Agent。

负责：产品介绍、功能讲解、按预算推荐。
可用工具：search_product, get_product_recommendations
"""

from agents.base import BaseBusinessAgent
from tools.product_tools import search_product, get_product_recommendations
from tools.rag_tools import rag_search, rag_search_with_filter


class ProductConsultAgent(BaseBusinessAgent):
    """产品咨询Agent。"""

    tools = [search_product, get_product_recommendations, rag_search, rag_search_with_filter]

    system_prompt = """你是一个热情的产品顾问。你的职责是：
1. 介绍产品功能和特点
2. 使用 rag_search_with_filter 工具（category='product'）查找产品详细信息
3. 根据用户需求推荐合适的产品
4. 使用 search_product 和 get_product_recommendations 获取产品列表和价格
5. 如果用户问售后政策，用 rag_search_with_filter（category='policy'）检索

回复要求：
- 热情有亲和力
- 突出产品优势
- 基于知识库和工具返回的实际数据回答
- 不要过度推销
- 如果用户画像中有预算和偏好，主动调用推荐工具并据此筛选"""

    fallback_message = "抱歉，产品信息查询暂时不可用。请稍后再试。"
