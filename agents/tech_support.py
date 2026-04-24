"""技术支持Agent。

负责：故障排除、使用帮助、FAQ 查询。
可用工具：search_faq
"""

from agents.base import BaseBusinessAgent
from tools.product_tools import search_faq
from tools.rag_tools import rag_search, rag_search_with_filter


class TechSupportAgent(BaseBusinessAgent):
    """技术支持Agent。"""

    tools = [search_faq, rag_search, rag_search_with_filter]

    system_prompt = """你是一个专业的技术支持工程师。你的职责是：
1. 分析用户遇到的技术问题
2. 优先使用 rag_search_with_filter 工具（category='tech'）从知识库检索解决方案
3. 如果 RAG 检索无结果，再使用 search_faq 工具查找
4. 如果问题超出能力范围，建议升级到人工支持

回复要求：
- 语气友好专业
- 步骤清晰有序
- 提供多个可能的解决方案
- 基于知识库检索结果回答，不要编造信息
- 如果用户画像中有相关信息，可以参考它做更个性化的回复"""

    fallback_message = "抱歉，我暂时无法处理您的问题。建议联系人工客服。"
