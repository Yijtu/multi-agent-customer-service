"""性能监控中间件。

统计每个节点的执行耗时，写入 state["metadata"]["node_timings"]。
"""

import time
from typing import Any, Dict

from middleware.base import Middleware
from state import CustomerServiceState


class TimingMiddleware(Middleware):
    """节点耗时统计中间件。"""

    def __init__(self):
        # 临时存储各节点的开始时间（node_name → timestamp）
        self._start_times: Dict[str, float] = {}

    def before_node(self, node_name: str, state: CustomerServiceState) -> None:
        self._start_times[node_name] = time.perf_counter()

    def after_node(
        self,
        node_name: str,
        state: CustomerServiceState,
        result: CustomerServiceState,
    ) -> None:
        start = self._start_times.pop(node_name, None)
        if start is None:
            return

        elapsed = time.perf_counter() - start
        elapsed_ms = round(elapsed * 1000, 1)

        # 写入 metadata
        metadata = result.get("metadata") or {}
        timings = metadata.get("node_timings") or {}
        timings[node_name] = elapsed_ms
        metadata["node_timings"] = timings
        result["metadata"] = metadata

        print(f"   ⏱️ {node_name} 耗时: {elapsed_ms}ms")

    def on_error(
        self,
        node_name: str,
        state: CustomerServiceState,
        error: Exception,
    ) -> None:
        start = self._start_times.pop(node_name, None)
        if start is not None:
            elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
            print(f"   ⏱️ {node_name} 异常耗时: {elapsed_ms}ms")
