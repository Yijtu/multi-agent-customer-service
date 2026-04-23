"""多Agent客服系统主类。

使用 LangGraph 编排：意图分类 → 画像提取 → 业务Agent → 质量检查 → 响应 / 升级。

通过 InMemorySaver 为每个 thread_id 持久化 state，
实现跨轮次的 user_profile 累积。
"""

from datetime import datetime
import sqlite3
from typing import Any, Dict, List, Literal, Optional

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import StateGraph, START, END

from agents.classifier import IntentClassifier
from agents.order_service import OrderServiceAgent
from agents.product_consult import ProductConsultAgent
from agents.profile_extractor import ProfileExtractor
from agents.quality_checker import QualityChecker
from agents.tech_support import TechSupportAgent
from config import MIN_INTENT_CONFIDENCE, MIN_QUALITY_SCORE, CHECKPOINT_DB_PATH
from middleware import (
    MiddlewareChain,
    LoggingMiddleware,
    TimingMiddleware,
    ErrorHandlerMiddleware,
    RateLimiterMiddleware,
)
from state import CustomerServiceState


class CustomerServiceSystem:
    """多Agent客服系统。"""

    # handoff 最大次数，防止无限循环
    MAX_HANDOFFS = 2

    # Agent 名称 → Agent 实例的映射（在 __init__ 中初始化）
    _agent_map: Dict[str, Any] = {}

    def __init__(self):
        self.classifier = IntentClassifier()
        self.profile_extractor = ProfileExtractor()
        self.tech_agent = TechSupportAgent()
        self.order_agent = OrderServiceAgent()
        self.product_agent = ProductConsultAgent()
        self.quality_checker = QualityChecker()

        # Agent 名称 → 实例映射，用于 handoff 动态路由
        self._agent_map = {
            "tech_support": self.tech_agent,
            "order_service": self.order_agent,
            "product_consult": self.product_agent,
        }

        # 中间件链：日志 → 计时 → 异常捕获 → 限流
        self.mw_chain = MiddlewareChain([
            LoggingMiddleware(),
            TimingMiddleware(),
            ErrorHandlerMiddleware(),
            RateLimiterMiddleware(),
        ])

        # Checkpointer: 按 thread_id 跨轮次保存 state
        # 优先使用 SqliteSaver 持久化，失败时回退到 InMemorySaver
        try:
            self._sqlite_conn = sqlite3.connect(CHECKPOINT_DB_PATH, check_same_thread=False)
            self.checkpointer = SqliteSaver(conn=self._sqlite_conn)
        except Exception:
            print("⚠️ SqliteSaver 初始化失败，回退到 InMemorySaver")
            self._sqlite_conn = None
            self.checkpointer = InMemorySaver()
        self.graph = self._build_graph()

    # ==================== 节点函数 ====================

    def _classify_intent(self, state: CustomerServiceState) -> CustomerServiceState:
        """节点：意图分类。"""
        result = self.classifier.classify(state["user_message"])
        state["intent"] = result.get("intent", "escalate")
        state["confidence"] = result.get("confidence", 0.5)
        return state

    def _extract_profile(self, state: CustomerServiceState) -> CustomerServiceState:
        """节点：从当前消息中提取画像，合并到已有 profile。"""
        current = state.get("user_profile") or {}
        updated = self.profile_extractor.extract(state["user_message"], current)
        state["user_profile"] = updated
        return state

    def _run_business_agent(self, agent_name: str, state: CustomerServiceState) -> CustomerServiceState:
        """通用业务 Agent 执行器，支持 handoff。"""
        agent = self._agent_map[agent_name]
        response, handoff_target = agent.handle(
            state["user_message"],
            profile=state.get("user_profile"),
        )
        state["agent_response"] = response
        state["handoff_target"] = handoff_target
        if handoff_target:
            state["handoff_count"] = state.get("handoff_count", 0) + 1
        return state

    def _tech_support_handler(self, state: CustomerServiceState) -> CustomerServiceState:
        """节点：技术支持处理。"""
        return self._run_business_agent("tech_support", state)

    def _order_service_handler(self, state: CustomerServiceState) -> CustomerServiceState:
        """节点：订单服务处理。"""
        return self._run_business_agent("order_service", state)

    def _product_consult_handler(self, state: CustomerServiceState) -> CustomerServiceState:
        """节点:产品咨询处理。"""
        return self._run_business_agent("product_consult", state)

    def _escalate_handler(self, state: CustomerServiceState) -> CustomerServiceState:
        """节点：直接升级（分类阶段就决定转人工）。"""
        state["needs_escalation"] = True
        state["escalation_reason"] = "意图识别置信度低或用户要求人工服务"
        state["agent_response"] = """非常抱歉，您的问题需要人工客服来处理。

我已经为您转接人工客服，请稍候...

在等待期间，您也可以：
1. 拨打客服热线：400-xxx-xxxx
2. 发送邮件至：support@example.com
3. 工作日 9:00-18:00 在线客服响应更快

感谢您的耐心等待！"""
        return state

    def _quality_check(self, state: CustomerServiceState) -> CustomerServiceState:
        """节点：回复质量检查。"""
        result = self.quality_checker.check(
            state["user_message"],
            state["agent_response"],
        )
        state["quality_score"] = result.get("total_score", 0) / 100

        if result.get("needs_escalation", False) or state["quality_score"] < MIN_QUALITY_SCORE:
            state["needs_escalation"] = True
            state["escalation_reason"] = result.get("reason", "质量检查未通过")

        return state

    def _final_escalate(self, state: CustomerServiceState) -> CustomerServiceState:
        """节点：质量检查后的升级——保留原回复，附加人工客服提示。"""
        original = state["agent_response"]
        state["agent_response"] = f"""{original}

---
⚠️ 系统提示：由于此问题可能需要更专业的处理，我们建议您联系人工客服以获得更好的服务。"""
        return state

    # ==================== 路由函数 ====================

    def _route_to_agent(
        self, state: CustomerServiceState
    ) -> Literal["tech_support", "order_service", "product_consult", "escalate"]:
        """条件路由：根据 intent 和 confidence 决定走哪个Agent。"""
        if state["confidence"] < MIN_INTENT_CONFIDENCE:
            return "escalate"

        intent = state["intent"]
        if intent in ("tech_support", "order_service", "product_consult"):
            return intent
        return "escalate"

    def _should_escalate(
        self, state: CustomerServiceState
    ) -> Literal["escalate_final", "handoff_route", "respond"]:
        """条件路由：质量检查后决定是否升级或 handoff。"""
        # 检查是否需要 handoff
        handoff_target = state.get("handoff_target", "")
        handoff_count = state.get("handoff_count", 0)
        if handoff_target and handoff_count <= self.MAX_HANDOFFS:
            return "handoff_route"

        if state.get("needs_escalation", False):
            return "escalate_final"
        return "respond"

    def _handoff_route(self, state: CustomerServiceState) -> CustomerServiceState:
        """节点：handoff 路由——将请求转发给目标 Agent。"""
        target = state.get("handoff_target", "")
        if target and target in self._agent_map:
            print(f"   🔄 Hand-off 到 {target}")
            state["handoff_target"] = ""  # 清除标记防止重复 handoff
            return self._run_business_agent(target, state)
        return state

    # ==================== 图构建 ====================

    def _build_graph(self):
        """构建并编译 LangGraph 工作流。"""
        graph = StateGraph(CustomerServiceState)

        wrap = self.mw_chain.wrap
        graph.add_node("classify", wrap("classify", self._classify_intent))
        graph.add_node("extract_profile", wrap("extract_profile", self._extract_profile))
        graph.add_node("tech_support", wrap("tech_support", self._tech_support_handler))
        graph.add_node("order_service", wrap("order_service", self._order_service_handler))
        graph.add_node("product_consult", wrap("product_consult", self._product_consult_handler))
        graph.add_node("escalate", wrap("escalate", self._escalate_handler))
        graph.add_node("quality_check", wrap("quality_check", self._quality_check))
        graph.add_node("escalate_final", wrap("escalate_final", self._final_escalate))
        graph.add_node("handoff_route", wrap("handoff_route", self._handoff_route))

        # 起点 → 分类 → 画像提取 → 路由
        graph.add_edge(START, "classify")
        graph.add_edge("classify", "extract_profile")

        graph.add_conditional_edges(
            "extract_profile",
            self._route_to_agent,
            {
                "tech_support": "tech_support",
                "order_service": "order_service",
                "product_consult": "product_consult",
                "escalate": "escalate",
            },
        )

        graph.add_edge("tech_support", "quality_check")
        graph.add_edge("order_service", "quality_check")
        graph.add_edge("product_consult", "quality_check")
        graph.add_edge("escalate", END)

        graph.add_conditional_edges(
            "quality_check",
            self._should_escalate,
            {
                "escalate_final": "escalate_final",
                "handoff_route": "handoff_route",
                "respond": END,
            },
        )

        # handoff 后重新走质量检查
        graph.add_edge("handoff_route", "quality_check")
        graph.add_edge("escalate_final", END)

        # 编译时传入 checkpointer, 自动按 thread_id 保存/恢复 state
        return graph.compile(checkpointer=self.checkpointer)

    # ==================== 对外 API ====================

    def handle_message(
        self,
        message: str,
        thread_id: str = "default",
        chat_history: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """处理一条用户消息。

        Args:
            message: 用户输入。
            thread_id: 会话标识；相同 thread_id 的多次调用共享 state（含 user_profile）。
            chat_history: 历史对话（未接入，留作扩展）。

        Returns:
            本轮处理结果字典。
        """
        print(f"\n{'=' * 60}")
        print(f"💬 [{thread_id}] 用户: {message}")
        print("=" * 60)

        # 每轮都重置"请求级"字段（intent/quality_score/needs_escalation 等）。
        # 不要包含 user_profile —— 它需要跨轮累积，由 Checkpointer 恢复。
        turn_input: Dict[str, Any] = {
            "user_message": message,
            "chat_history": chat_history or [],
            "intent": "",
            "confidence": 0.0,
            "agent_response": "",
            "needs_escalation": False,
            "escalation_reason": "",
            "quality_score": 0.0,
            "handoff_target": "",
            "handoff_count": 0,
            "metadata": {"timestamp": datetime.now().isoformat()},
        }

        # thread_id 通过 configurable 传递给 Checkpointer
        config = {"configurable": {"thread_id": thread_id}}
        result = self.graph.invoke(turn_input, config=config)

        return {
            "response": result["agent_response"],
            "intent": result["intent"],
            "confidence": result["confidence"],
            "quality_score": result["quality_score"],
            "escalated": result["needs_escalation"],
            "profile": result.get("user_profile", {}),
            "metadata": result.get("metadata", {}),
        }

    def get_profile(self, thread_id: str) -> Dict[str, Any]:
        """查询指定 thread 当前累积的用户画像。"""
        config = {"configurable": {"thread_id": thread_id}}
        snapshot = self.graph.get_state(config)
        return snapshot.values.get("user_profile", {}) if snapshot else {}
