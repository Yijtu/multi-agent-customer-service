"""全局异常捕获中间件。

节点抛异常时记录日志并设置 fallback 回复，
避免单个节点的异常导致整个工作流崩溃。
"""

import logging
from typing import Dict, Set

from middleware.base import Middleware
from state import CustomerServiceState

logger = logging.getLogger("customer_service")

# 关键节点列表：这些节点出错时走 fallback 回复而非直接 raise
_RECOVERABLE_NODES: Set[str] = {
    "tech_support",
    "order_service",
    "product_consult",
    "quality_check",
    "extract_profile",
}

_FALLBACK_RESPONSE = "非常抱歉，系统处理出现异常。已为您转接人工客服，请稍候..."


class ErrorHandlerMiddleware(Middleware):
    """异常捕获中间件。

    对于可恢复节点，在 on_error 中设置 fallback 回复和升级标志，
    MiddlewareChain 外层仍然会 raise，但 LangGraph 节点函数
    可以在自身 try/except 中利用本中间件设置的 state 值做兜底。
    """

    def before_node(self, node_name: str, state: CustomerServiceState) -> None:
        pass  # 无需前置处理

    def after_node(
        self,
        node_name: str,
        state: CustomerServiceState,
        result: CustomerServiceState,
    ) -> None:
        pass  # 无需后置处理

    def on_error(
        self,
        node_name: str,
        state: CustomerServiceState,
        error: Exception,
    ) -> None:
        logger.error(
            "[ErrorHandler] 节点 %s 异常: %s: %s",
            node_name,
            type(error).__name__,
            error,
        )

        if node_name in _RECOVERABLE_NODES:
            # 设置 fallback 状态，让后续节点可以继续
            state["agent_response"] = _FALLBACK_RESPONSE
            state["needs_escalation"] = True
            state["escalation_reason"] = f"节点 {node_name} 异常: {error}"
            logger.warning("[ErrorHandler] 已设置 fallback 回复，标记升级")
