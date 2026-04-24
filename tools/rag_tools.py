"""RAG 检索工具。

封装为 LangChain @tool，可被业务 Agent 直接调用。
支持全库检索和按类别（product/tech/policy）过滤检索。
"""

from langchain_core.tools import tool

from rag.vector_store import similarity_search


@tool
def rag_search(query: str) -> str:
    """从产品知识库中语义检索相关信息。

    适用于需要查找产品详情、技术问题解决方案、售后政策等场景。
    返回最相关的知识片段。

    Args:
        query: 用户的问题或搜索关键词

    Returns:
        检索到的相关知识内容
    """
    docs = similarity_search(query, top_k=3)
    if not docs:
        return "知识库中未找到相关信息。"

    results = []
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source", "未知")
        category = doc.metadata.get("category", "未知")
        results.append(
            f"【{i}】[来源: {source} | 类别: {category}]\n{doc.page_content}"
        )

    return "\n\n---\n\n".join(results)


@tool
def rag_search_with_filter(query: str, category: str) -> str:
    """从指定类别的知识库中语义检索相关信息。

    可按类别过滤，缩小检索范围，提高相关性：
    - product: 产品介绍、功能、规格、价格
    - tech: 技术问题、故障排除、使用帮助
    - policy: 售后政策、退换货、保修、会员权益

    Args:
        query: 用户的问题或搜索关键词
        category: 文档类别（product/tech/policy）

    Returns:
        检索到的相关知识内容
    """
    valid_categories = {"product", "tech", "policy"}
    filter_dict = None
    if category in valid_categories:
        filter_dict = {"category": category}

    docs = similarity_search(query, top_k=3, filter_dict=filter_dict)
    if not docs:
        return f"在 {category} 类别中未找到与 '{query}' 相关的信息。"

    results = []
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source", "未知")
        results.append(f"【{i}】[来源: {source}]\n{doc.page_content}")

    return "\n\n---\n\n".join(results)
