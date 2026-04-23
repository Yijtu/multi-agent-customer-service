"""结构化日志中间件。

记录每个节点的执行信息：节点名、输入摘要、输出摘要。
替代节点函数中散落的 print() 调用，统一日志风格。
"""

import logging
import time
from datetime import datetime
from typing import Any, Dict

from middleware.base import Middleware
from state import CustomerServiceState
from utils.tracer import create_trace_entry

logger = logging.getLogger("customer_service")


# 节点名称 → 显示用 emoji + 中文标签
_NODE_LABELS = {
    "classify": "🔍 意图分类",
    "extract_profile": "👤 画像提取",
    "tech_support": "🔧 技术支持",
    "order_service": "📦 订单服务",
    "product_consult": "🛍️ 产品咨询",
    "escalate": "👤 人工升级",
    "quality_check": "✅ 质量检查",
    "escalate_final": "⚠️ 质量升级",
}


class LoggingMiddleware(Middleware):
    """结构化日志中间件（含 trace 记录）。"""

    def __init__(self):
        self._start_times: Dict[str, float] = {}
        self._start_timestamps: Dict[str, str] = {}

    def before_node(self, node_name: str, state: CustomerServiceState) -> None:
        label = _NODE_LABELS.get(node_name, node_name)
        msg = f"{label} 处理中..."
        print(msg)
        logger.info("[%s] START | user_message=%s", node_name, _truncate(state.get("user_message", "")))
        self._start_times[node_name] = time.perf_counter()
        self._start_timestamps[node_name] = datetime.now().isoformat()

    def after_node(
        self,
        node_name: str,
        state: CustomerServiceState,
        result: CustomerServiceState,
    ) -> None:
        extras = _extract_summary(node_name, result)
        if extras:
            for line in extras:
                print(f"   {line}")
        logger.info("[%s] DONE | %s", node_name, " | ".join(extras) if extras else "ok")

        # 写入 trace
        start = self._start_times.pop(node_name, None)
        start_ts = self._start_timestamps.pop(node_name, "")
        end_ts = datetime.now().isoformat()
        duration_ms = round((time.perf_counter() - start) * 1000, 1) if start else 0

        metadata = result.get("metadata") or {}
        trace = metadata.get("trace") or []
        trace.append(create_trace_entry(
            node_name=node_name,
            start_time=start_ts,
            end_time=end_ts,
            duration_ms=duration_ms,
            status="ok",
            summary=" | ".join(extras) if extras else "",
        ))
        metadata["trace"] = trace
        result["metadata"] = metadata

    def on_error(
        self,
        node_name: str,
        state: CustomerServiceState,
        error: Exception,
    ) -> None:
        label = _NODE_LABELS.get(node_name, node_name)
        print(f"   ❌ {label} 异常: {error}")
        logger.error("[%s] ERROR | %s: %s", node_name, type(error).__name__, error)

        # 写入 error trace
        start = self._start_times.pop(node_name, None)
        start_ts = self._start_timestamps.pop(node_name, "")
        end_ts = datetime.now().isoformat()
        duration_ms = round((time.perf_counter() - start) * 1000, 1) if start else 0

        metadata = state.get("metadata") or {}
        trace = metadata.get("trace") or []
        trace.append(create_trace_entry(
            node_name=node_name,
            start_time=start_ts,
            end_time=end_ts,
            duration_ms=duration_ms,
            status="error",
            error=f"{type(error).__name__}: {error}",
        ))
        metadata["trace"] = trace
        state["metadata"] = metadata


def _truncate(text: str, max_len: int = 80) -> str:
    """截断长文本，用于日志摘要。"""
    return text[:max_len] + "..." if len(text) > max_len else text


def _extract_summary(node_name: str, state: CustomerServiceState) -> list[str]:
    """根据节点类型提取有意义的摘要信息。"""
    lines: list[str] = []
    if node_name == "classify":
        lines.append(f"意图: {state.get('intent', '?')} (置信度: {state.get('confidence', 0):.2f})")
    elif node_name == "extract_profile":
        lines.append(f"当前画像: {state.get('user_profile', {})}")
    elif node_name == "quality_check":
        lines.append(f"质量评分: {state.get('quality_score', 0):.2f}")
    return lines
