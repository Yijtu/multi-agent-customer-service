"""限流中间件。

对含 LLM 调用的节点做令牌桶限流，避免高并发时超出 API 速率限制。
"""

import threading
import time
from typing import Dict, Set

from middleware.base import Middleware
from state import CustomerServiceState

# 需要限流的节点（包含 LLM 调用的节点）
_LLM_NODES: Set[str] = {
    "classify",
    "extract_profile",
    "tech_support",
    "order_service",
    "product_consult",
    "quality_check",
}


class TokenBucket:
    """简单的令牌桶算法实现。"""

    def __init__(self, rate: float = 10.0, capacity: int = 20):
        """
        Args:
            rate: 每秒补充的令牌数。
            capacity: 桶的最大容量。
        """
        self.rate = rate
        self.capacity = capacity
        self._tokens = float(capacity)
        self._last_refill = time.monotonic()
        self._lock = threading.Lock()

    def acquire(self, timeout: float = 30.0) -> bool:
        """尝试获取一个令牌，最多等待 timeout 秒。"""
        deadline = time.monotonic() + timeout
        while True:
            with self._lock:
                self._refill()
                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    return True
            # 没有令牌，等一小段时间后重试
            if time.monotonic() >= deadline:
                return False
            time.sleep(0.1)

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self.capacity, self._tokens + elapsed * self.rate)
        self._last_refill = now


class RateLimiterMiddleware(Middleware):
    """限流中间件。

    Args:
        rate: 每秒允许的 LLM 调用次数（默认 10）。
        capacity: 令牌桶容量（默认 20，允许短时间突发）。
    """

    def __init__(self, rate: float = 10.0, capacity: int = 20):
        self._bucket = TokenBucket(rate=rate, capacity=capacity)

    def before_node(self, node_name: str, state: CustomerServiceState) -> None:
        if node_name not in _LLM_NODES:
            return

        acquired = self._bucket.acquire(timeout=30.0)
        if not acquired:
            raise RuntimeError(f"限流：节点 {node_name} 等待令牌超时（30s），请降低调用频率")

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
        pass  # 限流本身不处理异常
