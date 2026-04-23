"""产品咨询与 FAQ 相关的 Agent 工具。"""

import json

from langchain_core.tools import tool

from data.database import (
    search_products_by_keyword,
    get_products_by_budget,
    search_faq_by_keyword,
)


@tool
def search_product(keyword: str) -> str:
    """搜索产品信息

    Args:
        keyword: 产品关键词

    Returns:
        匹配产品的信息
    """
    products = search_products_by_keyword(keyword)
    if products:
        results = [
            {
                "name": p["name"],
                "price": f"¥{p['price']}",
                "features": p["features"],
                "rating": f"{p['rating']}分",
            }
            for p in products
        ]
        return json.dumps(results, ensure_ascii=False, indent=2)
    return f"未找到包含 '{keyword}' 的产品"


@tool
def get_product_recommendations(budget: int, category: str = "全部") -> str:
    """根据预算推荐产品

    Args:
        budget: 预算金额（单位：元）
        category: 产品类别（可选）

    Returns:
        推荐产品列表（JSON，最多 3 个，按评分排序）
    """
    products = get_products_by_budget(budget, limit=3)
    if products:
        recommendations = [
            {
                "name": p["name"],
                "price": f"¥{p['price']}",
                "rating": p["rating"],
            }
            for p in products
        ]
        return json.dumps(recommendations, ensure_ascii=False, indent=2)
    return f"在预算 ¥{budget} 内暂无推荐产品"


@tool
def search_faq(problem_type: str) -> str:
    """搜索常见问题解答

    Args:
        problem_type: 问题类型关键词（如 "连接"、"充电"、"退货"）

    Returns:
        相关 FAQ 答案
    """
    result = search_faq_by_keyword(problem_type)
    if result:
        return f"【{result['keyword']}】\n{result['answer']}"
    return "未找到相关FAQ，建议联系人工客服获取更多帮助。"
