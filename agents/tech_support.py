"""技术支持代理。

负责：故障排除、使用帮助、FAQ 查询。
可用工具：search_faq
"""

from agents.base import BaseBusinessAgent
from tools.product_tools import search_faq


class TechSupportAgent(BaseBusinessAgent):
    """技术支持代理。"""

    tools = [search_faq]

    system_prompt = """你是一个专业的技术支持工程师。你的职责是：
1. 分析用户遇到的技术问题
2. 提供清晰的故障排除步骤
3. 使用 search_faq 工具查找相关解决方案
4. 如果问题超出能力范围，建议升级到人工支持

回复要求：
- 语气友好专业
- 步骤清晰有序
- 提供多个可能的解决方案
- 如果用户画像中有相关信息，可以参考它做更个性化的回复"""

    fallback_message = "抱歉，我暂时无法处理您的问题。建议联系人工客服。"
