"""中间件基础设施。

定义 Middleware 抽象基类和 MiddlewareChain 编排器。
MiddlewareChain.wrap() 可将任意 LangGraph 节点函数包裹上
before / after / on_error 三阶段钩子，实现横切关注点的解耦注入。
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List

from state import CustomerServiceState


class Middleware(ABC):
    """中间件抽象基类。

    子类需实现三个钩子：
    - before_node: 节点执行前调用
    - after_node: 节点执行后调用
    - on_error: 节点抛异常时调用
    """

    @abstractmethod
    def before_node(self, node_name: str, state: CustomerServiceState) -> None:
        """节点执行前钩子。"""

    @abstractmethod
    def after_node(
        self,
        node_name: str,
        state: CustomerServiceState,
        result: CustomerServiceState,
    ) -> None:
        """节点执行后钩子。"""

    @abstractmethod
    def on_error(
        self,
        node_name: str,
        state: CustomerServiceState,
        error: Exception,
    ) -> None:
        """节点执行异常钩子。"""


class MiddlewareChain:
    """中间件链——按注册顺序依次执行所有中间件的钩子。

    用法:
        chain = MiddlewareChain([LoggingMiddleware(), TimingMiddleware()])
        wrapped_fn = chain.wrap("classify", original_node_fn)
        graph.add_node("classify", wrapped_fn)
    """

    def __init__(self, middlewares: List[Middleware] | None = None):
        self.middlewares: List[Middleware] = middlewares or []

    def add(self, mw: Middleware) -> "MiddlewareChain":
        """添加一个中间件，支持链式调用。"""
        self.middlewares.append(mw)
        return self

    def wrap(
        self,
        node_name: str,
        node_fn: Callable[[CustomerServiceState], CustomerServiceState],
    ) -> Callable[[CustomerServiceState], CustomerServiceState]:
        """包裹节点函数，注入 before → execute → after / on_error 流程。"""
        middlewares = self.middlewares

        def wrapped(state: CustomerServiceState) -> CustomerServiceState:
            # --- before ---
            for mw in middlewares:
                mw.before_node(node_name, state)

            # --- execute ---
            try:
                result = node_fn(state)
            except Exception as exc:
                for mw in middlewares:
                    mw.on_error(node_name, state, exc)
                raise

            # --- after ---
            for mw in middlewares:
                mw.after_node(node_name, state, result)

            return result

        # 保留原函数名，方便调试
        wrapped.__name__ = f"mw_{node_name}"
        wrapped.__qualname__ = f"MiddlewareChain.wrap.<{node_name}>"
        return wrapped
