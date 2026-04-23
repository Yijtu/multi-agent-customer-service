"""调用链追踪工具。

在 state["metadata"]["trace"] 中记录完整的节点执行链路，
每个 trace entry 包含：节点名、开始时间、结束时间、耗时、状态、摘要。
"""

from datetime import datetime
from typing import Any, Dict, List, Optional


def create_trace_entry(
    node_name: str,
    start_time: str,
    end_time: str,
    duration_ms: float,
    status: str = "ok",
    summary: str = "",
    error: str = "",
) -> Dict[str, Any]:
    """创建一条 trace 记录。"""
    return {
        "node": node_name,
        "start_time": start_time,
        "end_time": end_time,
        "duration_ms": duration_ms,
        "status": status,
        "summary": summary,
        "error": error,
    }


def format_trace(metadata: Dict[str, Any]) -> str:
    """将 trace 列表格式化为可读字符串。

    Args:
        metadata: state["metadata"]，应包含 "trace" 键。

    Returns:
        格式化后的 trace 文本。
    """
    trace: List[Dict] = metadata.get("trace", [])
    if not trace:
        return "无追踪记录"

    lines = ["=" * 50, "📋 调用链追踪", "=" * 50]

    total_ms = 0.0
    for i, entry in enumerate(trace, 1):
        node = entry.get("node", "?")
        duration = entry.get("duration_ms", 0)
        status = entry.get("status", "ok")
        summary = entry.get("summary", "")
        error = entry.get("error", "")
        total_ms += duration

        status_icon = "✅" if status == "ok" else "❌"
        line = f"  {i}. {status_icon} {node} ({duration:.1f}ms)"
        if summary:
            line += f" | {summary}"
        if error:
            line += f" | ERROR: {error}"
        lines.append(line)

    lines.append("-" * 50)
    lines.append(f"  总耗时: {total_ms:.1f}ms | 节点数: {len(trace)}")
    lines.append("=" * 50)

    return "\n".join(lines)


def format_trace_for_ui(metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
    """将 trace 格式化为适合 Streamlit 展示的结构。

    Returns:
        每个元素包含: node, duration_ms, status, summary, error
    """
    return metadata.get("trace", [])
