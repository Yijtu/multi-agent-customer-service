"""LangGraph 工作流共享状态定义。

State 是 LangGraph 节点之间传递数据的载体——
每个节点读取 state 的一部分，处理后写回 state，
下一个节点据此继续工作。

启用 Checkpointer 后，state 会按 thread_id 跨轮次保留，
user_profile 字段因此可以在多轮对话中累积。
"""

from typing import Any, Dict, List, Optional, TypedDict


class UserProfile(TypedDict, total=False):
    """用户画像——在多轮对话中逐步累积。

    使用 total=False 让所有字段可选:
    对话早期大部分字段都是空的，随着交互逐步填充。
    """

    budget: Optional[int]                  # 用户提到的预算（元）
    preferences: List[str]                 # 偏好关键词（降噪、续航...）
    mentioned_orders: List[str]            # 用户提过的订单号
    interested_products: List[str]         # 用户感兴趣的产品
    language: str                          # 用户语言代码（zh / en / ...）


class CustomerServiceState(TypedDict):
    """客服系统工作流状态。

    Fields:
        user_message: 用户输入的原始消息。
        chat_history: 历史对话记录，用于多轮对话上下文。
        user_profile: 跨轮次累积的用户画像。
        intent: 意图分类结果。
        confidence: 意图分类置信度，范围 [0.0, 1.0]。
        agent_response: 业务 Agent 生成的回复。
        needs_escalation: 是否需要升级到人工客服。
        escalation_reason: 升级原因。
        quality_score: 回复质量评分，范围 [0.0, 1.0]。
        handoff_target: Hand-off 目标 Agent（如 "order_service"），空串表示无 handoff。
        handoff_count: 当前轮次已发生的 handoff 次数，防止无限循环。
        metadata: 附加元信息（时间戳、trace_id 等）。
    """

    user_message: str
    chat_history: List[Dict[str, str]]
    user_profile: UserProfile
    intent: str
    confidence: float
    agent_response: str
    needs_escalation: bool
    escalation_reason: str
    quality_score: float
    handoff_target: str
    handoff_count: int
    metadata: Dict[str, Any]
