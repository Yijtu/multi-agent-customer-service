"""产品咨询与 FAQ 相关的 Agent 工具。"""

import json

from langchain_core.tools import tool

from data.mock_data import MOCK_PRODUCTS, FAQ_DATABASE


@tool
def search_product(keyword: str) -> str:
    """搜索产品信息

    Args:
        keyword: 产品关键词

    Returns:
        匹配产品的信息
    """
    results = []
    for name, info in MOCK_PRODUCTS.items():
        if keyword.lower() in name.lower():
            results.append({
                "name": name,
                "price": f"¥{info['price']}",
                "features": info["features"],
                "rating": f"{info['rating']}分",
            })

    if results:
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
    recommendations = []
    for name, info in MOCK_PRODUCTS.items():
        if info["price"] <= budget:
            recommendations.append({
                "name": name,
                "price": f"¥{info['price']}",
                "rating": info["rating"],
            })

    recommendations.sort(key=lambda x: float(x["rating"]), reverse=True)

    if recommendations:
        return json.dumps(recommendations[:3], ensure_ascii=False, indent=2)
    return f"在预算 ¥{budget} 内暂无推荐产品"


@tool
def search_faq(problem_type: str) -> str:
    """搜索常见问题解答

    Args:
        problem_type: 问题类型关键词（如 "连接"、"充电"、"退货"）

    Returns:
        相关 FAQ 答案
    """
    for key, answer in FAQ_DATABASE.items():
        if problem_type in key or key in problem_type:
            return f"【{key}】\n{answer}"
    return "未找到相关FAQ，建议联系人工客服获取更多帮助。"
